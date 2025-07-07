# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the memory model classes in linker/__init__.py.
"""

import unittest
from unittest.mock import MagicMock, patch

from assembler.common.config import GlobalConfig
from assembler.memory_model import mem_info
from linker import VariableInfo, HBM, MemoryModel


class TestVariableInfo(unittest.TestCase):
    """Tests for the VariableInfo class."""

    def test_init(self):
        """Test initialization of VariableInfo."""
        var_info = VariableInfo("test_var", 42)
        self.assertEqual(var_info.var_name, "test_var")
        self.assertEqual(var_info.hbm_address, 42)
        self.assertEqual(var_info.uses, 0)
        self.assertEqual(var_info.last_kernel_used, -1)

    def test_init_default_values(self):
        """Test initialization with default values."""
        var_info = VariableInfo("test_var")
        self.assertEqual(var_info.var_name, "test_var")
        self.assertEqual(var_info.hbm_address, -1)
        self.assertEqual(var_info.uses, 0)
        self.assertEqual(var_info.last_kernel_used, -1)


class TestHBM(unittest.TestCase):
    """Tests for the HBM class."""

    def setUp(self):
        """Set up test fixtures."""
        self.hbm_size = 10
        self.hbm = HBM(self.hbm_size)

    def test_init(self):
        """Test initialization of HBM."""
        self.assertEqual(len(self.hbm.buffer), self.hbm_size)
        self.assertEqual(self.hbm.capacity, self.hbm_size)
        # Check that buffer is initialized with None values
        for item in self.hbm.buffer:
            self.assertIsNone(item)

    def test_init_invalid_size(self):
        """Test initialization with invalid size."""
        with self.assertRaises(ValueError):
            HBM(0)
        with self.assertRaises(ValueError):
            HBM(-1)

    def test_capacity_property(self):
        """Test the capacity property."""
        self.assertEqual(self.hbm.capacity, self.hbm_size)

    def test_buffer_property(self):
        """Test the buffer property."""
        buffer = self.hbm.buffer
        self.assertEqual(len(buffer), self.hbm_size)
        # Check that buffer is initialized with None values
        for item in buffer:
            self.assertIsNone(item)

    def test_force_allocate_valid(self):
        """Test forceAllocate with valid parameters."""
        var_info = VariableInfo("test_var")
        self.hbm.forceAllocate(var_info, 5)
        self.assertEqual(var_info.hbm_address, 5)
        self.assertEqual(self.hbm.buffer[5], var_info)

    def test_force_allocate_out_of_bounds(self):
        """Test forceAllocate with out of bounds address."""
        var_info = VariableInfo("test_var")
        with self.assertRaises(IndexError):
            self.hbm.forceAllocate(var_info, -1)
        with self.assertRaises(IndexError):
            self.hbm.forceAllocate(var_info, self.hbm_size)

    def test_force_allocate_already_allocated(self):
        """Test forceAllocate with already allocated variable."""
        var_info = VariableInfo("test_var", 3)
        with self.assertRaises(ValueError):
            self.hbm.forceAllocate(var_info, 5)

    def test_force_allocate_address_occupied_with_hbm(self):
        """Test forceAllocate with address occupied and HBM enabled."""
        with patch.object(GlobalConfig, "hasHBM", True):
            # Occupy address 5
            var_info1 = VariableInfo("var1")
            var_info1.uses = 1
            self.hbm.forceAllocate(var_info1, 5)

            # Try to allocate another variable at the same address
            var_info2 = VariableInfo("var2")
            with self.assertRaises(RuntimeError):
                self.hbm.forceAllocate(var_info2, 5)

    def test_force_allocate_address_occupied_without_hbm(self):
        """Test forceAllocate with address occupied and HBM disabled."""
        with patch.object(GlobalConfig, "hasHBM", False):
            # Occupy address 5
            var_info1 = VariableInfo("var1")
            var_info1.uses = 1
            self.hbm.forceAllocate(var_info1, 5)

            # Try to allocate another variable at the same address
            var_info2 = VariableInfo("var2")
            with self.assertRaises(RuntimeError):
                self.hbm.forceAllocate(var_info2, 5)

    def test_force_allocate_address_recyclable_with_hbm(self):
        """Test forceAllocate with recyclable address and HBM enabled."""
        with patch.object(GlobalConfig, "hasHBM", True):
            # Occupy address 5 with a variable that's not used
            var_info1 = VariableInfo("var1")
            var_info1.uses = 0
            var_info1.last_kernel_used = 1
            self.hbm.forceAllocate(var_info1, 5)

            # Allocate another variable at the same address with higher kernel index
            var_info2 = VariableInfo("var2")
            var_info2.last_kernel_used = 2
            self.hbm.forceAllocate(var_info2, 5)

            # Check that the new variable is at the address
            self.assertEqual(self.hbm.buffer[5], var_info2)

    def test_allocate(self):
        """Test allocate method."""
        var_info = VariableInfo("test_var")
        self.hbm.allocate(var_info)
        # The variable should be allocated at the first available address (0)
        self.assertEqual(var_info.hbm_address, 0)
        self.assertEqual(self.hbm.buffer[0], var_info)

    def test_allocate_full_memory(self):
        """Test allocate with full memory."""
        # Fill up the HBM
        for i in range(self.hbm_size):
            var_info = VariableInfo(f"var{i}")
            var_info.uses = 1
            self.hbm.forceAllocate(var_info, i)

        # Try to allocate another variable
        var_info = VariableInfo("test_var")
        with self.assertRaises(RuntimeError):
            self.hbm.allocate(var_info)

    def test_allocate_with_recycling(self):
        """Test allocate with recycling unused addresses."""
        with patch.object(GlobalConfig, "hasHBM", True):
            # Fill up the HBM
            for i in range(self.hbm_size):
                var_info = VariableInfo(f"var{i}")
                var_info.uses = 1 if i != 3 else 0
                var_info.last_kernel_used = 1
                self.hbm.forceAllocate(var_info, i)

            # Allocate a new variable - should reuse address 3
            var_info = VariableInfo("test_var")
            var_info.last_kernel_used = 2
            self.hbm.allocate(var_info)
            self.assertEqual(var_info.hbm_address, 3)


class TestMemoryModel(unittest.TestCase):
    """Tests for the MemoryModel class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock MemInfo
        self.mock_mem_info = MagicMock(spec=mem_info.MemInfo)

        # Set up mock input variables
        self.input_var = MagicMock(spec=mem_info.MemInfoVariable)
        self.input_var.var_name = "input_var"
        self.input_var.hbm_address = 1

        # Set up mock output variables
        self.output_var = MagicMock(spec=mem_info.MemInfoVariable)
        self.output_var.var_name = "output_var"
        self.output_var.hbm_address = 2

        # Set up mock keygen variables
        self.keygen_var = MagicMock(spec=mem_info.MemInfoVariable)
        self.keygen_var.var_name = "keygen_var"
        self.keygen_var.hbm_address = 3

        # Set up mock metadata variables
        self.meta_var = MagicMock(spec=mem_info.MemInfoVariable)
        self.meta_var.var_name = "meta_var"
        self.meta_var.hbm_address = 4

        # Configure mock mem_info
        self.mock_mem_info.inputs = [self.input_var]
        self.mock_mem_info.outputs = [self.output_var]
        self.mock_mem_info.keygens = [self.keygen_var]

        # Configure metadata
        mock_metadata = MagicMock()
        mock_metadata.intt_auxiliary_table = [self.meta_var]
        mock_metadata.intt_routing_table = []
        mock_metadata.ntt_auxiliary_table = []
        mock_metadata.ntt_routing_table = []
        mock_metadata.ones = []
        mock_metadata.twiddle = []
        mock_metadata.keygen_seeds = []
        self.mock_mem_info.metadata = mock_metadata

        # Create the memory model
        self.memory_model = MemoryModel(10, self.mock_mem_info)

    def test_init(self):
        """Test initialization of MemoryModel."""
        self.assertIsInstance(self.memory_model.hbm, HBM)
        self.assertEqual(self.memory_model.hbm.capacity, 10)

        # Check that variables are correctly initialized
        self.assertEqual(len(self.memory_model.variables), 0)

        # Check mem_info_vars
        self.assertIn("input_var", self.memory_model.mem_info_vars)
        self.assertIn("output_var", self.memory_model.mem_info_vars)
        self.assertIn("meta_var", self.memory_model.mem_info_vars)
        self.assertNotIn("keygen_var", self.memory_model.mem_info_vars)

        # Check mem_info_meta
        self.assertIn("meta_var", self.memory_model.mem_info_meta)

    def test_add_variable_new(self):
        """Test adding a new variable."""
        self.memory_model.addVariable("test_var")

        # Check that variable was added
        self.assertIn("test_var", self.memory_model.variables)
        var_info = self.memory_model.variables["test_var"]
        self.assertEqual(var_info.var_name, "test_var")
        self.assertEqual(var_info.uses, 1)

        # Since it's not in mem_info_vars, it should not have an HBM address yet
        self.assertEqual(var_info.hbm_address, -1)

    def test_add_variable_existing(self):
        """Test adding an existing variable."""
        # Add the variable first
        self.memory_model.addVariable("test_var")

        # Add it again
        self.memory_model.addVariable("test_var")

        # Check that the uses were incremented
        var_info = self.memory_model.variables["test_var"]
        self.assertEqual(var_info.uses, 2)

    def test_add_variable_from_mem_info(self):
        """Test adding a variable that's in mem_info."""
        self.memory_model.addVariable("input_var")

        # Check that variable was added
        self.assertIn("input_var", self.memory_model.variables)
        var_info = self.memory_model.variables["input_var"]
        self.assertEqual(var_info.var_name, "input_var")
        self.assertEqual(var_info.uses, 1)

        # It should have the HBM address from mem_info
        self.assertEqual(var_info.hbm_address, 1)

    def test_add_variable_from_fixed_addr_vars(self):
        """Test adding a variable that's in fixed_addr_vars."""
        self.memory_model.addVariable("output_var")

        # Check that variable was added
        self.assertIn("output_var", self.memory_model.variables)
        var_info = self.memory_model.variables["output_var"]

        # It should have infinite uses (float('inf'))
        self.assertEqual(var_info.uses, float("inf") + 1)

        # It should have the HBM address from mem_info
        self.assertEqual(var_info.hbm_address, 2)

    def test_use_variable(self):
        """Test using a variable."""
        # Add the variable first
        self.memory_model.addVariable("test_var")

        # Use the variable
        hbm_address = self.memory_model.useVariable("test_var", 1)

        # Check that uses were decremented
        var_info = self.memory_model.variables["test_var"]
        self.assertEqual(var_info.uses, 0)

        # Check that last_kernel_used was updated
        self.assertEqual(var_info.last_kernel_used, 1)

        # Check that hbm_address was allocated and returned
        self.assertGreaterEqual(hbm_address, 0)
        self.assertEqual(var_info.hbm_address, hbm_address)

        # Check that the variable is in the HBM buffer
        self.assertEqual(self.memory_model.hbm.buffer[hbm_address], var_info)

    def test_use_variable_already_allocated(self):
        """Test using a variable that already has an HBM address."""
        # Add a variable from mem_info which already has an HBM address
        self.memory_model.addVariable("input_var")

        # Use the variable
        hbm_address = self.memory_model.useVariable("input_var", 1)

        # Check that the returned HBM address is the one from mem_info
        self.assertEqual(hbm_address, 1)


if __name__ == "__main__":
    unittest.main()

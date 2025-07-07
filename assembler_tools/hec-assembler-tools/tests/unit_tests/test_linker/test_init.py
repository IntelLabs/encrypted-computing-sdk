# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Unit tests for the memory model classes in linker/__init__.py.
"""

import unittest
from unittest.mock import MagicMock, patch

from assembler.common.config import GlobalConfig
from assembler.memory_model import mem_info
from linker import VariableInfo, HBM, MemoryModel


class TestVariableInfo(unittest.TestCase):
    """@brief Tests for the VariableInfo class."""

    def test_init(self):
        """@brief Test initialization of VariableInfo.

        @test Verifies that VariableInfo is properly initialized with the given values
        """
        var_info = VariableInfo("test_var", 42)
        self.assertEqual(var_info.var_name, "test_var")
        self.assertEqual(var_info.hbm_address, 42)
        self.assertEqual(var_info.uses, 0)
        self.assertEqual(var_info.last_kernel_used, -1)

    def test_init_default_values(self):
        """@brief Test initialization with default values.

        @test Verifies that VariableInfo is properly initialized with default values
        """
        var_info = VariableInfo("test_var")
        self.assertEqual(var_info.var_name, "test_var")
        self.assertEqual(var_info.hbm_address, -1)
        self.assertEqual(var_info.uses, 0)
        self.assertEqual(var_info.last_kernel_used, -1)


class TestHBM(unittest.TestCase):
    """@brief Tests for the HBM class."""

    def setUp(self):
        """@brief Set up test fixtures."""
        self.hbm_size = 10
        self.hbm = HBM(self.hbm_size)

    def test_init(self):
        """@brief Test initialization of HBM.

        @test Verifies that HBM is properly initialized with the given size
        """
        self.assertEqual(len(self.hbm.buffer), self.hbm_size)
        self.assertEqual(self.hbm.capacity, self.hbm_size)
        # Check that buffer is initialized with None values
        for item in self.hbm.buffer:
            self.assertIsNone(item)

    def test_init_invalid_size(self):
        """@brief Test initialization with invalid size.

        @test Verifies that ValueError is raised for invalid sizes
        """
        with self.assertRaises(ValueError):
            HBM(0)
        with self.assertRaises(ValueError):
            HBM(-1)

    def test_capacity_property(self):
        """@brief Test the capacity property.

        @test Verifies that the capacity property returns the correct size
        """
        self.assertEqual(self.hbm.capacity, self.hbm_size)

    def test_buffer_property(self):
        """@brief Test the buffer property.

        @test Verifies that the buffer property returns the correct buffer
        """
        buffer = self.hbm.buffer
        self.assertEqual(len(buffer), self.hbm_size)
        # Check that buffer is initialized with None values
        for item in buffer:
            self.assertIsNone(item)

    def test_force_allocate_valid(self):
        """@brief Test forceAllocate with valid parameters.

        @test Verifies that a variable is properly allocated at the specified address
        """
        var_info = VariableInfo("test_var")
        self.hbm.forceAllocate(var_info, 5)
        self.assertEqual(var_info.hbm_address, 5)
        self.assertEqual(self.hbm.buffer[5], var_info)

    def test_force_allocate_out_of_bounds(self):
        """@brief Test forceAllocate with out of bounds address.

        @test Verifies that IndexError is raised for out-of-bounds addresses
        """
        var_info = VariableInfo("test_var")
        with self.assertRaises(IndexError):
            self.hbm.forceAllocate(var_info, -1)
        with self.assertRaises(IndexError):
            self.hbm.forceAllocate(var_info, self.hbm_size)

    def test_force_allocate_already_allocated(self):
        """@brief Test forceAllocate with already allocated variable.

        @test Verifies that ValueError is raised when variable is already allocated
        """
        var_info = VariableInfo("test_var", 3)
        with self.assertRaises(ValueError):
            self.hbm.forceAllocate(var_info, 5)

    def test_force_allocate_address_occupied_with_hbm(self):
        """@brief Test forceAllocate with address occupied and HBM enabled.

        @test Verifies that RuntimeError is raised when address is occupied
        """
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
        """@brief Test forceAllocate with address occupied and HBM disabled.

        @test Verifies that RuntimeError is raised when address is occupied
        """
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
        """@brief Test forceAllocate with recyclable address and HBM enabled.

        @test Verifies that an address can be recycled when the variable is not used
        """
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
        """@brief Test allocate method.

        @test Verifies that a variable is allocated at the first available address
        """
        var_info = VariableInfo("test_var")
        self.hbm.allocate(var_info)
        # The variable should be allocated at the first available address (0)
        self.assertEqual(var_info.hbm_address, 0)
        self.assertEqual(self.hbm.buffer[0], var_info)

    def test_allocate_full_memory(self):
        """@brief Test allocate with full memory.

        @test Verifies that RuntimeError is raised when memory is full
        """
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
        """@brief Test allocate with recycling unused addresses.

        @test Verifies that unused addresses can be recycled
        """
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
    """@brief Tests for the MemoryModel class."""

    def setUp(self):
        """@brief Set up test fixtures."""
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
        """@brief Test initialization of MemoryModel.

        @test Verifies that MemoryModel is properly initialized
        """
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
        """@brief Test adding a new variable.

        @test Verifies that a new variable is correctly added to the model
        """
        self.memory_model.addVariable("test_var")

        # Check that variable was added
        self.assertIn("test_var", self.memory_model.variables)
        var_info = self.memory_model.variables["test_var"]
        self.assertEqual(var_info.var_name, "test_var")
        self.assertEqual(var_info.uses, 1)

        # Since it's not in mem_info_vars, it should not have an HBM address yet
        self.assertEqual(var_info.hbm_address, -1)

    def test_add_variable_existing(self):
        """@brief Test adding an existing variable.

        @test Verifies that the uses count is incremented for an existing variable
        """
        # Add the variable first
        self.memory_model.addVariable("test_var")

        # Add it again
        self.memory_model.addVariable("test_var")

        # Check that the uses were incremented
        var_info = self.memory_model.variables["test_var"]
        self.assertEqual(var_info.uses, 2)

    def test_add_variable_from_mem_info(self):
        """@brief Test adding a variable that's in mem_info.

        @test Verifies that a variable from mem_info is correctly added with its HBM address
        """
        self.memory_model.addVariable("input_var")

        # Check that variable was added
        self.assertIn("input_var", self.memory_model.variables)
        var_info = self.memory_model.variables["input_var"]
        self.assertEqual(var_info.var_name, "input_var")
        self.assertEqual(var_info.uses, 1)

        # It should have the HBM address from mem_info
        self.assertEqual(var_info.hbm_address, 1)

    def test_add_variable_from_fixed_addr_vars(self):
        """@brief Test adding a variable that's in fixed_addr_vars.

        @test Verifies that a fixed-address variable is added with infinite uses
        """
        self.memory_model.addVariable("output_var")

        # Check that variable was added
        self.assertIn("output_var", self.memory_model.variables)
        var_info = self.memory_model.variables["output_var"]

        # It should have infinite uses (float('inf'))
        self.assertEqual(var_info.uses, float("inf") + 1)

        # It should have the HBM address from mem_info
        self.assertEqual(var_info.hbm_address, 2)

    def test_use_variable(self):
        """@brief Test using a variable.

        @test Verifies that using a variable decrements its uses count and allocates an HBM address
        """
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
        """@brief Test using a variable that already has an HBM address.

        @test Verifies that the existing HBM address is returned
        """
        # Add a variable from mem_info which already has an HBM address
        self.memory_model.addVariable("input_var")

        # Use the variable
        hbm_address = self.memory_model.useVariable("input_var", 1)

        # Check that the returned HBM address is the one from mem_info
        self.assertEqual(hbm_address, 1)


if __name__ == "__main__":
    unittest.main()

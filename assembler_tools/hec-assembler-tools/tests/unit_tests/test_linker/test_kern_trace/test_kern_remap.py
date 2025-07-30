# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_kern_remap.py
@brief Unit tests for the kern_remap module
"""

from unittest.mock import MagicMock

import pytest
from linker.instructions.cinst import BLoad, BOnes, CLoad, CStore, NLoad
from linker.instructions.minst import MLoad, MStore
from linker.kern_trace.kern_remap import remap_dinstrs_vars, remap_m_c_instrs_vars
from linker.kern_trace.kern_var import KernVar
from linker.kern_trace.kernel_op import KernelOp


class TestRemapDinstrsVars:
    """
    @class TestRemapDinstrsVars
    @brief Test cases for the remap_dinstrs_vars function
    """

    def _create_mock_kernel_op(self):
        """
        @brief Helper method to create a mock KernelOp with sorted variables
        """
        mock_kernel_op = MagicMock(spec=KernelOp)

        # Create mock KernVar objects for the kern_vars property
        mock_vars = [
            KernVar("input", 8192, 2),
            KernVar("output", 8192, 2),
            KernVar("temp", 8192, 2),
        ]

        # Configure the mock to return the sorted variables
        mock_kernel_op.kern_vars = mock_vars

        return mock_kernel_op

    def test_remap_ct_variables(self):
        """
        @brief Test remapping of CT (ciphertext) variables
        """
        # Arrange
        # Create mock DInstructions with CT variable names
        dinstr1 = MagicMock()
        dinstr1.var = "ct0_data"

        dinstr2 = MagicMock()
        dinstr2.var = "ct1_result"

        kernel_dinstrs = [dinstr1, dinstr2]

        # Create mock KernelOp
        mock_kernel_op = self._create_mock_kernel_op()

        # Act
        result = remap_dinstrs_vars(kernel_dinstrs, mock_kernel_op)

        # Assert
        assert dinstr1.var == "input_data"  # ct0 -> input (index 0)
        assert dinstr2.var == "output_result"  # ct1 -> output (index 1)
        assert result == {"ct0_data": "input_data", "ct1_result": "output_result"}

    def test_remap_pt_variables(self):
        """
        @brief Test remapping of PT (plaintext) variables
        """
        # Arrange
        # Create mock DInstructions with PT variable names
        dinstr1 = MagicMock()
        dinstr1.var = "pt0_data"

        dinstr2 = MagicMock()
        dinstr2.var = "pt2_result"

        kernel_dinstrs = [dinstr1, dinstr2]

        # Create mock KernelOp
        mock_kernel_op = self._create_mock_kernel_op()

        # Act
        result = remap_dinstrs_vars(kernel_dinstrs, mock_kernel_op)

        # Assert
        assert dinstr1.var == "input_data"  # pt0 -> input (index 0)
        assert dinstr2.var == "temp_result"  # pt2 -> temp (index 2)
        assert result == {"pt0_data": "input_data", "pt2_result": "temp_result"}

    def test_skip_non_ct_pt_variables(self):
        """
        @brief Test that variables with prefixes other than CT/PT are skipped
        """
        # Arrange
        # Create mock DInstructions with various variable names
        dinstr1 = MagicMock()
        dinstr1.var = "ct0_data"  # Should be remapped

        dinstr2 = MagicMock()
        dinstr2.var = "ntt_data"  # Should be skipped

        dinstr3 = MagicMock()
        dinstr3.var = "psi_data"  # Should be skipped

        kernel_dinstrs = [dinstr1, dinstr2, dinstr3]

        # Create mock KernelOp
        mock_kernel_op = self._create_mock_kernel_op()

        # Act
        result = remap_dinstrs_vars(kernel_dinstrs, mock_kernel_op)

        # Assert
        assert dinstr1.var == "input_data"  # ct0 -> input (index 0)
        assert dinstr2.var == "ntt_data"  # Unchanged
        assert dinstr3.var == "psi_data"  # Unchanged
        assert result == {
            "ct0_data": "input_data",
        }

    def test_case_insensitivity(self):
        """
        @brief Test that CT/PT prefixes are case-insensitive
        """
        # Arrange
        dinstr1 = MagicMock()
        dinstr1.var = "CT0_data"  # Uppercase CT

        dinstr2 = MagicMock()
        dinstr2.var = "Pt1_result"  # Mixed case PT

        kernel_dinstrs = [dinstr1, dinstr2]

        # Create mock KernelOp
        mock_kernel_op = self._create_mock_kernel_op()

        # Act
        result = remap_dinstrs_vars(kernel_dinstrs, mock_kernel_op)

        # Assert
        assert dinstr1.var == "input_data"  # CT0 -> input (index 0)
        assert dinstr2.var == "output_result"  # Pt1 -> output (index 1)
        assert result == {"CT0_data": "input_data", "Pt1_result": "output_result"}

    def test_error_when_no_underscore(self):
        """
        @brief Test error when variable name doesn't contain underscore
        """
        # Arrange
        dinstr = MagicMock()
        dinstr.var = "ct0data"  # No underscore

        kernel_dinstrs = [dinstr]
        mock_kernel_op = self._create_mock_kernel_op()

        # Act & Assert
        with pytest.raises(ValueError, match="does not contain items to split by '_'"):
            remap_dinstrs_vars(kernel_dinstrs, mock_kernel_op)

    def test_error_when_no_number_in_prefix(self):
        """
        @brief Test error when prefix doesn't contain a number
        """
        # Arrange
        dinstr = MagicMock()
        dinstr.var = "ct_data"  # No number in prefix

        kernel_dinstrs = [dinstr]
        mock_kernel_op = self._create_mock_kernel_op()

        # Act & Assert
        with pytest.raises(ValueError, match="does not contain a number after text"):
            remap_dinstrs_vars(kernel_dinstrs, mock_kernel_op)

    def test_error_when_index_out_of_range(self):
        """
        @brief Test error when index is out of range of kernel variables
        """
        # Arrange
        # Create a simple MagicMock instead of using spec=DInstruction
        dinstr = MagicMock()
        dinstr.var = "ct5_data"  # Index 5 is out of range (only 3 variables)

        kernel_dinstrs = [dinstr]
        mock_kernel_op = self._create_mock_kernel_op()

        # Act & Assert
        with pytest.raises(IndexError, match="out of range"):
            remap_dinstrs_vars(kernel_dinstrs, mock_kernel_op)


class TestRemapMCInstrsVars:
    """
    @class TestRemapMCInstrsVars
    @brief Test cases for the remap_m_c_instrs_vars function
    """

    def _create_remap_dict(self):
        """
        @brief Helper method to create a remap dictionary
        """
        return {"old_source": "new_source", "old_dest": "new_dest"}

    def test_remap_m_load_instructions(self):
        """
        @brief Test remapping variables in MLoad instructions
        """
        # Arrange
        mock_instr = MagicMock(spec=MLoad)
        mock_instr.source = "old_source"
        mock_instr.comment = ""

        kernel_instrs = [mock_instr]
        remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(kernel_instrs, remap_dict)

        # Assert
        assert mock_instr.source == "new_source"

    def test_remap_m_store_instructions(self):
        """
        @brief Test remapping variables in MStore instructions
        """
        # Arrange
        mock_instr = MagicMock(spec=MStore)
        mock_instr.dest = "old_dest"
        mock_instr.comment = "Store old_dest"

        kernel_instrs = [mock_instr]
        remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(kernel_instrs, remap_dict)

        # Assert
        assert mock_instr.dest == "new_dest"

    def test_remap_c_load_instructions(self):
        """
        @brief Test remapping variables in CLoad, BLoad, BOnes, and NLoad instructions
        """
        # Arrange
        c_instrs = []

        # Create mock instructions of each type
        for instr_class in [CLoad, BLoad, BOnes, NLoad]:
            mock_instr = MagicMock(spec=instr_class)
            mock_instr.source = "old_source"
            mock_instr.comment = ""
            c_instrs.append(mock_instr)

        remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(c_instrs, remap_dict)

        # Assert
        for instr in c_instrs:
            assert instr.source == "new_source"

    def test_remap_c_store_instructions(self):
        """
        @brief Test remapping variables in CStore instructions
        """
        # Arrange
        mock_instr = MagicMock(spec=CStore)
        mock_instr.dest = "old_dest"
        mock_instr.comment = "Store old_dest"

        kernel_instrs = [mock_instr]
        remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(kernel_instrs, remap_dict)

        # Assert
        assert mock_instr.dest == "new_dest"

    def test_skip_unmapped_variables(self):
        """
        @brief Test that variables not in the remap dictionary are not changed
        """
        # Arrange
        mock_load = MagicMock(spec=MLoad)
        mock_load.source = "unmapped_source"

        mock_store = MagicMock(spec=MStore)
        mock_store.dest = "unmapped_dest"

        kernel_instrs = [mock_load, mock_store]
        remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(kernel_instrs, remap_dict)

        # Assert
        assert mock_load.source == "unmapped_source"  # Unchanged
        assert mock_store.dest == "unmapped_dest"  # Unchanged

    def test_empty_remap_dict(self):
        """
        @brief Test function with an empty remap dictionary
        """
        # Arrange
        mock_instr = MagicMock(spec=MLoad)
        mock_instr.source = "source"

        kernel_instrs = [mock_instr]
        remap_dict = {}  # Empty dict

        # Act
        remap_m_c_instrs_vars(kernel_instrs, remap_dict)

        # Assert
        assert mock_instr.source == "source"  # Unchanged

    def test_invalid_instruction_type(self):
        """
        @brief Test error when instruction is not a valid M or C instruction
        """
        # Arrange
        mock_instr = MagicMock()  # Not a proper instruction type

        kernel_instrs = [mock_instr]
        remap_dict = self._create_remap_dict()

        # Act & Assert
        with pytest.raises(TypeError, match="not a valid M or C Instruction"):
            remap_m_c_instrs_vars(kernel_instrs, remap_dict)

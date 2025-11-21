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
from linker.instructions.cinst import CLoad, CStore
from linker.instructions.minst import MLoad, MStore
from linker.instructions.xinst import Mac
from linker.kern_trace.kern_remap import remap_cinstrs_vars_hbm, remap_dinstrs_vars, remap_m_c_instrs_vars, remap_xinstrs_vars
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
        mock_instr.var_name = "old_source"
        mock_instr.comment = ""

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.var_name == "new_source"

    def test_remap_m_store_instructions(self):
        """
        @brief Test remapping variables in MStore instructions
        """
        # Arrange
        mock_instr = MagicMock(spec=MStore)
        mock_instr.var_name = "old_dest"
        mock_instr.comment = "Store old_dest"

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.var_name == "new_dest"
        assert mock_instr.comment == "Store new_dest"

    def test_remap_c_load_instructions(self):
        """
        @brief Test remapping variables in CLoad, BLoad, BOnes, and NLoad instructions
        """
        # Arrange
        mock_instr = MagicMock(spec=CLoad)
        mock_instr.var_name = "old_source"
        mock_instr.comment = "old_source"

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.var_name == "new_source"
        assert mock_instr.comment == "new_source"

    def test_remap_c_store_instructions(self):
        """
        @brief Test remapping variables in CStore instructions
        """
        # Arrange
        mock_instr = MagicMock(spec=CStore)
        mock_instr.var_name = "old_dest"
        mock_instr.comment = "Store old_dest"

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.var_name == "new_dest"

    def test_skip_unmapped_variables(self):
        """
        @brief Test that variables not in the remap dictionary are not changed
        """
        # Arrange
        mock_load = MagicMock(spec=MLoad)
        mock_load.var_name = "unmapped_source"
        mock_load.comment = "Load unmapped_source"

        mock_store = MagicMock(spec=MStore)
        mock_store.var_name = "unmapped_dest"
        mock_store.comment = ""

        kernel_instrs = [mock_load, mock_store]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_m_c_instrs_vars(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_load.var_name == "unmapped_source"  # Unchanged
        assert mock_store.var_name == "unmapped_dest"  # Unchanged

    def test_empty_remap_dict(self):
        """
        @brief Test function with an empty remap dictionary
        """
        # Arrange
        mock_instr = MagicMock(spec=MLoad)
        mock_instr.var_name = "source"

        kernel_instrs = [mock_instr]
        hbm_remap_dict = {}  # Empty dict

        # Act
        remap_m_c_instrs_vars(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.var_name == "source"  # Unchanged

    def test_invalid_instruction_type(self):
        """
        @brief Test error when instruction is not a valid M or C instruction
        """
        # Arrange
        mock_instr = MagicMock()  # Not a proper instruction type

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act & Assert
        with pytest.raises(TypeError, match="not a valid M or C Instruction"):
            remap_m_c_instrs_vars(kernel_instrs, hbm_remap_dict)

    def test_invalid_var_name(self):
        """
        @brief Test comment gets updated even if var_name is not a valid M or C instruction
        """
        # Arrange
        mock_instr = MagicMock(spec=CLoad)
        mock_instr.var_name = "0"  # Not a var_name
        mock_instr.comment = "Store old_dest"

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_cinstrs_vars_hbm(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.var_name == "0"  # Unchanged
        assert mock_instr.comment == "Store new_dest"


class TestRemapCinstrsVarsHbm:
    """
    @class TestRemapCinstrsVarsHbm
    @brief Test cases for the remap_cinstrs_vars_hbm function
    """

    def _create_remap_dict(self):
        """
        @brief Helper method to create a remap dictionary
        """
        return {"old_var": "new_var", "input_data": "remapped_input"}

    def test_remap_cload_comment(self):
        """
        @brief Test remapping variables in CLoad instruction comments
        """
        # Arrange
        mock_instr = MagicMock(spec=CLoad)
        mock_instr.comment = "Load from old_var"

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_cinstrs_vars_hbm(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.comment == "Load from new_var"

    def test_remap_cstore_comment(self):
        """
        @brief Test remapping variables in CStore instruction comments
        """
        # Arrange
        mock_instr = MagicMock(spec=CStore)
        mock_instr.comment = "Store to input_data buffer"

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_cinstrs_vars_hbm(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.comment == "Store to remapped_input buffer"

    def test_remap_after_first_match(self):
        """
        @brief Test that remapping even after first match (break statement)
        """
        # Arrange
        mock_instr = MagicMock(spec=CLoad)
        mock_instr.comment = "old_var and old_var again"

        kernel_instrs = [mock_instr]
        # Dict with multiple keys that could match
        hbm_remap_dict = {"old_var": "new_var", "again": "never"}

        # Act
        remap_cinstrs_vars_hbm(kernel_instrs, hbm_remap_dict)

        # Assert
        # Only first match should be replaced due to break
        assert mock_instr.comment == "new_var and new_var again"
        assert "never" not in mock_instr.comment

    def test_skip_unmapped_variables(self):
        """
        @brief Test that variables not in remap dict are unchanged
        """
        # Arrange
        mock_instr = MagicMock(spec=CLoad)
        mock_instr.comment = "Load unmapped_var"

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_cinstrs_vars_hbm(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.comment == "Load unmapped_var"  # Unchanged

    def test_empty_remap_dict(self):
        """
        @brief Test with empty remap dictionary
        """
        # Arrange
        mock_instr = MagicMock(spec=CStore)
        mock_instr.comment = "Original comment"

        kernel_instrs = [mock_instr]
        hbm_remap_dict = {}

        # Act
        remap_cinstrs_vars_hbm(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_instr.comment == "Original comment"

    def test_invalid_instruction_type(self):
        """
        @brief Test error when instruction is not a CInstruction
        """
        # Arrange
        mock_instr = MagicMock()  # Not a CInstruction

        kernel_instrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act & Assert
        with pytest.raises(TypeError, match="not a valid CInstruction"):
            remap_cinstrs_vars_hbm(kernel_instrs, hbm_remap_dict)

    def test_multiple_instructions(self):
        """
        @brief Test remapping across multiple instructions
        """
        # Arrange
        mock_cload = MagicMock(spec=CLoad)
        mock_cload.comment = "Load old_var"

        mock_cstore = MagicMock(spec=CStore)
        mock_cstore.comment = "Store input_data"

        kernel_instrs = [mock_cload, mock_cstore]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_cinstrs_vars_hbm(kernel_instrs, hbm_remap_dict)

        # Assert
        assert mock_cload.comment == "Load new_var"
        assert mock_cstore.comment == "Store remapped_input"


class TestRemapXinstrsVars:
    """
    @class TestRemapXinstrsVars
    @brief Test cases for the remap_xinstrs_vars function
    """

    def _create_remap_dict(self):
        """
        @brief Helper method to create a remap dictionary
        """
        return {"source_var": "remapped_source", "dest_var": "remapped_dest"}

    def test_remap_move_instruction_comment(self):
        """
        @brief Test remapping variables in Move instruction comments
        """
        # Arrange
        from linker.instructions.xinst import Move

        mock_move = MagicMock(spec=Move)
        mock_move.comment = "Move from source_var"

        kernel_xinstrs = [mock_move]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_xinstrs_vars(kernel_xinstrs, hbm_remap_dict)

        # Assert
        assert mock_move.comment == "Move from remapped_source"

    def test_remap_xstore_instruction_comment(self):
        """
        @brief Test remapping variables in XStore instruction comments
        """
        # Arrange
        from linker.instructions.xinst import XStore

        mock_xstore = MagicMock(spec=XStore)
        mock_xstore.comment = "Store to dest_var"

        kernel_xinstrs = [mock_xstore]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_xinstrs_vars(kernel_xinstrs, hbm_remap_dict)

        # Assert
        assert mock_xstore.comment == "Store to remapped_dest"

    def test_remap_after_first_match(self):
        """
        @brief Test that remapping even after first match (break statement)
        """
        # Arrange
        from linker.instructions.xinst import Move

        mock_instr = MagicMock(spec=Move)
        mock_instr.comment = "source_var and source_var repeated"

        kernel_xinstrs = [mock_instr]
        hbm_remap_dict = {"source_var": "new_src", "repeated": "never_used"}

        # Act
        remap_xinstrs_vars(kernel_xinstrs, hbm_remap_dict)

        # Assert
        # Only first match replaced due to break
        assert mock_instr.comment == "new_src and new_src repeated"
        assert "never_used" not in mock_instr.comment

    def test_skip_unmapped_variables(self):
        """
        @brief Test that unmapped variables remain unchanged
        """
        # Arrange
        from linker.instructions.xinst import Move

        mock_instr = MagicMock(spec=Move)
        mock_instr.comment = "Move unmapped_var"

        kernel_xinstrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_xinstrs_vars(kernel_xinstrs, hbm_remap_dict)

        # Assert
        assert mock_instr.comment == "Move unmapped_var"

    def test_empty_remap_dict(self):
        """
        @brief Test with empty remap dictionary
        """
        # Arrange
        from linker.instructions.xinst import XStore

        mock_instr = MagicMock(spec=XStore)
        mock_instr.comment = "Original XStore comment"

        kernel_xinstrs = [mock_instr]
        hbm_remap_dict = {}

        # Act
        remap_xinstrs_vars(kernel_xinstrs, hbm_remap_dict)

        # Assert
        assert mock_instr.comment == "Original XStore comment"

    def test_invalid_instruction_type(self):
        """
        @brief Test error when instruction is not an XInstruction
        """
        # Arrange
        mock_instr = MagicMock()  # Not an XInstruction

        kernel_xinstrs = [mock_instr]
        hbm_remap_dict = self._create_remap_dict()

        # Act & Assert
        with pytest.raises(TypeError, match="not a valid X Instruction"):
            remap_xinstrs_vars(kernel_xinstrs, hbm_remap_dict)

    def test_multiple_instructions(self):
        """
        @brief Test remapping across multiple X instructions
        """
        # Arrange
        from linker.instructions.xinst import Move, XStore

        mock_move = MagicMock(spec=Move)
        mock_move.comment = "Move source_var"

        mock_xstore = MagicMock(spec=XStore)
        mock_xstore.comment = "Store dest_var"

        kernel_xinstrs = [mock_move, mock_xstore]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_xinstrs_vars(kernel_xinstrs, hbm_remap_dict)

        # Assert
        assert mock_move.comment == "Move remapped_source"
        assert mock_xstore.comment == "Store remapped_dest"

    def test_non_move_xstore_instructions_ignored(self):
        """
        @brief Test that non-Move/XStore X instructions are not processed
        """
        # Create a mock XInstruction that's not Move or XStore
        mock_other = MagicMock(spec=Mac)
        # Remove Move and XStore from isinstance check
        type(mock_other).__name__ = "OtherXInst"
        mock_other.comment = "source_var reference"

        kernel_xinstrs = [mock_other]
        hbm_remap_dict = self._create_remap_dict()

        # Act
        remap_xinstrs_vars(kernel_xinstrs, hbm_remap_dict)

        # Assert
        # Comment should be unchanged since it's not Move or XStore
        assert mock_other.comment == "source_var reference"

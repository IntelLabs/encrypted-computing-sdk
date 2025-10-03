# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief Module for handling kernel operation tracing and analysis."""

from enum import Enum

from linker.instructions import cinst, minst
from linker.instructions.cinst.cinstruction import CInstruction
from linker.instructions.minst.minstruction import MInstruction
from linker.instructions.xinst.xinstruction import XInstruction


class InstrAct(Enum):
    """@class InstrAct
    @brief Enum for actions to be taken on instructions.
    """

    KEEP_HBM = 0
    KEEP_SPAD = 1
    KEEP_BANK0 = 2
    SKIP = 3


class MinstrMapEntry:
    """@class MinstrMapEntry
    @brief Structure for mapping MInstruction to its SPAD address and action.
    """

    def __init__(self, spad_addr: int, minstr: MInstruction, action: InstrAct):
        self.spad_addr = spad_addr
        self.minstr = minstr
        self.action = action


class CinstrMapEntry:
    """@class CinstrMapEntry
    @brief Structure for mapping CInstruction to its register name and action.
    """

    def __init__(self, reg_name: str, cinstr: CInstruction, action: InstrAct):
        self.reg_name = reg_name
        self.cinstr = cinstr
        self.action = action


class KernelInfo:
    """
    @class KernelInfo
    @brief Structure for kernel files.

    @details This class holds information about the kernel files used in the linker.

    @brief Dictionary for remapping variable names in DInstructions.

    """

    # Dictionary with keys 'directory', 'prefix', 'minst', 'cinst', 'xinst', and optional 'mem'
    _file_paths: dict[str, str]

    _minstrs: list[MInstruction]
    _cinstrs: list[CInstruction]
    _xinstrs: list[XInstruction]

    _hbm_remap_dict: dict[str, str]
    # Maps bundle -> (ifetch_index, [variable_names])
    _fetch_cstores_map: dict[int, tuple[int, list[str]]]
    _spad_size: int  # Reflects the spad memory used by the kernel
    _first_vars_bank0: dict[str, str] = {}

    def __init__(self, config: dict):
        """
        @brief Initializes KernelInfo with a configuration dictionary.

        @param config: Dictionary with keys 'directory', 'prefix', 'minst', 'cinst', 'xinst', and optional 'mem'.
        """
        self.file_paths = config

        self._hbm_remap_dict = {}
        self._spad_size = 0  # Reflects the spad memory used by the kernel
        self._fetch_cstores_map = {}
        self._first_vars_bank0 = {}

        self._minstrs = []  # Placeholder for kernel minst instructions
        self._minstrs_map: list[MinstrMapEntry] = []
        self._cinstrs = []  # Placeholder for kernel cinst instructions
        self._cinstrs_map: list[CinstrMapEntry] = []
        self._xinstrs = []  # Placeholder for kernel xinst instructions

    @property
    def files(self) -> list[str]:
        """
        @brief Returns a list of file names associated with the kernel.
        """
        return [self.minst, self.cinst, self.xinst] + ([self.mem] if self.mem else [])

    @property
    def hbm_remap_dict(self) -> dict[str, str]:
        """
        @brief Returns the remap dictionary for variable names in DInstructions.
        """
        return self._hbm_remap_dict

    @hbm_remap_dict.setter
    def hbm_remap_dict(self, value: dict[str, str]):
        """
        @brief Sets the remap dictionary for variable names in DInstructions.

        @param value: Dictionary mapping old variable names to new variable names.
        """
        if not isinstance(value, dict):
            raise TypeError("Remap dictionary must be of type dict.")
        self._hbm_remap_dict = value

    @property
    def fetch_cstores_map(self) -> dict[int, tuple[int, list[str]]]:
        """
        @brief Returns the cstore maps for bundle to variable names.
        """
        return self._fetch_cstores_map

    @fetch_cstores_map.setter
    def fetch_cstores_map(self, value: dict[int, tuple[int, list[str]]]):
        """
        @brief Sets the cstore maps for bundle to variable names.

        @param value: Dictionary mapping bundle number to list of variable names.
        """
        if not isinstance(value, dict):
            raise TypeError("CStore maps must be of type dict.")
        self._fetch_cstores_map = value

    @property
    def spad_size(self) -> int:
        """
        @brief Returns the scratchpad offset.

        This offset is used to adjust scratchpad addresses in instructions.
        """
        return self._spad_size

    @spad_size.setter
    def spad_size(self, value: int):
        """
        @brief Sets the scratchpad offset.

        @param value: The new scratchpad offset to set.
        """
        if not isinstance(value, int):
            raise TypeError("Scratchpad offset must be an integer.")
        self._spad_size = value

    @property
    def directory(self) -> str:
        """
        @brief Returns the directory where the kernel files are located.
        """
        return self.file_paths["directory"]

    @property
    def prefix(self) -> str:
        """
        @brief Returns the prefix for the kernel files.
        """
        return self.file_paths["prefix"]

    @property
    def minst(self) -> str:
        """
        @brief Returns the MInstruction file name.
        """
        return self.file_paths["minst"]

    @property
    def cinst(self) -> str:
        """
        @brief Returns the CInstruction file name.
        """
        return self.file_paths["cinst"]

    @property
    def xinst(self) -> str:
        """
        @brief Returns the XInstruction file name.
        """
        return self.file_paths["xinst"]

    @property
    def mem(self) -> str | None:
        """
        @brief Returns the memory file name, if available.

        @return Optional[str]: The memory file name or None if not set.
        """
        return self.file_paths.get("mem")

    @property
    def minstrs(self) -> list[MInstruction]:
        """
        @brief Returns the kernel minst instructions if loaded.

        @return Optional[dict]: The dict of kernel minst instructions.
        """
        return self._minstrs

    @minstrs.setter
    def minstrs(self, value: list[MInstruction]):
        """
        @brief Sets the kernel minst instructions.

        @param value: The dict of kernel minst instructions to set.
        """
        if not isinstance(value, list):
            raise TypeError("minstrs must be a list.")
        self._minstrs = value
        self._fill_minstrs_map()

    @property
    def minstrs_map(self) -> list:
        """
        @brief Returns the actions to be taken on minst instructions.

        @return list: The list of actions for minst instructions.
        """
        return self._minstrs_map

    @minstrs_map.setter
    def minstrs_map(self, value: list):
        """
        @brief Sets the actions to be taken on minst instructions.

        @param value: The list of actions for minst instructions to set.
        """
        if not isinstance(value, list):
            raise TypeError("minstrs_map must be a list.")
        self._minstrs_map = value

    @property
    def cinstrs_map(self) -> list:
        """
        @brief Returns the actions to be taken on cinst instructions.

        @return list: The list of actions for cinst instructions.
        """
        return self._cinstrs_map

    @cinstrs_map.setter
    def cinstrs_map(self, value: list):
        """
        @brief Sets the actions to be taken on cinst instructions.

        @param value: The list of actions for cinst instructions to set.
        """
        if not isinstance(value, list):
            raise TypeError("cinstrs_map must be a list.")
        self._cinstrs_map = value

    @property
    def cinstrs(self) -> list[CInstruction]:
        """
        @brief Returns the kernel cinst instructions if loaded.

        @return Optional[list]: The list of kernel cinst instructions.
        """
        return self._cinstrs

    @cinstrs.setter
    def cinstrs(self, value: list[CInstruction]):
        """
        @brief Sets the kernel cinst instructions.

        @param value: The list of kernel cinst instructions to set.
        """
        if not isinstance(value, list):
            raise TypeError("cinstrs must be a list.")
        self._cinstrs = value
        self._fill_cinstrs_map()

    @property
    def xinstrs(self) -> list[XInstruction]:
        """
        @brief Returns the kernel xinst instructions if loaded.

        @return Optional[list]: The list of kernel xinst instructions.
        """
        return self._xinstrs

    @xinstrs.setter
    def xinstrs(self, value: list[XInstruction]):
        """
        @brief Sets the kernel xinst instructions.

        @param value: The list of kernel xinst instructions to set.
        """
        if not isinstance(value, list):
            raise TypeError("xinstrs must be a list.")
        self._xinstrs = value

    def _fill_minstrs_map(self):
        """
        @brief Fills _minstrs_map with MinstrMapEntry for each instruction in _minstrs.
        If instruction is MSyncc, spad_addr is set to -1.
        """
        self._minstrs_map = []
        for minstr in self._minstrs:
            if isinstance(minstr, minst.MSyncc):
                spad_addr = -1
            else:
                spad_addr = minstr.spad_address
            entry = MinstrMapEntry(spad_addr, minstr, InstrAct.KEEP_HBM)
            self._minstrs_map.append(entry)

    def _fill_cinstrs_map(self):
        """
        @brief Fills _cinstrs_map with CinstrMapEntry for each instruction in _cinstrs.
        If instruction is CSyncc, reg_name is set to ''.
        """
        self._cinstrs_map = []
        for cinstr in self._cinstrs:
            if isinstance(cinstr, (cinst.CLoad, cinst.BLoad, cinst.BOnes, cinst.NLoad)):
                reg_name = cinstr.tokens[2]
            else:
                reg_name = ""
            entry = CinstrMapEntry(reg_name, cinstr, InstrAct.KEEP_SPAD)
            self._cinstrs_map.append(entry)

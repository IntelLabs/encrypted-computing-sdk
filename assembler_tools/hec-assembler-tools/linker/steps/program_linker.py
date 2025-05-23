
from linker import MemoryModel
from linker.instructions import minst, cinst, xinst
from assembler.common.config import GlobalConfig
from assembler.isa_spec import cinst as ISACInst

class LinkedProgram:
    """
    Encapsulates a linked program.

    This class offers facilities to track and link kernels, and
    outputs the linked program to specified output streams as kernels
    are linked.

    The program itself is not contained in this object.
    """

    def __init__(self,
                 program_minst_ostream,
                 program_cinst_ostream,
                 program_xinst_ostream,
                 mem_model: MemoryModel,
                 supress_comments: bool):
        """
        Initializes a LinkedProgram object.

        Parameters:
            program_minst_ostream: Output stream for MInst instructions.
            program_cinst_ostream: Output stream for CInst instructions.
            program_xinst_ostream: Output stream for XInst instructions.
            mem_model (MemoryModel): Correctly initialized linker memory model. It must already contain the
                                     variables used throughout the program and their usage.
                                     This memory model will be modified by this object when linking kernels.
            supress_comments (bool): Whether to suppress comments in the output.
        """
        self.__minst_ostream     = program_minst_ostream
        self.__cinst_ostream     = program_cinst_ostream
        self.__xinst_ostream     = program_xinst_ostream
        self.__mem_model         = mem_model
        self.__supress_comments  = supress_comments
        self.__bundle_offset     = 0
        self.__minst_line_offset = 0
        self.__cinst_line_offset = 0
        self.__xinst_line_offset = 0
        self.__kernel_count      = 0  # Number of kernels linked into this program
        self.__is_open           = True  # Tracks whether this program is still accepting kernels to link

    @property
    def isOpen(self) -> bool:
        """
        Checks if the program is open for linking new kernels.

        Returns:
            bool: True if the program is open, False otherwise.
        """
        return self.__is_open

    @property
    def supressComments(self) -> bool:
        """
        Checks if comments are suppressed in the output.

        Returns:
            bool: True if comments are suppressed, False otherwise.
        """
        return self.__supress_comments

    def close(self):
        """
        Completes the program by terminating the queues with the correct exit code.

        Program will not accept new kernels to link after this call.

        Raises:
            RuntimeError: If the program is already closed.
        """
        if not self.isOpen:
            raise RuntimeError('Program is already closed.')

        # Add closing `cexit`
        tokens = [str(self.__cinst_line_offset), cinst.CExit.name]
        cexit_cinstr = cinst.CExit(tokens)
        print(f'{cexit_cinstr.tokens[0]}, {cexit_cinstr.to_line()}', file=self.__cinst_ostream)

        # Add closing msyncc
        tokens = [str(self.__minst_line_offset), minst.MSyncc.name, str(self.__cinst_line_offset + 1)]
        cmsyncc_minstr = minst.MSyncc(tokens)
        print(f'{cmsyncc_minstr.tokens[0]}, {cmsyncc_minstr.to_line()}', end="", file=self.__minst_ostream)
        if not self.supressComments:
            print(' # terminating MInstQ', end="", file=self.__minst_ostream)
        print(file=self.__minst_ostream)

        # Program has been closed
        self.__is_open = False

    def __validateHBMAddress(self, var_name: str, hbm_address: int):
        """
        Validates the HBM address for a variable.

        Parameters:
            var_name (str): The name of the variable.
            hbm_address (int): The HBM address to validate.

        Raises:
            RuntimeError: If the HBM address is invalid or does not match the declared address.
        """
        if hbm_address < 0:
            raise RuntimeError(f'Invalid negative HBM address for variable "{var_name}".')
        if var_name in self.__mem_model.mem_info_vars:
            if self.__mem_model.mem_info_vars[var_name].hbm_address != hbm_address:
                raise RuntimeError(('Declared HBM address ({}) of mem Variable "{}"'
                                    ' differs from allocated HBM address ({}).').format(self.__mem_model.mem_info_vars[var_name].hbm_address,
                                                                                        var_name,
                                                                                        hbm_address))

    def __validateSPADAddress(self, var_name: str, spad_address: int):
        # only available when no HBM
        assert not GlobalConfig.hasHBM

        # this method will validate the variable SPAD address against the
        # original HBM address, since ther is no HBM
        if spad_address < 0:
            raise RuntimeError(f'Invalid negative SPAD address for variable "{var_name}".')
        if var_name in self.__mem_model.mem_info_vars:
            if self.__mem_model.mem_info_vars[var_name].hbm_address != spad_address:
                raise RuntimeError(('Declared HBM address ({}) of mem Variable "{}"'
                                    ' differs from allocated HBM address ({}).').format(self.__mem_model.mem_info_vars[var_name].hbm_address,
                                                                                        var_name,
                                                                                        spad_address))
            
    def __updateMInsts(self, kernel_minstrs: list):
        """
        Updates the MInsts in the kernel to offset to the current expected
        synchronization points, and convert variable placeholders/names into
        the corresponding HBM address.

        All MInsts in the kernel are expected to synchronize with CInsts starting at line 0.
        Does not change the `LinkedProgram` object.

        Parameters:
            kernel_minstrs (list): List of MInstructions to update.
        """
        for minstr in kernel_minstrs:
            # Update msyncc
            if isinstance(minstr, minst.MSyncc):
                minstr.target = minstr.target + self.__cinst_line_offset
            # Change mload variable names into HBM addresses
            if isinstance(minstr, minst.MLoad):
                var_name = minstr.source
                hbm_address = self.__mem_model.useVariable(var_name, self.__kernel_count)
                self.__validateHBMAddress(var_name, hbm_address)
                minstr.source = str(hbm_address)
                minstr.comment = f" var: {var_name} - HBM({hbm_address})" + f";{minstr.comment}" if minstr.comment else ""
            # Change mstore variable names into HBM addresses
            if isinstance(minstr, minst.MStore):
                var_name = minstr.dest
                hbm_address = self.__mem_model.useVariable(var_name, self.__kernel_count)
                self.__validateHBMAddress(var_name, hbm_address)
                minstr.dest = str(hbm_address)
                minstr.comment = f" var: {var_name} - HBM({hbm_address})" + f";{minstr.comment}" if minstr.comment else ""

    def __updateCInsts(self, kernel_cinstrs: list):
        """
        Updates the CInsts in the kernel to offset to the current expected bundle
        and synchronization points.

        All CInsts in the kernel are expected to start at bundle 0, and to
        synchronize with MInsts starting at line 0.
        Does not change the `LinkedProgram` object.

        Parameters:
            kernel_cinstrs (list): List of CInstructions to update.
        """

        if not GlobalConfig.hasHBM:
            # Remove csyncm instructions
            i = 0
            current_bundle = 0
            csyncm_count = 0 # Used by 1st code block: plz remove if second code block ends up being the one used
            while i < len(kernel_cinstrs):
                cinstr = kernel_cinstrs[i]
                cinstr.tokens[0] = i # Update the line number

                #------------------------------
                # This code block will remove csyncm instructions and keep track,
                # later adding their throughput into a cnop instruction before
                # a new bundle is fetched.

                if isinstance(cinstr, cinst.CNop):
                    # Add the missing cycles to any cnop we encounter up to this point
                    cinstr.cycles += (csyncm_count * ISACInst.CSyncM.Throughput)
                    csyncm_count = 0 # Idle cycles to account for the csyncm have been added

                if isinstance(cinstr, (cinst.IFetch, cinst.NLoad, cinst.BLoad)):
                    if csyncm_count > 0:
                        # Extra cycles needed before scheduling next bundle
                        cinstr_nop = cinst.CNop([i, cinst.CNop.name, str(csyncm_count * ISACInst.CSyncM.Throughput - 1)]) # Subtract 1 because cnop n, waits for n+1 cycles
                        kernel_cinstrs.insert(i, cinstr_nop)
                        csyncm_count = 0 # Idle cycles to account for the csyncm have been added
                        i += 1
                    if isinstance(cinstr, cinst.IFetch):
                        current_bundle = cinstr.bundle + 1
                        cinstr.tokens[0] = i # Update the line number

                if isinstance(cinstr, cinst.CSyncm):
                    # Remove instruction
                    kernel_cinstrs.pop(i)
                    if current_bundle > 0:
                        csyncm_count += 1
                else:
                    i += 1 # Next instruction

                #------------------------------
                # This code block differs from previous in that csyncm instructions
                # are replaced in place by cnops with the corresponding throughput.
                # This may result in several continuous cnop instructions, so,
                # the cnop merging code afterwards is needed to remove this side effect
                # if contiguous cnops are not desired.

                # if isinstance(cinstr, cinst.IFetch):
                #     current_bundle = cinstr.bundle + 1
                #
                # if isinstance(cinstr, cinst.CSyncm):
                #     # replace instruction by cnop
                #     kernel_cinstrs.pop(i)
                #     if current_bundle > 0:
                #         cinstr_nop = cinst.CNop([i, cinst.CNop.name, str(ISACInst.CSyncM.Throughput)]) # Subtract 1 because cnop n, waits for n+1 cycles
                #         kernel_cinstrs.insert(i, cinstr_nop)
                #
                # i += 1 # next instruction

            # Merge continuous cnop
            i = 0
            while i < len(kernel_cinstrs):
                cinstr = kernel_cinstrs[i]
                cinstr.tokens[0] = i # Update the line number

                if isinstance(cinstr, cinst.CNop):
                    # Do look ahead
                    if i + 1 < len(kernel_cinstrs):
                        if isinstance(kernel_cinstrs[i + 1], cinst.CNop):
                            kernel_cinstrs[i + 1].cycles += (cinstr.cycles + 1) # Add 1 because cnop n, waits for n+1 cycles
                            kernel_cinstrs.pop(i)
                            i -= 1
                i += 1
                
        for cinstr in kernel_cinstrs:
            # Update ifetch
            if isinstance(cinstr, cinst.IFetch):
                cinstr.bundle = cinstr.bundle + self.__bundle_offset
            # Update xinstfetch
            if isinstance(cinstr, cinst.XInstFetch):
                raise NotImplementedError('`xinstfetch` not currently supported by linker.')
            # Update csyncm
            if isinstance(cinstr, cinst.CSyncm):
                cinstr.target = cinstr.target + self.__minst_line_offset

            if not GlobalConfig.hasHBM:
                # update all SPAD instruction variable names to be SPAD addresses
                # change xload variable names into SPAD addresses
                if isinstance(cinstr, (cinst.BLoad, cinst.BOnes, cinst.CLoad, cinst.NLoad)):
                    var_name = cinstr.source
                    hbm_address = self.__mem_model.useVariable(var_name, self.__kernel_count)
                    self.__validateSPADAddress(var_name, hbm_address)
                    cinstr.source = str(hbm_address)
                    cinstr.comment = f" var: {var_name} - HBM({hbm_address})" + f";{cinstr.comment}" if cinstr.comment else ""
                if isinstance(cinstr, cinst.CStore):
                    var_name = cinstr.dest
                    hbm_address = self.__mem_model.useVariable(var_name, self.__kernel_count)
                    self.__validateSPADAddress(var_name, hbm_address)
                    cinstr.dest = str(hbm_address)
                    cinstr.comment = f" var: {var_name} - HBM({hbm_address})" + f";{cinstr.comment}" if cinstr.comment else ""

    def __updateXInsts(self, kernel_xinstrs: list) -> int:
        """
        Updates the XInsts in the kernel to offset to the current expected bundle.

        All XInsts in the kernel are expected to start at bundle 0.
        Does not change the `LinkedProgram` object.

        Parameters:
            kernel_xinstrs (list): List of XInstructions to update.

        Returns:
            int: The last bundle number after updating.
        """
        last_bundle = self.__bundle_offset
        for xinstr in kernel_xinstrs:
            xinstr.bundle = xinstr.bundle + self.__bundle_offset
            if last_bundle > xinstr.bundle:
                raise RuntimeError(f'Detected invalid bundle. Instruction bundle is less than previous: "{xinstr.to_line()}"')
            last_bundle = xinstr.bundle
        return last_bundle

    def linkKernel(self,
                   kernel_minstrs: list,
                   kernel_cinstrs: list,
                   kernel_xinstrs: list):
        """
        Links a specified kernel (given by its three instruction queues) into this
        program.

        The adjusted kernels will be appended into the output streams specified during
        construction of this object.

        Parameters:
            kernel_minstrs (list): List of MInstructions for the MInst Queue corresponding to the kernel to link.
                                   These instructions will be modified by this method.
            kernel_cinstrs (list): List of CInstructions for the CInst Queue corresponding to the kernel to link.
                                   These instructions will be modified by this method.
            kernel_xinstrs (list): List of XInstructions for the XInst Queue corresponding to the kernel to link.
                                   These instructions will be modified by this method.

        Raises:
            RuntimeError: If the program is closed and does not accept new kernels.
        """
        if not self.isOpen:
            raise RuntimeError('Program is closed and does not accept new kernels.')

        # No minsts without HBM
        if not GlobalConfig.hasHBM:
            kernel_minstrs = []

        self.__updateMInsts(kernel_minstrs)
        self.__updateCInsts(kernel_cinstrs)
        self.__bundle_offset = self.__updateXInsts(kernel_xinstrs) + 1

        # Append the kernel to the output

        for xinstr in kernel_xinstrs:
            print(xinstr.to_line(), end="", file=self.__xinst_ostream)
            if not self.supressComments and xinstr.comment:
                print(f' #{xinstr.comment}', end="", file=self.__xinst_ostream)
            print(file=self.__xinst_ostream)

        for idx, cinstr in enumerate(kernel_cinstrs[:-1]):  # Skip the `cexit`
            line_no = idx + self.__cinst_line_offset
            print(f'{line_no}, {cinstr.to_line()}', end="", file=self.__cinst_ostream)
            if not self.supressComments and cinstr.comment:
                print(f' #{cinstr.comment}', end="", file=self.__cinst_ostream)
            print(file=self.__cinst_ostream)

        for idx, minstr in enumerate(kernel_minstrs[:-1]):  # Skip the exit `msyncc`
            line_no = idx + self.__minst_line_offset
            print(f'{line_no}, {minstr.to_line()}', end="", file=self.__minst_ostream)
            if not self.supressComments and minstr.comment:
                print(f' #{minstr.comment}', end="", file=self.__minst_ostream)
            print(file=self.__minst_ostream)

        self.__minst_line_offset += (len(kernel_minstrs) - 1)  # Subtract last line that is getting removed
        self.__cinst_line_offset += (len(kernel_cinstrs) - 1)  # Subtract last line that is getting removed
        self.__kernel_count += 1  # Count the appended kernel
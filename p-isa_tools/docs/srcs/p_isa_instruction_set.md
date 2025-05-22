P-ISA Instruction Set Overview {#PISA_overview}
========================

[TOC]

##P-ISA Overview

This page describes the p-ISA instruction set. The current set of p-ISA instructions are each described in the below table.

##Memory Model
The p-ISA instructions assume a flat memory model. Inputs and outputs are addressed using c-style labels.
Instructions operate on vectors of 32 bit unsigned integers referred to as a multi-register.
The length of these registers is defined as 8192 in the current execution model.

##Instructions

| P-ISA Instruction | Class Link | Instruction Description |
| :---------------- | :------: | :------|
| add       |   [Add](@ref pisa::instruction::Add)   | @copybrief pisa::instruction::Add  \n \n <b>Instruction Format: </b> @copydetails pisa::instruction::description_Add \n @copydetails pisa::instruction::Add  \n \n <b>Functional Modeler Implementation: </b> @ref pisa::PISAFunctionalModel::addInstrDecodeExecute "add implementation" |
| sub       |   [Sub](@ref pisa::instruction::Sub)   | @copybrief pisa::instruction::Sub  \n \n <b>Instruction Format: </b> @copydetails pisa::instruction::description_Sub \n @copydetails pisa::instruction::Sub \n \n <b>Functional Modeler Implementation:</b> @ref pisa::PISAFunctionalModel::subInstrDecodeExecute "sub implementation" |
| mul       |   [Mul](@ref pisa::instruction::Mul)   | @copybrief pisa::instruction::Mul  \n <b>Instruction Format: </b> @copydetails pisa::instruction::description_Mul \n \n <b>Details</b>: @copydetails pisa::instruction::Mul \n \n <b>Functional Modeler Implementation:</b> @ref pisa::PISAFunctionalModel::mulInstrDecodeExecute" mul implementation" |
| mac       |   [Mac](@ref pisa::instruction::Mac)   | @copybrief pisa::instruction::Mac  \n <b>Instruction Format: </b> @copydetails pisa::instruction::description_Mac \n \n <b>Details</b>: @copydetails pisa::instruction::Mac \n \n <b>Functional Modeler Implementation:</b> @ref pisa::PISAFunctionalModel::macInstrDecodeExecute "mac implementation" |
| maci       |   [Maci](@ref pisa::instruction::Maci)   | @copybrief pisa::instruction::Maci  \n <b>Instruction Format: </b> @copydetails pisa::instruction::description_Maci \n \n <b>Details</b>: @copydetails pisa::instruction::Maci \n \n <b>Functional Modeler Implementation:</b> @ref pisa::PISAFunctionalModel::maciInstrDecodeExecute "maci implementation" |
| intt       |   [Intt](@ref pisa::instruction::Intt)   | @copybrief pisa::instruction::Intt  \n <b>Instruction Format: </b> @copydetails pisa::instruction::description_Intt \n \n <b>Details</b>: @copydetails pisa::instruction::Intt \n \n <b>Functional Modeler Implementation:</b> @ref pisa::PISAFunctionalModel::iNttInstrDecodeExecute "intt implementation" |
| ntt       |   [Ntt](@ref pisa::instruction::Ntt)   | @copybrief pisa::instruction::Ntt  \n <b>Instruction Format: </b> @copydetails pisa::instruction::description_Ntt \n \n <b>Details</b>: @copydetails pisa::instruction::Ntt \n \n <b>Functional Modeler Implementation:</b> @ref pisa::PISAFunctionalModel::nttInstrDecodeExecute "ntt implementation" |
| muli       |   [Muli](@ref pisa::instruction::Muli)   | @copybrief pisa::instruction::Muli  \n <b>Instruction Format: </b> @copydetails pisa::instruction::description_Muli \n \n <b>Details</b>: @copydetails pisa::instruction::Muli \n \n <b>Functional Modeler Implementation:</b> @ref pisa::PISAFunctionalModel::muliInstrDecodeExecute "muli implementation" |
| copy       |   [Copy](@ref pisa::instruction::Copy)   | @copybrief pisa::instruction::Copy  \n <b>Instruction Format: </b> @copydetails pisa::instruction::description_Copy \n \n <b>Details</b>: @copydetails pisa::instruction::Copy \n \n <b>Functional Modeler Implementation:</b>  @ref pisa::PISAFunctionalModel::copyInstrDecodeExecute "copy implementation" |

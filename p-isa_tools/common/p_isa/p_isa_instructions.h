// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "p_isa_instruction.h"
#include <string>

/**
 * @brief This namespace encapulates p-ISA instruction(s).
 *
 */
namespace pisa::instruction {

/**
 *
 *  {POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, RESIDUAL}
 *  **/
static const pisa::InstructionDesc description_Add = { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, RESIDUAL };
/**
 * @class Add
 * \brief
 * The Add class represents an Add instruction in P_ISA.
 * It receives as input 2 source registers which are added modulus some environment state value Q and result is written to dst.
 *
 * | Argument | Type | Description |
 * | :---------------- | :------ | :--------|
 * | POLYMOD_DEG_LOG2 | Int | Not used |
 * | OP_NAME | string | add |
 * | OUTPUT_OPERAND [out] | string | dst = label of output register |
 * | INPUT_OPERAND | string |  src1 = label of input register |
 * | INPUT_OPERAND | string | src2 = label of input register |
 * | RESIDUAL | int | mod_q = index of modulus value to use |
 * @details <b>High level functional description</b>:
 * dst = (src1+src2) % modulus_chain[mod_q]
 */
class Add : public PISAInstruction
{
public:
    Add() :
        PISAInstruction(baseName, description_Add) {}

    Add(int poly_mod, Operand output_op, Operand input_op0, Operand input_op1, int residual) :
        Add()
    {
        setPMD(poly_mod);
        addOutputOperand(output_op);
        addInputOperand(input_op0);
        addInputOperand(input_op1);
        setResidual(residual);
    }

    inline static const std::string baseName = "add";
    PISAInstruction *create() override { return new Add(); }
};

/**
 *
 *  {POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, RESIDUAL}
 *  **/
static const pisa::InstructionDesc description_Sub = { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, RESIDUAL };

/**
 * @class Sub
 * @brief The Sub class represents a Sub instruction in P_ISA.
 * It receives as input 2 source registers which are subtracted modulus some environment state value Q and result is written to dst.
 *
 * | Argument | Type | Description |
 * | :---------------- | :------ | :--------|
 * | POLYMOD_DEG_LOG2 | Int | Not used |
 * | OP_NAME | string | sub |
 * | OUTPUT_OPERAND [out] | string | dst = label of output register |
 * | INPUT_OPERAND | string |  src1 = label of input register |
 * | INPUT_OPERAND | string | src2 = label of input register |
 * | RESIDUAL | int | mod_q = index of modulus value to use |
 *
 * @details <b>High level functional description</b>:
 * dst = (src1-src2) % modulus_chain[mod_q]
 */
class Sub : public PISAInstruction
{
public:
    Sub() :
        PISAInstruction(baseName, description_Sub) {}
    Sub(int poly_mod, Operand output_op, Operand input_op0, Operand input_op1, int residual) :
        Sub()
    {
        setPMD(poly_mod);
        addOutputOperand(output_op);
        addInputOperand(input_op0);
        addInputOperand(input_op1);
        setResidual(residual);
        return;
    }

    inline static const std::string baseName = "sub";
    PISAInstruction *create() override { return new Sub(); }
};

/**
 *
 *  { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, RESIDUAL }
 *  **/
static const pisa::InstructionDesc description_Mul = { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, RESIDUAL };
/**
 * @class Mul
 * @brief The Mul class represents an multiply instruction in P_ISA.
 * It receives as input 2 source registers which are multiplied modulus some environment state value Q and result is written to dst.
 *
 * | Argument | Type | Description |
 * | :---------------- | :------ | :--------|
 * | POLYMOD_DEG_LOG2 | Int | Not used |
 * | OP_NAME | string | mul |
 * | OUTPUT_OPERAND [out] | string | dst = label of output register |
 * | INPUT_OPERAND | string |  src1 = label of input register |
 * | INPUT_OPERAND | string | src2 = label of input register |
 * | RESIDUAL | int | mod_q = index of modulus value to use |
 * @details <b>High level functional description</b>:
 * dst = (src1*src2) % modulus_chain[mod_q]
 */
class Mul : public PISAInstruction
{
public:
    Mul() :
        PISAInstruction(baseName, description_Mul) {}

    Mul(int poly_mod, Operand output_op, Operand input_op0, Operand input_op1, int residual) :
        Mul()
    {
        setPMD(poly_mod);
        addOutputOperand(output_op);
        addInputOperand(input_op0);
        addInputOperand(input_op1);
        setResidual(residual);
        return;
    }

    inline static const std::string baseName = "mul";
    PISAInstruction *create() override { return new Mul(); }
};
/**
 *
 *  { POLYMOD_DEG_LOG2, OP_NAME, INPUT_OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, RESIDUAL }
 *  **/
static const pisa::InstructionDesc description_Mac = { POLYMOD_DEG_LOG2, OP_NAME, INPUT_OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, RESIDUAL };
/**
 * @brief The Mac class represents an multiply accumulate instruction in P_ISA.
 * It receives as input 2 source registers which are multiplied and then added to the value in the output register modulus some environment state value Q.
 * | Argument | Type | Description |
 * | :---------------- | :------ | :--------|
 * | POLYMOD_DEG_LOG2 | Int | Not used |
 * | OP_NAME | string | mac |
 * | INPUT_OUTPUT_OPERAND [in/out] | string | dst = label of register to accumulate result value to|
 * | INPUT_OPERAND | string |  src1 = label of input register |
 * | INPUT_OPERAND | string | src2 = label of input register |
 * | RESIDUAL | int | mod_q = index of modulus value to use |
 * @details <b>High level functional description</b>:
 * dst = (dst + (src1*src2) % modulus_chain[mod_q]) % modulus_chain[mod_q]
 */
class Mac : public PISAInstruction
{
public:
    Mac() :
        PISAInstruction(baseName, description_Mac) {}
    Mac(int poly_mod, Operand input_output_op, Operand input_op0, Operand input_op1, int residual) :
        Mac()
    {
        setPMD(poly_mod);
        addOutputOperand(input_output_op);
        addInputOperand(input_output_op);
        addInputOperand(input_op0);
        addInputOperand(input_op1);
        setResidual(residual);
        return;
    }

    inline static const std::string baseName = "mac";
    PISAInstruction *create() override { return new Mac(); }
};

/**
 *
 *  { POLYMOD_DEG_LOG2, OP_NAME, INPUT_OUTPUT_OPERAND, INPUT_OPERAND, IMMEDIATE, RESIDUAL }
 *  **/
static const pisa::InstructionDesc description_Maci = { POLYMOD_DEG_LOG2, OP_NAME, INPUT_OUTPUT_OPERAND, INPUT_OPERAND, IMMEDIATE, RESIDUAL };
/**
 * @brief The Maci class represents a multiply accumulate immediate instruction in P_ISA.
 * It receives as input 1 source register and 1 immediate which are multiplied and then added to the value in the output register modulus some environment state value Q.
 * | Argument | Type | Description |
 * | :---------------- | :------ | :--------|
 * | POLYMOD_DEG_LOG2 | Int | Not used |
 * | OP_NAME | string | maci |
 * | INPUT_OUTPUT_OPERAND [in/out] | string | dst = label of input and output register |
 * | INPUT_OPERAND | string |  src1 = label of input register |
 * | IMMEDIATE | string | imm = label of input immediate |
 * | RESIDUAL | int | mod_q = index of modulus value to use |
 * @details <b>High level functional description</b>:
 * dst = (dst + (src1*imm) % modulus_chain[mod_q]) % modulus_chain[mod_q]
 */
class Maci : public PISAInstruction
{
public:
    Maci() :
        PISAInstruction(baseName, description_Maci) {}
    Maci(int poly_mod, Operand input_output_op, Operand input_op0, Operand input_op1, int residual) :
        Maci()
    {
        setPMD(poly_mod);
        addOutputOperand(input_output_op);
        addInputOperand(input_output_op);
        addInputOperand(input_op0);
        input_op1.setImmediate(true);
        addInputOperand(input_op1);
        setResidual(residual);
        return;
    }

    inline static const std::string baseName = "maci";
    PISAInstruction *create() override { return new Maci(); }
};

/**
 *
 *  { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, W_PACKED_PARAM, RESIDUAL, GALOIS_ELEMENT }
 *  **/
static const pisa::InstructionDesc description_Intt = { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, W_PACKED_PARAM, RESIDUAL, GALOIS_ELEMENT };
/**
 * @brief The Intt class represents a intt instruction in P_ISA. Each intt instruction performs a partial intt operation on a given ciphertext. To fully perform an inverse
 * intt a series of operations
 * | Argument | Type | Description |
 * | :---------------- | :------ | :--------|
 * | POLYMOD_DEG_LOG2 | Int | Used for bit reversal and address calculations |
 * | OP_NAME | string | intt |
 * | OUTPUT_OPERAND [out] | string | dst1 = label of output register |
 * | OUTPUT_OPERAND [out] | string | dst2 = label of output register |
 * | INPUT_OPERAND | string |  src1 = label of input register |
 * | INPUT_OPERAND | string | src2 = label of input register |
 * | W_PACKED_PARAM | string | encodes as a string the following values residual_stage_block used for intt calculations |
 * | RESIDUAL | int | mod_q = index of modulus value to use |
 * | GALOIS_ELEMENT | int | ge = used to determine which set of inverse twiddle factors to use for the current intt operation |
 *
 * @details <b>High level functional description</b>:
 * #TBD needs to inverse ntt?
 */
class Intt : public PISAInstruction
{
public:
    Intt() :
        PISAInstruction(baseName, description_Intt)
    {
        m_galois_element = 1;
    }

    inline static const std::string baseName = "intt";
    PISAInstruction *create() override { return new Intt(); }
    // galois element default param will be removed or labeled in future update
    Intt(int poly_mod, Operand output_op0, Operand output_op1, Operand input_op0, Operand input_op1, WParam w_param, int residual, int galois_element = 1) :
        Intt()
    {
        setPMD(poly_mod);
        addOutputOperand(output_op0);
        addOutputOperand(output_op1);
        addInputOperand(input_op0);
        addInputOperand(input_op1);
        setWParam(w_param);
        setResidual(residual);
        // temporary
        setGalois_element(galois_element);
        return;
    }
};

/**
 *
 *   { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, W_PACKED_PARAM, RESIDUAL }
 *  **/
static const pisa::InstructionDesc description_Ntt = { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, OUTPUT_OPERAND, INPUT_OPERAND, INPUT_OPERAND, W_PACKED_PARAM, RESIDUAL };
/**
 * @brief The Ntt class represents an ntt instruction in P_ISA.
 * | Argument | Type | Description |
 * | :---------------- | :------ | :--------|
 * | POLYMOD_DEG_LOG2 | Int | Used for bit reversal and address calculations |
 * | OP_NAME | string | ntt |
 * | OUTPUT_OPERAND [out] | string | dst1 = label of output register |
 * | OUTPUT_OPERAND [out] | string | dst2 = label of output register |
 * | INPUT_OPERAND | string |  src1 = label of input register |
 * | INPUT_OPERAND | string | src2 = label of input register |
 * | W_PACKED_PARAM | string | encodes as a string the following values residual_stage_block used for intt calculations |
 * | RESIDUAL | int | mod_q = index of modulus value to use |
 *
 * @details <b>High level functional description</b>:
 * #TBD needs to ntt?
 */
class Ntt : public PISAInstruction
{
public:
    Ntt() :
        PISAInstruction(baseName, description_Ntt) {}
    Ntt(int poly_mod, Operand output_op0, Operand output_op1, Operand input_op0, Operand input_op1, WParam w_param, int residual) :
        Ntt()
    {
        setPMD(poly_mod);
        addOutputOperand(output_op0);
        addOutputOperand(output_op1);
        addInputOperand(input_op0);
        addInputOperand(input_op1);
        setWParam(w_param);
        setResidual(residual);
        return;
    }

    inline static const std::string baseName = "ntt";
    PISAInstruction *create() override { return new Ntt(); }
};

/**
 *
 *  { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND, IMMEDIATE, RESIDUAL }
 *  **/
static const pisa::InstructionDesc description_Muli = { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND, IMMEDIATE, RESIDUAL };
/**
 * @brief The Muli class represents an multiply immediate instruction in P_ISA.
 * It receives as input 1 source register and scalar 1 immediate value which are multiplied and then added to the value in the output register modulus some environment state value Q.
 * Modulus is implemented as montgomery form modulus
 * | Argument | Type | Description |
 * | :---------------- | :------ | :--------|
 * | POLYMOD_DEG_LOG2 | Int | Not used |
 * | OP_NAME | string | muli |
 * | OUTPUT_OPERAND [out] | string | dst = label of output register |
 * | INPUT_OPERAND | string |  src1 = label of input register |
 * | IMMEDIATE | string | imm = label of input immediate |
 * | RESIDUAL | int | mod_q = index of modulus value to use |
 * @details <b>High level functional description</b>:
 * dst = (src1*imm1 ) % modulus_chain[modulus_q]
 */
class Muli : public PISAInstruction
{
public:
    Muli() :
        PISAInstruction(baseName, description_Muli) {}
    Muli(int poly_mod, Operand output_op, Operand input_op0, Operand input_op1, int residual) :
        Muli()
    {
        setPMD(poly_mod);
        addOutputOperand(output_op);
        addInputOperand(input_op0);
        input_op1.setImmediate(true);
        addInputOperand(input_op1);
        setResidual(residual);
        return;
    }

    inline static const std::string baseName = "muli";
    PISAInstruction *create() override { return new Muli(); }
};

/**
 *
 *  { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND }
 *  **/
static const pisa::InstructionDesc description_Copy = { POLYMOD_DEG_LOG2, OP_NAME, OUTPUT_OPERAND, INPUT_OPERAND };
/**
 * @brief The copy class represents an copy instruction in P_ISA.
 * This instruction copies the value stored at the input register to the output register.
 * | Argument | Type | Description |
 * | :---------------- | :------ | :--------|
 * | POLYMOD_DEG_LOG2 | Int | Not used |
 * | OP_NAME | string | copy |
 * | OUTPUT_OPERAND [out] | string | dst = label of output register |
 * | INPUT_OPERAND | string |  src1 = label of input register |
 * @details <b>High level functional description</b>:
 * dst = src1;
 */
class Copy : public PISAInstruction
{
public:
    Copy() :
        PISAInstruction(baseName, description_Copy)
    {
        m_residual = 0;
    }
    Copy(int poly_mod, Operand output_op, Operand input_op0) :
        Copy()
    {
        setPMD(poly_mod);
        addOutputOperand(output_op);
        addInputOperand(input_op0);
        return;
    }

    inline static const std::string baseName = "copy";
    PISAInstruction *create() override { return new Copy(); }
};

} // namespace pisa::instruction

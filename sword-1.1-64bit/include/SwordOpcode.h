//  vim: ft=cpp:ts=2:sw=2:expandtab
#ifndef SWORD__SWORDOPCODE_H
#define SWORD__SWORDOPCODE_H

#include <vector>

namespace SWORD {

enum OPCODE {
  UNKNOWN, // variable                                 (0)              

  // predicate symbols
  CONST,    // constant term                            (1)
  EQUAL,    // equality predicate                       (2)
  NEQUAL,   // inequality predicate                     (3)
  DISTINCT, // distinct predicate                       (4)
  IMPLIES,  // implies predicate                        (5)
  SLT,      // signed less than predicate               (6)
  SLE,      // signed less or equal predicate           (7)
  ULT,      // unsigned less than predicate             (8)
  ULE,      // unsigned less or equal predicate         (9)
  SGT,      // signed greater than predicate            (10)
  SGE,      // signed greater or equal predicate        (11)
  UGT,      // unsigned greater than predicate          (12)
  UGE,      // unsigned greater or equal predicate      (13)
  NOT,      // not predicate and bitwise negation       (14)

  // function symbols
  ITE,      // if-then-else function                    (15)
  NEG,      // 2er complement negation                  (16)
  ADD,      // addition function                        (17)
  SUB,      // subtraction function                     (18)  
  MUL,      // multiplication function                  (19)
  SDIV,     // signed division                          (20)
  SREM,     // signed remainder (sign follows dividend) (21)
  SMOD,     // signed remainder (sign follows divisor)  (22)
  UDIV,     // unsigned division                        (23)
  UREM,     // unsigned remainder                       (24)
  AND,      // bitwise and function                     (25)
  NAND,     // bitwise nand function                    (26)
  OR,       // bitwise or function                      (27)
  NOR,      // bitwise nor function                     (28)
  XOR,      // bitwise xor function                     (29)
  XNOR,     // bitwise xnor function                    (30)

  LSHL,     // logical left shift                       (31)
  LSHR,     // logical right shift                      (32)
  ASHR,     // arithmetic right shift                   (33)

  RED_OR,   // reduce-or: maps a bitvector to 1 iff it contains a 1       (34)
  RED_AND,  // reduce-and:maps a bitvector to 1 iff it contains only 1's  (35)

  CONCAT,   // concatenation of two signals				(36)
  EXTRACT,  // extraction from a signal				(37)
  REPEAT,   // repeat							(38)
  ROTATE_LEFT, // cyclic shift left					(39)
  ROTATE_RIGHT, // cyclic shift right					(40)
  SELECT,       // array read operation				(41)
  STORE,        // array write operation				(42)
  SIGN_EXTEND,  // concat with a number of 0/1 for positive/negative numbers	(43)
  ZERO_EXTEND,  // concat with a number of 0					(44)


  OP_UPPER_BOUND  // just to fix an upper bound number for this enum
};

/**
 * @return true if the operator is commutative, false otherwise
 */
inline bool isCommutative(const OPCODE& o) {
  switch (o) {
    // all commutative operations --> true
    case AND: case NAND:
    case OR: case NOR:
    case XOR: case XNOR:
    case EQUAL: case NEQUAL:
    case DISTINCT:
    case ADD: case MUL:
      return true;
      // else false
    default:
      return false;
  }
}


/**
 * return the coresponding string for an OPCODE
 */
inline const char* toString (const OPCODE& o) {
  switch(o) {
    case EQUAL: return "=";
    case NEQUAL:return "!=";
    case IMPLIES: return "=>";
    case SGT:   return ">s";
    case UGT:   return ">u";
    case SLT:   return "<s";
    case ULT:   return "<u";
    case SGE:   return ">=s";
    case UGE:   return ">=u";
    case SLE:   return "<=s";
    case ULE:   return "<=u";
    case NOT:   return "not";
    case NEG:   return "-";
    case ITE:   return "ite";
    case AND:   return "and";
    case OR:    return "or";
    case XOR:   return "xor";
    case ADD:   return "+";
    case SUB:   return "-";
    case MUL:   return "*";
    case SDIV:  return "/s";
    case UDIV:  return "/u";
    case SMOD:  return "%";
    case SREM:  return "rem s";
    case UREM:  return "rem u";
    case LSHL:  return "<<";
    case LSHR:  return ">>";
    case ASHR:  return ">>a";
    case EXTRACT: return "extract";
    case SIGN_EXTEND:   return "sgn_ext";
    case ZERO_EXTEND:   return "zero_ext";
    case ROTATE_LEFT:   return "rot_l";
    case ROTATE_RIGHT:  return "rot_r";
    case REPEAT:        return "rep";
    case CONCAT:        return "++";
    default: return "nyi";
  }
}

/**
 * return the coresponding string for an OPCODE
 */
inline const char* toStringStrict (const OPCODE& o) {
  switch(o) {
    case UNKNOWN: return "UNKNOWN";
    case CONST: return "CONST";
    case EQUAL: return "EQUAL";
    case NEQUAL:return "NEQUAL";
    case IMPLIES: return "IMPLIES";
    case DISTINCT: return "DISTINCT";
    case SGT:   return "SGT";
    case UGT:   return "UGT";
    case SLT:   return "SLT";
    case ULT:   return "ULT";
    case SGE:   return "SGE";
    case UGE:   return "UGE";
    case SLE:   return "SLE";
    case ULE:   return "ULE";
    case NOT:   return "NOT";
    case NEG:   return "NEG";
    case ITE:   return "ITE";
    case AND:   return "AND";
    case OR:    return "OR";
    case XOR:   return "XOR";
    case NAND:  return "NAND";
    case NOR:   return "NOR";
    case XNOR:  return "XNOR";
    case ADD:   return "ADD";
    case SUB:   return "SUB";
    case MUL:   return "MUL";
    case SDIV:  return "SDIV";
    case UDIV:  return "UDIV";
    case SMOD:  return "SMOD";
    case SREM:  return "SREM";
    case UREM:  return "UREM";
    case LSHL:  return "LSHL";
    case LSHR:  return "LSHR";
    case ASHR:  return "ASHR";
    case RED_OR:  return "RED_OR";
    case RED_AND: return "RED_AND";
    case EXTRACT: return "EXTRACT";
    case SIGN_EXTEND:   return "SIGN_EXTEND";
    case ZERO_EXTEND:   return "ZERO_EXTEND";
    case ROTATE_LEFT:   return "ROTATE_LEFT";
    case ROTATE_RIGHT:  return "ROTATE_RIGHT";
    case REPEAT:        return "REPEAT";
    case CONCAT:        return "CONCAT";
    case SELECT:        return "SELECT";
    case STORE:         return "STORE";

    case OP_UPPER_BOUND: return "OP_UPPER_BOUND";
  }
  return "unknown";
}

/**
 * @return true if the operator is an arithmetic operator, i.e. works bitwise
 */
inline bool isArithmetic(const OPCODE& o) {
  switch (o) {
    // all arithmetic operations --> true
    case AND: case NAND:
    case OR: case NOR:
    case XOR: case XNOR:
    case ADD: case MUL: case SUB:
    case SDIV: case UDIV:
    case SREM: case SMOD:
    case UREM: case NEG: 
    case LSHL: case LSHR: case ASHR:
    case NOT:
      return true;
    default: 
      return false;
  }
}


/**
 * @return true if the operator is an logical operator, i.e. works like a predicate
 */
inline bool isLogical(const OPCODE& o) {
  switch (o) {
    // all logical operations --> true
    case EQUAL: case NEQUAL: 
    case UGT: case ULT: case UGE: case ULE:
    case SGT: case SLT: case SGE: case SLE:
    case DISTINCT: case IMPLIES:
    case RED_OR: case RED_AND: 
      return true;
    default:
      return false;
  }
}

} /* namespace SWORD */

#endif /* SWORD__SWORDOPCODE_H */

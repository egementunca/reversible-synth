//  vim: ft=cpp:ts=2:sw=2:expandtab
#ifndef LIBSWORD__H
#define LIBSWORD__H

#include "SwordOpcode.h"

#include <list>
#include <vector>
#include <string>
#include <ostream>


namespace SWORD {

//forward 
class Signal;
class Generator;
class Options;
class SwordModule;

typedef Signal* PSignal;

/* constant returned by getEvaluation */
const int SWORD_TRUE        =  1; 
const int SWORD_FALSE       =  0;
const int SWORD_DONTCARE    = -1;
const int SWORD_ONE   =  SWORD_TRUE;
const int SWORD_ZERO  =  SWORD_FALSE;

class sword {
  friend class SwordModule;

public: /* Constructors/Destructor */

   sword();
  ~sword();

public: /* member functions */

  /**
   * wrapper function for 1, 2 and 3 arguments
   */
  PSignal addOperator(const OPCODE& o, PSignal, PSignal = PSignal(), PSignal = PSignal());
  /**
   * adds a term with the operator <code> o </code> using the input signals <code> inputs </code>
   */
  PSignal addOperator(const OPCODE& o, std::vector<PSignal>* inputs); 

  /**
   * extracts the signal [a, b) from a given signal [0, n)
   */
  PSignal addExtract(PSignal, const unsigned a, const unsigned b);

  /**
   * concatenates the signal s n times
   */
  PSignal addRepeat(PSignal s, const unsigned n);

  /**
   * rotates the signal s by n positions to the left
   */
  PSignal addRotateLeft(PSignal s, const unsigned n);

  /**
   * rotates the signal s by n positions to the right
   */
  PSignal addRotateRight(PSignal s, const unsigned n);

  /**
   * extends (prefixes) the signal s by n zeros
   */
  PSignal addZeroExtend(PSignal s, const size_t n);

  /*
   * extends (prefixes) the signal s  
   * by n bits with the value of the first bit of s
   */
  PSignal addSignExtend(PSignal s, const size_t n);

  /**
   * adds a constant expression of given bitsize to the term
   */
  PSignal addConstant(unsigned bitsize, unsigned long value);

  /**
   * adds a constant expression of given bitsize to the term, value is in base 10 
   */
  PSignal addConstant(unsigned bitsize, std::string const& value);
  
  /**
   * adds a constant bitstring, value is in base 2 
   */
  PSignal addBinConstant(unsigned bitsize, std::string const& bitstring);

  /**
   * adds a constant bitstring, value is in base 2, bitsize is the length
   */
  PSignal addBinConstant(std::string const& bitstring);
 
  /**
   * adds a constant bitstring, value is in base 16, bitsize is 4*length
   */
  PSignal addHexConstant(unsigned bitsize, std::string const& hexstring);

  /**
   * adds a constant bitstring, value is in base 16, bitsize is 4*length
   */
  PSignal addHexConstant(std::string const& hexstring);

  /**
   * adds a variable declared by <code>(extrafuns varname bv[bitsize])</code>
   */
  PSignal addVariable(unsigned bitsize, const std::string& name);

  /**
   * adds a module and asserts it
   * */
  void addAndAssertModule(SwordModule* mod);

  /**
   * assert a (boolean) signal to a certain value.
   *
   * Can be used to assert Signal or ~Signal.
   * 
   */
  void addAssertion(PSignal, bool b=true);

  /**
   * Like add Assertion but only valid for a single call to the solver.
   */
  void addAssumption(PSignal, bool b=true);

  /**
   * Solve the instance
   */
  bool solve();

  /**
   * Read the assignments
   */
  std::vector<int> getVariableAssignment(PSignal s) const;

  /**
   * Record all calls to the specified filename
   * (to be included in bug reports)
   */
  void recordTo(const std::string & filename);

private: /* member variables */

  /**
   * adds a module and returns the signal that enables the Module
   * */
  PSignal addModule(SwordModule* mod);
  
  Options*   _opt;
  Generator* _gen;
  std::list<SwordModule*> _externalModules;

  std::ostream* _out;

}; /* class sword */

}  /* namespace SWORD */

#endif /* LIBSWORD__H */

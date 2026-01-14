
// standard includes for input/output and vector
#include <iostream>  
#include <iterator>
#include <vector>
using namespace std;


// include sword interface
#include "libsword.h"
#include "libmodule.h"

using namespace SWORD;

class CardinalityLessThan : public SwordModule {
  public:
    CardinalityLessThan(sword * swd, PSignal signal, unsigned maxOnes) 
      : SwordModule(swd)
        , _vars(signalToLiterals(signal))
        , _maxOnes(maxOnes)
  {
    useVariables(_vars);
  }
    virtual Lit decide () {
      for (unsigned i = 0; i < _vars.size(); ++i) {
        if (isFree(_vars[i]))       // check if variable is still free
          return ~_vars[i];         // then set it to false
      }
      return lit_Undef;             // no free variable in the module
    }

    virtual Clause* propagate() {
      conflict_set_t reason;
      for(unsigned i = 0; i< _vars.size(); ++i) {
        if( getValue(_vars[i]) == l_True )
          reason.push_back( _vars[i] );
      }
      if ( reason.size() >=  _maxOnes) {
        return makeConflict(reason);
      } else if (reason.size() + 1 == _maxOnes) {
        for (unsigned i = 0; i < _vars.size(); ++i) {
          if ( getValue(_vars[i]) == l_Undef ) {
            inferLiteral(~_vars[i], reason);
          }
        }
      } else { 
        return NULL;
      }
    }
    const std::vector<Lit> _vars;
    const unsigned _maxOnes;
}; // class CardinalityLessThan


int main () {
  // create a new solver object
  sword * solver = new sword();

  // add variable with name "x" and bit width 8
  PSignal x = solver->addVariable(8, "x");

  // add variable with name "y" and bit width 8
  PSignal y = solver->addVariable(8, "x");

  // add constant with bit width 8 and value 18
  PSignal eighteen= solver->addConstant(8, 18);

  // add multiplication term x*y
  PSignal mult = solver->addOperator(MUL, x, y);

  // add equality x*y = 18
  PSignal equality = solver->addOperator(EQUAL, mult, eighteen);

  // assert the equality
  solver->addAssertion(equality);

  unsigned maxOnes = 4;
  solver->addAndAssertModule(new CardinalityLessThan(solver, x, maxOnes));

  bool sat = solver->solve();
  if (sat) {
    // get solution from solver
    vector<int> solutionX = solver->getVariableAssignment(x);
    vector<int> solutionY = solver->getVariableAssignment(y);
    // print solution
    cout << "solution for x: "; 
    copy(solutionX.begin(), solutionX.end(), ostream_iterator<int>(cout, " "));
    cout << endl;

    cout << "solution for y: "; 
    copy(solutionY.begin(), solutionY.end(), ostream_iterator<int>(cout, " "));
    cout << endl;
  }
  // clean up solver object
  delete solver;

  return 0;
}

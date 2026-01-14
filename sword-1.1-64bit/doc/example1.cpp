
// standard includes for input/output and vector
#include <iostream>  
#include <iterator>
#include <vector>
using namespace std;


// include sword interface
#include "libsword.h"
using namespace SWORD;

int main () {
  // create a new solver object
  sword * solver = new sword();

  // add variable with name "x" and bit width 8
  PSignal x = solver->addVariable(8, "x");

  // add variable with name "y" and bit width 8
  PSignal y = solver->addVariable(8, "y");

  // add constant with bit width 8 and value 18
  PSignal eighteen= solver->addConstant(8, 18);

  // add multiplication term x*y
  PSignal mult = solver->addOperator(MUL, x, y);

  // add equality x*y = 18
  PSignal equality = solver->addOperator(EQUAL, mult, eighteen);

  // assert the equality
  solver->addAssertion(equality);

  // solve the problem
  solver->solve();

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

  // prints on our computer: 
  // solution for x: 1 1 0 1 1 0 1 0 
  // solution for y: 0 1 1 0 1 0 1 1 


  bool one_negative = (solutionX.back()==SWORD_TRUE xor solutionY.back()==SWORD_TRUE);

  if (one_negative) {
    cout << "found solution with different signs for x and y\n";
    PSignal zero   = solver->addConstant(8, 0);
    PSignal x_gt_0 = solver->addOperator(SGT, x, zero);
    PSignal y_gt_0 = solver->addOperator(SGT, y, zero);

    solver->addAssumption (solver->addOperator (AND, x_gt_0, y_gt_0));
    if (solver->solve())
      cout << "found solution with x>0 and y>0\n";

    solver->addAssumption (solver->addOperator (NOR, x_gt_0, y_gt_0));
    if (solver->solve())
      cout << "found solution with x<=0 and y<=0\n";
  } else {
    cout << "found solution with same signs for x and y\n";
  }

  // clean up solver object
  delete solver;

  return 0;
}

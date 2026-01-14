//  vim: ft=cpp:ts=2:sw=2:expandtab
#ifndef LIBMODULE__H
#define LIBMODULE__H

#include "libsword.h"
#include "SolverTypes.h"

#include <iterator>

namespace SWORD {

class sword;
class ExternalModule;

class SwordModule {
  friend class sword;

public: /* Constructors/Destructor */
     SwordModule(sword * solver);
     virtual ~SwordModule();

public: /* module API */
    virtual Lit decide(); 
    virtual Clause* propagate();	

    /**
     * true if the module is enabled
     *
     * checks _module->_enabledLit;
     */
    bool isEnabled() const; 

protected: /* module helper*/
    lbool getValue(Lit literal);
    bool isFree(Lit literal);
    bool isSet(Lit literal);
    
    typedef std::vector<Lit> conflict_set_t;
    /**
     * returns a clause suitable to be returned by propagate
     *
     * adds _module->_enableLit to conflict
     */
    Clause* makeConflict(conflict_set_t conflict);
  
    /* *
     * sets a literal
     * and the reason why it is set
     * reason: set of assignments that imply <code>inferedLit</code>
     *  */
    void inferLiteral(Lit inferedLit, const std::vector<Lit>& reason); 
    std::vector<Lit> signalToLiterals(PSignal signal);
    void useVariables(const std::vector<Lit> & lits);

private: /* member variables */
  sword*          _sword;
  ExternalModule* _module;


};

} /* namespace SWORD */

#endif /* LIBMODULE__H */

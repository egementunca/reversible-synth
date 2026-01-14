#ifndef HEADER_CardinalityLessThan_hpp
#define HEADER_CardinalityLessThan_hpp

#include "../libsword.h"
#include "../libmodule.h"

namespace SWORD {

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
        } else { 
          return NULL;
        }
      }
      const std::vector<Lit> _vars;
      const unsigned _maxOnes;
  }; // class CardinalityLessThan

} // namespace sword

#endif // HEADER_CardinalityLessThan_hpp
//  vim: ft=cpp:ts=2:sw=2:expandtab

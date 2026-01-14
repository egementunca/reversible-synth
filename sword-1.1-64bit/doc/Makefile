# user variables 
SWORDPATH=..

# derived variables
SWORDLIB     = ${SWORDPATH}/lib/libsword.a
SWORDINCLUDE = ${SWORDPATH}/include

CXXFLAGS   	+= -I${SWORDINCLUDE} ${EXTRAFLAGS}
LDFLAGS			+= ${SWORDLIB} ${EXTRAFLAGS}

examples: example1 example2

example1: example1.o
	$(CXX) -o $@ $< $(LDFLAGS) 
 
example2: example2.o
	$(CXX) -o $@ $< $(LDFLAGS) 

clean:
	rm -rf *.o example1 example2

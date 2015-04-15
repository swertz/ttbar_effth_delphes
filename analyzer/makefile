CXXFLAGS := -O2 -g $(shell root-config --cflags) -Wall
LIBS := $(shell root-config --ldflags --libs --glibs) -lTMVA
CXX := g++

sourcedir_tmva := source_tmva/
objdir_tmva := objs_tmva/
objects_tmva := $(objdir_tmva)/main.o $(objdir_tmva)/panalysis.o $(objdir_tmva)/pproc.o $(objdir_tmva)/pconfig.o $(objdir_tmva)/Chameleon.o $(objdir_tmva)/ConfigFile.o

all: tmva makefile

tmva: $(objects_tmva) makefile
	$(CXX) -o $@ $(objects_tmva) $(LIBS)  

$(objdir_tmva)/%.o: $(sourcedir_tmva)/%.cpp $(sourcedir_tmva)/*.h
	if test ! -d $(objdir_tmva); then mkdir $(objdir_tmva); fi
	$(CXX) -o $@ $(CXXFLAGS) -c $< 

.PHONY: clean
clean:
	-rm $(objdir_tmva)/*.o tmva
	-rmdir $(objdir_tmva)



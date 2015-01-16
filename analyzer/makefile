CXXFLAGS := -O3 -std=c++0x -Wall -l $(shell root-config --cflags)
LIBS := $(shell root-config --libs --glibs) -lMLP -lTMVA
CXX := g++

sourcedir_tmlp := source_tmlp/
objdir_tmlp := objs_tmlp/
objects_tmlp := $(objdir_tmlp)/nn_main.o $(objdir_tmlp)/nn_panalysis.o $(objdir_tmlp)/nn_pdata.o $(objdir_tmlp)/nn_pconfig.o $(objdir_tmlp)/Chameleon.o $(objdir_tmlp)/ConfigFile.o

sourcedir_tmva := source_tmva/
objdir_tmva := objs_tmva/
objects_tmva := $(objdir_tmva)/nn_main.o $(objdir_tmva)/nn_panalysis.o $(objdir_tmva)/nn_pdata.o $(objdir_tmva)/nn_pconfig.o $(objdir_tmva)/Chameleon.o $(objdir_tmva)/ConfigFile.o

all: tmlp tmva makefile

tmlp: $(objects_tmlp) makefile
	$(CXX) $(LIBS) $(objects_tmlp) -o $@

$(objdir_tmlp)/%.o: $(sourcedir_tmlp)/%.cpp $(sourcedir_tmlp)/*.h
	if test ! -d $(objdir_tmlp); then mkdir $(objdir_tmlp); fi
	$(CXX) $(CXXFLAGS) $(LIBS) -c $< -o $@

tmva: $(objects_tmva) makefile
	$(CXX) $(LIBS) $(objects_tmva) -o $@

$(objdir_tmva)/%.o: $(sourcedir_tmva)/%.cpp $(sourcedir_tmva)/*.h
	if test ! -d $(objdir_tmva); then mkdir $(objdir_tmva); fi
	$(CXX) $(CXXFLAGS) $(LIBS) -c $< -o $@

.PHONY: clean
clean:
	-rm $(objdir_tmlp)/*.o tmlp
	-rmdir $(objdir_tmlp)
	-rm $(objdir_tmva)/*.o tmva
	-rmdir $(objdir_tmva)



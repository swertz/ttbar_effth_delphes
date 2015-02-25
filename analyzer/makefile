CXXFLAGS := -O3 -std=c++0x -Wall -l $(shell root-config --cflags)
LIBS := $(shell root-config --libs --glibs) -lTMVA
CXX := g++

sourcedir_tmva := source_tmva/
objdir_tmva := objs_tmva/
objects_tmva := $(objdir_tmva)/nn_main.o $(objdir_tmva)/nn_panalysis.o $(objdir_tmva)/nn_pdata.o $(objdir_tmva)/nn_pconfig.o $(objdir_tmva)/Chameleon.o $(objdir_tmva)/ConfigFile.o

all: tmva makefile

tmva: $(objects_tmva) makefile
	$(CXX) $(LIBS) $(objects_tmva) -o $@

$(objdir_tmva)/%.o: $(sourcedir_tmva)/%.cpp $(sourcedir_tmva)/*.h
	if test ! -d $(objdir_tmva); then mkdir $(objdir_tmva); fi
	$(CXX) $(CXXFLAGS) $(LIBS) -c $< -o $@

.PHONY: clean
clean:
	-rm $(objdir_tmva)/*.o tmva
	-rmdir $(objdir_tmva)



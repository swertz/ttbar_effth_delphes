CXXFLAGS := -O2 -g -Wall $(shell root-config --cflags)
LDFLAGS := $(shell root-config --ldflags)
ROOT_LIBS := $(shell root-config --libs) -lTMVA -lTreePlayer
CXX := g++

EXTERNAL_CXXFLAGS := -I/cvmfs/cp3.uclouvain.be/boost/boost-1.57.0-sl6_amd64_gcc49/include -Iexternal/include
EXTERNAL_LDFLAGS := -Lexternal/lib -lyaml-cpp

sourcedir_tmva := source_tmva/
objdir_tmva := objs_tmva/
objects_tmva := $(objdir_tmva)/main.o $(objdir_tmva)/panalysis.o $(objdir_tmva)/pproc.o $(objdir_tmva)/pconfig.o

all: tmva

tmva: $(objects_tmva)
	$(CXX) -o $@ $(objects_tmva) $(LDFLAGS) $(EXTERNAL_LDFLAGS) $(ROOT_LIBS)

$(objdir_tmva)/%.o: $(sourcedir_tmva)/%.cpp $(sourcedir_tmva)/*.h | $(objdir_tmva)
	$(CXX) -o $@ $(CXXFLAGS) $(EXTERNAL_CXXFLAGS) -c $< 

$(objdir_tmva):
	if test ! -d $(objdir_tmva); then mkdir $(objdir_tmva); fi

.PHONY: clean
clean:
	-rm $(objdir_tmva)/*.o tmva
	-rmdir $(objdir_tmva)



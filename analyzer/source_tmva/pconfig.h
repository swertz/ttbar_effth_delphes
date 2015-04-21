#ifndef DEF_NN_PCONFIG
#define DEF_NN_PCONFIG

#include <vector>
#include <string>

template<class T, class U>
bool contains(const std::vector<T>& vector, const U& value) {
  return std::find(std::begin(vector), std::end(vector), value) != std::end(vector);
}


class PConfig{
  public:
  
  PConfig(const std::string& configFile);

  std::string GetPath(uint32_t i) const;
  std::string GetName(uint32_t i) const;
  int8_t GetType(uint32_t i) const;
  Color_t GetColor(uint32_t i) const;
  double GetXSection(uint32_t i) const;
  uint64_t GetTotEvents(uint32_t i) const;
  std::string GetTreeName(uint32_t i) const;
  std::vector<std::string> GetEvtWeights(uint32_t i) const;
  
  uint32_t GetNProc(void) const;
  std::string GetAnaName(void) const;
  std::string GetOutputDir(void) const;
  std::string GetOutputName(void) const;
  std::string GetTopology(void) const;
  std::string GetMvaMethod(void) const;
  std::vector<std::string> GetCommonEvtWeights(void) const;
  uint64_t GetIterations(void) const;
  uint64_t GetTrainEntries(void) const;
  double GetWorkingPoint(void) const;
  double GetLumi(void) const;
  int16_t GetHistBins(void) const;
  int16_t GetPlotBins(void) const;
  std::vector<std::string> GetWriteOptions(void) const;
  std::vector<std::string> GetOutputTasks(void) const;
  std::string GetSplitName(void) const;
  std::string GetLogName(void) const;
  std::string GetInputVar(uint32_t i) const;
  uint32_t GetNInputVars(void) const;

  private:

  std::vector<std::string> paths;
  std::vector<std::string> names;
  std::vector<int8_t> types;
  std::vector<int16_t> colors;
  std::vector<double> xSections;
  std::vector<uint64_t> totEvents;
  std::vector<std::string> treeNames;
  std::vector< std::vector<std::string> > evtWeights;
  uint32_t nProc, nInputVars;

  std::string anaName, outputDir, outputName, topology, mvaMethod;
  uint64_t iterations, trainEntries;
  double workingPoint, lumi;
  int16_t histBins, plotBins;
  std::string splitName, logName;
  std::vector<std::string> inputVars, commonEvtWeights, writeOptions, outputTasks;

  std::map<std::string, int16_t> colorMap;
  int16_t TranslateColor(const std::string& color) const;
};

#endif

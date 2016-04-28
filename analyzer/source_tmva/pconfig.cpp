#include <sstream>
#include <iostream>
#include <map>
#include <cstdlib>

#include <TColor.h>
#include "pconfig.h"

#include <boost/algorithm/string.hpp>
#include "yaml-cpp/yaml.h"

PConfig::PConfig(const std::string& configFile){

  // Init colors map
  colorMap["kWhite"] = kWhite;
  colorMap["kBlack"] = kBlack;
  colorMap["kGray"] = kGray;
  colorMap["kRed"] = kRed;
  colorMap["kGreen"] = kGreen;
  colorMap["kBlue"] = kBlue;
  colorMap["kYellow"] = kYellow;
  colorMap["kMagenta"] = kMagenta;
  colorMap["kCyan"] = kCyan;
  colorMap["kOrange"] = kOrange;
  colorMap["kSpring"] = kSpring;
  colorMap["kTeal"] = kTeal;
  colorMap["kAzure"] = kAzure;
  colorMap["kViolet"] = kViolet;
  colorMap["kPink"] = kPink;

  YAML::Node root = YAML::LoadFile(configFile);

  const YAML::Node& analysis = root["analysis"];

  anaName = analysis["name"].as<std::string>();
  outputDir = analysis["outputdir"].as<std::string>();
  outputName = analysis["outputname"].as<std::string>();
  mvaMethod = analysis["mvamethod"].as<std::string>();
  
  topology = "";
  if(mvaMethod.find("MLP") != std::string::npos)
    topology = analysis["topology"].as<std::string>();

  iterations = 0;
  commonEvtWeight = ""; 
  trainEntries = 0;
  histLoX = 0.;
  histHiX = 1.;
  if(mvaMethod.find("Singleton") == std::string::npos){
    iterations = analysis["iterations"].as<uint64_t>();
    commonEvtWeight = analysis["commonweights"].as<std::string>();
    trainEntries = analysis["trainentries"].as<uint64_t>();
  }else{
    histLoX = analysis["histLoX"].as<double>();
    histHiX = analysis["histHiX"].as<double>();
  }
  workingPoint = analysis["workingpoint"].as<double>();
  lumi = analysis["lumi"].as<double>();
  histBins = analysis["histbins"].as<int16_t>();
  plotBins = analysis["plotbins"].as<int16_t>();
  writeOptions = analysis["writeoptions"].as<std::vector<std::string>>();
  outputTasks = analysis["outputtasks"].as<std::vector<std::string>>();
  splitMode = "";
  if (analysis["splitmode"])
    splitMode = analysis["splitmode"].as<std::string>();
  splitName = analysis["splitname"].as<std::string>();
  logName = analysis["log"].as<std::string>();

  inputVars = analysis["inputvar"].as<std::vector<std::string>>();
  nInputVars = inputVars.size();

  if(nInputVars != 1 && mvaMethod.find("Singleton") != std::string::npos){
    std::cerr << "ERROR: when in \"Singleton\" mode, only one input variable can be specified!\n";
    exit(1);
  }

  const YAML::Node& datasets = root["datasets"];
  nProc = 0;
  for (YAML::const_iterator it = datasets.begin(); it != datasets.end(); ++it) {
    std::string name = it->first.as<std::string>();
    YAML::Node dataset = it->second;

    paths.push_back(dataset["path"].as<std::vector<std::string>>());
    names.push_back(name);
    types.push_back(dataset["signal"].as<int>());
    xSections.push_back(dataset["xsection"].as<double>());
    totEvents.push_back(dataset["genevents"].as<uint64_t>());
    treeNames.push_back(dataset["treename"].as<std::string>());
    colors.push_back(TranslateColor(dataset["color"].as<std::string>()));

    evtWeights.push_back(dataset["evtweight"].as<std::string>());

    nProc++;
  }
}

std::vector<std::string> PConfig::GetPaths(uint32_t i) const{
  return paths.at(i);
}

std::string PConfig::GetName(uint32_t i) const{
  return names.at(i);
}

int8_t PConfig::GetType(uint32_t i) const{
  return types.at(i);
}

int16_t PConfig::GetColor(uint32_t i) const{
  return colors.at(i);
}

double PConfig::GetXSection(uint32_t i) const{
  return xSections.at(i);
}

uint64_t PConfig::GetTotEvents(uint32_t i) const{
  return totEvents.at(i);
}

std::string PConfig::GetTreeName(uint32_t i) const{
  return treeNames.at(i);
}

std::string PConfig::GetEvtWeight(uint32_t i) const{
  return evtWeights.at(i);
}

uint32_t PConfig::GetNProc(void) const{
  return nProc;
}

uint32_t PConfig::GetNInputVars(void) const{
  return nInputVars;
}

std::string PConfig::GetAnaName(void) const{
  return anaName;
}

std::string PConfig::GetOutputDir(void) const{
  return outputDir;
}

std::string PConfig::GetOutputName(void) const{
  return outputName;
}

std::string PConfig::GetTopology(void) const{
  return topology;
}

std::string PConfig::GetMvaMethod(void) const{
  return mvaMethod;
}

uint64_t PConfig::GetIterations(void) const{
  return iterations;
}

uint64_t PConfig::GetTrainEntries(void) const{
  return trainEntries;
}

std::string PConfig::GetCommonEvtWeight(void) const{
  return commonEvtWeight;
}

double PConfig::GetWorkingPoint(void) const{
  return workingPoint;
}

double PConfig::GetLumi(void) const{
  return lumi;
}

int16_t PConfig::GetHistBins(void) const{
  return histBins;
}

int16_t PConfig::GetPlotBins(void) const{
  return plotBins;
}

double PConfig::GetHistLoX(void) const{
  return histLoX;
}

double PConfig::GetHistHiX(void) const{
  return histHiX;
}

std::vector<std::string> PConfig::GetWriteOptions(void) const{
  return writeOptions;
}

std::vector<std::string> PConfig::GetOutputTasks(void) const{
  return outputTasks;
}

std::string PConfig::GetSplitMode(void) const{
  return splitMode;
}

std::string PConfig::GetSplitName(void) const{
  return splitName;
}

std::string PConfig::GetLogName(void) const{
  return logName;
}

std::string PConfig::GetInputVar(uint32_t i) const{
  return inputVars.at(i);
}

int16_t PConfig::TranslateColor(const std::string& color) const{
  int16_t finalColor = 0;

  std::vector<std::string> tempColor;
  boost::split(tempColor, color, boost::is_any_of("+"));

  if (tempColor.size() > 2) {
    std::cerr << "WARNING: Invalid color specified: " << color << std::endl;
    return 0;
  }

  if (tempColor.at(0).find("k") != std::string::npos) {
    finalColor = colorMap.at(tempColor.at(0));
    if(tempColor.size() == 2)
      finalColor += std::stoi(tempColor.at(1));
  } else {
    finalColor += std::stoi(tempColor.at(0));
  }

  return finalColor;
}

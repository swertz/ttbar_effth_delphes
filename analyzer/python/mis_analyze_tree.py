from mis_facilities import *

# usage : python python/mis_analyze_tree.py examples/mis_play.yml
cfgFile = sys.argv[1]

myConfig = PConfig(cfgFile)
inFile = myConfig.mvaCfg["outputdir"]+"/"+myConfig.mvaCfg["name"]+"_results.out"
#nameOutDir = "tests"

#print myConfig.mvaCfg
#print myConfig.procCfg

nameout = "llbbX_agressiveStoppingCriteria"
nameplus = ""
splitMode = "bothCSV_njets" #bothCSV_njets, CSVprod, jetNumb


#inFile = "results/%s/MIS_results.out"%(nameOutDir)
procList = ["DY","TT","ZZ","ZH","WW","WZ", "data_obs"]
createHistoOrderedYields(inFile,"TT", 0, procList, "data_obs")
createHistoOrderedYields(inFile,"DY", 0, procList, "")

(Dict, nbox) = getDictProc_rootFileList_nbox(myConfig, inFile)

#createRootFilesSplitted(inFile, splitMode, procList, myConfig)
fileout = writeHistoSplitted(inFile, splitMode, procList, myConfig, nameout, nameplus)
rootfileout = createHistoStat(fileout, procList, splitMode, nameout)

drawMCdata("histoMIS/histoSplittedCSV_and_nJets_%s.root"%nameout, procList, splitMode, myConfig, nbox, nameout+splitMode)

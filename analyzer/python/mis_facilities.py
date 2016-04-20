import ROOT
from ROOT import TFile, TH1F, THStack,  TCanvas, TH1D, kRed, kGreen, kBlue, kYellow, kMagenta, kCyan, kOrange, kBlack, TLegend, TTreeFormula
ROOT.PyConfig.IgnoreCommandLineOptions = True 
ROOT.gROOT.SetBatch(ROOT.kTRUE) 
from utils import PConfig, getEntriesEffentriesYieldTuple
import sys
import collections
from array import array
from math import log10
import os

def getDictProc_rootFileList(config):
    # return a dictionary with {"process_name":[list of rootfiles]} 
    listProc = config.procCfg.keys()
    fileName = config.mvaCfg["outputdir"]+"/"+config.mvaCfg["name"]+"_results.out"
    print fileName
    file = open(fileName,'r')

    lines = file.read().split("\n")
    print "number of final boxes: ", len(lines)-1
     
    Dict = {}
    for proc in listProc:
        Dict[proc]=[]

    for line in lines :
        try :
          List = line.split(":")[1].replace(config.mvaCfg["name"],config.mvaCfg["outputdir"])
        except IndexError : continue
        for process in listProc :
          fullname = List+"_proc_"+process+".root"
          Dict[process].append(fullname)

    return Dict 

def getDictProc_rootFileList_nbox(myConfig, inFile):

    listProc = myConfig.procCfg.keys()
    fileName = inFile
    print fileName
    file = open(fileName,'r')

    lines = file.read().split("\n")
    nbox=len(lines)-1
    print "number of final boxes: ", nbox

    Dict = {}
    for proc in listProc:
        Dict[proc]=[]

    for line in lines :
        try :
          List = line.split(":")[1].replace(myConfig.mvaCfg["name"],myConfig.mvaCfg["outputdir"])
        except IndexError : continue
        for process in listProc :
          fullname = List+"_proc_"+process+".root"
          Dict[process].append(fullname)
    return Dict, nbox
    

def findBestCut(Dict, listProc, box_i, myConfig):

  binning=1344
  xmin=0.68*0.68
  xmax=1.0
  step=(xmax-xmin)/binning
  
  
  allHist=TH1F("histo","histo",binning ,xmin , xmax)
  for name in listProc:
    ListSample= Dict[name]
    i=box_i
    sample=Dict[name][i-1]

    filein=TFile(sample)
    inChain = filein.Get(myConfig.procCfg[name]["treename"])
  
    histo = TH1F("histo","histo",binning ,xmin , xmax)
  
    lumi = myConfig.mvaCfg["lumi"] 
    count=0    
    for entry in xrange(inChain.GetEntries()):
          inChain.GetEntry(entry)
          count=count+1
          csv1=float(inChain.jetmetbjet1CSVdisc)
          csv2=float(inChain.jetmetbjet2CSVdisc)
          value=csv1*csv2
          histo.Fill(value)

    histo.Scale(((TTreeFormula("evtWeight",myConfig.procCfg[name]["evtweight"],inChain)).EvalInstance())*lumi*myConfig.procCfg[name]["xsection"]*count/myConfig.procCfg[name]["genevents"])
    allHist.Add(histo)
 
  
    cut=0
    integral_all=allHist.Integral()
    for j in range(0,binning):
      integral_l=allHist.Integral(0,j)
      if (integral_l >= (integral_all/2)):

	cut=j*step+xmin;
	break
      else: j=j+1
  
    return cut
  
def createRootFilesSplitted(inFile, splitMode, listProc, myConfig):
  # split rootfile according to csv scores, njets or both
 
  (Dict, nbox) = getDictProc_rootFileList_nbox(myConfig, inFile)

  
  histoList={}  
  file=open(inFile,'r')
  
  
  if splitMode=="CSVprod": 
    extraname="CSV"
    nameh1="_bc"
    nameh2="_light"    
  elif splitMode=="jetNumb":                   
    extraname="nJets"
    nameh1="_3j"
    nameh2="_2j"
  else:
    extraname="CSV_and_nJets"
    nameh1="_bc_3j"
    nameh2="_bc_2j"  
    nameh3="_light_3j"
    nameh4="_light_2j"   

  
  num_lines = sum(1 for line in open(inFile))
  
 
  
  for name in listProc:
    ListSample= Dict[name]
    i=0
    for sample in ListSample: 
      i=i+1 
      j=str(i)
      cut=0
      if   splitMode=="CSVprod" or splitMode=="bothCSV_njets": 
        cut=findBestCut(Dict, listProc, i, myConfig)
	#print cut
      filein=TFile(sample)
      print "sample in is ", sample
      fileoutname_1=str(sample).replace(".root",nameh1+".root")
      fileoutname_2=str(sample).replace(".root",nameh2+".root")
      if splitMode=="bothCSV_njets":
        fileoutname_3=str(sample).replace(".root",nameh3+".root")
        fileoutname_4=str(sample).replace(".root",nameh4+".root") 
	    
      fileOut_1 = TFile.Open(fileoutname_1,"recreate")
      fileOut_2 = TFile.Open(fileoutname_2,"recreate")
      if splitMode=="bothCSV_njets":
        fileOut_3 = TFile.Open(fileoutname_3,"recreate")
        fileOut_4 = TFile.Open(fileoutname_4,"recreate") 
	
      print "file out 1 is", fileoutname_1
	     
      inChain = filein.Get(myConfig.procCfg[name]["treename"])
    
      
      formulaNameCSV="(jetmetbjet1CSVdisc*jetmetbjet2CSVdisc)>"+str(cut)
      formulaNameJet="jetmetnj>2"  
      
      formulaCSV = TTreeFormula(splitMode,formulaNameCSV , inChain)
      formulaJet = TTreeFormula(splitMode,formulaNameJet , inChain)
      
      inChain.SetNotify(formulaCSV)
      inChain.SetNotify(formulaJet)
      
      fileOut_1.cd()
      treeOut1 = inChain.CloneTree(0)
      fileOut_2.cd()
      treeOut2 = inChain.CloneTree(0)
      if splitMode=="bothCSV_njets":
        fileOut_3.cd()
        treeOut3 = inChain.CloneTree(0)
	fileOut_4.cd()
        treeOut4 = inChain.CloneTree(0) 
	       
      for entry in xrange(inChain.GetEntries()):
        inChain.GetEntry(entry)	
	
	if splitMode=="CSVprod":
            if formulaCSV.EvalInstance() :treeOut1.Fill()
	    else:treeOut2.Fill()
	  
	elif splitMode=="bothCSV_njets":
	    if formulaCSV.EvalInstance() :
              if formulaJet.EvalInstance(): 
		treeOut1.Fill() 
              else: 
		treeOut2.Fill()                         
	    
            else:                         
              if formulaJet.EvalInstance(): 
		treeOut3.Fill() 
              else: 
		treeOut4.Fill()                        
	    
	else:
            if formulaJet.EvalInstance(): treeOut1.Fill()
            else:  treeOut2.Fill()                       
                        
	            
      
      fileOut_1.cd()  
      treeOut1.Write()
      fileOut_1.Close()  

      fileOut_2.cd()  
      treeOut2.Write()
      fileOut_2.Close() 

      if splitMode=="bothCSV_njets":
        fileOut_3.cd()  
        treeOut3.Write()
        fileOut_3.Close()  

        fileOut_4.cd()  
        treeOut4.Write()
        fileOut_4.Close()   

def writeHistoSplitted(inFile, splitMode, listProc, myConfig, nameout, nameplus):

  (Dict, nbox) = getDictProc_rootFileList_nbox(myConfig, inFile)

  
  histoList={}  
  file=open(inFile,'r')
  
  if splitMode=="CSVprod": 
    extraname="CSV"
    nameh1="_bc"
    nameh2="_light"
      
  elif splitMode=="jetNumb":                   
    extraname="nJets"
    nameh1="_3j"
    nameh2="_2j"
  else:
    extraname="CSV_and_nJets"
    nameh1="_bc_3j"
    nameh2="_bc_2j" 
    nameh3="_light_3j"
    nameh4="_light_2j"
  
  
  namefileout= "histoMIS/histoSplitted"+extraname+"_"+nameout+".root"      
  fileOut = TFile.Open(namefileout,"recreate")
  
  num_lines = sum(1 for line in open(inFile))
  print "num_lines", num_lines
  print "create histo"
  for name in listProc:
      histo_l = TH1F(name+nameh2,name+nameh2,num_lines,1,num_lines)
      histoList[name+nameh2]=histo_l
      histo_b = TH1F(name+nameh1,name+nameh1,num_lines,1,num_lines)
      histoList[name+nameh1]=histo_b
      histo_l_pure = TH1F(name+nameh2+"pure",name+nameh2+"pure",num_lines,1,num_lines)
      histoList[name+nameh2+"pure"]=histo_l_pure
      histo_b_pure = TH1F(name+nameh1+"pure",name+nameh1+"pure",num_lines,1,num_lines)
      histoList[name+nameh1+"pure"]=histo_b_pure      
      
      if splitMode=="bothCSV_njets":
        histo_l2 = TH1F(name+nameh3,name+nameh3,num_lines,1,num_lines)
        histoList[name+nameh3]=histo_l2
        histo_b2 = TH1F(name+nameh4,name+nameh4,num_lines,1,num_lines)
        histoList[name+nameh4]=histo_b2  
        histo_l2_pure = TH1F(name+nameh3+"pure",name+nameh3+"pure",num_lines,1,num_lines)
        histoList[name+nameh3+"pure"]=histo_l2_pure
        histo_b2_pure = TH1F(name+nameh4+"pure",name+nameh4+"pure",num_lines,1,num_lines)
        histoList[name+nameh4+"pure"]=histo_b2_pure  	
	
  print "filling histo"
  for name in listProc:
    print "treating process", name
    ListSample= Dict[name]
    i=0
    for sample in ListSample: 
      i=i+1
      if   splitMode=="CSVprod":
        filename1= sample.replace(".root","_bc.root")
	filename2= sample.replace(".root","_light.root")
        filein1=TFile.Open(filename1)
	filein2=TFile.Open(filename2)
      elif splitMode=="bothCSV_njets": 
        filename1=sample.replace(".root","_bc_2j.root")
        filename2=sample.replace(".root","_light_2j.root")
        filename3=sample.replace(".root","_bc_3j.root")
        filename4=sample.replace(".root","_light_3j.root") 

        filein1=TFile.Open(filename1)
	filein2=TFile.Open(filename2)
        filein3=TFile.Open(filename3)
	filein4=TFile.Open(filename4)
      else : 
        filename1=sample.replace(".root","_3j.root")
	filename2=sample.replace(".root","_2j.root")
        filein1=TFile.Open(filename1)
	filein2=TFile.Open(filename2)    

      
      lumi = myConfig.mvaCfg["lumi"]
      yield1= getEntriesEffentriesYieldTuple(filename1, myConfig.procCfg[name], lumi)[2]
      yield2= getEntriesEffentriesYieldTuple(filename2, myConfig.procCfg[name], lumi)[2]
      yield1pure= getEntriesEffentriesYieldTuple(filename1, myConfig.procCfg[name], lumi)[0]
      yield2pure= getEntriesEffentriesYieldTuple(filename2, myConfig.procCfg[name], lumi)[0]      
       
      filein1.Close() 
      filein2.Close() 
      if splitMode=="bothCSV_njets":
        yield3= getEntriesEffentriesYieldTuple(filename3, myConfig.procCfg[name], lumi)[2] 
        yield4= getEntriesEffentriesYieldTuple(filename4, myConfig.procCfg[name], lumi)[2] 
        yield3pure= getEntriesEffentriesYieldTuple(filename3, myConfig.procCfg[name], lumi)[0] 
        yield4pure= getEntriesEffentriesYieldTuple(filename4, myConfig.procCfg[name], lumi)[0] 	
	      
        filein3.Close() 
        filein4.Close()       
       
      
      if splitMode!="bothCSV_njets":            
        histoList[name+nameh1].SetBinContent(i, yield1)
        histoList[name+nameh2].SetBinContent(i, yield2)  
        histoList[name+nameh1+"pure"].SetBinContent(i, yield1pure)
        histoList[name+nameh2+"pure"].SetBinContent(i, yield2pure) 	

      else:
        histoList[name+nameh1].SetBinContent(i, yield3)
        histoList[name+nameh2].SetBinContent(i, yield1)
        histoList[name+nameh3].SetBinContent(i, yield4)
        histoList[name+nameh4].SetBinContent(i, yield2)
			            
        histoList[name+nameh1+"pure"].SetBinContent(i, yield3pure)
        histoList[name+nameh2+"pure"].SetBinContent(i, yield1pure)
        histoList[name+nameh3+"pure"].SetBinContent(i, yield4pure)
        histoList[name+nameh4+"pure"].SetBinContent(i, yield2pure)      
  fileOut .cd() 
  
  
  "writting histo"  
  for name in  listProc:        
    
    if splitMode=="bothCSV_njets": 
      histo_bl =TH1F(name+nameh1+nameh4+nameplus,name+nameh1+nameh4,num_lines*4,1,num_lines*4)
      histo_bl_pure =TH1F(name+nameh1+nameh4+"pure",name+nameh1+nameh4+"pure",num_lines*4,1,num_lines*4)
    else:                        
      histo_bl =TH1F(name+nameh1+nameh2+nameplus,name+nameh1+nameh2,num_lines*2,1,num_lines*2)
      histo_bl_pure =TH1F(name+nameh1+nameh2+"pure",name+nameh1+nameh2+"pure",num_lines*2,1,num_lines*2)
     
    
    for i in range(1,num_lines+1):
      print i
      if splitMode=="bothCSV_njets":
        histo_bl.SetBinContent(i,histoList[name+nameh1].GetBinContent(i))
        histo_bl.SetBinContent(i+num_lines,histoList[name+nameh2].GetBinContent(i))
        histo_bl.SetBinContent(i+num_lines*2,histoList[name+nameh3].GetBinContent(i))
        histo_bl.SetBinContent(i+num_lines*3,histoList[name+nameh4].GetBinContent(i))
	
        histo_bl_pure.SetBinContent(i,histoList[name+nameh1+"pure"].GetBinContent(i))
        histo_bl_pure.SetBinContent(i+num_lines,histoList[name+nameh2+"pure"].GetBinContent(i))
        histo_bl_pure.SetBinContent(i+num_lines*2,histoList[name+nameh3+"pure"].GetBinContent(i))
        histo_bl_pure.SetBinContent(i+num_lines*3,histoList[name+nameh4+"pure"].GetBinContent(i))	
	
      else:
        histo_bl.SetBinContent(i,histoList[name+nameh1].GetBinContent(i))
        histo_bl.SetBinContent(i+num_lines,histoList[name+nameh2].GetBinContent(i))      
        histo_bl_pure.SetBinContent(i,histoList[name+nameh1+"pure"].GetBinContent(i))
        histo_bl_pure.SetBinContent(i+num_lines,histoList[name+nameh2+"pure"].GetBinContent(i))  

    histoList[name+nameh1+"pure"].Write()
    histoList[name+nameh2+"pure"].Write()
    histoList[name+nameh1].Write()
    histoList[name+nameh2].Write()	
    if splitMode=="bothCSV_njets":
        histoList[name+nameh3+"pure"].Write()
        histoList[name+nameh4+"pure"].Write()
        histoList[name+nameh3].Write()
        histoList[name+nameh4].Write()     
      
    histo_bl.Write()
    histo_bl_pure.Write()
      
  fileOut.Close() 
  
  return namefileout

def createHistoStat(inFile, listProc, splitMode, nameout):

    nameOut= "histoMIS/histoSplitted_withErrStat"+nameout+splitMode+".root"
    fileOut = TFile.Open(nameOut,"recreate")

    fileIn = TFile.Open(inFile,"read")


    print "compute error stat"
    for proc in listProc:
      print "treating process", proc
      histo = TH1F()
      
      if splitMode=="bothCSV_njets": histoname=proc+"_bc_3j_light_2jpure"
      elif splitMode== "CSVprod": histoname=proc+"_bc_lightpure"
      else: histoname=proc+"_2j_3jpure"
      histopure = fileIn.Get(histoname)
      histo = fileIn.Get(histoname.replace("pure",""))
      

      binning=histo.GetNbinsX()
      
      fileOut.cd()
      histo.Write()
         
      for bin in range(1,binning+1):
#	 a=histopure.GetBinErrorLow(bin)
#	 b=histopure.GetBinErrorUp(bin)
	 aw = histopure.GetBinContent(bin)
	 #if aw > 5: 
	 a=ROOT.TMath.Sqrt(aw) 
	 b=ROOT.TMath.Sqrt(aw) 
#	 else :
#	   a=ROOT.TMath.Poisson(aw,5)
#	   b=ROOT.TMath.Poisson(aw,5)	  
	 
	 if histopure.GetBinContent(bin)!=0: wht= histo.GetBinContent(bin)/histopure.GetBinContent(bin)
	 else: wht=0
#	 if aw>0 : a=a/aw
#	 if aw>0 : b=b/aw
	 histo_up=   histo.Clone(histoname.replace("pure","")+"_"+proc+"_"+"stat_bin"+str(bin)+"Up")
	 histo_down= histo.Clone(histoname.replace("pure","")+"_"+proc+"_"+"stat_bin"+str(bin)+"Down")
	 

   	 tmp = histopure.GetBinContent(bin)
	 if aw>0 :
	       histo_up.SetBinContent(bin,(tmp+b)*wht)
	       histo_down.SetBinContent(bin,(tmp-a)*wht)
	 else :
	       histo_up.SetBinContent(bin,0)
   
         fileOut.cd()
	 histo_up.Write()
         histo_down.Write()
	 
    fileOut.Close()  
    return  nameOut 

def createHisto(inFile):
  # create histogram with yields in each box
  listProc=["DYbx","DYbb_xx","TT","ZZ","ZH","WW","WZ","Data"]
  outRootFile="histo.root"
  
  file=open(inFile,'r')
  fileOut = TFile.Open(outRootFile,"recreate")
  
  num_lines = sum(1 for line in open(inFile))
  
  print "number of final boxes: ", num_lines
  
  histoList={}
  for name in  listProc:
    histo = TH1F(name,name,num_lines,1,num_lines)
    histoList[name]=histo
  
  lines=file.read().split("\n")
  i=0
  for line in lines :
    try :
      List= line.split(":")[2]
    except IndexError : continue
    i=i+1
    processes= List.split(",")
    
    
    for proc in processes:
        if proc =="": continue
        name=proc.split("=")[0]
	yields=proc.split("=")[1]
	yields=float(yields)
	if name in  listProc:	  
	  histoList[name].SetBinContent(i,yields)
	  
  for name in  listProc:    histoList[name].Write()
  
  fileOut.Close()
  
def createHistoOrderedYields(inFile, processOrdered, doKolmoTest, listProc, dataName = ""):
  # create histogram with yields in each box, ordered according to a given process decreasing yield
  outDir = inFile.replace(inFile.split("/")[-1],"")+"/"
  outRootFile = outDir + "histoOrder_"+processOrdered+".root"
  print outRootFile
  
  file=open(inFile,'r')
  fileOut = TFile.Open(outRootFile,"recreate")
  
  num_lines = sum(1 for line in open(inFile))
  
  print "number of final boxes: ", num_lines
  

  yieldsDic={}  
  for proc in listProc:
    yieldsDic[proc]=[]
    
  histoList={}
  
  for name in  listProc:
    histo = TH1F(name,name,num_lines,1,num_lines)
    histoList[name]=histo
  
  lines=file.read().split("\n")
  i=0
  for line in lines :
    try :
      List= line.split(":")[2]
    except IndexError : continue
    i=i+1
    processes= List.split(",")
    
    
    for proc in processes:
        #print "proc is", proc
        if proc =="": continue
        name=proc.split("=")[0]
	yields=proc.split("=")[1]
	yields=float(yields)
	if name in  listProc:
          yieldsDic[name].append(yields)

  yieldsRev=[]
  if processOrdered != "All":  # FIXME 
    yieldsRev=sorted(yieldsDic[processOrdered], reverse=True)

  for j in range(0, len(yieldsRev)):
    histoList[processOrdered].SetBinContent(j+1,yieldsRev[j])
  
  
  for name in listProc:
    if name==processOrdered: continue
    for j in range(0,len(yieldsRev)):
      for i in range (0,len(yieldsDic[name])):  
        if yieldsRev[j]==yieldsDic[processOrdered][i]:
	  histoList[name].SetBinContent(j+1,yieldsDic[name][i])
	  
  histoAllMC = TH1F("histoAllMC","histoAllMC",num_lines,1,num_lines)   
  stack = THStack("stackMC","stackMC")
  	  
  for name in  listProc: 
      if "ata" in name : continue
      if name=="DYbb_xx":   histoList[name].SetFillColor(600)
      if name=="DYbx":   histoList[name].SetFillColor(600-4)
      if name=="DYxx":   histoList[name].SetFillColor(600-4)
      if name=="DY" : histoList[name].SetFillColor(600)
      if name=="TT":   histoList[name].SetFillColor(5)
      if name=="ZH":   histoList[name].SetFillColor(1)
      if name=="ZZ":   histoList[name].SetFillColor(6)
      if name=="WZ":   histoList[name].SetFillColor(7)
      if name=="WW":   histoList[name].SetFillColor(kOrange) 
      stack.Add(histoList[name])  
      histoAllMC.Add(histoList[name])
       
    #histoList[name].Write()
  C = TCanvas("CANVAS","CANVAS",1200,600) 
  stack.Draw()
  if dataName != "" : 
      histoList[dataName].SetMarkerStyle(20)  
      histoList[dataName].Draw("sameE1")
  C.Write()
  C.SaveAs(outDir+"histoOrder_"+processOrdered+".png")
  
  if doKolmoTest: 
    kolmoTH1 = TH1D("kolmoTH1" + processOrdered,"kolmoTH1" + processOrdered, 500, -0.001, 1) 
    chi2TH1 = TH1D("chi2TH1" + processOrdered,"chi2TH1" + processOrdered, 500, -0.001, 1) 
    kolmoTestRes= histoAllMC.KolmogorovTest(histoList[dataName])
    chi2res= histoAllMC.Chi2Test(histoList[dataName])
    kolmoTH1.Fill(kolmoTestRes)
    kolmoTH1.Write()
    chi2TH1.Fill(chi2res)
    chi2TH1.Write()
    
    #fileOutTest = open('resultStatTests.out','w')
    #fileOutTest.write("result of Kolmo test is "+str(kolmoTestRes)+" for yields ordered according to " + processOrdered + " process \n")
    #fileOutTest.write("result of chi2 test is "+str(chi2res)+"\n")
    
  fileOut.Close()  


def drawMCdata(inFile, listProc, splitMode, myConfig, nbox, nameout):
    
    fileOut = TFile.Open("PlotsMIS/Plots_"+nameout+".root","recreate")
    fileIn = TFile.Open(inFile,"read")
     
    histonameList=[]


    if splitMode=="bothCSV_njets": 
      histoname1="_bc_3j_light_2j"
      histoname2="_bc_2j"	 
      histoname3="_bc_3j"
      histoname4="_light_3j"	 
      histoname5="_light_2j"
      histonameList.append(histoname1)
      histonameList.append(histoname2)        
      histonameList.append(histoname3)        
      histonameList.append(histoname4)        
      histonameList.append(histoname5)        

    elif splitMode=="CSVprod": 
      histoname1="_bc_light"
      histoname2="_bc"
      histoname3="_light"
      histonameList.append(histoname1)
      histonameList.append(histoname2)        
      histonameList.append(histoname3)        

    else: 
      histoname1="_2j_3j"
      histoname2="_3j"        
      histoname3="_2j" 
      histonameList.append(histoname1)
      histonameList.append(histoname2)        
      histonameList.append(histoname3)
   
       
    for histname in histonameList:
      i=0    
      histoAllMC   = TH1F()
      histoAllMCstat   = TH1F()   
      histodata    = TH1F()  
      histoZH      = TH1F()   
      histoZA      = TH1F()         
      stack        = THStack()
    
      newhist      = TH1F()    
      newhist_data = TH1F() 
      newhist_ZH   = TH1F() 
      newhist_ZA   = TH1F()
      
      C1 = TCanvas("CANVAS1 yields "+histname+"ZH","CANVAS1 yields "+histname+"ZH",1200,600) 
      C2 = TCanvas("CANVAS2 yields ordered "+histname+"ZH","CANVAS2 yields ordered "+histname+"ZH",1200,600)
      C3 = TCanvas("CANVAS1 yields "+histname+"ZA","CANVAS1 yields "+histname+"ZA",1200,600)
      C4 = TCanvas("CANVAS2 yields ordered "+histname+"ZA","CANVAS2 yields ordered "+histname+"ZA",1200,600)
      C5 = TCanvas("CANVAS1"+histname+"ZH significance","CANVAS1"+histname+"ZH significance",1200,600)
      C6 = TCanvas("CANVAS2"+histname+"ZA significance","CANVAS2"+histname+"ZA significance",1200,600)      
      
      
      legend=TLegend(0.50,0.70,0.80,0.80)
      
      print "create plots"
      
      for proc in listProc:
        histo = TH1F()
        histo = fileIn.Get(proc+histname)

        i=i+1
        if "data" not in proc:       
          if proc=="DYbb": histo.SetFillColor(2)
          elif proc=="DYbx": histo.SetFillColor(3)
	  elif proc=="DYxx": histo.SetFillColor(4)
          elif proc=="TT":   histo.SetFillColor(5)
          elif proc=="ZZ":   histo.SetFillColor(6)
          elif proc=="WZ":   histo.SetFillColor(7)
          elif proc=="WW":   histo.SetFillColor(kOrange) 
          elif proc=="ZA": 
	    histo.SetLineColor(9)
	    histo.SetLineWidth(2)
	    histoZA=histo.Scale(7.6)
	    histoZA=histo.Clone()
	    
	  elif proc=="ZH":
	    
	    histo.SetLineColor(2)
	    histo.SetLineWidth(2)     
	    histo.Scale(76)#76
	    histoZH=histo.Clone()
	  if proc!="ZA" and  proc!="ZH":
	    stack.Add(histo)  
            if i==1:
	      histoAllMC=histo.Clone()
	      histoAllMCstat=histo.Clone()
	    else: 
	      histoAllMC.Add(histo)
	      histo1=histo.Clone()
	      histo1.Sumw2()
	      histoAllMCstat.Add(histo1)	    
        else: histodata=histo.Clone()
	
        if proc=="ZH":legend.AddEntry(histo, proc+" x 100")
	elif "data" in proc:legend.AddEntry(histodata, "Data (19.7 fb^{-1})")
	else: legend.AddEntry(histo, proc)
	
##########create extra histograms ##################################################################       

      mc_uncertainty=histoAllMCstat.Clone() 
      mc_uncertainty.Divide(histoAllMCstat)
      for i in range (0,mc_uncertainty.GetNbinsX()) :
        if mc_uncertainty.GetBinContent(i)==0:
          mc_uncertainty.SetBinContent(i,1)
          mc_uncertainty.SetBinError(i,1) 
	      
      binning=histoAllMC.GetNbinsX()
      
      listYield={}  
      listSigniZH={} 
      listSigniZA={}
      
      for i in range(1, binning+1):
        yields= histoAllMC.GetBinContent(i)
	sigZH= (ROOT.TMath.Sqrt(histoZH.GetBinContent(i)+histoAllMC.GetBinContent(i))-ROOT.TMath.Sqrt(histoAllMC.GetBinContent(i)))
	sigZA= (ROOT.TMath.Sqrt(histoZA.GetBinContent(i)+histoAllMC.GetBinContent(i))-ROOT.TMath.Sqrt(histoAllMC.GetBinContent(i)))
        listYield[i-1]=yields
        listSigniZH[i-1]=sigZH
	listSigniZA[i-1]=sigZA
	
      newdict=collections.OrderedDict(sorted(listYield.items(), key=lambda t: t[1]))
      newdictZH=collections.OrderedDict(sorted(listSigniZH.items(), key=lambda t: t[1]))
      newdictZA=collections.OrderedDict(sorted(listSigniZA.items(), key=lambda t: t[1]))
      
      newhist     =histoAllMC.Clone()
      newhist_ZH  =histoZH.Clone()
      newhist_ZA  =histoZA.Clone()
      newhist_data=histodata.Clone()
      
      newhistsigzh     =histoAllMC.Clone()
      newhistsigza     =histoAllMC.Clone()
      newhist_sigZH    =histoZH.Clone()
      newhist_sigZA    =histoZA.Clone()
      newhist_sigdatazh=histodata.Clone()      
      newhist_sigdataza=histodata.Clone() 
      
      histoAllMCstat_new  =histoAllMCstat.Clone()    
      histoAllMCstat_new2 =histoAllMCstat.Clone()    
      histoAllMCstat_new3 =histoAllMCstat.Clone()    
      	
      i=binning
      for key in newdict:
          cont=newdict[key]
          newhist.SetBinContent(i,cont)
          newhist_data.SetBinContent(i,histodata.GetBinContent(key+1))
          newhist_ZH.SetBinContent(i,histoZH.GetBinContent(key+1))
          newhist_ZA.SetBinContent(i,histoZA.GetBinContent(key+1))
	  histoAllMCstat_new.SetBinContent(i,histoAllMCstat.GetBinContent(key+1))
	  histoAllMCstat_new.SetBinError(i,histoAllMCstat.GetBinError(key+1))
          i=i-1
	  
      izh=binning
      for key in newdictZH:
          cont=newdictZH[key]
          newhistsigzh.SetBinContent(izh,histoAllMC.GetBinContent(key+1))
          newhist_sigdatazh.SetBinContent(izh,histodata.GetBinContent(key+1))
          newhist_sigZH.SetBinContent(izh,histoZH.GetBinContent(key+1))
          newhist_sigZA.SetBinContent(izh,histoZA.GetBinContent(key+1))
	  histoAllMCstat_new2.SetBinContent(izh,histoAllMCstat.GetBinContent(key+1))
	  histoAllMCstat_new2.SetBinError(izh,histoAllMCstat.GetBinError(key+1))
          izh=izh-1
	      
	  
      mc_uncertainty_new=histoAllMCstat_new.Clone() 
      mc_uncertainty_new.Divide(histoAllMCstat_new)
	  
      mc_uncertainty_new2=histoAllMCstat_new2.Clone() 
      mc_uncertainty_new2.Divide(histoAllMCstat_new2)
 
	    
      mc_uncertainty_new3=histoAllMCstat_new3.Clone() 
      mc_uncertainty_new3.Divide(histoAllMCstat_new3)

	  	  
      newhist.SetFillColor(17)
      newhist_data.SetMarkerStyle(20)
      
      newhistsigzh.SetFillColor(27)
      newhist_sigdatazh.SetMarkerStyle(20)     
      
      newhistsigza.SetFillColor(27)
      newhist_sigdataza.SetMarkerStyle(20)  
      
      histodata.SetMarkerStyle(20)
      
      legendZH=TLegend(0.50,0.70,0.80,0.80)
      legendZH.AddEntry(newhist, "Total MC")
      legendZH.AddEntry(newhist_data, "Data (19.7 fb^{-1})")
      legendZH.AddEntry(histoZH, "ZH x 100")
      
      legendZA=TLegend(0.50,0.70,0.80,0.80)
      legendZA.AddEntry(newhist, "Total MC")
      legendZA.AddEntry(histodata, "Data (19.7 fb^{-1})")
      legendZA.AddEntry(histoZH, "ZH x CLs x 20") 
      legendZA.AddEntry(histoZA, "ZA x CLs x 20")
      
      legendSigZH=TLegend(0.50,0.70,0.80,0.80)
      legendSigZH.AddEntry(newhistsigzh, "Total MC")
      legendSigZH.AddEntry(newhist_sigdatazh, "Data (19.7 fb^{-1})")
      legendSigZH.AddEntry(histoZH, "ZH x CLs x 20")
      legendSigZH.AddEntry(histoZA, "ZA x CLs x 20")
      
      legendSigZA=TLegend(0.50,0.70,0.80,0.80)
      legendSigZA.AddEntry(newhistsigza, "Total MC")
      legendSigZA.AddEntry(newhist_sigdatazh, "Data (19.7 fb^{-1})")
      legendSigZA.AddEntry(histoZH, "ZH x CLs x 20") 
      legendSigZA.AddEntry(histoZA, "ZA x CLs x 20") 	
	
	
	
	
      ######################################################################################################################
      C1.Divide(1,2)
      
      C1.cd(1)
      stack.Draw()
      histoZH.GetYaxis().SetTitle("# of events")
      histoZH.GetXaxis().SetTitle("Box event yields")
      histoZH.GetXaxis().SetLabelSize(0.05)
      histoZH.GetYaxis().SetLabelSize(0.05)      
      histoZH.GetXaxis().SetTitleSize(0.07)
      histoZH.GetYaxis().SetTitleSize(0.05)      
      histoZH.GetYaxis().SetTitleOffset( 0.3 )
      histoZH.GetXaxis().SetTitleOffset( 0.3 )      
      histodata.Draw("sameE1")
      histoZH.Draw("same")    
      legend.Draw()

           
      C1.cd(2)
      histo_ratio=histodata.Clone()
      histo_ratio.SetName("histo_ratio")
      histo_ratio.SetTitle("")
      histo_ratio.Sumw2()
      histo_ratio.Divide(histoAllMC)
   
      mc_uncertainty.SetFillColor(kYellow) 

      mc_uncertainty.GetYaxis().SetRangeUser(-1.0,5.0)
      mc_uncertainty.Draw("E3")
      mc_uncertainty.GetYaxis().SetTitle("Data/MC")
      mc_uncertainty.GetXaxis().SetTitle("Box event yields")
      mc_uncertainty.GetYaxis().SetTitleFont(42)
      mc_uncertainty.GetYaxis().SetTitleOffset( 0.2 )
      mc_uncertainty.GetXaxis().SetTitleOffset( 0.2 )
      mc_uncertainty.GetYaxis().SetTitleSize( 0.07 )
      mc_uncertainty.GetYaxis().SetLabelFont(42)
      mc_uncertainty.GetYaxis().SetLabelSize(0.05)
      mc_uncertainty.GetYaxis().SetNdivisions( 505 )
      mc_uncertainty.GetXaxis().SetTitleFont(42)
      mc_uncertainty.GetXaxis().SetTitleSize( 0.07 )
      mc_uncertainty.GetXaxis().SetLabelSize(0.05)
      mc_uncertainty.GetXaxis().SetLabelFont(42)
      mc_uncertainty.GetXaxis().SetRange(histodata.GetXaxis().GetFirst(), histodata.GetXaxis().GetLast())
      mc_uncertainty.GetXaxis().SetNdivisions(10, 2, 0, True)
      
      histo_ratio.SetMarkerStyle(20)
      histo_ratio.SetMarkerSize(0.7)

      histo_ratio.Draw("E1X0 same")
      mc_uncertainty.Draw("AXIG same")
      ######################################################################################################################
        
      C3.cd()
      stack.Draw()
      histoZA.GetYaxis().SetTitle("# of events")
      histoZA.GetXaxis().SetTitle("Box event yields")
      histoZA.GetXaxis().SetLabelSize(0.10)
      histoZA.GetYaxis().SetLabelSize(0.10)       
      
      histodata.Draw("sameE1")
      histoZA.Draw("same") 
      legend.Draw()
     

      ######################################################################################################################
    
      
      C2.Divide(1,2)      
      C2.cd(1)      
      ###################################################################################################################
      
      newhist.GetYaxis().SetTitle("# of events")
      newhist.GetXaxis().SetTitle("Box event yields ordered by increasing yields")
      newhist.GetXaxis().SetLabelSize(0.10)
      newhist.GetYaxis().SetLabelSize(0.10)      
      newhist.GetXaxis().SetTitleSize(0.07)
      newhist.GetYaxis().SetTitleSize(0.05)      
      newhist.GetYaxis().SetTitleOffset( 0.3 )
      newhist.GetXaxis().SetTitleOffset( 0.3 )
      newhist.Draw()
      newhist_data.Draw("sameE1") 
      newhist_ZH.Draw("same")     
      legendZH.Draw() 
            
      C2.cd(2)
      histo_ratio3=newhist_data.Clone()
      histo_ratio3.SetName("histo_ratio3")
      histo_ratio3.SetTitle("")
      histo_ratio3.Sumw2()
      histo_ratio3.Divide(newhist)
      
      mc_uncertainty_new.SetFillColor(kYellow) 
      mc_uncertainty_new.GetYaxis().SetRangeUser(-1.0,5.0)
      mc_uncertainty_new.Draw("E3")
      mc_uncertainty_new.GetYaxis().SetTitle("Data/MC")
      mc_uncertainty_new.GetXaxis().SetTitle("Box event yields")
      mc_uncertainty_new.GetYaxis().SetTitleFont(42)
      mc_uncertainty_new.GetYaxis().SetTitleOffset( 0.3 )
      mc_uncertainty_new.GetXaxis().SetTitleOffset( 0.3 )
      mc_uncertainty_new.GetYaxis().SetTitleSize( 0.05 )
      mc_uncertainty_new.GetYaxis().SetLabelFont(42)
      mc_uncertainty_new.GetYaxis().SetLabelSize(0.05)
      mc_uncertainty_new.GetYaxis().SetNdivisions( 505 )
      mc_uncertainty_new.GetXaxis().SetTitleFont(42)
      mc_uncertainty_new.GetXaxis().SetTitleSize( 0.07 )
      mc_uncertainty_new.GetXaxis().SetLabelSize(0.05)
      mc_uncertainty_new.GetXaxis().SetLabelFont(42)
      mc_uncertainty_new.GetXaxis().SetRange(newhist_data.GetXaxis().GetFirst(), newhist_data.GetXaxis().GetLast())
      mc_uncertainty_new.GetXaxis().SetNdivisions(10, 2, 0, True)
      
      histo_ratio3.SetMarkerStyle(20)
      histo_ratio3.SetMarkerSize(0.7)

      histo_ratio3.Draw("E1X0 same")
      mc_uncertainty_new.Draw("AXIG same")
      ######################################################################################################################  
     
       
      C4.Divide(1,2)
      C4.cd(1)      
      newhist.GetYaxis().SetTitle("# of events")
      newhist.GetXaxis().SetTitle("Box event yields ordered by increasing yields")
      newhist.GetXaxis().SetLabelSize(0.05)
      newhist.GetYaxis().SetLabelSize(0.05)      
      newhist.GetXaxis().SetTitleSize(0.07)
      newhist.GetYaxis().SetTitleSize(0.05)      
      newhist.GetYaxis().SetTitleOffset( 0.3 )
      newhist.GetXaxis().SetTitleOffset( 0.3 )
      newhist.Draw()
      newhist_data.Draw("sameE1") 
      newhist_ZA.Draw("same")      
      newhist_ZH.Draw("same") 
      legendZA.Draw()
       
      C4.cd(2)      
      histo_ratio33=newhist_data.Clone()
      histo_ratio33.SetName("histo_ratio33")
      histo_ratio33.SetTitle("")
      histo_ratio33.Sumw2()
      histo_ratio33.Divide(newhist)
    
      
      mc_uncertainty_new.SetFillColor(kYellow) 
      mc_uncertainty_new.GetYaxis().SetRangeUser(-1.0,5.0)
      mc_uncertainty_new.Draw("E3")
      mc_uncertainty_new.GetYaxis().SetTitle("Data/MC")
      mc_uncertainty_new.GetXaxis().SetTitle("Box event yields")
      mc_uncertainty_new.GetYaxis().SetTitleFont(42)
      mc_uncertainty_new.GetYaxis().SetTitleOffset( 0.3 )
      mc_uncertainty_new.GetXaxis().SetTitleOffset( 0.3 )
      mc_uncertainty_new.GetYaxis().SetTitleSize( 0.05 )
      mc_uncertainty_new.GetYaxis().SetLabelFont(42)
      mc_uncertainty_new.GetYaxis().SetLabelSize(0.05)
      mc_uncertainty_new.GetYaxis().SetNdivisions( 505 )
      mc_uncertainty_new.GetXaxis().SetTitleFont(42)
      mc_uncertainty_new.GetXaxis().SetTitleSize( 0.07 )
      mc_uncertainty_new.GetXaxis().SetLabelSize(0.05)
      mc_uncertainty_new.GetXaxis().SetLabelFont(42)
      mc_uncertainty_new.GetXaxis().SetRange(newhist_data.GetXaxis().GetFirst(), newhist_data.GetXaxis().GetLast())
      mc_uncertainty_new.GetXaxis().SetNdivisions(10, 2, 0, True)
      mc_uncertainty_new.Draw("AXIG same") 
              
      histo_ratio33.SetMarkerStyle(20)
      histo_ratio33.SetMarkerSize(0.7)
      histo_ratio33.Draw("E1X0 same")    
      
      ###################################################################################################################
      
      C5.Divide(1,2)
      C5.cd(1)      
      newhistsigzh.GetYaxis().SetTitle("# of events")
      newhistsigzh.GetXaxis().SetTitle("Box event yields ordered by S/B")
      newhistsigzh.GetXaxis().SetLabelSize(0.05)
      newhistsigzh.GetYaxis().SetLabelSize(0.05)      
      newhistsigzh.GetXaxis().SetTitleSize(0.07)
      newhistsigzh.GetYaxis().SetTitleSize(0.05)      
      newhistsigzh.GetYaxis().SetTitleOffset( 0.3 )
      newhistsigzh.GetXaxis().SetTitleOffset( 0.3 )
      newhistsigzh.Draw()
      newhist_sigdatazh.Draw("sameE1") 
      newhist_sigZH.Draw("same") 
      newhist_sigZA.Draw("same")  
      legendSigZH.Draw()       
      ###################################################################################################################
           
      C5.cd(2)
      histo_ratio2=newhist_sigdatazh.Clone()
      histo_ratio2.SetName("histo_ratio2")
      histo_ratio2.SetTitle("")
      histo_ratio2.Sumw2()
      histo_ratio2.Divide(newhistsigzh)     
      
      
      mc_uncertainty_new2.SetFillColor(kYellow) 
      mc_uncertainty_new2.GetYaxis().SetRangeUser(-1.0,5.0)
      mc_uncertainty_new2.Draw("E3")
      mc_uncertainty_new2.GetYaxis().SetTitle("Data/MC")
      mc_uncertainty_new2.GetXaxis().SetTitle("Box event yields")
      mc_uncertainty_new2.GetYaxis().SetTitleFont(42)
      mc_uncertainty_new2.GetYaxis().SetTitleOffset( 0.3 )
      mc_uncertainty_new2.GetXaxis().SetTitleOffset( 0.3 )
      mc_uncertainty_new2.GetYaxis().SetTitleSize( 0.05 )
      mc_uncertainty_new2.GetYaxis().SetLabelFont(42)
      mc_uncertainty_new2.GetYaxis().SetLabelSize(0.05)
      mc_uncertainty_new2.GetYaxis().SetNdivisions( 505 )
      mc_uncertainty_new2.GetXaxis().SetTitleFont(42)
      mc_uncertainty_new2.GetXaxis().SetTitleSize( 0.07 )
      mc_uncertainty_new2.GetXaxis().SetLabelSize(0.05)
      mc_uncertainty_new2.GetXaxis().SetLabelFont(42)
      mc_uncertainty_new2.GetXaxis().SetRange(newhist_sigdatazh.GetXaxis().GetFirst(), newhist_sigdatazh.GetXaxis().GetLast())
      mc_uncertainty_new2.GetXaxis().SetNdivisions(10, 2, 0, True)
      
      histo_ratio2.SetMarkerStyle(20)
      histo_ratio2.SetMarkerSize(0.7)

      histo_ratio2.Draw("E1X0 same")
      mc_uncertainty_new2.Draw("AXIG same")
      
                     
      fileOut.cd()
      C1.Write()
      C2.Write() 
      C3.Write()
      C4.Write()
      C5.Write()
      
      chi2= histoAllMC.Chi2Test(histodata,"CHI2/NDF") 
      print "chi2 test gives " , chi2

def cardWriter_shape(myConfig, inrootfile, listProc, splitMode, nbox, nameout) :
# Takes a .yml specific for fits and limit in argument


    analysisName = myConfig.mvaCfg["name"]
    cardDir = "CardZH" + "/" + analysisName +"_"+nameout+splitMode+ "_combineCard.txt"
    cardFile = open(cardDir, 'w')
    
    fileIn = TFile.Open(inrootfile,"read")

      
    if splitMode=="bothCSV_njets": histoname="_bc_3j_light_2j"
    elif splitMode== "CSVprod": histoname="_bc_light"
    else: histoname="_2j_3j"
    
    if splitMode=="bothCSV_njets": binning=nbox*4
    else: binning=nbox*2

    cardFile.write("#Card for a simple counting experiment\n")
    cardFile.write("imax {0}  number of channelsi\n".format(1))
    cardFile.write("jmax {0}  number of backgrounds\n".format(7)) #   .format(nProc))
    cardFile.write("kmax {0}  number of nuisance parameters \n".format((binning*8)+12))
    cardFile.write("shapes * *  "+inrootfile+"    $PROCESS"+histoname+"  $PROCESS"+histoname+"$SYSTEMATIC  \n")
    cardFile.write("------------------------\n")
    cardFile.write("bin          {0} \n".format(1))
    cardFile.write("observation  {0} \n".format(-1))
   
    cardFile.write(" # number of expected events, per source\n") 
    cardFile.write("bin             1          1    1   1   1  1    1     1     \n")
    cardFile.write("process         ZH         ZZ   WZ  WW  TT DYbb DYbx  DYxx  \n") 
    cardFile.write("process         0          1    2   3   4  5    6     7     \n")
    cardFile.write("rate            -1         -1   -1  -1  -1 -1   -1    -1    \n")
    cardFile.write("------------------------------------------------------------\n")
    
    cardFile.write("# the description of the systematic uncertainties\n")
    
    cardFile.write("Btag_bc      shape 1 1 1 1 1 1 1 1 \n")
    cardFile.write("Btag_light   shape 1 1 1 1 1 1 1 1 \n")
    cardFile.write("JES          shape 1 1 1 1 1 1 1 1 \n") 
    cardFile.write("JER          shape 1 1 1 1 1 1 1 1 \n")
    cardFile.write("bgnorm1      lnN   1.0 1.0	 1.0   1.0  1.00249 0.99046  0.98851  1.09533 \n")
    cardFile.write("bgnorm2      lnN   1.0 1.0	 1.0   1.0  1.02739 0.970966 0.981492 0.973434 \n")
    cardFile.write("bgnorm3      lnN   1.0 1.0	 1.0   1.0  1.01102 1.03613  0.970716 0.99687 \n")
    cardFile.write("bgnorm4      lnN   1.0 1.0	 1.0   1.0  1.02966 1.0142   1.02894  1.01769 \n")
    cardFile.write("bgnorm5      lnN   1.0 1.15	 1.0   1.0  1.0     1.0      1.0      1.0 \n")
    cardFile.write("lepunc       lnN   1.04 1 1 1 1 1 1 1 \n")
    cardFile.write("lumi  	 lnN   1.044 1.044 1 1 1 1 1 1 \n")
    cardFile.write("signorm 	 lnN   1.04 1 1 1 1 1 1 1 \n")
    for proc in listProc:
    
      if   "ZH" in proc  : stringplus="1 - - - - - - -"
      elif "ZZ" in proc  : stringplus="- 1 - - - - - -"
      elif "WZ" in proc  : stringplus="- - 1 - - - - -"
      elif "WW" in proc  : stringplus="- - - 1 - - - -"
      elif "TT" in proc  : stringplus="- - - - 1 - - -"
      elif "DYbb" in proc: stringplus="- - - - - 1 - -"
      elif "DYbx" in proc: stringplus="- - - - - - 1 -"
      elif "DYxx" in proc: stringplus="- - - - - - - 1"
      else: break
      
      for i in range(0, binning):
        cardFile.write("_"+proc+"_"+"stat_bin{0}  shape ".format(i+1)+stringplus+" \n")  
   
    cardFile.write("# end of card")
    
def cardWriter_shapeZA(myConfig, inrootfile, listProc, splitMode, nbox, nameout) :
# Takes a .yml specific for fits and limit in argument


    analysisName = myConfig.mvaCfg["name"]
    cardDir = myConfig.mvaCfg["outputdir"] + "/" + analysisName +"_"+nameout+splitMode+ "_ZA_combineCard.txt"
    cardFile = open(cardDir, 'w')
    
    fileIn = TFile.Open(inrootfile,"read")

      
    if splitMode=="bothCSV_njets": histoname="_bc_3j_light_2j"
    elif splitMode== "CSVprod": histoname="_bc_light"
    else: histoname="_2j_3j"
    
    if splitMode=="bothCSV_njets": binning=nbox*4
    else: binning=nbox*2

    cardFile.write("#Card for a simple counting experiment\n")
    cardFile.write("imax {0}  number of channelsi\n".format(1))
    cardFile.write("jmax {0}  number of backgrounds\n".format(8)) #   .format(nProc))
    cardFile.write("kmax {0}  number of nuisance parameters \n".format((binning)*8))
    cardFile.write("shapes * *  "+inrootfile+"    $PROCESS"+histoname+"  $PROCESS"+histoname+"$SYSTEMATIC  \n")
    cardFile.write("------------------------\n")
    cardFile.write("bin          {0} \n".format(1))
    cardFile.write("observation  {0} \n".format(-1))
   
    cardFile.write(" # number of expected events, per source\n") 
    cardFile.write("bin         1     1          1    1   1   1  1    1     1     \n")
    cardFile.write("process     ZA    ZH         ZZ   WZ  WW  TT DYbb DYbx  DYxx  \n") 
    cardFile.write("process     0     1          2    3   4   5  6    7     8     \n")
    cardFile.write("rate        -1    -1         -1   -1  -1  -1 -1   -1    -1    \n")
    cardFile.write("------------------------------------------------------------\n")
    
    cardFile.write("# the description of the systematic uncertainties\n")
    
    for proc in listProc:
    
      if   "ZA" in proc  : stringplus="1 - - - - - - - -"
      elif "ZH" in proc  : stringplus="- 1 - - - - - - -"
      elif "ZZ" in proc  : stringplus="- - 1 - - - - - -"
      elif "WZ" in proc  : stringplus="- - - 1 - - - - -"
      elif "WW" in proc  : stringplus="- - - - 1 - - - -"
      elif "TT" in proc  : stringplus="- - - - - 1 - - -"
      elif "DYbb" in proc: stringplus="- - - - - - 1 - -"
      elif "DYbx" in proc: stringplus="- - - - - - - 1 -"
      elif "DYxx" in proc: stringplus="- - - - - - - - 1"      
      else: break
      
      for i in range(0, binning):
        cardFile.write("_"+proc+"_"+"stat_bin{0}  shape ".format(i+1)+stringplus+" \n")  
   
    cardFile.write("# end of card")     


def main():

  cfgFile = sys.argv[1]

  myConfig = PConfig(cfgFile)

  print myConfig.mvaCfg
  print myConfig.procCfg
  
  nameout="test"
  nameplus=""
  splitMode = "bothCSV_njets" #bothCSV_njets, CSVprod, jetNumb

  #listProc=["DY","TT","ZZ","ZH","WW","WZ","Data"]
  listProc=["DYbx","DYbb","DYxx","TT","ZZ","ZH","WW","WZ","ZA","data_obs"]
  #inFile="results/purMinMax_withZh_DYsplit_Pur1/purMinMax_withZh_results.out"
  inFile=myConfig.mvaCfg["outputdir"]+"/"+myConfig.mvaCfg["name"]+"_results.out"
  
  (Dict, nbox)=getDictProc_rootFileList_nbox(myConfig, inFile)
  
  
  #createRootFilesSplitted(inFile,splitMode , listProc, myConfig)
  #fileout= writeHistoSplitted(inFile,splitMode , listProc, myConfig, nameout, nameplus)
  #rootfileout= createHistoStat(fileout,listProc, splitMode, nameout)
  drawMCdata("histoMIS/histoSplittedCSV_and_nJets_test.root", listProc,splitMode, myConfig, nbox, nameout+splitMode)
  #cardWriter_shape(myConfig, "histoMIS/histofinal.root", listProc, splitMode, nbox, nameout)
  #cardWriter_shapeZA(myConfig,rootfileout , listProc, splitMode, nbox, nameout)

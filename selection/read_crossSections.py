#!/cvmfs/cp3.uclouvain.be/python/python-2.7.9-sl6_amd64_gcc49/bin/python2.7

from xml.etree import ElementTree as ET
import os
import ROOT
import warnings

def find_banner(dir):
    content = os.listdir(dir)
    content = [ os.path.join(dir, file) for file in content ]
    banners = []
    for file in content:
        if "banner.txt" in file:
            banners.append(file)
    if len(banners) > 1:
        print "More than one banner found in directory {}".format(dir)
    if len(banners) == 0:
        print "No banner found in directory {}".format(dir)
    return banners[0]

def find_lhe(dir):
    content = os.listdir(dir)
    content = [ os.path.join(dir, file) for file in content if file[0] != "." ]
    lhe = ""
    for file in content:
        if "unweighted_events.lhe" in file:
            lhe = file
            break
    if lhe == "":
        print "No lhe found in directory {}".format(dir)
    return lhe

def decompress_lhe(lhe, process = ""):
    if os.path.isfile(lhe):
        if ".gz" in lhe:
            #os.system("gunzip {}".format(lhe))
            #return lhe[:len(lhe)-3]
            os.system("gunzip -c {} > tempLHE_{}.lhe".format(lhe, process))
            return "tempLHE_{}.lhe".format(process)
        else:
            return lhe
    else:
        print "Warning: file {} does not exist.".format(lhe)

def compress_lhe(lhe, process = ""):
    if os.path.isfile(lhe):
        if ".gz" not in lhe:
            #os.system("gzip {}".format(lhe))
            #return lhe + ".gz"
            os.system("rm tempLHE_{}.lhe".format(process))
        else:
            return lhe
    else:
        print "Warning: file {} does not exist.".format(lhe)

## MADGRAPH ##

def get_mg_prod_info(lhe_list, process = ""):
    
    all_prod_weights = []
    all_prod_XS = []
    all_tot_nEvents = []
    
    for lhe in lhe_list:
        new_lhe = decompress_lhe(lhe, process)
        xml = ET.parse(new_lhe)
        root = xml.getroot()
        infoString =  root.find("header").find("MGGenerationInfo").text
        
        nEvents = int(infoString.split("\n")[1].split(":")[1])
        XS = float(infoString.split("\n")[2].split(":")[1])
        weight = float(infoString.split("\n")[4].split(":")[1])
    
        print "File {}: {} events, weight = {}, XS = {}".format(new_lhe, nEvents, weight, XS)
    
        all_prod_weights.append(weight*nEvents)
        all_prod_XS.append(XS)
        all_tot_nEvents.append(nEvents)
    
        compress_lhe(new_lhe, process)

    return all_prod_weights, all_prod_XS, all_tot_nEvents

def get_mg_decayed_info(lhe_list, process = ""):
   
    all_decayed_weights = []
    all_decayed_nEvents = []

    for lhe in lhe_list:
        new_lhe = decompress_lhe(lhe, process)
        xml = ET.parse(new_lhe)
        root = xml.getroot()
   
        nEvents = len(root.findall("event"))
        
        eventString = [ item for item in root.find("event").text.split("\n")[1].split(" ") if item != "" ]
        weight = float(eventString[2])
        
        print "File {}: {} events, weight = {}".format(new_lhe, nEvents, weight)
    
        all_decayed_weights.append(weight*nEvents)
        all_decayed_nEvents.append(nEvents)
    
        compress_lhe(new_lhe, process)

    return all_decayed_weights, all_decayed_nEvents

def get_mg_info(mg_base_dir, usedMS = False, process = ""):

    mg_all_dirs = [ os.path.join(mg_base_dir, dir) for dir in os.listdir(mg_base_dir) if ( "try2_extended_" in dir or "try0_" in dir or "try1_" in dir ) and os.path.isdir(os.path.join(mg_base_dir, dir)) ]
    #mg_all_dirs = [ os.path.join(mg_base_dir, dir) for dir in os.listdir(mg_base_dir) if "try" in dir and "_" in dir and os.path.isdir(os.path.join(mg_base_dir, dir)) ]
    
    mg_prod_dirs = [ dir for dir in mg_all_dirs if "decayed" not in dir and find_lhe(dir) != "" ]
    mg_prod_lhe = [ find_lhe(dir) for dir in mg_prod_dirs ]
    mg_prod_lhe = [ lhe for lhe in mg_prod_lhe if lhe != "" ]
    
    mg_decayed_dirs = []
    mg_decayed_lhe = []
    if usedMS:
        mg_decayed_dirs = [ dir for dir in mg_all_dirs if "decayed" in dir and find_lhe(dir) != "" ]
        mg_decayed_lhe = [ find_lhe(dir) for dir in mg_decayed_dirs ]
        mg_decayed_lhe = [ lhe for lhe in mg_decayed_lhe if lhe != "" ]
    
        if len(mg_prod_lhe) != len(mg_decayed_lhe):
            raise Exception("Number of decay and production LHE is different.")
    
    nFiles = len(mg_prod_lhe)
    
    all_prod_weights, all_prod_XS, all_tot_nEvents = get_mg_prod_info(mg_prod_lhe, process)
    tot_nEvents = sum(all_tot_nEvents)
    avg_prod_weights = sum(all_prod_weights)/(len(all_prod_weights)*tot_nEvents)
    prod_XS = sum(all_prod_XS)/nFiles
    
    if usedMS:
        all_decayed_weights, all_decayed_nEvents = get_mg_decayed_info(mg_decayed_lhe, process)
        decayed_nEvents = sum(all_decayed_nEvents)
        if decayed_nEvents != tot_nEvents:
            raise Exception("Production and decay number of events are different.")
        avg_decayed_weights = sum(all_decayed_weights)/(len(all_decayed_weights)*decayed_nEvents)

        return { "avgProdWeights": avg_prod_weights, "prodXS": prod_XS, "totEvents": tot_nEvents, "avgDecayWeights": avg_decayed_weights }
        
    return { "avgProdWeights": avg_prod_weights, "prodXS": prod_XS, "totEvents": tot_nEvents }

## PYTHIA+DELPHES ##

warnings.filterwarnings(action='ignore', category=RuntimeWarning, message='no dictionary*')

def get_matching_info(files):
    
    chain = ROOT.TChain("Delphes")
    chain.Add(files)
    #chain.Add("/nfs/user/swertz/Delphes/condorDelphes/OG_qCut50_1/condor/output/output_delphes_*.root")
    chain.Add("/nfs/user/swertz/Delphes/condorDelphes/O83qq_qCut50_1/condor/output/output_delphes_*.root")
    
    matched_nEvents = chain.GetEntries()
    
    chain.Draw("1>>hist", "Event.Weight", "goff")
    hist = ROOT.gDirectory.Get("hist")
    matched_sumWeights = int(hist.Integral())
    
    del chain
    
    return { "events": matched_nEvents, "sumWeights": matched_sumWeights } 

## SELECTED ##

def get_selection_info(files):
    chain = ROOT.TChain("t")
    chain.Add(files)
    
    selected_nEvents = chain.GetEntries()
    
    chain.Draw("1>>hist", "GenWeight", "goff")
    hist = ROOT.gDirectory.Get("hist")
    selected_sumWeights = int(hist.Integral())
    
    del chain
    
    return { "events": selected_nEvents, "sumWeights": selected_sumWeights } 

## MAIN ##

if __name__ == "__main__":

    #process = "TTbar"
    #usedMS = True
    #mg_base_dir = "/home/fynu/swertz/scratch/Madgraph/madgraph5/TTbar_2j_sm_5f_MSdecay_0/Events/"
   
    #process = "OtG"
    #usedMS = True
    #mg_base_dir = "/home/fynu/swertz/scratch/Madgraph/madgraph_TopEffTh/TTbar_2j_TopEffTh_" + process + "_NPsq2_QED1_MSdecay/Events/"

    usedMS = False
    
    #process = "OG"
    #process = "OphiG"
    #process = "O8dt"
    #mg_base_dir = "/home/fynu/swertz/scratch/Madgraph/madgraph_TopEffTh/TTbar_2j_TopEffTh_" + process + "_NPleq2_QED1_MEdecay/Events/"
    
    #process = "O81qq"
    process = "O83qq"
    #process = "O8ut"
    mg_base_dir = "/home/fynu/sbrochet/scratch/EffOperators/Madgraph/MG5_aMC_v2_3_3/TTbar_2j_TopEffTh_" + process + "_NPleq2_QED1_MEdecay/Events/"

    delphes_files = "/nfs/user/swertz/Delphes/condorDelphes/" + process + "_qCut50/condor/output/output_delphes_*.root"
    selected_file = "/home/fynu/swertz/ttbar_effth_delphes/15_November/selectedEvents/" + process + "_qCut50.root"
    
    print "Retrieving MadGraph info."
    mg_info = get_mg_info(mg_base_dir, usedMS, process)
    
    print "\nRetrieving Delphes info."
    delphes_info = get_matching_info(delphes_files)
    
    print "\nRetrieving selection info."
    selection_info = get_selection_info(selected_file)

    print "\n## Summary ##\n"
    print "Production cross section:  {}".format(mg_info["prodXS"]).replace(".",",")
    print "Production event weight:  {0:.50f}".format(mg_info["avgProdWeights"]).replace(".",",")
    print "Production nEvents:        {}".format(mg_info["totEvents"])
    if usedMS:
        print "Decay event weight:       {0:.50f}".format(mg_info["avgDecayWeights"]).replace(".",",")
    print "Matched sum of weights:    {}".format(delphes_info["sumWeights"]).replace(".",",")
    print "Matched nEvents:           {}".format(delphes_info["events"])
    print "Selected sum of weights:   {}".format(selection_info["sumWeights"]).replace(".",",")
    print "Selected nEvents:          {}".format(selection_info["events"])

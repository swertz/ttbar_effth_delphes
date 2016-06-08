#!/cvmfs/cms.cern.ch/slc6_amd64_gcc491/cms/cmssw/CMSSW_7_4_15/external/slc6_amd64_gcc491/bin/python

import sys
import os
from math import cos
import ROOT as R
from DataFormats.FWLite import Events, Handle

if len(sys.argv) != 4 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
    raise Exception( "Usage: {} folder number_of_files output".format(sys.argv[0]) )

path = sys.argv[1]
number = int(sys.argv[2])
output = sys.argv[3]

files = [ os.path.join(path, "output_pythia8_{}.root".format(i)) for i in range(number) ]

events = Events(files)
handle = Handle("std::vector<reco::GenParticle>")
label = ("genParticles")

handleEvt = Handle("GenEventInfoProduct")
labelEvt = ("generator")

file = R.TFile(output, "recreate")

plots = {
        "Top Pt": (50, 0, 700),
        "Top Mass": (50, 150, 200),
        "Top Eta": (50, -6, 6),
        "Top Rapidity": (50, -4, 4),
        
        "AntiTop Pt": (50, 0, 700),
        "AntiTop Mass": (50, 150, 200),
        "AntiTop Eta": (50, -6, 6),
        "AntiTop Rapidity": (50, -4, 4),
        
        "TTbar Pt": (50, 0, 500),
        "TTbar Mass": (50, 300, 2000),
        "TTbar Eta": (50, -6, 6),
        "TTbar DeltaEta": (50, 0, 10),
        "TTbar Rapidity": (50, -4, 4),

        "LepPlus Pt": (50, 0, 400),
        "LepPlus Eta": (50, -6, 6),
        "LepPlus Rapidity": (50, -5, 5),
        
        "LepMinus Pt": (50, 0, 400),
        "LepMinus Eta": (50, -6, 6),
        "LepMinus Rapidity": (50, -5, 5),

        "CosPlus": (50, -1, 1),
        "CosMinus": (50, -1, 1),
        "CosPlusCosMinus": (50, -1, 1),

        "CosStarPlus": (50, -1, 1),
        "CosStarMinus": (50, -1, 1),
        "CosStarPlusCosStarMinus": (50, -1, 1),
        
        "LepPlusLepMinus CosPhi": (50, -1, 1),

        "LepPlusLepMinus DeltaPhi": (50, 0, 3.14159),
        "LepPlusLepMinus DeltaEta": (50, 0, 8)
    }

histos = {}

for plot in plots.items():
    histos[ plot[0] ] = R.TH1F(plot[0], plot[0], plot[1][0], plot[1][1], plot[1][2])

histos["CosPlus_vs_CosMinus"] = R.TH2F("CosPlus_vs_CosMinus", "CosPlus_vs_CosMinus", 50, -1, 1, 50, -1, 1)
histos["CosStarPlus_vs_CosStarMinus"] = R.TH2F("CosStarPlus_vs_CosStarMinus", "CosStarPlus_vs_CosStarMinus", 50, -1, 1, 50, -1, 1)

nEvent = 0

def DeltaEta(p1, p2):
    return abs(p1.Eta() - p2.Eta())

def printV(p):
    print "PxPyPzE: ({}, {}, {}, {})".format(p.Px(), p.Py(), p.Pz(), p.E())
    print "PtEtaPhiE: ({}, {}, {}, {})".format(p.Pt(), p.Eta(), p.Phi(), p.E())

for event in events:
    nEvent += 1
    if nEvent % 1000 == 0:
        print "Event {}".format(nEvent)

    event.getByLabel(label, handle)
    event.getByLabel(labelEvt, handleEvt)

    particles = handle.product()
    weight = handleEvt.product().weight()

    top_p4 = ""
    antiTop_p4 = ""
    lepM_p4 = ""
    lepP_p4 = ""

    foundTop = False
    foundAntiTop = False
    foundGoodLepM = False
    foundLepM = False
    foundGoodLepP = False
    foundLepP = False
        
    #print "Event:"
    for part in particles:
        if abs(part.status()) == 22 and part.pdgId() == 6:
            top_p4 = part.p4()
            foundTop = True

        if abs(part.status()) == 22 and part.pdgId() == -6:
            antiTop_p4 = part.p4()
            foundAntiTop = True

        #if part.status() == 23:
        #    print "PID = {}".format(part.pdgId())

        #if part.status() == 23 and (part.pdgId() == 11 or part.pdgId() == 13):
        #    #print "Plus: {}, Pt = {}".format(part.status(), part.p4().Pt())
        #    lepM_p4 = part.p4()
        #    foundGoodLepM = True
        #    foundLepM = True

        #if part.status() == 23 and (part.pdgId() == -11 or part.pdgId() == -13):
        #    #print "Minus: {}, Pt = {}".format(part.status(), part.p4().Pt())
        #    lepP_p4 = part.p4()
        #    foundGoodLepP = True
        #    foundLepP = True

        #if (not foundGoodLepM) and part.statusFlags().isHardProcess() and part.status() == 1 and (part.pdgId() == 11 or part.pdgId() == 13):
        if part.isPromptFinalState() and (part.pdgId() == 11 or part.pdgId() == 13):
            #print "Plus: {}, hard? {}, fromHard? {}, Pt = {}".format(part.status(), part.statusFlags().isHardProcess(), part.statusFlags().fromHardProcess(), part.p4().Pt())
            lepM_p4 = part.p4()
            foundLepM = True

        #if (not foundGoodLepP) and part.statusFlags().isHardProcess() and part.status() == 1 and (part.pdgId() == -11 or part.pdgId() == -13):
        if part.isPromptFinalState() and (part.pdgId() == -11 or part.pdgId() == -13):
            #print "Minus: {}, hard? {}, fromHard? {}, Pt = {}".format(part.status(), part.statusFlags().isHardProcess(), part.statusFlags().fromHardProcess(), part.p4().Pt())
            lepP_p4 = part.p4()
            foundLepP = True

        if foundTop and foundAntiTop and foundLepM and foundLepP:
            break
    #print ""

    histos["Top Pt"].Fill(top_p4.pt(), weight)
    histos["Top Eta"].Fill(top_p4.eta(), weight)
    histos["Top Rapidity"].Fill(top_p4.Rapidity(), weight)
    histos["Top Mass"].Fill(top_p4.mass(), weight)

    histos["AntiTop Pt"].Fill(antiTop_p4.pt(), weight)
    histos["AntiTop Eta"].Fill(antiTop_p4.eta(), weight)
    histos["AntiTop Rapidity"].Fill(antiTop_p4.Rapidity(), weight)
    histos["AntiTop Mass"].Fill(antiTop_p4.mass(), weight)
    
    ttbar_p4 = top_p4 + antiTop_p4
    
    histos["TTbar Pt"].Fill(ttbar_p4.pt(), weight)
    histos["TTbar Eta"].Fill(ttbar_p4.eta(), weight)
    histos["TTbar DeltaEta"].Fill( DeltaEta(top_p4, antiTop_p4), weight)
    histos["TTbar Rapidity"].Fill(ttbar_p4.Rapidity(), weight)
    histos["TTbar Mass"].Fill(ttbar_p4.mass(), weight)

    vec_TTbarToCM = ttbar_p4.BoostToCM()
    TTbarToCM = R.Math.Boost(vec_TTbarToCM.X(), vec_TTbarToCM.Y(), vec_TTbarToCM.Z())

    newTop = TTbarToCM(top_p4)
    newAntiTop = TTbarToCM(antiTop_p4)

    #test = newTop + newAntiTop
    #print "TTbar:"
    #printV(test)
    #print "Top:"
    #printV(newTop)
    #print "AntiTop:"
    #printV(newAntiTop)

    vec_TopToCM = newTop.BoostToCM()
    TopToCM = R.Math.Boost(vec_TopToCM.X(), vec_TopToCM.Y(), vec_TopToCM.Z())
    #restTop = TopToCM(newTop)

    vec_AntiTopToCM = newAntiTop.BoostToCM()
    AntiTopToCM = R.Math.Boost(vec_AntiTopToCM.X(), vec_AntiTopToCM.Y(), vec_AntiTopToCM.Z())
    #restAntiTop = AntiTopToCM(newAntiTop)
    
    if not (foundLepM and foundLepP):
        print "Couldn't retrieve all the particles for event {}".format(nEvent)
        print "LepP: {} LepM: {}".format(foundLepP, foundLepM)
        continue

    cosP = 0
    cosM = 0
    cosStarP = 0
    cosStarM = 0


    histos["LepPlus Pt"].Fill(lepP_p4.pt(), weight)
    histos["LepPlus Eta"].Fill(lepP_p4.eta(), weight)
    histos["LepPlus Rapidity"].Fill(lepP_p4.Rapidity(), weight)
    
    newLepP = TTbarToCM(lepP_p4)
    cosP = R.Math.VectorUtil.CosTheta( newLepP.Vect(), newTop.Vect())
    histos["CosPlus"].Fill(cosP, weight)
    
    newLepP = TopToCM(newLepP)
    cosStarP = R.Math.VectorUtil.CosTheta(newLepP.Vect(), newTop.Vect())
    #cosStarP = cos(newLepP.Theta())
    histos["CosStarPlus"].Fill(cosStarP, weight)
    

    histos["LepMinus Pt"].Fill(lepM_p4.pt(), weight)
    histos["LepMinus Eta"].Fill(lepM_p4.eta(), weight)
    histos["LepMinus Rapidity"].Fill(lepM_p4.Rapidity(), weight)
    
    newLepM = TTbarToCM(lepM_p4)
    cosM = R.Math.VectorUtil.CosTheta( newLepM.Vect(), newAntiTop.Vect())
    histos["CosMinus"].Fill(cosM, weight)
    
    newLepM = AntiTopToCM(newLepM)
    cosStarM = R.Math.VectorUtil.CosTheta(newLepM.Vect(), newAntiTop.Vect())
    #cosStarM = cos(newLepM.Theta())
    histos["CosStarMinus"].Fill(cosStarM, weight)
   

    histos["CosPlus_vs_CosMinus"].Fill(cosP, cosM, weight)
    histos["CosPlusCosMinus"].Fill(cosP*cosM, weight)
    
    histos["CosStarPlus_vs_CosStarMinus"].Fill(cosStarP, cosStarM, weight)
    histos["CosStarPlusCosStarMinus"].Fill(cosStarP*cosStarM, weight)

    histos["LepPlusLepMinus CosPhi"].Fill( R.Math.VectorUtil.CosTheta(TopToCM(newLepP).Vect(), AntiTopToCM(newLepM).Vect()), weight )
    
    histos["LepPlusLepMinus DeltaPhi"].Fill(abs(R.Math.VectorUtil.DeltaPhi(lepP_p4, lepM_p4)), weight)
    histos["LepPlusLepMinus DeltaEta"].Fill(DeltaEta(lepP_p4, lepM_p4), weight)

file.cd()
for histo in histos.values():
    histo.Write()
file.Close()

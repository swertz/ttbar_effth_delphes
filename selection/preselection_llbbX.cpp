#include <iostream>
#include <cmath>
#include <utility> 
#include <vector>
#include <limits>

#include <TTree.h>
#include <TROOT.h>
#include <TChain.h>
#include <TFile.h>
#include <TClonesArray.h>
#include <TCollection.h>

#include <Math/PtEtaPhiM4D.h>
#include <Math/LorentzVector.h>
#include <Math/VectorUtil.h>

#include "classes/DelphesClasses.h"

#define LorentzVector ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>

float DeltaEta(const LorentzVector& v1, const LorentzVector& v2){
  return std::abs(v1.Eta() - v2.Eta());
}

using namespace std;
using namespace ROOT::Math::VectorUtil;

int main(int argv, char** argc){
    const char* inputFile = argc[1];
    const char* outputFile = argc[2];
    
    //=================================================================
    TChain *chain = new TChain("Delphes");
    chain->Add(inputFile);
    //=================================================================
    
    float ptlep = 20, ptjet = 30, etalep = 2.4, etajet = 2.4, minDRjlCut = 0.3, mll_cut = 20, mll_ZVetoLow = 76, mll_ZVetoHigh = 106, met_sf_cut = 40;   
    LorentzVector bjet1_p4, bjet2_p4, jet3_p4, jet4_p4, lep1_p4, lep2_p4, bb_p4, ll_p4, llbb_p4, llbbMet_p4t;
    LorentzVector gen_t_p4, gen_tbar_p4;
    float MET_met, MET_phi;
    float ll_DR, ll_DEta, ll_DPhi;
    float bb_DR, bb_DEta, bb_DPhi;
    float DRbl_min, DRbl_max, DR_ll_bb, DEta_ll_bb, DPhi_ll_bb, DPhi_ll_Met, DPhi_bb_Met, DPhi_llbb_Met;
    float ScalHT;
    int NAllJet, NJet, NBJet, leadLepPID, subleadLepPID;
    bool IsEE, IsEMu, IsMuMu;
    float GenWeight;

    TFile rootOutFile(outputFile, "recreate");
    TTree *outputTree = new TTree("t", "t");
    
    outputTree->Branch("lep1_p4", &lep1_p4);
    outputTree->Branch("lep2_p4", &lep2_p4);
    outputTree->Branch("ll_p4", &ll_p4);
    outputTree->Branch("ll_DR", &ll_DR);
    outputTree->Branch("ll_DEta", &ll_DEta);
    outputTree->Branch("ll_DPhi", &ll_DPhi);
    
    outputTree->Branch("bjet1_p4", &bjet1_p4);
    outputTree->Branch("bjet2_p4", &bjet2_p4);
    outputTree->Branch("jet3_p4", &jet3_p4);
    outputTree->Branch("jet4_p4", &jet4_p4);
    outputTree->Branch("bb_p4", &bb_p4);
    outputTree->Branch("bb_DR", &bb_DR);
    outputTree->Branch("bb_DEta", &bb_DEta);
    outputTree->Branch("bb_DPhi", &bb_DPhi);

    outputTree->Branch("llbb_p4", &llbb_p4);
    outputTree->Branch("llbbMet_p4t", &llbbMet_p4t);
    outputTree->Branch("DRbl_min", &DRbl_min);
    outputTree->Branch("DRbl_max", &DRbl_max);
    outputTree->Branch("DR_ll_bb", &DR_ll_bb);
    outputTree->Branch("DEta_ll_bb", &DEta_ll_bb);
    outputTree->Branch("DPhi_ll_bb", &DPhi_ll_bb);
    outputTree->Branch("DPhi_ll_Met", &DPhi_ll_Met);
    outputTree->Branch("DPhi_bb_Met", &DPhi_bb_Met);
    outputTree->Branch("DPhi_llbb_met", &DPhi_llbb_Met);

    outputTree->Branch("MET_met", &MET_met);
    outputTree->Branch("MET_phi", &MET_phi);

    outputTree->Branch("ScalHT", &ScalHT);
    
    outputTree->Branch("NAllJet", &NAllJet);
    outputTree->Branch("NJet", &NJet);
    outputTree->Branch("NBJet", &NBJet);
    
    outputTree->Branch("IsEE", &IsEE);
    outputTree->Branch("IsEMu", &IsEMu);
    outputTree->Branch("IsMuMu", &IsMuMu);

    outputTree->Branch("leadLepPID", &leadLepPID);
    outputTree->Branch("subleadLepPID", &subleadLepPID);
    
    outputTree->Branch("gen_t_p4", &gen_t_p4);
    outputTree->Branch("gen_tbar_p4", &gen_tbar_p4);
    
    outputTree->Branch("GenWeight", &GenWeight);

    TClonesArray *branchEvent( nullptr );
    chain->SetBranchAddress("Event", &branchEvent);
    TClonesArray *branchParticle( nullptr );
    chain->SetBranchAddress("Particle", &branchParticle);
    TClonesArray *branchElectron( nullptr );
    chain->SetBranchAddress("Electron", &branchElectron);
    TClonesArray *branchMuon( nullptr );
    chain->SetBranchAddress("Muon", &branchMuon);
    TClonesArray *branchJet( nullptr );
    chain->SetBranchAddress("Jet", &branchJet);
    TClonesArray *branchMissingET( nullptr );
    chain->SetBranchAddress("MissingET", &branchMissingET);
    TClonesArray *branchScalarHT( nullptr );
    chain->SetBranchAddress("ScalarHT", &branchScalarHT);

    int numberOfEntries = chain->GetEntries();
    int selectedEvtAll = 0, selectedEvtLeptons = 0, selectedEvtJets = 0, selectedEvtBJets = 0, selectedEvtLeptonsCuts = 0;

    cout << "Processing events..." << endl;
    
    for(int entry = 0; entry < numberOfEntries; ++entry){
        chain->GetEntry(entry);
        
        vector<Jet*> bjets;
        vector<Jet*> jets;
        vector<Muon*> muons;
        vector<Electron*> electrons;
    
        IsEE = 0;
        IsEMu = 0;
        IsMuMu = 0;
        NJet = 0;
        NAllJet = 0;
        NBJet = 0;

        jet3_p4.SetCoordinates(0,0,0,0);
        jet4_p4.SetCoordinates(0,0,0,0);
        
        int Nmu = 0;
        int Ne = 0;
        int Nlep = 0;
        int NjetDelphes = branchJet->GetEntries();
        int NmuDelphes = branchMuon->GetEntries();
        int NeDelphes = branchElectron->GetEntries();
        int NlepDelphes = NmuDelphes+NeDelphes;
        
        if(NjetDelphes < 2) continue;
        if(NlepDelphes < 2) continue;

        HepMCEvent* event = (HepMCEvent*) branchEvent->At(0);
        GenWeight = event->Weight;


        TIter itMuon( (TCollection*)branchMuon );
        Muon* muon;
        while( muon = (Muon*) itMuon.Next() ){
            if( abs(muon->Eta) > etalep || muon->PT < ptlep)
                continue;
            Nmu++;
            muons.push_back(muon);
        }

        TIter itElectron( (TCollection*)branchElectron );
        Electron* electron;
        while( electron = (Electron*) itElectron.Next() ){
            if( abs(electron->Eta) > etalep || electron->PT < ptlep)
                continue;
            Ne++;
            electrons.push_back(electron);
        }

        Nlep = Nmu + Ne;
        if(Nlep < 2)
            continue;       // Don't loose time if there is not 2 leptons

        selectedEvtLeptons++;
    
        TIter itJet( (TCollection*)branchJet );    
        Jet* jet;
        
        while( jet = (Jet*) itJet.Next() ){
      
            float minDRjl( std::numeric_limits<float>::max() );
      
            for(Electron* electron: electrons){
                LorentzVector elep4(electron->PT, electron->Eta, electron->Phi, 0.);
                LorentzVector jetp4(jet->PT, jet->Eta, jet->Phi, 0.);
                if( DeltaR(elep4, jetp4) < minDRjl )
                    minDRjl = DeltaR(elep4, jetp4);
            }
      
            for(Muon* muon: muons){
                LorentzVector mup4(muon->PT, muon->Eta, muon->Phi, 0.);
                LorentzVector jetp4(jet->PT, jet->Eta, jet->Phi, 0.);
                if( DeltaR(mup4, jetp4) < minDRjl )
                    minDRjl = DeltaR(mup4, jetp4);
            }
            
            if( abs(jet->Eta) < etajet && jet->PT > ptjet && minDRjl > minDRjlCut){
                NAllJet++;
                if(jet->BTag){
                    NBJet++;
                    bjets.push_back(jet);
                }else{
                    NJet++;
                    jets.push_back(jet);
                }
            }
        
        }
        
        if(NAllJet < 2)
            continue;
        selectedEvtJets++;
        if(NBJet < 2)
            continue;
        selectedEvtBJets++;

        // Decide in which channel we are : EMu, MuMu or EE

        if(Ne > 1 && Nmu == 0){
      
            lep1_p4.SetCoordinates(electrons.at(0)->PT, electrons.at(0)->Eta, electrons.at(0)->Phi, 0.);
            lep2_p4.SetCoordinates(electrons.at(1)->PT, electrons.at(1)->Eta, electrons.at(1)->Phi, 0.);
            ll_p4 = lep1_p4 + lep2_p4;
            if(electrons.at(0)->Charge == electrons.at(1)->Charge || ll_p4.M() < mll_cut || (ll_p4.M() > mll_ZVetoLow && ll_p4.M() < mll_ZVetoHigh))
                continue;
      
            IsEE = true;
            leadLepPID = -11*electrons.at(0)->Charge;
            subleadLepPID = -11*electrons.at(1)->Charge;
    
        }else if (Ne == 0 && Nmu > 1){
      
            lep1_p4.SetCoordinates(muons.at(0)->PT, muons.at(0)->Eta, muons.at(0)->Phi, 0.);
            lep2_p4.SetCoordinates(muons.at(1)->PT, muons.at(1)->Eta, muons.at(1)->Phi, 0.);
            ll_p4 = lep1_p4 + lep2_p4;
            if(muons.at(0)->Charge == muons.at(1)->Charge || ll_p4.M() < mll_cut || (ll_p4.M() > mll_ZVetoLow && ll_p4.M() < mll_ZVetoHigh))
                continue;
      
            IsMuMu = true;
            leadLepPID = -13*muons.at(0)->Charge;
            subleadLepPID = -13*muons.at(1)->Charge;
        
        }else if (Ne == 1 && Nmu == 1){
        //}else if (Ne > 1 && Nmu > 1){ // should be this...
      
            if(muons.at(0)->PT > electrons.at(0)->PT){
                lep1_p4.SetCoordinates(muons.at(0)->PT, muons.at(0)->Eta, muons.at(0)->Phi, 0.);
                lep2_p4.SetCoordinates(electrons.at(0)->PT, electrons.at(0)->Eta, electrons.at(0)->Phi, 0.);
                leadLepPID = -13*muons.at(0)->Charge;
                subleadLepPID = -11*electrons.at(0)->Charge;
            }else{
                lep2_p4.SetCoordinates(muons.at(0)->PT, muons.at(0)->Eta, muons.at(0)->Phi, 0.);
                lep1_p4.SetCoordinates(electrons.at(0)->PT, electrons.at(0)->Eta, electrons.at(0)->Phi, 0.);
                leadLepPID = -11*electrons.at(0)->Charge;
                subleadLepPID = -13*muons.at(0)->Charge;
            }
            ll_p4 = lep1_p4 + lep2_p4;
            if(muons.at(0)->Charge == electrons.at(0)->Charge || ll_p4.M() < mll_cut)
                continue;
      
            IsEMu = true;

        }

        selectedEvtLeptonsCuts++;

        if( (IsEE || IsMuMu) && MET_met < met_sf_cut)
            continue;
    
        bjet1_p4.SetCoordinates(bjets.at(0)->PT, bjets.at(0)->Eta, bjets.at(0)->Phi, bjets.at(0)->Mass);
        bjet2_p4.SetCoordinates(bjets.at(1)->PT, bjets.at(1)->Eta, bjets.at(1)->Phi, bjets.at(1)->Mass);

        if(NJet >= 1)
            jet3_p4.SetCoordinates(jets.at(0)->PT, jets.at(0)->Eta, jets.at(0)->Phi, jets.at(0)->Mass);
        if(NJet >= 2)
            jet4_p4.SetCoordinates(jets.at(1)->PT, jets.at(1)->Eta, jets.at(1)->Phi, jets.at(1)->Mass);

        bb_p4 = bjet1_p4 + bjet2_p4;
        llbb_p4 = ll_p4 + bb_p4;
        
        LorentzVector met_p4;
        MissingET *met;
        met = (MissingET*) branchMissingET->At(0);
        MET_met=met->MET;
        MET_phi=met->Phi;
        met_p4.SetCoordinates(MET_met, 0., MET_phi, 0.);
        llbbMet_p4t = llbb_p4 + met_p4;
        llbbMet_p4t.SetEta(0.);
        
        ll_DR = DeltaR(lep1_p4, lep2_p4); 
        ll_DEta = DeltaEta(lep1_p4, lep2_p4); 
        ll_DPhi = std::abs( DeltaPhi(lep1_p4, lep2_p4) ); 
    
        bb_DR = DeltaR(bjet1_p4, bjet2_p4); 
        bb_DEta = DeltaEta(bjet1_p4, bjet2_p4); 
        bb_DPhi = std::abs( DeltaPhi(bjet1_p4, bjet2_p4) ); 

        DRbl_min = std::min( {
            DeltaR(lep1_p4, bjet1_p4),
            DeltaR(lep1_p4, bjet2_p4),
            DeltaR(lep2_p4, bjet1_p4),
            DeltaR(lep2_p4, bjet2_p4)
            });

        DRbl_max = std::max( {
            DeltaR(lep1_p4, bjet1_p4),
            DeltaR(lep1_p4, bjet2_p4),
            DeltaR(lep2_p4, bjet1_p4),
            DeltaR(lep2_p4, bjet2_p4)
            });

        DR_ll_bb = DeltaR(bb_p4, ll_p4);
        DEta_ll_bb = DeltaEta(bb_p4, ll_p4);
        DPhi_ll_bb = std::abs( DeltaPhi(bb_p4, ll_p4) );
            
        DPhi_ll_Met = std::abs( DeltaPhi(met_p4, ll_p4) );
        DPhi_bb_Met = std::abs( DeltaPhi(met_p4, bb_p4) );
        DPhi_llbb_Met = std::abs( DeltaPhi(met_p4, llbb_p4) );
            
        ScalarHT *sht;
        if(branchScalarHT->GetEntriesFast() > 0){
            sht = (ScalarHT*) branchScalarHT->At(0);
            ScalHT = sht->HT;
        }
        
        TIter itParticles( (TCollection*)branchParticle );
        GenParticle* part;
        bool found_t = false, found_tbar = false;
        while( part = (GenParticle*) itParticles.Next() ){
            if (part->Status == 22) {
                if (part->PID == 6 && !found_t) {
                    gen_t_p4.SetCoordinates(part->PT, part->Eta, part->Phi, part->Mass);
                    found_t = true;
                }
                if (part->PID == -6 && !found_tbar) {
                    gen_tbar_p4.SetCoordinates(part->PT, part->Eta, part->Phi, part->Mass);
                    found_tbar = true;
                }
            }
            if (found_t && found_tbar)
                continue;
        }
        
        selectedEvtAll++;
        outputTree->Fill();
        
    }

    outputTree->Write();
    rootOutFile.Close();

    std::cout << "Selected " << selectedEvtAll << " out of " << numberOfEntries << " (" << 100.*selectedEvtAll/numberOfEntries << "%)." << std::endl;
    std::cout << "Leptons " << selectedEvtLeptons << " out of " << numberOfEntries << " (" << 100.*selectedEvtLeptons/numberOfEntries << "%)." << std::endl;
    std::cout << "Jets    " << selectedEvtJets << " out of " << selectedEvtLeptons << " (" << 100.*selectedEvtJets/selectedEvtLeptons << "%)." << std::endl;
    std::cout << "B-Jets  " << selectedEvtBJets << " out of " << selectedEvtJets << " (" << 100.*selectedEvtBJets/selectedEvtJets << "%)." << std::endl;
    std::cout << "Lepton Cuts " << selectedEvtLeptonsCuts << " out of " << selectedEvtBJets << " (" << 100.*selectedEvtLeptonsCuts/selectedEvtBJets << "%)." << std::endl;

    return 0;
}

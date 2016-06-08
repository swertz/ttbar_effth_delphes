sample_cut = ""
#sample_cut = "(GenWeight<0)*"

plots = [
    # Leptons
    {
        "name": "lep1_Pt",
        "variable": "lep1_p4.Pt()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 20, 600)"
    },
    {
        "name": "lep1_Eta",
        "variable": "lep1_p4.Eta()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -2.4, 2.4)"
    },
    {
        "name": "lep1_Phi",
        "variable": "lep1_p4.Phi()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -3.14159, 3.14159)"
    },
    {
        "name": "lep2_Pt",
        "variable": "lep2_p4.Pt()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 20, 400)"
    },
    {
        "name": "lep2_Eta",
        "variable": "lep2_p4.Eta()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -2.4, 2.4)"
    },
    {
        "name": "lep1_Phi",
        "variable": "lep2_p4.Phi()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -3.14159, 3.14159)"
    },
    
    # di-Lepton
    {
        "name": "ll_Pt",
        "variable": "ll_p4.Pt()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 600)"
    },
    {
        "name": "ll_M",
        "variable": "ll_p4.M()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 1000)"
    },
    {
        "name": "ll_Eta",
        "variable": "ll_p4.Eta()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -5, 5)"
    },
    {
        "name": "ll_DR",
        "variable": "ll_DR",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 6)"
    },
    {
        "name": "ll_DEta",
        "variable": "ll_DEta",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 6)"
    },
    {
        "name": "ll_DPhi",
        "variable": "ll_DPhi",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 3.14159)"
    },
    
    
    # B-Jets
    {
        "name": "bjet1_Pt",
        "variable": "bjet1_p4.Pt()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 30, 800)"
    },
    {
        "name": "bjet1_Eta",
        "variable": "bjet1_p4.Eta()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -2.4, 2.4)"
    },
    {
        "name": "bjet1_Phi",
        "variable": "bjet1_p4.Phi()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -3.14159, 3.14159)"
    },
    {
        "name": "bjet2_Pt",
        "variable": "bjet2_p4.Pt()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 30, 400)"
    },
    {
        "name": "bjet2_Eta",
        "variable": "bjet2_p4.Eta()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -2.4, 2.4)"
    },
    {
        "name": "bjet1_Phi",
        "variable": "bjet2_p4.Phi()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -3.14159, 3.14159)"
    },
    
    # di-B-Jet
    {
        "name": "bb_Pt",
        "variable": "bb_p4.Pt()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 600)"
    },
    {
        "name": "bb_M",
        "variable": "bb_p4.M()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 1000)"
    },
    {
        "name": "bb_Eta",
        "variable": "bb_p4.Eta()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -5, 5)"
    },
    {
        "name": "bb_DR",
        "variable": "bb_DR",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 6)"
    },
    {
        "name": "bb_DEta",
        "variable": "bb_DEta",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 6)"
    },
    {
        "name": "bb_DPhi",
        "variable": "bb_DPhi",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 3.14159)"
    },
    
    # Extra-Jets
    {
        "name": "jet3_Pt",
        "variable": "jet3_p4.Pt()",
        "plot_cut": sample_cut + "GenWeight * NJet >= 1",
        "binning": "(40, 30, 600)"
    },
    {
        "name": "jet3_Eta",
        "variable": "jet3_p4.Eta()",
        "plot_cut": sample_cut + "GenWeight * NJet >= 1",
        "binning": "(40, -2.4, 2.4)"
    },
    {
        "name": "jet3_Phi",
        "variable": "jet3_p4.Phi()",
        "plot_cut": sample_cut + "GenWeight * NJet >= 1",
        "binning": "(40, -3.14159, 3.14159)"
    },
    {
        "name": "jet4_Pt",
        "variable": "jet4_p4.Pt()",
        "plot_cut": sample_cut + "GenWeight * NJet >= 2",
        "binning": "(40, 30, 300)"
    },
    {
        "name": "jet4_Eta",
        "variable": "jet4_p4.Eta()",
        "plot_cut": sample_cut + "GenWeight * NJet >= 2",
        "binning": "(40, -2.4, 2.4)"
    },
    {
        "name": "jet4_Phi",
        "variable": "jet4_p4.Phi()",
        "plot_cut": sample_cut + "GenWeight * NJet >= 2",
        "binning": "(40, -3.14159, 3.14159)"
    },

    # LLBB
    {
        "name": "llbb_Pt",
        "variable": "llbb_p4.Pt()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 800)"
    },
    {
        "name": "llbb_M",
        "variable": "llbb_p4.M()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 100, 2000)"
    },
    {
        "name": "llbb_Eta",
        "variable": "llbb_p4.Eta()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, -5, 5)"
    },
    {
        "name": "DR_ll_bb",
        "variable": "DR_ll_bb",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 6)"
    },
    {
        "name": "DRbl_min",
        "variable": "DRbl_min",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 6)"
    },
    {
        "name": "DRbl_max",
        "variable": "DRbl_max",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 6)"
    },
    {
        "name": "DEta_ll_bb",
        "variable": "DEta_ll_bb",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 6)"
    },
    {
        "name": "DPhi_ll_bb",
        "variable": "DPhi_ll_bb",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 3.14159)"
    },
    
    # LLBBMET
    {
        "name": "ScalHT",
        "variable": "ScalHT",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 100, 2500)"
    },
    {
        "name": "llbbMet_Pt",
        "variable": "llbbMet_p4t.Pt()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 800)"
    },
    {
        "name": "llbbMet_Mt",
        "variable": "llbbMet_p4t.Mt()",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 100, 2500)"
    },
    {
        "name": "DPhi_ll_Met",
        "variable": "DPhi_ll_Met",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 3.14159)"
    },
    {
        "name": "DPhi_bb_Met",
        "variable": "DPhi_bb_Met",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 3.14159)"
    },
    {
        "name": "DPhi_llbb_Met",
        "variable": "DPhi_llbb_met",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 3.14159)"
    },
    
    # MET
    {
        "name": "Met_met",
        "variable": "MET_met",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 0, 600)"
    },

    # Number of jets
    {
        "name": "nBJet",
        "variable": "NBJet",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(3, 2, 5)"
    },
    {
        "name": "nExtraJet",
        "variable": "NJet",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(7, 0, 7)"
    },

    # Weights
    {
        "name": "Weight_TTbar",
        "variable": "-log10(Weight_SM)",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 20, 50)"
    },
    {
        "name": "Weight_TTbar_good",
        "variable": "-log10(Weight_SM)",
        "plot_cut": sample_cut + "GenWeight*(Weight_SM>0)*(Weight_SM_Err/Weight_SM<0.2)",
        "binning": "(40, 20, 30)"
    },
    {
        "name": "RelPrec_Weight_TTbar",
        "variable": "Weight_SM_Err/Weight_SM",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(100, 0, 2)"
    },
    {
        "name": "Weight_OtG",
        "variable": "-log10(abs(Weight_OtG))",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 20, 50)"
    },
    {
        "name": "Weight_OtG_good",
        "variable": "-log10(abs(Weight_OtG))",
        "plot_cut": sample_cut + "GenWeight*(abs(Weight_OtG)>0)*(abs(Weight_OtG_Err/Weight_OtG)<0.2)",
        "binning": "(40, 20, 30)"
    },
    {
        "name": "Discr_OtG",
        "variable": "(atan(log10(abs(Weight_OtG)/Weight_SM))+1.570795)/3.14159",
        "plot_cut": sample_cut + "GenWeight*(Weight_SM_Err/Weight_SM<0.2)*(abs(Weight_OtG_Err/Weight_OtG)<0.2)*(Weight_SM>0)*(abs(Weight_OtG)>0)",
        "binning": "(40, 0.25, 0.6)"
    },
    {
        "name": "RelPrec_Weight_OtG",
        "variable": "abs(Weight_OtG_Err/Weight_OtG)",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(100, 0, 2)"
    },
    {
        "name": "Weight_OG",
        "variable": "-log10(abs(Weight_OG))",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 21, 50)"
    },
    {
        "name": "Weight_OG_good",
        "variable": "-log10(abs(Weight_OG))",
        "plot_cut": sample_cut + "GenWeight*(abs(Weight_OG)>0)*(abs(Weight_OG_Err/Weight_OG)<0.2)",
        "binning": "(40, 21, 30)"
    },
    {
        "name": "Discr_OG",
        "variable": "(atan(1+log10(abs(Weight_OG)/Weight_SM))+1.570795)/3.14159",
        "plot_cut": sample_cut + "GenWeight*(Weight_SM_Err/Weight_SM<0.2)*(abs(Weight_OG_Err/Weight_OG)<0.2)*(Weight_SM>0)*(abs(Weight_OG)>0)",
        "binning": "(40, 0.1, 0.8)"
    },
    {
        "name": "RelPrec_Weight_OG",
        "variable": "abs(Weight_OG_Err/Weight_OG)",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(100, 0, 2)"
    },
    {
        "name": "Weight_OphiG",
        "variable": "-log10(abs(Weight_OphiG))",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 22, 50)"
    },
    {
        "name": "Weight_OphiG_good",
        "variable": "-log10(abs(Weight_OphiG))",
        "plot_cut": sample_cut + "GenWeight*(abs(Weight_OphiG)>0)*(abs(Weight_OphiG_Err/Weight_OphiG)<0.2)",
        "binning": "(40, 22, 30)"
    },
    {
        "name": "Discr_OphiG",
        "variable": "(atan(2+log10(abs(Weight_OphiG)/Weight_SM))+1.570795)/3.14159",
        "plot_cut": sample_cut + "GenWeight*(Weight_SM_Err/Weight_SM<0.2)*(abs(Weight_OphiG_Err/Weight_OphiG)<0.2)*(Weight_SM>0)*(abs(Weight_OphiG)>0)",
        "binning": "(40, 0.1, 0.8)"
    },
    {
        "name": "RelPrec_Weight_OphiG",
        "variable": "abs(Weight_OphiG_Err/Weight_OphiG)",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(100, 0, 2)"
    },
    {
        "name": "Weight_O81qq",
        "variable": "-log10(abs(Weight_O81qq))",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 22, 50)"
    },
    {
        "name": "Weight_O81qq_good",
        "variable": "-log10(abs(Weight_O81qq))",
        "plot_cut": sample_cut + "GenWeight*(abs(Weight_O81qq)>0)*(abs(Weight_O81qq_Err/Weight_O81qq)<0.2)",
        "binning": "(40, 22, 30)"
    },
    {
        "name": "Discr_O81qq",
        "variable": "(atan(2+log10(abs(Weight_O81qq)/Weight_SM))+1.570795)/3.14159",
        "plot_cut": sample_cut + "GenWeight*(Weight_SM_Err/Weight_SM<0.2)*(abs(Weight_O81qq_Err/Weight_O81qq)<0.2)*(Weight_SM>0)*(abs(Weight_O81qq)>0)",
        "binning": "(40, 0.1, 0.9)"
    },
    {
        "name": "RelPrec_Weight_O81qq",
        "variable": "abs(Weight_O81qq_Err/Weight_O81qq)",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(100, 0, 2)"
    },
    {
        "name": "Weight_O83qq",
        "variable": "-log10(abs(Weight_O83qq))",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 22, 50)"
    },
    {
        "name": "Weight_O83qq_good",
        "variable": "-log10(abs(Weight_O83qq))",
        "plot_cut": sample_cut + "GenWeight*(abs(Weight_O83qq)>0)*(abs(Weight_O83qq_Err/Weight_O83qq)<0.2)",
        "binning": "(40, 23, 32)"
    },
    {
        "name": "Discr_O83qq",
        "variable": "(atan(3+log10(abs(Weight_O83qq)/Weight_SM))+1.570795)/3.14159",
        "plot_cut": sample_cut + "GenWeight*(Weight_SM_Err/Weight_SM<0.2)*(abs(Weight_O83qq_Err/Weight_O83qq)<0.2)*(Weight_SM>0)*(abs(Weight_O83qq)>0)",
        "binning": "(40, 0.1, 0.9)"
    },
    {
        "name": "RelPrec_Weight_O83qq",
        "variable": "abs(Weight_O83qq_Err/Weight_O83qq)",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(100, 0, 2)"
    },
    {
        "name": "Weight_O8ut",
        "variable": "-log10(abs(Weight_O8ut))",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 22, 50)"
    },
    {
        "name": "Weight_O8ut_good",
        "variable": "-log10(abs(Weight_O8ut))",
        "plot_cut": sample_cut + "GenWeight*(abs(Weight_O8ut)>0)*(abs(Weight_O8ut_Err/Weight_O8ut)<0.2)",
        "binning": "(40, 22, 30)"
    },
    {
        "name": "Discr_O8ut",
        "variable": "(atan(2+log10(abs(Weight_O8ut)/Weight_SM))+1.570795)/3.14159",
        "plot_cut": sample_cut + "GenWeight*(Weight_SM_Err/Weight_SM<0.2)*(abs(Weight_O8ut_Err/Weight_O8ut)<0.2)*(Weight_SM>0)*(abs(Weight_O8ut)>0)",
        "binning": "(40, 0.1, 0.9)"
    },
    {
        "name": "RelPrec_Weight_O8ut",
        "variable": "abs(Weight_O8ut_Err/Weight_O8ut)",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(100, 0, 2)"
    },
    {
        "name": "Weight_O8dt",
        "variable": "-log10(abs(Weight_O8dt))",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(40, 22, 50)"
    },
    {
        "name": "Weight_O8dt_good",
        "variable": "-log10(abs(Weight_O8dt))",
        "plot_cut": sample_cut + "GenWeight*(abs(Weight_O8dt)>0)*(abs(Weight_O8dt_Err/Weight_O8dt)<0.2)",
        "binning": "(40, 22, 30)"
    },
    {
        "name": "Discr_O8dt",
        "variable": "(atan(2+log10(abs(Weight_O8dt)/Weight_SM))+1.570795)/3.14159",
        "plot_cut": sample_cut + "GenWeight*(Weight_SM_Err/Weight_SM<0.2)*(abs(Weight_O8dt_Err/Weight_O8dt)<0.2)*(Weight_SM>0)*(abs(Weight_O8dt)>0)",
        "binning": "(40, 0.1, 0.9)"
    },
    {
        "name": "RelPrec_Weight_O8dt",
        "variable": "abs(Weight_O8dt_Err/Weight_O8dt)",
        "plot_cut": sample_cut + "GenWeight",
        "binning": "(100, 0, 2)"
    },
    {
        "name": "Time_Weights",
        "variable": "MEMpp_time_s",
        "plot_cut": "",
        "binning": "(100, 0, 500)"
    },
] 

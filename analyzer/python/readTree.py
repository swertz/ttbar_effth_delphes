import pickle

def read(file):
    with open(file,"rb") as inFile:
        myP = pickle.Unpickler(inFile)

        tree = myP.load()

        _str = 
        "Loaded MISTree {}. \n
        Example usages:\n
            * tree.firstBox.goodMVA.sigLike.printLog() => print log of the signal-like box defined at the root node\n
            * tree.firstBox.printBelow() => print summary of every existing box below (and including) the root node\n
            * for mva in tree.firstBox.goodMVA.bkgLike.MVA: mva.printLog() => print log of all the MVAs defined inside the background-like box defined at the root node\n".format(tree.firstBox.mvaCfg["name"])

        print _str

        return tree

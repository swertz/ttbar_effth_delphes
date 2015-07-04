import pickle
import sys

def read(file):
    with open(file,"rb") as inFile:
        myP = pickle.Unpickler(inFile)

        tree = myP.load()

        _str = """
        Loaded MISTree {}.

        Example usages:

            * myTree.firstBox.goodMVA.sigLike.printLog() => print log of the signal-like box defined at the root node
            * myTree.printBelow() => print summary of every existing box below (and including) the root node
            * print myTree.firstBox() => print summary of the first box's content
            * for mva in myTree.firstBox.goodMVA.bkgLike.MVA: mva.printLog() => print log of all the MVAs defined inside the background-like box defined at the root node
            * myTree.returnByPath(\"{}/TT_vs_DY_SigLike/ZH_vs_DY_BkgLike/ZH_vs_TT\") => return object (box or MVA) by path
            """.format(tree.firstBox.name, tree.firstBox.name)

        print _str

        return tree

myTree = read(sys.argv[1])

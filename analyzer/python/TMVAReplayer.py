import array, os, sys
import ROOT

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

class Node:
    """
    Tree node: left and right child + data which can be any object
    """
    def __init__(self, data, parent = None):
        """
        Node constructor
        @param data node data object
        """
        self.background = None
        self.signal = None
        self.data = data
        self.parent = parent

    def setBackground(self, data):
        self.background = Node(data, self)
        return self.background

    def setSignal(self, data):
        self.signal = Node(data, self)
        return self.signal

    def hasChildren(self):
        return self.signal is not None and self.background is not None

class TMVAReplayer:

    class MVANodeData:
        """
        Data associated to a MVA node inside the binary tree
        """

        def __init__(self, name, reader, mva):
            self.name = name
            self.reader = reader
            self.mva = mva
            self.inputVariables = {}
            self.mvaValue = array.array('f', [0])

        def syncInputVariables(self, variablesCache):
            """
            Synchronize MVA input values with tree values
            """
            for var in self.mva.cfg.mvaCfg["inputvar"]:
                if not var in self.inputVariables.keys():
                    a = array.array('f', [0])
                    self.inputVariables[var] = a
                    self.reader.AddVariable(var, a)

                # variablesCache is TTreeFormula, inputVariables is float
                self.inputVariables[var][0] = variablesCache[var].EvalInstance()

        def book(self):
            self.reader.BookMVA("MVA", TMVAReplayer.getXMLPath(self.mva))

        def evaluate(self):
            self.mvaValue[0] = self.reader.EvaluateMVA("MVA")
            return self.mvaValue[0]

    class EndNodeData:
        """
        Data associated with an end node inside the binary tree
        """
        def __init__(self, name, file, chain):
            self.name = name
            self.file = file
            self.chain = chain
            self.entries = 0
            self.binNumber = 0

        def fill(self, weight):
            self.chain.Fill()
            self.entries = self.entries + weight



    
    def __init__(self, configuration, root):
        self.configuration = configuration
        datasets = configuration["datasets"]
        if len(datasets.keys()) > 1:
            print("Error: only one dataset is supported for replay for the moment")
            sys.exit(1)

        name, data = datasets.iterkeys().next(), datasets.itervalues().next()
        self.inputDataset = data
        self.outputDirectory = configuration["analysis"]["outputdir"]
        self.name = name
        self.root = root
        self.mvas = {}
        self.inputVariables = {}
        self.numberOfEndNodes = 0
        self.treeRoot = None

        self.chain = ROOT.TChain(data["treename"])
        for file in data["path"]:
            self.chain.Add(file)

    def createMVAs(self, node, parentNode = None):
        if not node.isEnd:
            print("Creating MVA reader for node '%s'" % node.name)
            mvaNode = TMVAReplayer.MVANodeData(node.name, ROOT.TMVA.Reader("Silent"), node.goodMVA)
            self.linkInputVariables(node.goodMVA, mvaNode)
            mvaNode.book()

            if parentNode is None:
                self.treeRoot = Node(mvaNode)
                parentNode = self.treeRoot
            else:
                if node.type == "sig":
                    parentNode = parentNode.setSignal(mvaNode)
                else:
                    parentNode = parentNode.setBackground(mvaNode)

            for child in node.daughters:
                self.createMVAs(child, parentNode)
        else:
            print("End of chain with node '%s'" % node.name)
            path = os.path.join(self.outputDirectory, node.name, self.name + ".root")
            print("\tOutput file: '%s'" % path)
            ensure_dir(path)

            f = ROOT.TFile(path, "recreate")
            chain = self.chain.CloneTree(0)

            endNode = TMVAReplayer.EndNodeData(node.name, f, chain)
            self.numberOfEndNodes = self.numberOfEndNodes + 1

            treeNode = None
            if node.type == "sig":
                treeNode = parentNode.setSignal(endNode)
            else:
                treeNode = parentNode.setBackground(endNode)

            # Iterate backwards and create branch in chain with mva outputs

            # Skip this node
            treeNode = treeNode.parent
            parent = treeNode.parent
            while treeNode is not None:

                branchName = "MVAOUT__%s" % (treeNode.data.name.replace("/", "_"))
                chain.Branch(branchName, treeNode.data.mvaValue, branchName + "/F")

                treeNode = parent
                if treeNode is not None:
                    parent = treeNode.parent


    def linkInputVariables(self, mva, mvaNode):
        """For all 'inputvar' of the MVA, create the associated TTreeFormula in the chain if needed"""
        for var in mva.cfg.mvaCfg["inputvar"]:
            # var can be a complex expression. Use TTreeFormula
            if not var in self.inputVariables.keys():
                formulaName = var.replace(' ', '_')
                formula = ROOT.TTreeFormula(formulaName, var, self.chain)
                formula.GetNdata()
                self.chain.SetNotify(formula)
                self.inputVariables[var] = formula


        mvaNode.syncInputVariables(self.inputVariables)

    def syncMVAInputVariables(self, node):
        if node is None or not node.hasChildren():
            return

        node.data.syncInputVariables(self.inputVariables)
        self.syncMVAInputVariables(node.signal)
        self.syncMVAInputVariables(node.background)

    def getNextMVA(self, node, value):
        """Given a mva value, find the next mva we should use to classify.
        Return None if we are at the end of the chain"""
        cut = node.data.mva.cutValue
        if value > cut:
            return node.signal
        else:
            return node.background

    def runOnEndNodes(self, rootNode, lambda_):
        """Iterator over the tree from rootNode, and execute lambda_
        on each end node"""

        if rootNode is None:
            return

        if rootNode.hasChildren():
            self.runOnEndNodes(rootNode.background, lambda_)
            self.runOnEndNodes(rootNode.signal, lambda_)
        else:
            lambda_(rootNode)


    def run(self):
        self.createMVAs(self.root)

        self.binNumber = 1
        def assignBinNumber(node):
            node.data.binNumber = self.binNumber
            self.binNumber = self.binNumber + 1

        self.runOnEndNodes(self.treeRoot, assignBinNumber)
        del self.binNumber

        lumi = self.configuration["analysis"]["lumi"]
        xsection = self.inputDataset["xsection"]
        ngen = self.inputDataset["genevents"]

        datasetWeight = (xsection * lumi) / ngen

        summaryName = "%s_yields" % (self.name)
        self.summaryHist = ROOT.TH1F(summaryName, summaryName, self.numberOfEndNodes, 0, self.numberOfEndNodes)
        self.summaryHist.SetDirectory(0)
        self.summaryHist.Sumw2()

        # Create weight formula
        weightFormula = self.inputDataset["evtweight"]
        if len(weightFormula) > 0:
            weightFormulaName = weightFormula.replace(' ', '_')
            weightFormula = ROOT.TTreeFormula(weightFormulaName, weightFormula, self.chain)
            weightFormula.GetNdata()
            self.chain.SetNotify(weightFormula)
        else:
            weightFormula = None

        print("\nProcessing events...")

        i = 0
        # Main loop
        for event in self.chain:

            if i % 10000 == 0:
                print("Event %d over %d" % (i + 1, self.chain.GetEntries()))

            weight = datasetWeight
            if weightFormula is not None:
                weight = weight * weightFormula.EvalInstance()

            # Sync MVA readers variables with tree
            self.syncMVAInputVariables(self.treeRoot)

            # Evaluate root MVA, and start classifying
            node = self.treeRoot
            mvaValue = self.treeRoot.data.evaluate()

            while True:
                node = self.getNextMVA(node, mvaValue)
                if node is None:
                    break

                if not node.hasChildren():
                    node.data.fill(weight)

                    self.summaryHist.Fill(node.data.binNumber - 0.5, weight)
                    break

                # Evaluate new MVA
                mvaValue = node.data.evaluate()

            i = i + 1

        print("\nAll done. Writing files ...")

        def writeFile(node):
            print("%.2f expected events in node '%s'" % (node.data.entries, node.data.name))
            node.data.file.Write()

        self.runOnEndNodes(self.treeRoot, writeFile)

        def setBinLabels(node):
            self.summaryHist.GetXaxis().SetBinLabel(node.data.binNumber, node.data.name)

        self.runOnEndNodes(self.treeRoot, setBinLabels)

        f = ROOT.TFile(os.path.join(self.outputDirectory, "%s_hists.root" % self.name), "recreate")
        self.summaryHist.Write()
        f.Close()


    @staticmethod
    def getXMLPath(mva):
        cfg = mva.cfg.mvaCfg
        return os.path.join(cfg["outputdir"], "{0}_{1}_{0}.weights.xml".format(cfg["outputname"], cfg["mvamethod"]))

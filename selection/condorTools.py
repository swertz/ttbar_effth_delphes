##
## Utilities to submit condor jobs to create the histograms.
## See condorExample.py for how-to usage.
##

import os
import sys
import stat
import copy

class condorSubmitter:

    def __init__(self, MGdir, baseDir = ".", usedMadSpin = False):

        self.MGdir = MGdir
        self.fileList = self.getSampleFiles(usedMadSpin)
        self.baseDir = os.path.join(os.path.abspath(baseDir), "condor")
        self.isCreated = False
        self.user = os.environ["USER"]

        self.baseCmd = """
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
universe       = vanilla
requirements   = (CMSFARM =?= TRUE)&&(Memory > 200)

"""
        self.jobCmd = """
output         = #LOGDIR_RELPATH#/condor_#JOB_ID#.out
error          = #LOGDIR_RELPATH#/condor_#JOB_ID#.err
log            = #LOGDIR_RELPATH#/condor_#JOB_ID#.log
executable     = #INDIR_PATH#/condor_#JOB_ID#.sh
queue 1

"""

        with open("delphes_fromPy6.sh") as baseSh:
            self.baseShell = baseSh.read()

    def getSampleFiles(self, usedMadSpin):
        """ Get sample name/list of sample files from the MG5 dir. """
   
        eventDir = os.path.join(self.MGdir, "Events")
        myDirs = [ os.path.join(eventDir, dir) for dir in os.listdir(eventDir) ]
        myDirs = [ dir for dir in myDirs if os.path.isdir(dir) ]
        
        if usedMadSpin:
            myDirs = [ dir for dir in myDirs if "decayed" in dir ]

        if len(myDirs) == 0:
            raise Exception("Couldn't find any events directory in {}.".format(eventDir))
        
        fileList = []

        for dir in myDirs:
            content = os.listdir(dir)
            
            lheFile = ""
            
            for file in content:
                #if "unweighted_events.lhe" in file:
                if "tag_1_pythia_events.hep" in file:
                    lheFile = file

            if lheFile == "":
                print "No LHE file in {}.".format(dir)
                continue

            fileList.append( (dir, lheFile) )

        if len(fileList) == 0:
            raise Exception("Couldn't find event files in directory {}.".format(eventDir))

        return fileList


    def setupCondorDirs(self):
        """ Setup the condor directories (input/output) in baseDir. """
    
        if not os.path.isdir(self.baseDir):
            os.makedirs(self.baseDir)
    
        inDir = os.path.join(self.baseDir, "input")
        if not os.path.isdir(inDir):
            os.makedirs(inDir)
        self.inDir = inDir
        
        outDir = os.path.join(self.baseDir, "output")
        if not os.path.isdir(outDir):
            os.makedirs(outDir)
        self.outDir = outDir

        logDir = os.path.join(self.baseDir, "logs_selection")
        if not os.path.isdir(logDir):
            os.makedirs(logDir)
        self.logDir = os.path.relpath(logDir)

    def createCondorFiles(self):
        """ Create the .sh and .cmd files for Condor."""

        jobCount = 0

        for files in self.fileList:

            dico = {}
            dico["#JOB_ID#"] = str(jobCount)
            dico["#MG_EVENT_DIR#"] = files[0]
            dico["#MG_INPUT_FILE#"] = files[1]
            dico["#OUTDIR_PATH#"] = self.outDir
            dico["#INDIR_PATH#"] = self.inDir
            dico["#LOGDIR_RELPATH#"] = os.path.relpath(self.logDir)

            thisCmd = str(self.jobCmd)
            thisSh = str(self.baseShell)
            
            for key in dico.items():
                thisCmd = thisCmd.replace(key[0], key[1])
                thisSh = thisSh.replace(key[0], key[1])
            self.baseCmd += thisCmd

            shFileName = os.path.join(self.inDir, "condor_{}.sh".format(jobCount))
            with open(shFileName, "w") as sh:
                sh.write(thisSh)
            perm = os.stat(shFileName)
            os.chmod(shFileName, perm.st_mode | stat.S_IEXEC)

            jobCount += 1
           
        cmdFileName = os.path.join(self.inDir, "condor.cmd")
        with open(cmdFileName, "w") as cmd:
            cmd.write(self.baseCmd)

        print "Created {} job command files. Caution: the jobs are not submitted yet!.".format(jobCount)

        self.jobCount = jobCount
        self.isCreated = True

    
    def submitOnCondor(self):

        if not self.isCreated:
            raise Exception("Job files must be created first using createCondorFiles().")

        print "Submitting {} condor jobs.".format(self.jobCount)
        os.system("condor_submit {}".format( os.path.join(self.inDir, "condor.cmd") ) )

        print "Submitting {} jobs done.".format(self.jobCount)
        print "Monitor your jobs with `condor_status -submitter` or `condor_q {}`".format(self.user)



if __name__ == "__main__":
    raise Exception("Not destined to be run stand-alone.")

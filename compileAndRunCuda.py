#!/usr/bin/python

import sys
import os

cudaCompiler = "nvcc"
workLoadFile = sys.argv[2]
resultFile   = sys.argv[4]
exeName      = "runFile_" + workLoadFile.split("_")[1][:-3] + ".exe"
cmdCompile = cudaCompiler + " " + workLoadFile + " -o " + exeName

os.system(cmdCompile)

cmdRun = "./" + exeName + " > " + resultFile 
os.system(cmdRun)

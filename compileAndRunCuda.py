#!/usr/bin/python
import sys
import os

cudaCompiler      = "nvcc"
cudaCompilerFlags = " --disable-warnings "
workLoadFile      = sys.argv[2]
resultFile        = sys.argv[4]
exeName           = "runFile_" + workLoadFile.split("_")[1] + workLoadFile.split("_")[2][:-3] + ".exe"


cmdCompile = cudaCompiler + cudaCompilerFlags + workLoadFile + " -o " + exeName

print "COMPILATION COMMAND : ", cmdCompile

os.system(cmdCompile)

cmdRun = "./" + exeName + " > " + resultFile 
os.system(cmdRun)

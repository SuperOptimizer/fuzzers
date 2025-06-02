import os
import shutil
import re
import sys
import random
import string
import subprocess

def triage_afl_crashes(input_dir, executable):
    for path in list(os.listdir(input_dir))[:100]:
      try:
        ret =subprocess.run([executable, f"{input_dir}/{path}"],stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,timeout=1)
        if ret.returncode!= 0:
          print(f"triaging {input_dir}/{path}")
          print(ret.stdout.decode('ascii'))
          print(ret.stderr.decode('ascii'))
      except:

        pass #subprocess.run raises if we get a timeout. ignore for now

def main():
   if len(sys.argv) != 3:
       print("Usage: python script.py <pocs_dir> <executable_path>")
       sys.exit(1)
   input_dir = sys.argv[1]
   executable = sys.argv[2]
   if not os.path.exists(input_dir):
       print("Error: Input directory does not exist!")
       sys.exit(1)
   try:
       triage_afl_crashes(input_dir, executable)
   except Exception as e:
       print(f"An error occurred: {str(e)}")
       sys.exit(1)

if __name__ == "__main__":
   main()

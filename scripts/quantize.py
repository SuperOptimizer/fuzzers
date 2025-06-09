import os
import shutil
import re
import sys
import random
import string
import subprocess

quantize_types = {
       2,
       3,
       8,
       9,
      19,
      20,
      28,
      29,
      24,
      31,
      36,
      37,
      10,
      21,
      23,
      26,
      27,
      12,
      22,
      11,
      12,
      13,
      25,
      30,
      15,
      14,
      15,
      17,
      16,
      17,
      18,
       7,
       1,
      32,
       0,
}

def quantize_model(gguf_path, output_dir, executable):
    for t in quantize_types:
        fname = os.path.basename(gguf_path)
        ret = subprocess.run([executable, f"{gguf_path}", f"{output_dir}/{t}_{fname}", f"{t}", "32"], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        if ret.returncode != 0:
            stdout = ret.stdout.decode('ascii')
            stderr = ret.stderr.decode('ascii')
            print(stdout)
            print(stderr)



def main():
    if len(sys.argv) != 4:
        print("Usage: python script.py <gguf_file> <output_dir> <llama_quantize_path")
        sys.exit(1)
    gguf_file = sys.argv[1]
    output_dir = sys.argv[2]
    llama_quantize_path = sys.argv[3]
    quantize_model(gguf_file, output_dir, llama_quantize_path)



if __name__ == "__main__":
    main()

import os
import shutil
import re
import sys
import random
import string

def process_afl_crashes(input_dir, output_dir):
   os.makedirs(output_dir, exist_ok=True)
   for root, _, files in os.walk(input_dir):
       if 'crashes' not in root:
           continue
       for filename in files:
           full_path = os.path.join(root, filename)
           if  filename.startswith('id:'):
               new_filename = f"poc_{''.join(random.choices(string.ascii_letters + string.digits, k=32))}.gguf"
               new_path = os.path.join(output_dir, new_filename)
               shutil.copy2(full_path, new_path)
               print(f"Copied {full_path} to {new_path}")

def main():
   if len(sys.argv) != 3:
       print("Usage: python script.py <input_dir> <output_dir>")
       sys.exit(1)
   input_dir = sys.argv[1]
   output_dir = sys.argv[2]
   if not os.path.exists(input_dir):
       print("Error: Input directory does not exist!")
       sys.exit(1)
   try:
       process_afl_crashes(input_dir, output_dir)
   except Exception as e:
       print(f"An error occurred: {str(e)}")
       sys.exit(1)

if __name__ == "__main__":
   main()

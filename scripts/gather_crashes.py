import os
import shutil
import re
file_counter = 1
import sys

def process_afl_crashes(input_dir, output_dir):
    global file_counter
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    # Walk through the input directory
    for root, _, files in os.walk(input_dir):
        for filename in files:
            full_path = os.path.join(root, filename)

            # Check if the path contains 'crashes/' and filename starts with 'id:'
            if 'crashes/' in full_path and filename.startswith('id:'):
                # Create new filename
                new_filename = f"poc_{file_counter}.gguf"
                new_path = os.path.join(output_dir, new_filename)

                # Copy the file to the new location with the new name
                shutil.copy2(full_path, new_path)
                print(f"Copied {full_path} to {new_path}")

                file_counter += 1


def main():
    global file_counter
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_dir> <output_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    # Validate input directory
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
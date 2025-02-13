import os
import shutil
import re


def process_afl_crashes(input_dir, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Counter for renaming files
    file_counter = 1

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
    # Get input and output directories from user
    input_dir = input("Enter the input directory path: ")
    output_dir = input("Enter the output directory path: ")

    # Validate directories
    if not os.path.exists(input_dir):
        print("Error: Input directory does not exist!")
        return

    try:
        process_afl_crashes(input_dir, output_dir)
        print(f"\nProcessing complete! {file_counter - 1} files were processed.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
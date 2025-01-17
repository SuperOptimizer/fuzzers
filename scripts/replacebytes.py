import sys
import argparse


def replace_bytes(input_file, output_file, original_byte, new_byte, max_occurrences=None, specific_occurrences=None):
    try:
        orig_byte = bytes([int(original_byte, 16) if '0x' in original_byte else int(original_byte)])
        replacement_byte = bytes([int(new_byte, 16) if '0x' in new_byte else int(new_byte)])
    except ValueError:
        print("Error: Byte values must be valid integers or hex values")
        sys.exit(1)

    try:
        # Read input file in binary mode
        with open(input_file, 'rb') as f:
            content = f.read()

        content_array = bytearray(content)
        count = 0
        total_found = 0

        # Find all occurrences
        positions = []
        for i in range(len(content_array)):
            if content_array[i] == orig_byte[0]:
                positions.append(i)
                total_found += 1

        # Determine which positions to replace
        to_replace = []
        if specific_occurrences:
            # Convert 1-based indices to 0-based
            to_replace = [pos - 1 for pos in specific_occurrences if pos <= len(positions)]
        elif max_occurrences:
            to_replace = positions[:max_occurrences]
        else:
            to_replace = positions

        # Perform replacements
        for pos in to_replace:
            content_array[positions[pos]] = replacement_byte[0]
            count += 1

        modified = bytes(content_array)

        # Write to output file in binary mode
        with open(output_file, 'wb') as f:
            f.write(modified)

        print(f"Found {total_found} occurrences")
        print(f"Replaced {count} occurrences")

    except FileNotFoundError:
        print(f"Error: Could not find input file {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replace bytes in a file')
    parser.add_argument('input_file', help='Input file path')
    parser.add_argument('output_file', help='Output file path')
    parser.add_argument('original_byte', help='Byte to replace (hex or decimal)')
    parser.add_argument('new_byte', help='New byte value (hex or decimal)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-m', '--max', type=int, help='Maximum number of occurrences to replace')
    group.add_argument('-s', '--specific', type=int, nargs='+',
                       help='Specific occurrences to replace (1-based indexing)')

    args = parser.parse_args()

    replace_bytes(args.input_file, args.output_file, args.original_byte, args.new_byte,
                  args.max, args.specific)
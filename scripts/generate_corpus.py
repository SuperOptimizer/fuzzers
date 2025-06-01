#!/usr/bin/env python3
"""
Generate a corpus of GGUF files for fuzzing.
Creates various edge cases and normal files.
This script can work standalone or import from generate_gguf.py
"""

import os
import struct
import random
import numpy as np

# GGUF constants
GGUF_MAGIC = b'GGUF'
GGUF_VERSION = 3

# Try to import the full generator, otherwise use simplified version
try:
    from generate_gguf import generate_random_gguf
except ImportError:
    def generate_random_gguf(max_size_kb=100):
        """Simplified random GGUF generator"""
        data = bytearray()
        data.extend(GGUF_MAGIC)
        data.extend(struct.pack('<I', GGUF_VERSION))
        
        # Random counts
        n_tensors = random.randint(1, 3)
        n_kv = random.randint(2, 10)
        
        data.extend(struct.pack('<q', n_tensors))
        data.extend(struct.pack('<q', n_kv))
        
        # Generate KV pairs
        for i in range(n_kv):
            key = f"key_{i}"
            data.extend(struct.pack('<Q', len(key)))
            data.extend(key.encode('utf-8'))
            
            # Random type (simplified - just int32, float32, or string)
            kv_type = random.choice([5, 6, 8])  # INT32, FLOAT32, STRING
            data.extend(struct.pack('<i', kv_type))
            
            if kv_type == 5:  # INT32
                data.extend(struct.pack('<i', random.randint(-1000, 1000)))
            elif kv_type == 6:  # FLOAT32
                data.extend(struct.pack('<f', random.uniform(-100, 100)))
            else:  # STRING
                val = f"value_{i}"
                data.extend(struct.pack('<Q', len(val)))
                data.extend(val.encode('utf-8'))
        
        # Generate tensor info
        tensor_sizes = []
        for i in range(n_tensors):
            name = f"tensor_{i}"
            data.extend(struct.pack('<Q', len(name)))
            data.extend(name.encode('utf-8'))
            
            # Dimensions
            n_dims = random.randint(1, 3)
            data.extend(struct.pack('<I', n_dims))
            
            shape = []
            for d in range(4):
                if d < n_dims:
                    dim_size = random.randint(1, 20)
                    shape.append(dim_size)
                else:
                    shape.append(1)
                data.extend(struct.pack('<q', shape[d]))
            
            # Type (F32)
            data.extend(struct.pack('<i', 0))
            
            # Offset placeholder
            offset_pos = len(data)
            data.extend(struct.pack('<Q', 0))
            
            n_elements = np.prod(shape[:n_dims])
            tensor_sizes.append((offset_pos, n_elements))
        
        # Align to 32 bytes
        while len(data) % 32 != 0:
            data.append(0)
        
        data_start = len(data)
        
        # Generate tensor data
        for offset_pos, n_elements in tensor_sizes:
            # Update offset
            offset = len(data) - data_start
            struct.pack_into('<Q', data, offset_pos, offset)
            
            # Random float32 data
            tensor_data = np.random.randn(n_elements).astype(np.float32)
            data.extend(tensor_data.tobytes())
            
            # Align
            while len(data) % 32 != 0:
                data.append(0)
        
        return bytes(data[:max_size_kb * 1024])

def generate_minimal_gguf():
    """Generate a minimal valid GGUF file"""
    data = bytearray()
    data.extend(GGUF_MAGIC)
    data.extend(struct.pack('<I', GGUF_VERSION))
    data.extend(struct.pack('<q', 0))  # 0 tensors
    data.extend(struct.pack('<q', 0))  # 0 KV pairs
    return bytes(data)

def generate_empty_tensor_gguf():
    """Generate GGUF with tensor info but no data"""
    data = bytearray()
    data.extend(GGUF_MAGIC)
    data.extend(struct.pack('<I', GGUF_VERSION))
    data.extend(struct.pack('<q', 1))  # 1 tensor
    data.extend(struct.pack('<q', 0))  # 0 KV pairs
    
    # Tensor info
    # Name
    name = "empty_tensor"
    data.extend(struct.pack('<Q', len(name)))
    data.extend(name.encode('utf-8'))
    
    # Dimensions
    data.extend(struct.pack('<I', 1))  # 1D
    data.extend(struct.pack('<q', 0))  # 0 elements
    data.extend(struct.pack('<q', 1))  # ne[1]
    data.extend(struct.pack('<q', 1))  # ne[2]
    data.extend(struct.pack('<q', 1))  # ne[3]
    
    # Type and offset
    data.extend(struct.pack('<i', 0))  # F32
    data.extend(struct.pack('<Q', 0))  # offset
    
    # Add padding
    while len(data) % 32 != 0:
        data.append(0)
    
    return bytes(data)

def generate_large_metadata_gguf():
    """Generate GGUF with large metadata strings"""
    data = bytearray()
    data.extend(GGUF_MAGIC)
    data.extend(struct.pack('<I', GGUF_VERSION))
    data.extend(struct.pack('<q', 0))  # 0 tensors
    data.extend(struct.pack('<q', 3))  # 3 KV pairs
    
    # Large string values
    for i in range(3):
        key = f"large_string_{i}"
        data.extend(struct.pack('<Q', len(key)))
        data.extend(key.encode('utf-8'))
        data.extend(struct.pack('<i', 8))  # STRING type
        
        # Large string value
        large_string = 'A' * 1000
        data.extend(struct.pack('<Q', len(large_string)))
        data.extend(large_string.encode('utf-8'))
    
    return bytes(data)

def generate_max_dimensions_gguf():
    """Generate GGUF with maximum dimensions"""
    data = bytearray()
    data.extend(GGUF_MAGIC)
    data.extend(struct.pack('<I', GGUF_VERSION))
    data.extend(struct.pack('<q', 1))  # 1 tensor
    data.extend(struct.pack('<q', 0))  # 0 KV pairs
    
    # Tensor with 4 dimensions
    name = "max_dims"
    data.extend(struct.pack('<Q', len(name)))
    data.extend(name.encode('utf-8'))
    
    data.extend(struct.pack('<I', 4))  # 4D
    data.extend(struct.pack('<q', 2))  # 2x3x4x5
    data.extend(struct.pack('<q', 3))
    data.extend(struct.pack('<q', 4))
    data.extend(struct.pack('<q', 5))
    
    data.extend(struct.pack('<i', 0))  # F32
    data.extend(struct.pack('<Q', 0))  # offset
    
    # Padding
    while len(data) % 32 != 0:
        data.append(0)
    
    # Tensor data (2*3*4*5 = 120 floats)
    tensor_data = np.random.randn(120).astype(np.float32)
    data.extend(tensor_data.tobytes())
    
    return bytes(data)

def generate_array_metadata_gguf():
    """Generate GGUF with array metadata"""
    data = bytearray()
    data.extend(GGUF_MAGIC)
    data.extend(struct.pack('<I', GGUF_VERSION))
    data.extend(struct.pack('<q', 0))  # 0 tensors
    data.extend(struct.pack('<q', 2))  # 2 KV pairs
    
    # Array of integers
    key1 = "int_array"
    data.extend(struct.pack('<Q', len(key1)))
    data.extend(key1.encode('utf-8'))
    data.extend(struct.pack('<i', 9))  # ARRAY type
    data.extend(struct.pack('<i', 5))  # INT32
    data.extend(struct.pack('<Q', 5))  # 5 elements
    for i in range(5):
        data.extend(struct.pack('<i', i * 10))
    
    # Array of floats
    key2 = "float_array"
    data.extend(struct.pack('<Q', len(key2)))
    data.extend(key2.encode('utf-8'))
    data.extend(struct.pack('<i', 9))  # ARRAY type
    data.extend(struct.pack('<i', 6))  # FLOAT32
    data.extend(struct.pack('<Q', 3))  # 3 elements
    for i in range(3):
        data.extend(struct.pack('<f', i * 3.14))
    
    return bytes(data)

def generate_malformed_gguf(variant):
    """Generate various malformed GGUF files"""
    if variant == 0:
        # Wrong magic
        return b'XXXX' + struct.pack('<I', GGUF_VERSION) + b'\x00' * 16
    elif variant == 1:
        # Wrong version
        return GGUF_MAGIC + struct.pack('<I', 999) + b'\x00' * 16
    elif variant == 2:
        # Truncated header
        return GGUF_MAGIC + struct.pack('<I', GGUF_VERSION)
    elif variant == 3:
        # Negative counts
        data = bytearray()
        data.extend(GGUF_MAGIC)
        data.extend(struct.pack('<I', GGUF_VERSION))
        data.extend(struct.pack('<q', -1))  # negative tensor count
        data.extend(struct.pack('<q', -1))  # negative KV count
        return bytes(data)
    elif variant == 4:
        # Huge counts
        data = bytearray()
        data.extend(GGUF_MAGIC)
        data.extend(struct.pack('<I', GGUF_VERSION))
        data.extend(struct.pack('<q', 2**60))  # huge tensor count
        data.extend(struct.pack('<q', 2**60))  # huge KV count
        return bytes(data)
    elif variant == 5:
        # Invalid string length
        data = bytearray()
        data.extend(GGUF_MAGIC)
        data.extend(struct.pack('<I', GGUF_VERSION))
        data.extend(struct.pack('<q', 0))  # 0 tensors
        data.extend(struct.pack('<q', 1))  # 1 KV pair
        data.extend(struct.pack('<Q', 2**62))  # huge string length
        return bytes(data)
    elif variant == 6:
        # Misaligned data
        data = bytearray()
        data.extend(GGUF_MAGIC)
        data.extend(struct.pack('<I', GGUF_VERSION))
        data.extend(struct.pack('<q', 1))  # 1 tensor
        data.extend(struct.pack('<q', 0))  # 0 KV pairs
        
        # Tensor info
        name = "misaligned"
        data.extend(struct.pack('<Q', len(name)))
        data.extend(name.encode('utf-8'))
        data.extend(struct.pack('<I', 1))  # 1D
        data.extend(struct.pack('<q', 10))
        data.extend(struct.pack('<q', 1))
        data.extend(struct.pack('<q', 1))
        data.extend(struct.pack('<q', 1))
        data.extend(struct.pack('<i', 0))  # F32
        data.extend(struct.pack('<Q', 17))  # Misaligned offset
        
        # Don't add proper padding
        data.extend(b'\x00' * 17)
        data.extend(b'\x41' * 40)  # Some data
        
        return bytes(data)
    else:
        # Random garbage
        return bytes(random.getrandbits(8) for _ in range(100))

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate GGUF corpus for fuzzing')
    parser.add_argument('output_dir', help='Output directory for corpus files')
    parser.add_argument('--count', type=int, default=20, 
                        help='Number of random files to generate (default: 20)')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate edge cases
    edge_cases = [
        ('minimal.gguf', generate_minimal_gguf()),
        ('empty_tensor.gguf', generate_empty_tensor_gguf()),
        ('large_metadata.gguf', generate_large_metadata_gguf()),
        ('max_dimensions.gguf', generate_max_dimensions_gguf()),
        ('array_metadata.gguf', generate_array_metadata_gguf()),
    ]
    
    # Add malformed files
    for i in range(8):
        edge_cases.append((f'malformed_{i}.gguf', generate_malformed_gguf(i)))
    
    # Write edge cases
    for filename, data in edge_cases:
        path = os.path.join(args.output_dir, filename)
        with open(path, 'wb') as f:
            f.write(data)
        print(f"Generated: {path} ({len(data)} bytes)")
    
    # Generate random valid files
    for i in range(args.count):
        filename = f'random_{i:03d}.gguf'
        path = os.path.join(args.output_dir, filename)
        
        # Vary the size
        max_size = random.choice([10, 50, 100, 200])
        data = generate_random_gguf(max_size)
        
        with open(path, 'wb') as f:
            f.write(data)
        print(f"Generated: {path} ({len(data)} bytes)")
    
    print(f"\nGenerated {len(edge_cases) + args.count} files in {args.output_dir}")

if __name__ == '__main__':
    main()

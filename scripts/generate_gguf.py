#!/usr/bin/env python3
"""
Random GGUF file generator for fuzzing purposes.
Generates small GGUF files with random metadata and tensors.
"""

import struct
import random
import string
import numpy as np
from typing import List, Tuple, Any
import argparse

# GGUF constants from the C++ code
GGUF_MAGIC = b'GGUF'
GGUF_VERSION = 3
GGUF_DEFAULT_ALIGNMENT = 32

# GGUF types
class GGUFType:
    UINT8 = 0
    INT8 = 1
    UINT16 = 2
    INT16 = 3
    UINT32 = 4
    INT32 = 5
    FLOAT32 = 6
    BOOL = 7
    STRING = 8
    ARRAY = 9
    UINT64 = 10
    INT64 = 11
    FLOAT64 = 12

# GGML types (tensor types)
class GGMLType:
    F32 = 0
    F16 = 1
    Q4_0 = 2
    Q4_1 = 3
    Q5_0 = 6
    Q5_1 = 7
    Q8_0 = 8
    Q8_1 = 9
    I8 = 16
    I16 = 17
    I32 = 18

def write_string(data: bytearray, s: str):
    """Write a GGUF string (uint64 length + UTF-8 data)"""
    encoded = s.encode('utf-8')
    data.extend(struct.pack('<Q', len(encoded)))
    data.extend(encoded)

def write_padding(data: bytearray, alignment: int):
    """Add padding to align to the specified boundary"""
    while len(data) % alignment != 0:
        data.append(0)

def random_string(min_len=1, max_len=20):
    """Generate a random string"""
    length = random.randint(min_len, max_len)
    # Use printable characters to avoid encoding issues
    return ''.join(random.choices(string.ascii_letters + string.digits + '_.-', k=length))

def random_key():
    """Generate a random metadata key"""
    # Include more realistic prefixes from the spec
    prefixes = [
        'model.', 'tokenizer.', 'general.', 'training.', 'custom.',
        'llama.', 'mpt.', 'gptneox.', 'bloom.', 'falcon.',
        'llama.rope.', 'llama.attention.', 'tokenizer.ggml.',
        'general.source.', 'general.base_model.'
    ]
    prefix = random.choice(prefixes)
    
    # Common suffixes
    suffixes = [
        'version', 'count', 'length', 'size', 'type', 'weight',
        'epsilon', 'factor', 'scale', 'dimension', 'layer',
        'head_count', 'vocab_size', 'hidden_size', 'intermediate_size'
    ]
    
    if random.random() < 0.7:
        # Use common suffix
        suffix = random.choice(suffixes)
    else:
        # Random suffix
        suffix = random_string(5, 15)
    
    return prefix + suffix

def generate_random_value(gguf_type: int) -> Tuple[Any, bytes]:
    """Generate a random value of the specified GGUF type"""
    if gguf_type == GGUFType.UINT8:
        val = random.randint(0, 255)
        return val, struct.pack('<B', val)
    elif gguf_type == GGUFType.INT8:
        val = random.randint(-128, 127)
        return val, struct.pack('<b', val)
    elif gguf_type == GGUFType.UINT16:
        val = random.randint(0, 65535)
        return val, struct.pack('<H', val)
    elif gguf_type == GGUFType.INT16:
        val = random.randint(-32768, 32767)
        return val, struct.pack('<h', val)
    elif gguf_type == GGUFType.UINT32:
        val = random.randint(0, 2**32-1)
        return val, struct.pack('<I', val)
    elif gguf_type == GGUFType.INT32:
        val = random.randint(-2**31, 2**31-1)
        return val, struct.pack('<i', val)
    elif gguf_type == GGUFType.FLOAT32:
        val = random.uniform(-1000, 1000)
        return val, struct.pack('<f', val)
    elif gguf_type == GGUFType.BOOL:
        val = random.choice([True, False])
        return val, struct.pack('<b', 1 if val else 0)
    elif gguf_type == GGUFType.STRING:
        val = random_string()
        return val, b''  # String handled separately
    elif gguf_type == GGUFType.ARRAY:
        # Arrays are handled separately in the main generator
        raise ValueError(f"ARRAY type should not be passed to generate_random_value")
    elif gguf_type == GGUFType.UINT64:
        val = random.randint(0, 2**63-1)  # Keep it reasonable
        return val, struct.pack('<Q', val)
    elif gguf_type == GGUFType.INT64:
        val = random.randint(-2**63, 2**63-1)
        return val, struct.pack('<q', val)
    elif gguf_type == GGUFType.FLOAT64:
        val = random.uniform(-1000, 1000)
        return val, struct.pack('<d', val)
    else:
        raise ValueError(f"Unknown GGUF type: {gguf_type}")

def generate_tensor_data(shape: List[int], ggml_type: int) -> bytes:
    """Generate random tensor data based on shape and type"""
    n_elements = np.prod(shape)
    
    if ggml_type == GGMLType.F32:
        data = np.random.randn(n_elements).astype(np.float32)
        return data.tobytes()
    elif ggml_type == GGMLType.F16:
        data = np.random.randn(n_elements).astype(np.float16)
        return data.tobytes()
    elif ggml_type == GGMLType.I8:
        data = np.random.randint(-128, 127, size=n_elements, dtype=np.int8)
        return data.tobytes()
    elif ggml_type == GGMLType.I16:
        data = np.random.randint(-32768, 32767, size=n_elements, dtype=np.int16)
        return data.tobytes()
    elif ggml_type == GGMLType.I32:
        data = np.random.randint(-2**31, 2**31-1, size=n_elements, dtype=np.int32)
        return data.tobytes()
    else:
        # For quantized types, just generate random bytes
        # In real GGUF files these would be properly quantized
        if ggml_type in [GGMLType.Q4_0, GGMLType.Q4_1]:
            # Q4 types pack data more densely
            block_size = 32
            n_blocks = (n_elements + block_size - 1) // block_size
            if ggml_type == GGMLType.Q4_0:
                bytes_per_block = 18  # 2 + 16 bytes
            else:
                bytes_per_block = 20  # 2 + 2 + 16 bytes
            return bytes(random.getrandbits(8) for _ in range(n_blocks * bytes_per_block))
        elif ggml_type in [GGMLType.Q5_0, GGMLType.Q5_1]:
            block_size = 32
            n_blocks = (n_elements + block_size - 1) // block_size
            if ggml_type == GGMLType.Q5_0:
                bytes_per_block = 22  # More complex packing
            else:
                bytes_per_block = 24
            return bytes(random.getrandbits(8) for _ in range(n_blocks * bytes_per_block))
        elif ggml_type == GGMLType.Q8_0:
            block_size = 32
            n_blocks = (n_elements + block_size - 1) // block_size
            bytes_per_block = 34  # 2 + 32 bytes
            return bytes(random.getrandbits(8) for _ in range(n_blocks * bytes_per_block))
        else:
            # Default: treat as float32
            data = np.random.randn(n_elements).astype(np.float32)
            return data.tobytes()

def generate_random_gguf(max_size_kb: int = 100) -> bytes:
    """Generate a random GGUF file"""
    data = bytearray()
    
    # Write magic
    data.extend(GGUF_MAGIC)
    
    # Write version
    data.extend(struct.pack('<I', GGUF_VERSION))
    
    # Decide on number of tensors
    n_tensors = random.randint(1, 5)
    
    # We'll count KV pairs as we add them
    # Reserve space for tensor count and KV count (we'll update KV count later)
    data.extend(struct.pack('<q', n_tensors))
    kv_count_pos = len(data)
    data.extend(struct.pack('<q', 0))  # Placeholder for KV count
    
    # Generate and write KV pairs
    kv_pairs = []
    kv_count = 0
    
    # Add standard metadata first
    architectures = ['llama', 'mpt', 'gptneox', 'gptj', 'gpt2', 'bloom', 'falcon', 'mamba', 'rwkv']
    arch = random.choice(architectures)
    
    # Required: general.architecture
    write_string(data, "general.architecture")
    data.extend(struct.pack('<i', GGUFType.STRING))
    write_string(data, arch)
    kv_pairs.append(("general.architecture", arch))
    kv_count += 1
    
    # Required: general.alignment (even though spec says it can be omitted)
    write_string(data, "general.alignment")
    data.extend(struct.pack('<i', GGUFType.UINT32))
    data.extend(struct.pack('<I', GGUF_DEFAULT_ALIGNMENT))
    kv_pairs.append(("general.alignment", GGUF_DEFAULT_ALIGNMENT))
    kv_count += 1
    
    # Optional but common: general.name
    if random.random() < 0.8:
        model_name = f"test-model-{random.randint(1, 100)}"
        write_string(data, "general.name")
        data.extend(struct.pack('<i', GGUFType.STRING))
        write_string(data, model_name)
        kv_pairs.append(("general.name", model_name))
        kv_count += 1
    
    # Optional: general.author
    if random.random() < 0.5:
        write_string(data, "general.author")
        data.extend(struct.pack('<i', GGUFType.STRING))
        write_string(data, "GGUF Fuzzer")
        kv_pairs.append(("general.author", "GGUF Fuzzer"))
        kv_count += 1
    
    # Optional: general.version
    if random.random() < 0.5:
        write_string(data, "general.version")
        data.extend(struct.pack('<i', GGUFType.STRING))
        version = f"{random.randint(1, 3)}.{random.randint(0, 9)}"
        write_string(data, version)
        kv_pairs.append(("general.version", version))
        kv_count += 1
    
    # Optional: general.description
    if random.random() < 0.3:
        write_string(data, "general.description")
        data.extend(struct.pack('<i', GGUFType.STRING))
        desc = "A randomly generated GGUF file for fuzzing purposes"
        write_string(data, desc)
        kv_pairs.append(("general.description", desc))
        kv_count += 1
    
    # Optional: general.file_type (enum)
    if random.random() < 0.7:
        write_string(data, "general.file_type")
        data.extend(struct.pack('<i', GGUFType.UINT32))
        file_type = random.choice([0, 1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18])
        data.extend(struct.pack('<I', file_type))
        kv_pairs.append(("general.file_type", file_type))
        kv_count += 1
    
    # Architecture-specific metadata
    if arch == 'llama':
        # Add some llama-specific metadata
        write_string(data, "llama.context_length")
        data.extend(struct.pack('<i', GGUFType.UINT64))
        ctx_len = random.choice([2048, 4096, 8192, 16384, 32768])
        data.extend(struct.pack('<Q', ctx_len))
        kv_pairs.append(("llama.context_length", ctx_len))
        kv_count += 1
        
        write_string(data, "llama.embedding_length")
        data.extend(struct.pack('<i', GGUFType.UINT64))
        emb_len = random.choice([2048, 4096, 5120, 6656])
        data.extend(struct.pack('<Q', emb_len))
        kv_pairs.append(("llama.embedding_length", emb_len))
        kv_count += 1
        
        write_string(data, "llama.block_count")
        data.extend(struct.pack('<i', GGUFType.UINT64))
        block_count = random.choice([24, 32, 40, 48, 60, 80])
        data.extend(struct.pack('<Q', block_count))
        kv_pairs.append(("llama.block_count", block_count))
        kv_count += 1
        
        write_string(data, "llama.attention.head_count")
        data.extend(struct.pack('<i', GGUFType.UINT64))
        head_count = random.choice([32, 40, 52, 64])
        data.extend(struct.pack('<Q', head_count))
        kv_pairs.append(("llama.attention.head_count", head_count))
        kv_count += 1
    
    # Tokenizer metadata
    if random.random() < 0.5:
        write_string(data, "tokenizer.ggml.model")
        data.extend(struct.pack('<i', GGUFType.STRING))
        tokenizer_model = random.choice(['llama', 'replit', 'gpt2', 'rwkv'])
        write_string(data, tokenizer_model)
        kv_pairs.append(("tokenizer.ggml.model", tokenizer_model))
        kv_count += 1
        
        # Add some token IDs
        write_string(data, "tokenizer.ggml.bos_token_id")
        data.extend(struct.pack('<i', GGUFType.UINT32))
        bos_id = random.randint(1, 10)
        data.extend(struct.pack('<I', bos_id))
        kv_pairs.append(("tokenizer.ggml.bos_token_id", bos_id))
        kv_count += 1
        
        write_string(data, "tokenizer.ggml.eos_token_id")
        data.extend(struct.pack('<i', GGUFType.UINT32))
        eos_id = random.randint(1, 10)
        data.extend(struct.pack('<I', eos_id))
        kv_pairs.append(("tokenizer.ggml.eos_token_id", eos_id))
        kv_count += 1
    
    # Add remaining random KV pairs (aim for 10-25 total)
    target_kv = random.randint(10, 25)
    for _ in range(max(0, target_kv - kv_count)):
        key = random_key()
        
        # Decide if it's an array or single value
        is_array = random.random() < 0.3
        
        if is_array:
            # Array type
            write_string(data, key)
            data.extend(struct.pack('<i', GGUFType.ARRAY))
            
            # Choose array element type (exclude ARRAY and handle STRING specially)
            arr_type = random.choice([GGUFType.UINT8, GGUFType.INT32, GGUFType.FLOAT32, 
                                    GGUFType.BOOL, GGUFType.STRING])
            data.extend(struct.pack('<i', arr_type))
            
            # Array length
            arr_len = random.randint(1, 10)
            data.extend(struct.pack('<Q', arr_len))
            
            # Array data
            if arr_type == GGUFType.STRING:
                # String array - write each string separately
                for j in range(arr_len):
                    string_val = f"array_str_{j}"
                    write_string(data, string_val)
            else:
                # Numeric/bool array
                for _ in range(arr_len):
                    _, val_data = generate_random_value(arr_type)
                    data.extend(val_data)
            
            kv_pairs.append((key, f"array[{arr_len}]"))
        else:
            # Single value (exclude ARRAY type which is 9)
            value_type = random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12])
            
            write_string(data, key)
            data.extend(struct.pack('<i', value_type))
            
            if value_type == GGUFType.STRING:
                string_val = random_string()
                write_string(data, string_val)
                kv_pairs.append((key, string_val))
            else:
                val, val_data = generate_random_value(value_type)
                data.extend(val_data)
                kv_pairs.append((key, val))
    
    # Update the KV count in the header
    final_kv_count = len(kv_pairs)
    struct.pack_into('<q', data, kv_count_pos, final_kv_count)
    
    # Generate and write tensor info
    tensors = []
    tensor_data_size = 0
    
    # Use standardized tensor names from the spec
    base_tensor_names = ['token_embd', 'pos_embd', 'output_norm', 'output']
    block_tensor_names = [
        'attn_norm', 'attn_q', 'attn_k', 'attn_v', 'attn_output',
        'ffn_norm', 'ffn_up', 'ffn_gate', 'ffn_down',
        'attn_norm_2', 'attn_qkv'
    ]
    
    for i in range(n_tensors):
        # Generate standardized tensor name
        if i == 0 and random.random() < 0.8:
            # First tensor is often token embedding
            name = random.choice(base_tensor_names) + ".weight"
        elif random.random() < 0.7:
            # Block layer tensor
            block_num = random.randint(0, 31)
            tensor_type = random.choice(block_tensor_names)
            suffix = ".weight" if random.random() < 0.9 else ".bias"
            name = f"blk.{block_num}.{tensor_type}{suffix}"
        else:
            # Fallback to generic name
            name = f"tensor_{i}"
        
        write_string(data, name)
        
        # Number of dimensions (1-4)
        n_dims = random.randint(1, 4)
        data.extend(struct.pack('<I', n_dims))
        
        # Shape - keep it small
        shape = []
        remaining_size = (max_size_kb * 1024 - len(data)) // n_tensors
        max_elements = min(remaining_size // 4, 1000)  # Assume float32
        
        for dim in range(n_dims):
            if dim == 0:
                # First dimension can be larger
                dim_size = random.randint(1, min(64, max_elements))
            else:
                # Keep other dimensions smaller
                dim_size = random.randint(1, min(16, max_elements // np.prod(shape)))
            shape.append(dim_size)
            data.extend(struct.pack('<q', dim_size))
        
        # Pad remaining dimensions with 1
        for _ in range(n_dims, 4):
            data.extend(struct.pack('<q', 1))
        
        # Tensor type
        tensor_type = random.choice([GGMLType.F32, GGMLType.F16, GGMLType.I8, GGMLType.I16, GGMLType.I32])
        data.extend(struct.pack('<i', tensor_type))
        
        # Offset (will be calculated later)
        offset_pos = len(data)
        data.extend(struct.pack('<Q', 0))  # Placeholder
        
        tensors.append({
            'name': name,
            'shape': shape,
            'type': tensor_type,
            'offset_pos': offset_pos
        })
    
    # Align to GGUF_DEFAULT_ALIGNMENT before data section
    write_padding(data, GGUF_DEFAULT_ALIGNMENT)
    data_section_start = len(data)
    
    # Write tensor data
    for i, tensor in enumerate(tensors):
        # Calculate and update offset
        offset = len(data) - data_section_start
        struct.pack_into('<Q', data, tensor['offset_pos'], offset)
        
        # Generate and write tensor data
        tensor_data = generate_tensor_data(tensor['shape'], tensor['type'])
        data.extend(tensor_data)
        
        # Align each tensor
        write_padding(data, GGUF_DEFAULT_ALIGNMENT)
    
    return bytes(data)

def main():
    parser = argparse.ArgumentParser(description='Generate random GGUF files for fuzzing')
    parser.add_argument('output', help='Output GGUF file path')
    parser.add_argument('--max-size', type=int, default=100, 
                        help='Maximum file size in KB (default: 100)')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    # Generate GGUF file
    gguf_data = generate_random_gguf(args.max_size)
    
    # Write to file
    with open(args.output, 'wb') as f:
        f.write(gguf_data)
    
    print(f"Generated GGUF file: {args.output} ({len(gguf_data)} bytes)")

if __name__ == '__main__':
    main()

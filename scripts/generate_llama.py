#!/usr/bin/env python3
"""
HuggingFace Model Generator for Testing
Creates small, compliant models for common llama.cpp architectures in HuggingFace format

Requirements:
- pip install transformers
- pip install sentencepiece
"""

import os
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import argparse

try:
    from transformers import (
        LlamaConfig, LlamaForCausalLM,
        MistralConfig, MistralForCausalLM,
        PhiConfig, PhiForCausalLM,
        GemmaConfig, GemmaForCausalLM,
        AutoTokenizer, LlamaTokenizer
    )
except ImportError:
    print("Please install transformers: pip install transformers")
    exit(1)

try:
    import sentencepiece as spm
except ImportError:
    print("Please install sentencepiece: pip install sentencepiece")
    exit(1)

@dataclass
class ModelSpec:
    """Specification for a small model architecture"""
    name: str
    config_class: Any
    model_class: Any
    vocab_size: int
    hidden_size: int
    intermediate_size: int
    num_hidden_layers: int
    num_attention_heads: int
    num_key_value_heads: Optional[int] = None
    max_position_embeddings: int = 512
    rms_norm_eps: float = 1e-6
    rope_theta: float = 10000.0
    extra_config: Dict[str, Any] = None

class TinyModelGenerator:
    """Generator for small HuggingFace models compatible with llama.cpp"""

    def __init__(self, output_dir: str = "tiny_models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Define small model specifications
        self.model_specs = {
            "llama_tiny": ModelSpec(
                name="llama_tiny",
                config_class=LlamaConfig,
                model_class=LlamaForCausalLM,
                vocab_size=64,  # Increased for better tokenizer stability
                hidden_size=256,
                intermediate_size=512,
                num_hidden_layers=4,
                num_attention_heads=4,
                num_key_value_heads=4,
                extra_config={
                    "torch_dtype": "float32",
                    "use_cache": True,
                    "pad_token_id": 0,
                    "bos_token_id": 1,
                    "eos_token_id": 2,
                    "tie_word_embeddings": False,
                }
            ),
            "llama_micro": ModelSpec(
                name="llama_micro",
                config_class=LlamaConfig,
                model_class=LlamaForCausalLM,
                vocab_size=64,  # Increased from 500
                hidden_size=128,
                intermediate_size=256,
                num_hidden_layers=2,
                num_attention_heads=2,
                num_key_value_heads=2,
                max_position_embeddings=256,
                extra_config={
                    "torch_dtype": "float32",
                    "use_cache": True,
                    "pad_token_id": 0,
                    "bos_token_id": 1,
                    "eos_token_id": 2,
                    "tie_word_embeddings": False,
                }
            ),
            "mistral_tiny": ModelSpec(
                name="mistral_tiny",
                config_class=MistralConfig,
                model_class=MistralForCausalLM,
                vocab_size=64,  # Increased for better tokenizer stability
                hidden_size=256,
                intermediate_size=512,
                num_hidden_layers=4,
                num_attention_heads=4,
                num_key_value_heads=2,  # GQA
                extra_config={
                    "torch_dtype": "float32",
                    "use_cache": True,
                    "pad_token_id": 0,
                    "bos_token_id": 1,
                    "eos_token_id": 2,
                    "sliding_window": 256,
                    "tie_word_embeddings": False,
                }
            ),
            "phi_tiny": ModelSpec(
                name="phi_tiny",
                config_class=PhiConfig,
                model_class=PhiForCausalLM,
                vocab_size=64,  # Increased for better tokenizer stability
                hidden_size=256,
                intermediate_size=512,
                num_hidden_layers=4,
                num_attention_heads=4,
                extra_config={
                    "torch_dtype": "float32",
                    "use_cache": True,
                    "pad_token_id": 0,
                    "bos_token_id": 1,
                    "eos_token_id": 2,
                    "tie_word_embeddings": False,
                }
            ),
            "gemma_tiny": ModelSpec(
                name="gemma_tiny",
                config_class=GemmaConfig,
                model_class=GemmaForCausalLM,
                vocab_size=64,  # Increased for better tokenizer stability
                hidden_size=256,
                intermediate_size=512,
                num_hidden_layers=4,
                num_attention_heads=4,
                num_key_value_heads=4,
                extra_config={
                    "torch_dtype": "float32",
                    "use_cache": True,
                    "pad_token_id": 0,
                    "bos_token_id": 1,
                    "eos_token_id": 2,
                    "hidden_activation": "gelu_pytorch_tanh",
                    "tie_word_embeddings": False,
                }
            )
        }

    def create_model(self, spec: ModelSpec) -> torch.nn.Module:
        """Create a model with random weights based on specification"""
        config_kwargs = {
            "vocab_size": spec.vocab_size,
            "hidden_size": spec.hidden_size,
            "intermediate_size": spec.intermediate_size,
            "num_hidden_layers": spec.num_hidden_layers,
            "num_attention_heads": spec.num_attention_heads,
            "max_position_embeddings": spec.max_position_embeddings,
            "rms_norm_eps": spec.rms_norm_eps,
            "rope_theta": spec.rope_theta,
        }

        # Add num_key_value_heads if specified
        if spec.num_key_value_heads is not None:
            config_kwargs["num_key_value_heads"] = spec.num_key_value_heads

        # Add extra config
        if spec.extra_config:
            config_kwargs.update(spec.extra_config)

        try:
            config = spec.config_class(**config_kwargs)
            model = spec.model_class(config)

            # Initialize with random weights
            model.apply(self._init_weights)

            print(f"Created {spec.name} model with {self.count_parameters(model):,} parameters")
            return model, config

        except Exception as e:
            print(f"Error creating {spec.name}: {e}")
            return None, None

    def _init_weights(self, module):
        """Initialize model weights randomly"""
        if isinstance(module, torch.nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, torch.nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def count_parameters(self, model):
        """Count total parameters in model"""
        return sum(p.numel() for p in model.parameters())

    def create_tokenizer_files(self, spec: ModelSpec, model_dir: Path):
        """Create a SentencePiece tokenizer that convert_hf_to_gguf.py will recognize"""

        # Create a simple vocabulary file for SentencePiece training
        vocab_file = model_dir / "temp_vocab.txt"
        with open(vocab_file, 'w', encoding='utf-8') as f:
            # Add some basic text to train on with explicit newlines
            basic_text = []
            basic_text.append("Hello world! This is a test.\n")
            basic_text.append("The quick brown fox jumps over the lazy dog.\n")
            basic_text.append("SentencePiece tokenizer training data.\n")
            basic_text.append("Creating a vocabulary for language model.\n")
            basic_text.append("New line characters are important.\n")
            basic_text.append("Multiple sentences on separate lines.\n")

            # Add some variety with numbers and punctuation
            for i in range(200):
                basic_text.append(f"This is sentence number {i}.\n")
                basic_text.append(f"Token {i} with various punctuation: !@#$%^&*().\n")
                basic_text.append(f"Line {i} with newline handling.\n")

            # Add alphabet and common words to ensure good coverage
            alphabet_text = []
            alphabet_text.append("abcdefghijklmnopqrstuvwxyz\n")
            alphabet_text.append("ABCDEFGHIJKLMNOPQRSTUVWXYZ\n")
            alphabet_text.append("0123456789\n")
            alphabet_text.append("the and or not but if then else\n")
            alphabet_text.append("a an the is are was were be been\n")

            # Write all text
            for text in basic_text + alphabet_text:
                f.write(text)

        # Train a SentencePiece model with better configuration
        tokenizer_model_path = model_dir / "tokenizer.model"

        # Use a larger minimum vocab size to avoid issues
        effective_vocab_size = spec.vocab_size

        spm.SentencePieceTrainer.train(
            input=str(vocab_file),
            model_prefix=str(model_dir / "tokenizer"),
            vocab_size=effective_vocab_size,
            model_type='unigram',  # Use unigram model type
            # Fix token ID assignments - make them consistent
            pad_id=0,    # <pad>
            bos_id=1,    # <s>
            eos_id=2,    # </s>
            unk_id=3,    # <unk>
            pad_piece='<pad>',
            bos_piece='<s>',
            eos_piece='</s>',
            unk_piece='<unk>',
            # Add important tokens that llama.cpp expects
            user_defined_symbols=['<mask>', '\n', '\t', ' '],
            character_coverage=1.0,  # Use full coverage for small vocab
            max_sentence_length=8192,
            shuffle_input_sentence=True,
            train_extremely_large_corpus=False,
            split_by_whitespace=True,
            split_by_number=True,
            split_by_unicode_script=True,
            allow_whitespace_only_pieces=True,
            remove_extra_whitespaces=False,
            # Ensure we capture newlines and whitespace properly
            treat_whitespace_as_suffix=False,
            normalization_rule_name='nmt_nfkc_cf',
        )

        # Clean up temp file
        vocab_file.unlink()

        # Create tokenizer_config.json with corrected token assignments
        tokenizer_config = {
            "add_bos_token": True,
            "add_eos_token": False,
            "bos_token": "<s>",
            "eos_token": "</s>",
            "pad_token": "<pad>",
            "unk_token": "<unk>",
            "clean_up_tokenization_spaces": False,
            "model_max_length": spec.max_position_embeddings,
            "tokenizer_class": "LlamaTokenizer",
            "legacy": False,
            # Add these to help with token ID mapping
            "bos_token_id": 1,
            "eos_token_id": 2,
            "pad_token_id": 0,
            "unk_token_id": 3,
        }

        with open(model_dir / "tokenizer_config.json", 'w') as f:
            json.dump(tokenizer_config, f, indent=2)

    def generate_all_models(self, models: list = None):
        """Generate all specified models in HuggingFace format"""
        if models is None:
            models = list(self.model_specs.keys())

        generated_models = []

        for model_name in models:
            if model_name not in self.model_specs:
                print(f"Unknown model: {model_name}")
                continue

            print(f"\nGenerating {model_name}...")
            spec = self.model_specs[model_name]

            # Create model
            model, config = self.create_model(spec)
            if model is None:
                continue

            # Create output directory for this model
            model_dir = self.output_dir / model_name
            model_dir.mkdir(exist_ok=True)

            # Save model in HuggingFace format
            model.save_pretrained(model_dir)
            config.save_pretrained(model_dir)

            # Create tokenizer files
            self.create_tokenizer_files(spec, model_dir)

            # Create a generation config
            generation_config = {
                "bos_token_id": 1,
                "eos_token_id": 2,
                "pad_token_id": 0,
                "max_length": spec.max_position_embeddings,
                "do_sample": True,
                "temperature": 0.7,
                "top_p": 0.9
            }

            with open(model_dir / "generation_config.json", 'w') as f:
                json.dump(generation_config, f, indent=2)

            print(f"Model {model_name} saved to {model_dir}")
            generated_models.append(str(model_dir.absolute()))

        return generated_models

def main():
    parser = argparse.ArgumentParser(description="Generate small HuggingFace models for testing")
    parser.add_argument("--output-dir", default="tiny_models", help="Output directory")
    parser.add_argument("--models", nargs="+", help="Specific models to generate",
                       choices=["llama_tiny", "llama_micro", "mistral_tiny", "phi_tiny", "gemma_tiny"])

    args = parser.parse_args()

    generator = TinyModelGenerator(args.output_dir)
    generated_models = generator.generate_all_models(args.models)

    print(f"\nAll models generated in {args.output_dir}/")
    print("Each model directory contains:")
    print("  - config.json (model configuration)")
    print("  - pytorch_model.bin (model weights)")
    print("  - tokenizer.model (SentencePiece tokenizer)")
    print("  - tokenizer_config.json (tokenizer config)")
    print("  - generation_config.json (generation config)")

    print("\n" + "="*60)
    print("CONVERSION COMMANDS:")
    print("="*60)
    print("To convert these models to GGUF format, run:")
    print()

    for model_path in generated_models:
        model_name = Path(model_path).name
        print(f"# Convert {model_name}")
        print(f"python convert_hf_to_gguf.py {model_path} --outtype f16")
        print()

if __name__ == "__main__":
    main()
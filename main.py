#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path
from multiprocessing import Pool
from functools import partial

VARIANTS = {
    "nosan",
    "asan",
    "ubsan",
    "msan",
    "tsan",
    "lsan",
    "cfisan",
    "laf",
    "redqueen"
}

def build_variant(path: str, variant: str, extra_flags: dict):
    assert variant in VARIANTS

    build_dir = "build_" + variant
    build_path = Path(path) / build_dir
    build_path.parent.mkdir(exist_ok=True)

    if build_path.exists():
        subprocess.run(["rm", "-rf", str(build_path)], check=True)
    build_path.mkdir()

    sanitize_flags = {
        "nosan": "",
        "asan": "-fsanitize=address -fsanitize-address-use-after-return=always -fsanitize-address-use-after-scope",
        "ubsan": "-fsanitize=undefined",
        "msan": "-fsanitize=memory",
        "tsan": "-fsanitize=thread",
        "lsan": "-fsanitize=leak",
        "cfisan": "-fsanitize=cfi ",
        "laf": "",
        "redqueen": "",
    }

    sanitize_string = sanitize_flags[variant]

    cmake_flags = {
        "CMAKE_C_COMPILER":f"afl-clang-lto",
        "CMAKE_CXX_COMPILER":f"afl-clang-lto++",
        "BUILD_SHARED_LIBS":f"OFF",
        "CMAKE_EXE_LINKER_FLAGS":f"-fuse-ld=ld.lld -flto=full -fno-sanitize-recover=all -fno-omit-frame-pointer {sanitize_string}",
        "CMAKE_SHARED_LINKER_FLAGS":f"-fuse-ld=ld.lld -flto=full -fno-sanitize-recover=all -fno-omit-frame-pointer {sanitize_string}",
        "CMAKE_C_FLAGS":f"-O3 -march=native -funroll-loops -fvisibility=hidden -g3 -flto=full -fno-sanitize-recover=all -fno-omit-frame-pointer {sanitize_string}",
        "CMAKE_CXX_FLAGS":f"-O3 -march=native -funroll-loops -fvisibility=hidden -g3 -flto=full -fno-sanitize-recover=all -fno-omit-frame-pointer {sanitize_string}",
    }

    env_vars = {
        "nosan": {},
        "asan": {"AFL_USE_ASAN": "1"},
        "ubsan": {"AFL_USE_UBSAN": "1"},
        "msan": {"AFL_USE_MSAN": "1"},
        "tsan": {"AFL_USE_TSAN": "1"},
        "lsan": {"AFL_USE_LSAN": "1"},
        "cfisan": {"AFL_USE_CFISAN": "1"},
        "laf": {"AFL_LLVM_LAF_ALL": "1"},
        "redqueen": {"AFL_LLVM_CMPLOG": "1"},
    }[variant]

    args = ["cmake",".."]

    for k,v in cmake_flags.items():
        args.append(f"-D{k}={v}")

    for k,v in extra_flags.items():
        if k in cmake_flags:

            args.append(f"-D{k}={cmake_flags.get(k, "") + v}")
        else:
            args.append(f"-D{k}={v}")


    env = os.environ.copy()
    env.update(env_vars)

    subprocess.run(args, env=env, check=True, cwd=build_path)
    cpu_count = str(os.cpu_count())
    subprocess.run(["make", f"-j{cpu_count}"], env=env, check=True, cwd=build_path)




def build_target(path, variants, flags):
    build_configs = [(path, v, flags) for v in variants]

    with Pool() as pool:
        pool.starmap(build_variant, build_configs)

def ggml():
    extra_flags = {
        "GGML_BACKEND_DL":"OFF",
        "GGML_STATIC":"ON",
        "GGML_NATIVE":"ON",
        "GGML_LTO":"OFF",
        "GGML_BUILD_EXAMPLES":"OFF",
        "GGML_BUILD_TESTS":"ON",
    }
    build_target("targets/ggml", VARIANTS, extra_flags)


def llama_cpp():
    extra_flags = {
        "GGML_BACKEND_DL":"OFF",
        "GGML_STATIC":"ON",
        "GGML_NATIVE":"ON",
        "GGML_LTO":"OFF",
        "GGML_BUILD_EXAMPLES":"OFF",
        "GGML_BUILD_TESTS":"OFF",
        "LLAMA_ALL_WARNINGS":"OFF",
        "LLAMA_STATIC":"ON",
        "LLAMA_NATIVE":"ON",
        "LLAMA_LTO":"OFF",
        "LLAMA_BUILD_EXAMPLES":"OFF",
        "LLAMA_BUILD_TESTS":"ON"
    }
    build_target("targets/llama.cpp", VARIANTS, extra_flags)



if __name__ == "__main__":
    ggml()
    llama_cpp()

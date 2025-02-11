#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path


def build_variant(build_dir: str, env_vars: dict = None, extra_flags: list = None):
    build_path = Path("targets/llama.cpp") / build_dir
    build_path.parent.mkdir(exist_ok=True)

    if build_path.exists():
        subprocess.run(["rm", "-rf", str(build_path)], check=True)
    build_path.mkdir()

    cmake_flags = [
        "-DCMAKE_C_COMPILER=afl-clang-lto",
        "-DCMAKE_CXX_COMPILER=afl-clang-lto++",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DCMAKE_EXE_LINKER_FLAGS=-fuse-ld=ld.lld -flto=full",
        "-DCMAKE_SHARED_LINKER_FLAGS=-fuse-ld=ld.lld -flto=full",
        "-DCMAKE_C_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fno-finite-math-only -fvisibility=hidden",
        "-DCMAKE_CXX_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fno-finite-math-only -fvisibility=hidden",
        "-DGGML_BACKEND_DL=OFF", "-DGGML_STATIC=ON", "-DGGML_NATIVE=ON",
        "-DGGML_LTO=OFF", "-DGGML_BUILD_EXAMPLES=OFF", "-DGGML_BUILD_TESTS=OFF",
        "-DLLAMA_ALL_WARNINGS=OFF", "-DLLAMA_STATIC=ON", "-DLLAMA_NATIVE=ON",
        "-DLLAMA_LTO=OFF", "-DLLAMA_BUILD_EXAMPLES=OFF", "-DLLAMA_BUILD_TESTS=ON"
    ]

    if extra_flags:
        cmake_flags.extend(extra_flags)

    base_dir = Path(__file__).parent
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    subprocess.run(["cmake", ".."] + cmake_flags, env=env, check=True, cwd=build_path)
    subprocess.run(["make", "-j16"], env=env, check=True, cwd=build_path)


def main():
    # Standard build
    build_variant("build")

    # ASAN build
    build_variant("build_asan",
                  {"AFL_USE_ASAN": "1"},
                  ["-DGGML_SANITIZE_ADDRESS=ON", "-DLLAMA_SANITIZE_ADDRESS=ON"])

    # UBSAN build
    build_variant("build_ubsan",
                  {"AFL_USE_UBSAN": "1"},
                  ["-DGGML_SANITIZE_UNDEFINED=ON", "-DLLAMA_SANITIZE_UNDEFINED=ON"])

    # MSAN build
    build_variant("build_msan",
                  {"AFL_USE_MSAN": "1"},
                  [
                      "-DCMAKE_C_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fvisibility=hidden -fsanitize=memory",
                      "-DCMAKE_CXX_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fvisibility=hidden -fsanitize=memory"])

    # TSAN build
    build_variant("build_tsan",
                  {"AFL_USE_TSAN": "1"},
                  [
                      "-DCMAKE_C_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fvisibility=hidden -fsanitize=thread",
                      "-DCMAKE_CXX_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fvisibility=hidden -fsanitize=thread"])

    # LSAN build
    build_variant("build_lsan",
                  {"AFL_USE_LSAN": "1"},
                  [
                      "-DCMAKE_C_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fvisibility=hidden -fsanitize=leak",
                      "-DCMAKE_CXX_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fvisibility=hidden -fsanitize=leak"])

    # CFI build
    build_variant("build_cfisan",
                  {"AFL_USE_CFISAN": "1"},
                  [
                      "-DCMAKE_C_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fvisibility=hidden -fsanitize=cfi -fsanitize-cfi-cross-dso -fsanitize=function",
                      "-DCMAKE_CXX_FLAGS=-Ofast -march=native -ffast-math -funroll-loops -fvisibility=hidden -fsanitize=cfi -fsanitize-cfi-cross-dso -fsanitize=function"])

    # LAF build
    build_variant("build_laf", {"AFL_LLVM_LAF_ALL": "1"})

    # RedQueen build
    build_variant("build_redqueen", {"AFL_LLVM_CMPLOG": "1"})


if __name__ == "__main__":
    main()
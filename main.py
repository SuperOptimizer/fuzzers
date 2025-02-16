#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path
from multiprocessing import Pool
from functools import partial
import random

VARIANTS = {
    "nosan",
    "asan",
    "msan",
    "tsan",
    "cfisan",
    "laf",
    "redqueen",
    "sand_asan",
    "sand_msan",
    "sand_tsan",
    "sand_cfisan"
}

def build_variant(path: str, variant: str, extra_flags: dict):
    assert variant in VARIANTS

    build_dir = "build_" + variant
    build_path = Path(path) / build_dir
    build_path.parent.mkdir(exist_ok=True)

    sanitize_flags = {
        "nosan": "",
        "asan": "-fsanitize=address,undefined -fsanitize-address-use-after-return=always -fsanitize-address-use-after-scope -fsanitize=leak ",
        "msan": "-fsanitize=memory",
        "tsan": "-fsanitize=thread",
        "cfisan": "-fsanitize=cfi",
        "laf": "",
        "redqueen": "",
        "sand_asan": " -fsanitize=address,undefined -fsanitize-address-use-after-return=always -fsanitize-address-use-after-scope -fsanitize=leak ",
        "sand_msan": "-fsanitize=memory",
        "sand_tsan": "-fsanitize=thread",
        "sand_cfisan": "-fsanitize=cfi",
    }

    sanitize_string = sanitize_flags[variant]

    ccflags = f"-O3 -march=native  -fvisibility=hidden -g3 -flto=full -fno-sanitize-recover=all -fno-omit-frame-pointer {sanitize_string}  -ggdb  -rdynamic -Weverything -Wno-error -Wno-unsafe-buffer-usage -ffunction-sections -fdata-sections -Wl,--gc-sections -Wno-unused-function -Wno-c++98-compat-pedantic -Wno-unused-macros -Wno-padded"
    linkflags = f"-fuse-ld=ld.lld -flto=full -fno-sanitize-recover=all -fno-omit-frame-pointer {sanitize_string} -g3 -ggdb  -rdynamic -ffunction-sections -fdata-sections -Wl,--gc-sections "

    cmake_flags = {
        "CMAKE_C_COMPILER": f"afl-clang-lto",
        "CMAKE_CXX_COMPILER": f"afl-clang-lto++",
        "BUILD_SHARED_LIBS": f"OFF",
        "CMAKE_EXE_LINKER_FLAGS": linkflags,
        "CMAKE_SHARED_LINKER_FLAGS": linkflags,
        "CMAKE_C_FLAGS": ccflags,
        "CMAKE_CXX_FLAGS": ccflags,
    }

    env_vars = {
        "nosan": {},
        "asan": {"AFL_USE_ASAN": "1", "AFL_USE_UBSAN": "1","AFL_USE_LSAN": "1"},
        "msan": {"AFL_USE_MSAN": "1"},
        "tsan": {"AFL_USE_TSAN": "1"},
        "cfisan": {"AFL_USE_CFISAN": "1"},
        "laf": {"AFL_LLVM_LAF_ALL": "1"},
        "redqueen": {"AFL_LLVM_CMPLOG": "1"},

        "sand_asan": {"AFL_USE_ASAN": "1", "AFL_USE_UBSAN": "1","AFL_SAN_NO_INST":"1","AFL_USE_LSAN": "1"},
        "sand_msan": {"AFL_USE_MSAN": "1","AFL_SAN_NO_INST":"1"},
        "sand_tsan": {"AFL_USE_TSAN": "1","AFL_SAN_NO_INST":"1"},
        "sand_cfisan": {"AFL_USE_CFISAN": "1","AFL_SAN_NO_INST":"1"},


    }[variant]

    args = ["cmake", "..", "-G", "Ninja"]

    for k, v in cmake_flags.items():
        args.append(f"-D{k}={v}")

    for k, v in extra_flags.items():
        if k in cmake_flags:

            args.append(f"-D{k}={cmake_flags.get(k, "") + v}")
        else:
            args.append(f"-D{k}={v}")

    env = os.environ.copy()
    env.update(env_vars)

    if "incremental" not in sys.argv:
        if build_path.exists():
            subprocess.run(["rm", "-rf", str(build_path)], check=True)
        build_path.mkdir()
        subprocess.run(args, env=env, check=True, cwd=build_path)

    subprocess.run(["ninja"], env=env, check=True, cwd=build_path)




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
        "LLAMA_BUILD_EXAMPLES":"ON",
        "LLAMA_BUILD_TESTS":"ON"
    }
    build_target("targets/llama.cpp", VARIANTS, extra_flags)

def gen_commands(target, corpus, out, executable):

    fmt_str = "{env_args} nohup afl-fuzz -t {timeout} {mem_limit_str} {M_or_S} {variant} -i {corpus} -o {out} {sand_str} {redqueen_str} {afl_args} {executable} @@ &> /dev/null &"

    cmds = [
        fmt_str.format(env_args="", timeout=100, M_or_S="-M", mem_limit_str="", variant="main", redqueen_str="", sand_str="", afl_args="", corpus=corpus, out=out, executable=f"./targets/{target}/build_nosan/{executable}")
    ]

    for variant in VARIANTS:
        if "sand" in variant:
            executable_path = f"./targets/{target}/build_nosan/{executable}"
            sand_str = f" -w ./targets/{target}/build_sand_asan/{executable} -w ./targets/{target}/build_sand_tsan/{executable} -w ./targets/{target}/build_sand_asan/{executable} -w ./targets/{target}/build_sand_cfisan/{executable} "
        else:
            executable_path = f"./targets/{target}/build_{variant}/{executable}"
            sand_str = ""

        redqueen_str = f"-c ./targets/{target}/build_redqueen/{executable}" if "redqueen" == variant else ""
        afl_args = ""
        env_args = ""
        if random.randint(1,10) == 1:
            afl_args += " -L 0 "
        if random.randint(1,10) == 1:
            afl_args += " -Z "
        if random.randint(1,3) == 1:
            afl_args += " -P explore"
        elif random.randint(1,2) == 1:
            afl_args +=  " -P exploit "


        if random.randint(1, 8) == 1:
            afl_args += " -p explore "
        elif random.randint(1, 7) == 1:
            afl_args += " -p fast "
        elif random.randint(1, 6) == 1:
            afl_args += " -p exploit "
        elif random.randint(1, 5) == 1:
            afl_args += " -p seek "
        elif random.randint(1, 4) == 1:
            afl_args += " -p rare "
        elif random.randint(1, 3) == 1:
            afl_args += " -p mmopt "
        elif random.randint(1, 2) == 1:
            afl_args += " -p coe "

        if random.randint(1,2) == 1:
            env_args += "AFL_DISABLE_TRIM=1 "
        if random.randint(1,2) == 1:
            env_args += "AFL_KEEP_TIMEOUTS=1 "
        if random.randint(1,2) == 1:
            env_args += "AFL_EXPAND_HAVOC_NOW=1 "

        if variant in ['nosan','redqueen','laf']:
            mem_limit_str = f"-m {random.randint(64,1024)}"
        else:
            mem_limit_str = ""

        if variant == "redqueen":
            if random.randint(1,2):
                afl_args += " -l 2 "
            elif random.randint(1,2):
                afl_args += " -l 2AT "
            elif random.randint(1,2):
                afl_args += " -l 3 "

        cmds.append(fmt_str.format(env_args=env_args, timeout=random.randint(5,500), mem_limit_str=mem_limit_str, M_or_S="-S", variant=variant, redqueen_str=redqueen_str, sand_str=sand_str, afl_args=afl_args,  corpus=corpus, out=out, executable=executable_path))

    return "\n".join(cmds)

import sys

'''
export TMPDIR=/tmp
export AFL_TMPDIR=/tmp
export AFL_AUTORESUME=1
export AFL_QUIET=1
export AFL_IGNORE_SEED_PROBLEMS=1
export AFL_CRASH_EXITCODE='-1'
export AFL_CYCLE_SCHEDULES=1
export AFL_IMPORT_FIRST=1
export AFL_FINAL_SYNC=1
export AFL_INPUT_LEN_MIN=1
export AFL_INPUT_LEN_MAX=10000000
export AFL_NO_AFFINITY=1
export AFL_SHUFFLE_QUEUE=1
export AFL_SKIP_CPUFREQ=1
export AFL_SYNC_TIME=1
export AFL_TESTCACHE_SIZE=1000
export AFL_CMPLOG_ONLY_NEW=1
export AFL_FAST_CAL=1
'''

if __name__ == "__main__":
    print(sys.argv)
    if "ggml" in sys.argv:
        ggml()
        print(gen_commands("ggml","corpus/gguf","out","bin/test-fuzz"))
    if "llama.cpp" in sys.argv:
        llama_cpp()

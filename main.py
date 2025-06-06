#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path
from multiprocessing import Pool
from functools import partial
import random
import sys
import multiprocessing
import string



if "nofuzz" in sys.argv:
    VARIANTS = {"nosan"}
else:
    VARIANTS = sorted([
        "noopt",
        "nosan",
        "asan",
        #"msan",
        #"tsan",
        "ubsan",
        #"leak",
        #"cfisan",
        "laf",
        "redqueen",
        "sand_asan",
        "sand_msan",
        #"sand_tsan",
        "sand_ubsan",
        #"sand_cfisan"
    ])

def build_variant(path: str, variant: str, extra_flags: dict):
    assert variant in VARIANTS

    build_dir = "build_" + variant
    build_path = Path(path) / build_dir
    build_path.parent.mkdir(exist_ok=True)

    sanitize_flags = {
        "noopt": "",
        "nosan": "",
        "asan": "-fsanitize=address -fsanitize-address-use-after-return=always -fsanitize-address-use-after-scope  ",
        "msan": "-fsanitize=memory",
        "tsan": "-fsanitize=thread",
        "cfisan": "-fsanitize=cfi",
        "ubsan": "-fsanitize=undefined -fno-sanitize-recover=undefined",
        "leak": "-fsanitize=leak",
        "laf": "",
        "redqueen": "",
        "sand_asan": " -fsanitize=address -fsanitize-address-use-after-return=always -fsanitize-address-use-after-scope  ",
        "sand_msan": "-fsanitize=memory",
        "sand_tsan": "-fsanitize=thread",
        "sand_cfisan": "-fsanitize=cfi",
        "sand_ubsan": "-fsanitize=undefined",
        "sand_leak": "-fsanitize=leak",
    }
    sanitize_string = sanitize_flags[variant]

    ccflags =   f" -w -g3 -march=native -stdlib=libc++ --rtlib=compiler-rt -unwind=libunwind -fno-omit-frame-pointer "
    linkflags = f"    -g3 -fuse-ld=lld  -stdlib=libc++ --rtlib=compiler-rt -unwind=libunwind -fno-omit-frame-pointer -Wl,--threads=32 "

    if "nosanitize" not in sys.argv:
        ccflags +=   f" -fno-sanitize-recover=all {sanitize_string} "
        linkflags += f" -fno-sanitize-recover=all {sanitize_string} "

    if "nolto" in sys.argv or variant == "noopt":
        cc = "afl-clang-fast"
        cxx = "afl-clang-fast++"
    else:
        cc = "afl-clang-lto"
        cxx = "afl-clang-lto++"
        ccflags +=   " -flto=full -O3 "
        linkflags += " -flto=full -Wl,-O3 "

    if "nofuzz" in sys.argv:
        cc = "clang"
        cxx = "clang++"
        ccflags += f" -DNOFUZZ "
        if "profile" in sys.argv:
            ccflags += ' -pg '
            linkflags += ' -pg '

    if "variant" == "noopt":
        ccflags += " -O0 "

    ccflags += f" -DFUZZING_UNIQUE=\"{''.join(random.choice(string.ascii_letters) for _ in range(32))}\" "
    if "unstable" in sys.argv:
        ccflags += " -DFUZZING_UNSTABLE "
    else:
        ccflags += " -UFUZZING_UNSTABLE "


    cmake_flags = {
        "CMAKE_C_COMPILER": cc,
        "CMAKE_CXX_COMPILER": cxx,
        "BUILD_SHARED_LIBS": f"OFF",
        "CMAKE_EXE_LINKER_FLAGS": linkflags,
        "CMAKE_SHARED_LINKER_FLAGS": linkflags,
        "CMAKE_C_FLAGS": ccflags,
        "CMAKE_CXX_FLAGS": ccflags,
    }

    env_vars = {
        "nosan": {},
        "noopt": {},
        "asan": {"AFL_USE_ASAN": "1"},
        "msan": {"AFL_USE_MSAN": "1"},
        "tsan": {"AFL_USE_TSAN": "1"},
        "cfisan": {"AFL_USE_CFISAN": "1"},
        "ubsan": {"AFL_USE_UBSAN":"1", "AFL_UBSAN_VERBOSE":"1"},
        "leak": {"AFL_USE_LEAK":"1"},
        "laf": {"AFL_LLVM_LAF_ALL": "1"},
        "redqueen": {"AFL_LLVM_CMPLOG": "1"},


        "sand_asan": {"AFL_USE_ASAN": "1", "AFL_SAN_NO_INST":"1"},
        "sand_msan": {"AFL_USE_MSAN": "1","AFL_SAN_NO_INST":"1"},
        "sand_tsan": {"AFL_USE_TSAN": "1","AFL_SAN_NO_INST":"1"},
        "sand_cfisan": {"AFL_USE_CFISAN": "1","AFL_SAN_NO_INST":"1"},
        "sand_ubsan": {"AFL_USE_UBSAN": "1","AFL_SAN_NO_INST":"1"},
        "sand_leak": {"AFL_USE_LSAN": "1","AFL_SAN_NO_INST":"1"},


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

    if build_path.exists():
        subprocess.run(["rm", "-rf", str(build_path)], check=True)
    build_path.mkdir()
    subprocess.run(args, env=env, check=True, cwd=build_path)

    subprocess.run(["ninja","-k","0"], env=env, check=True, cwd=build_path)




def build_target(path, variants, flags):
    build_configs = [(path, v, flags) for v in variants]

    nprocs=1
    if "nprocs=16" in sys.argv:
        nprocs = 16
    elif "nprocs=8" in sys.argv:
        nprocs = 5

    with Pool(nprocs) as pool:
        pool.starmap(build_variant, build_configs)

def ggml():
    extra_flags = {
        "GGML_BACKEND_DL":"OFF",
        "GGML_STATIC":"ON",
        "GGML_NATIVE":"ON",
        "GGML_LTO":"OFF",
        "GGML_BUILD_EXAMPLES":"ON" if "nofuzz" in sys.argv else "OFF",
        "GGML_BUILD_TESTS":"ON",
        "GGML_CPU_AARCH64":"OFF",
        "GGML_AVX":"ON",
        "GGML_AVX2":"ON",
        "GGML_FMA":"OFF",
        "GGML_F16C":"OFF",
        "GGML_LASX":"OFF",
        "GGML_LSX":"OFF",
        "GGML_RVV":"OFF",
        "GGML_CPU_ALL_VARIANTS":"OFF",
        "GGML_ACCELERATE":"OFF",
        "GGML_BLAS":"OFF",
        "GGML_LLAMAFILE":"OFF",
        "GGML_OPENMP":"OFF",
        "GGML_OPENCL_EMBED_KERNELS":"OFF",

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
        "LLAMA_BUILD_EXAMPLES":"OFF",
        "LLAMA_BUILD_TESTS":"ON",
        "GGML_CPU_AARCH64":"OFF",
        "GGML_AVX":"ON",
        "GGML_AVX2":"ON",
        "GGML_FMA":"OFF",
        "GGML_F16C":"OFF",
        "GGML_LASX":"OFF",
        "GGML_LSX":"OFF",
        "GGML_RVV":"OFF",
        "GGML_CPU_ALL_VARIANTS":"OFF",
        "GGML_ACCELERATE":"OFF",
        "GGML_BLAS":"OFF",
        "GGML_LLAMAFILE":"OFF",
        "GGML_OPENMP":"OFF",
        "GGML_OPENCL_EMBED_KERNELS":"OFF",
        "LLAMA_CURL":"OFF",
        "FUZZ":"ON" if "nofuzz" not in sys.argv else "OFF",
    }
    build_target("targets/llama.cpp", VARIANTS, extra_flags)

def gen_commands(target, corpus, out, executable):
    session_name = "afl-fuzzing"

    # AFL command format (without nohup/backgrounding)
    fmt_str = "{env_args} afl-fuzz -t {timeout} {mem_limit_str} {M_or_S} {variant} -i {corpus} -o {out} {sand_str} {redqueen_str} {afl_args} {executable} @@"

    cmds = []

    # Create the tmux session with the first (main) command
    main_cmd = fmt_str.format(
        env_args="", timeout=100, M_or_S="-M", mem_limit_str="",
        variant="main", redqueen_str="", sand_str="", afl_args="",
        corpus=corpus, out=out,
        executable=f"./targets/{target}/build_nosan/{executable}"
    )

    cmds.append(f"tmux new-session -d -s {session_name} -n main")
    cmds.append(f"tmux send-keys -t {session_name}:main '{main_cmd}' C-m")

    # Generate secondary fuzzer commands

    for variant in VARIANTS:
        num_procs = 1
        if "redqueen" in variant:
            num_procs = 3
        elif "laf" in variant:
            num_procs = 3
        for i in range(num_procs):
            env_args = ""
            afl_args = ""
            sand_str = ""
            redqueen_str = ""

            if "sand" in variant:
                executable_path = f"./targets/{target}/build_nosan/{executable}"
                #-w ./targets/{target}/build_sand_msan/{executable}
                sand_str = f" -w ./targets/{target}/build_sand_asan/{executable} -w ./targets/{target}/build_sand_ubsan/{executable}  "
            elif "redqueen" in variant:
                executable_path = f"./targets/{target}/build_nosan/{executable}"
                redqueen_str = f"-c ./targets/{target}/build_redqueen/{executable}"
            else:
                executable_path = f"./targets/{target}/build_{variant}/{executable}"



            if random.randint(1,10) == 1:
                afl_args += " -L 0 "
            if random.randint(1,10) == 1:
                afl_args += " -Z "
            #if random.randint(1,3) == 1:
            #    afl_args += " -P explore"
            #elif random.randint(1,2) == 1:
            #    afl_args +=  " -P exploit "

            #if random.randint(1, 8) == 1:
            #    afl_args += " -p explore "
            #elif random.randint(1, 7) == 1:
            #    afl_args += " -p fast "
            #elif random.randint(1, 6) == 1:
            #    afl_args += " -p exploit "
            #elif random.randint(1, 5) == 1:
            #    afl_args += " -p seek "
            #elif random.randint(1, 4) == 1:
            #    afl_args += " -p rare "
            #elif random.randint(1, 3) == 1:
            #    afl_args += " -p mmopt "
            #elif random.randint(1, 2) == 1:
            #    afl_args += " -p coe "

            #if random.randint(1,2) == 1:
            #    env_args += "AFL_DISABLE_TRIM=1 "
            #if random.randint(1,2) == 1:
            #    env_args += "AFL_KEEP_TIMEOUTS=1 "
            #if random.randint(1,2) == 1:
            #    env_args += "AFL_EXPAND_HAVOC_NOW=1 "

            if "redqueen" in variant:
                if random.randint(1,2) == 1:
                    afl_args += " -l 2 "
                elif random.randint(1,2) == 1:
                    afl_args += " -l 2AT "
                elif random.randint(1,2) == 1:
                    afl_args += " -l 3 "

            window_name = variant + str(i)
            afl_cmd = fmt_str.format(
                env_args=env_args, timeout=10000, mem_limit_str="",
                M_or_S="-S", variant=window_name, redqueen_str=redqueen_str,
                sand_str=sand_str, afl_args=afl_args, corpus=corpus, out=out,
                executable=executable_path
            )

            # Create new window and send command
            cmds.append(f"tmux new-window -t {session_name} -n {window_name}")
            cmds.append(f"tmux send-keys -t {session_name}:{window_name} '{afl_cmd}' C-m")

    # Add cleanup command in its own window
    cmds.append(f"tmux new-window -t {session_name} -n cleanup")
    cmds.append(f"tmux send-keys -t {session_name}:cleanup 'while true; do rm -rf /tmp/fuzz_model_*; sleep 60; done' C-m")

    # Add final instruction
    cmds.append(f"echo 'Fuzzing session started. Connect with: tmux attach-session -t {session_name}'")

    return "\nsleep .1\n".join(cmds)


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
        if "commandsonly" in sys.argv:
            print(gen_commands("ggml","corpus/gguf","out","bin/test-fuzz-mnist"))
            sys.exit(0)
        ggml()
    if "llama.cpp" in sys.argv:
        if "commandsonly" in sys.argv:
            print(gen_commands("llama.cpp","corpus/llama","out","bin/test-fuzz"))
            sys.exit(0)
        llama_cpp()


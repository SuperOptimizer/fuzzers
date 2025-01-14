import os
import subprocess

import targets.libtiff

# fuzzers/
#   bin/ # where c harness executables go
#   build/ # where git projects are checked out
#   src/ # .c harnesses
#   targets/ # py fuzzing scripts


#ROOTDIR is the root of all the things we can fuzz
ROOTDIR = os.path.abspath(os.path.dirname(__file__))
#BUILDDIR is where the git repos are checked out and built
BUILDDIR = f"{ROOTDIR}/build"
#BINDIR is where our fuzzer harness executables go
BINDIR = f"{ROOTDIR}/bin"
#SRCDIR is where our fuzzer harness code goes
SRCDIR = f"{ROOTDIR}/src"

VARIANTS = ["main", "cmpcov", "redqueen", "asan", "msan", "ubsan", "cfisan", "lsan"]

def variant_dir(name, variant):
    return f"{BUILDDIR}/{name}/build_{variant}"

def get_lib(giturl, name):
    if not os.path.exists(f"{BUILDDIR}/{name}"):
        subprocess.run(["git", "clone", giturl, name], check=True, cwd=BUILDDIR)


def build_lib(name, variant, build_env, cmake_flags) -> None:

    cmake_cmd = [
        "/usr/bin/cmake", f"{BUILDDIR}/{name}",
        *cmake_flags,
        "-DCMAKE_C_COMPILER=/usr/local/bin/afl-clang-lto",
        "-DCMAKE_CXX_COMPILER=/usr/local/bin/afl-clang-lto++",
        "-DCMAKE_BUILD_TYPE=Release",
        '-DCMAKE_C_FLAGS=-O3 -g3 -flto -fno-omit-frame-pointer -fsanitize-coverage=trace-cmp',
        '-DLINK_FLAGS=-O3 -g3 -flto',
        '-DLINK_OPTIONS=-flto ',
        '-DCMAKE_MAKE_PROGRAM=/usr/bin/make',
        "-DCMAKE_LINKER_TYPE=LLD"
    ]

    vdir = variant_dir(name,variant)
    os.makedirs(vdir, exist_ok=True)
    subprocess.run(cmake_cmd, cwd = vdir, env=build_env, check=True)
    subprocess.run(["/usr/bin/make", "-j8"], cwd = vdir, env=build_env, check=True)



def build_exe(main, variant, incpath, libpath, build_env, ) -> None:

    compile_cmd = [
        "afl-cc", main,
        "-o", f"{main}.{variant}.c.o",
        "-I", f"{incpath}",
        f"{libpath}",
        "-lm", "-lz", "-lzstd", "-ldeflate", "-llzma", "-ljpeg", "-ljbig", "-lLerc", "-lwebp", "-flto", "-fsanitize=fuzzer",
        "-fno-omit-frame-pointer", "-O3"
    ]

    subprocess.run([arg for arg in compile_cmd if arg], env=build_env, check=True, cwd=ROOTDIR)



def build_all_variants(giturl, gitpath):

    variants = {
        "main_thread": {
            "env": "",
            "cflags": "-fsanitize-coverage=trace-cmp"
        },
        "cmpcov": {
            "env": {"AFL_LLVM_LAF_ALL": "1"},
            "cflags": "",
        },
        "redqueen": {
            "env": {"AFL_LLVM_CMPLOG": "1"},
            "cflags": ""
        },
        "asan": {
            "env": {"AFL_USE_ASAN": "1"},
            "cflags": "-fsanitize=address"
        },
        "msan": {
            "env": {"AFL_USE_MSAN": "1"},
            "cflags": "-fsanitize=memory"
        },
        "ubsan": {
            "env": {"AFL_USE_UBSAN": "1"},
            "cflags": "-fsanitize=undefined"
        },
        "cfisan": {
            "env": {"AFL_USE_CFISAN": "1"},
            "cflags": "-fsanitize=cfi"
        },
        "lsan": {
            "env": {"AFL_USE_LSAN": "1"},
            "cflags": "-fsanitize=leak"
        }
    }




if __name__ == "__main__":
    import targets
    targets.libtiff.libtiff()

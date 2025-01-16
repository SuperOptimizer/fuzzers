import os
import subprocess



# fuzzers/
#   bin/ # where c harness executables go
#   build/ # where git projects are checked out
#   src/ # .c harnesses
#   targets/ # py fuzzing scripts

ROOTDIR = os.path.abspath(os.path.dirname(__file__)) # where the top level fuzzers dir goes
BUILDDIR = f"{ROOTDIR}/build" # where the git repos are checked out and built
BINDIR = f"{ROOTDIR}/bin" # where our fuzzer harness executables go
SRCDIR = f"{ROOTDIR}/src" # where our fuzzer harness code goes

VARIANTS = ["nofuzz", "fuzz","cmpcov", "redqueen", "asan", "msan", "ubsan", "cfisan", "lsan"]
CONFIGS = ["CC","CXX","CFLAGS","CXXFLAGS"]


def get_env( do_fuzz: bool, variant: str = "fuzz", opt: str = "-O3"):
    env = os.environ.copy()
    env['INCPATHS']  = " "
    env['LINKPATHS'] = " "
    env['LDFLAGS']   = " "

    if do_fuzz:
        env.update({"CC": "afl-clang-lto", "CXX": "afl-clang-lto++"})
    else:
        env.update({"CC": "clang", "CXX": "clang"})

    fuzz_str = "-DFUZZING" if do_fuzz else ""
    env.update({"CFLAGS": f" {opt} -flto -g3 {fuzz_str} ", "CXXFLAGS": f" {opt} -flto -g3 {fuzz_str} "})

    if variant not in VARIANTS:
        raise Exception

    if variant == "cmpcov":
        env['AFL_LLVM_LAF_ALL']="1"
    elif variant == "redqueen":
        env['AFL_LLVM_CMPLOG']="1"
    elif variant == "asan":
        env['AFL_USE_ASAN']="1"
        env['CFLAGS'] = " " + env['CFLAGS'] + " -fsanitize=address"
    elif variant == "msan":
        env['AFL_USE_MSAN']="1"
        env['CFLAGS'] = " " + env['CFLAGS'] + " -fsanitize=memory"
    elif variant == "ubsan":
        env['AFL_USE_UBSAN']="1"
        env['CFLAGS'] = " " + env['CFLAGS'] + " -fsanitize=undefined"
    elif variant == "cfisan":
        env['AFL_USE_CFISAN']="1"
        env['CFLAGS'] = " " + env['CFLAGS'] + " -fsanitize=cfi"
    elif variant == "lsan":
        env['AFL_USE_LSAN']="1"
        env['CFLAGS'] = " " + env['CFLAGS'] + " -fsanitize=leak"

    return env

def get_lib(giturl, name):
    if not os.path.exists(f"{BUILDDIR}/{name}"):
        subprocess.run(["git", "clone", giturl, name], check=True, cwd=BUILDDIR)


def build_cmake(gitpath, variant, env, cmake_flags) -> None:

    cmake_cmd = [
        "/usr/bin/cmake", "..",
        cmake_flags,
        f"-DCMAKE_C_COMPILER={env['CC']}",
        f"-DCMAKE_CXX_COMPILER={env['CXX']}",
        "-DCMAKE_BUILD_TYPE=Release",
        f'-DCMAKE_C_FLAGS={env['CFLAGS']}',
        '-DCMAKE_MAKE_PROGRAM=/usr/bin/make',
        "-DCMAKE_LINKER_TYPE=LLD"
    ]

    vdir = f"{gitpath}/build_{variant}"
    os.makedirs(vdir, exist_ok=True)
    subprocess.run(cmake_cmd, cwd = vdir, env=env, check=True)
    subprocess.run(["/usr/bin/make", "-j16"], cwd = vdir, env=env, check=True)



def build_exe(main, libs, variant, env) -> None:

    fuzzing_args = ['-DFUZZING', '-fsanitize=fuzzer'] if variant != "nofuzz" else []
    compile_cmd = [
        env['CC'], main, *libs,
        "-o", f"{main.replace('src/','bin/')}.{variant}.elf",
        *env['INCPATHS'].split(),
        *env['LDFLAGS'].split(),
        *env['LINKPATHS'].split(),
        "-flto",
        "-fno-omit-frame-pointer",
        "-g3",
        "-O0",

        *fuzzing_args
    ]
    print("asdf")

    subprocess.run(compile_cmd, env=env, check=True, cwd=ROOTDIR)



if __name__ == "__main__":
    import targets.libtiff
    import targets.libjpeg_turbo
    #targets.libtiff.libtiff()
    targets.libjpeg_turbo.libjpeg_turbo()

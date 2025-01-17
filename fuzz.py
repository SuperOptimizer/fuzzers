import os
import subprocess

def expand(env, s):
    while '{' in s:
        old_s = s
        for k, v in env.items():
            s = s.replace('{' + k + '}', v)
        if old_s == s:  # No more expansions possible but still has brackets - likely an undefined variable
            break
    return s


VARIANTS = ["nofuzz", "fuzz","cmpcov", "redqueen", "asan", "msan", "ubsan", "cfisan", "lsan"]

def get_env(target, variant, do_fuzz: bool, opt: str = "-O3"):
    env = os.environ.copy()

    env["TARGET"] = target
    env["VARIANT"] = variant

    env["ROOTDIR"] = os.path.abspath(os.path.dirname(__file__))
    env["TARGETDIR"] = "{ROOTDIR}/targets/{TARGET}"
    env['GITDIR'] = "{TARGETDIR}/{TARGET}"
    env["BUILDDIR"] = "{ROOTDIR}/build/{TARGET}/{VARIANT}"
    env["BINDIR"] = "{BUILDDIR}/bin"
    env["SRCDIR"] = "{TARGETDIR}/src"
    env["INCPATHS"] = " -I{GITDIR} -I{GITDIR}/include "
    env["LINKPATHS"] = " -L{BUILDDIR} "
    env["LDFLAGS"] = " "

    if do_fuzz:
        env["CC"] = "afl-clang-lto"
        env["CXX"] = "afl-clang-lto++"
    else:
        env["CC"] = "clang"
        env["CXX"]= "clang"

    fuzz_str = "-DFUZZING" if do_fuzz else ""

    env["CFLAGS"]   = f" {opt} -flto -g3 {fuzz_str} "
    env["CXXFLAGS"] = f" {opt} -flto -g3 {fuzz_str} "

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

def git_checkout(env, giturl, name):
    if not os.path.exists(expand(env, "{TARGETDIR}/{name}").format(name=name)):
        subprocess.run(["git", "clone", giturl, name], check=True, cwd=expand(env,"{TARGETDIR}"))


def build_cmake(env, gitpath, variant, cmake_flags) -> None:

    cmake_cmd = [
        "/usr/bin/cmake", gitpath,
        cmake_flags,
        f"-DCMAKE_C_COMPILER={env['CC']}",
        f"-DCMAKE_CXX_COMPILER={env['CXX']}",
        "-DCMAKE_BUILD_TYPE=Release",
        f'-DCMAKE_C_FLAGS={env['CFLAGS']}',
        '-DCMAKE_MAKE_PROGRAM=/usr/bin/make',
        "-DCMAKE_LINKER_TYPE=LLD"
    ]

    vdir = expand(env, "{BUILDDIR}")
    os.makedirs(vdir, exist_ok=True)
    subprocess.run(cmake_cmd, cwd = vdir, env=env, check=True)
    subprocess.run(["/usr/bin/make", "-j16"], cwd = vdir, env=env, check=True)



def build_exe(env, main, libs, variant) -> None:

    fuzzing_args = ['-DFUZZING', '-fsanitize=fuzzer'] if variant != "nofuzz" else []
    compile_cmd = " ".join([
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
    ])
    print("asdf")
    compile_cmd = expand(env, compile_cmd)

    subprocess.run(compile_cmd.split(), env=env, check=True, cwd=expand(env,"{ROOTDIR}"))



if __name__ == "__main__":
    pass

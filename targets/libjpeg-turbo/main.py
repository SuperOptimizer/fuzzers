import fuzz
import os

TARGET = "libjpeg-turbo"
GITURL = "https://github.com/libjpeg-turbo/libjpeg-turbo.git"

CMAKE_FLAGS = "-DENABLE_SHARED=FALSE"
LDFLAGS = " -lm -lz -lzstd -ldeflate -llzma -ljpeg -ljbig -lLerc -lwebp "

HARNESSES = [f'targets/{TARGET}/{TARGET}.c']

def libjpeg_turbo():
    for variant in fuzz.VARIANTS:

        env = fuzz.get_env(TARGET, variant, variant != "nofuzz")
        env['VARIANT'] = variant
        fuzz.git_checkout(env, GITURL, TARGET)

        env['LDFLAGS']   = env['LDFLAGS']   + LDFLAGS
        env['INCPATHS']  = env['INCPATHS']  +  " -I{GITDIR}/src "
        env['LINKPATHS'] = env['LINKPATHS'] +  "  "

        fuzz.build_cmake(env, fuzz.expand(env,"{GITDIR}"), variant, CMAKE_FLAGS)
        libs = ["{BUILDDIR}/libturbojpeg.a",
                 "{BUILDDIR}/libjpeg.a"]

        for main in HARNESSES:
            fuzz.build_exe(env, main, libs, variant)


if __name__ == '__main__':
    libjpeg_turbo()
    # afl-fuzz -i corpus/tiff -o output bin/libtiff.c.main.elf -- @@
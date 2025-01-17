import fuzz
import os

TARGET = "libtiff"
GITURL = "https://gitlab.com/libtiff/libtiff.git"

CMAKE_FLAGS = " -DBUILD_SHARED_LIBS=OFF -Dtiff-docs=OFF -Dtiff-contrib=OFF -Dtiff-tests=OFF -Dtiff-tools=OFF "
LDFLAGS = " -lm -lz -lzstd -ldeflate -llzma -ljpeg -ljbig -lLerc -lwebp "

def libtiff():
    fuzz.get_lib(GITURL,TARGET)
    for VARIANT in fuzz.VARIANTS:

        env = fuzz.get_env(VARIANT)
        env['LDFLAGS']   = env['LDFLAGS']   + LDFLAGS
        env['INCPATHS']  = env['INCPATHS']  + INCPATHS + f" -I{GITDIR}/build_{VARIANT}/{TARGET} "
        env['LINKPATHS'] = env['LINKPATHS'] + LINKPATHS + f" -L{GITDIR}/build_{VARIANT}/{TARGET} "

        fuzz.build_cmake(env, GITDIR, VARIANT, CMAKE_FLAGS)

        for main in HARNESSES:
            fuzz.build_exe(env, main, [f"{GITDIR}/build_{VARIANT}/{TARGET}/{TARGET}.a"], VARIANT)


if __name__ == '__main__':
    libtiff()
    # afl-fuzz -i corpus/tiff -o output bin/libtiff.c.main.elf -- @@
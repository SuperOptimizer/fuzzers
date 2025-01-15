import fuzz
from fuzz import ROOTDIR, BUILDDIR
import os

NAME = "libtiff"
GITURL = "https://gitlab.com/libtiff/libtiff.git"
GITDIR = f"{BUILDDIR}/{NAME}"

CMAKE_FLAGS = " -DBUILD_SHARED_LIBS=OFF -Dtiff-docs=OFF -Dtiff-contrib=OFF -Dtiff-tests=OFF -Dtiff-tools=OFF "
LDFLAGS = " -lm -lz -lzstd -ldeflate -llzma -ljpeg -ljbig -lLerc -lwebp "
INCPATHS = f" -I{GITDIR} -I{GITDIR}/{NAME} "
LINKPATHS = f" -L{GITDIR} "

HARNESSES = [f'{ROOTDIR}/src/{NAME}.c']

def libtiff():
    fuzz.get_lib(GITURL,NAME)
    for VARIANT in fuzz.VARIANTS:

        env = fuzz.get_env(VARIANT)
        env['LDFLAGS']   = env['LDFLAGS']   + LDFLAGS
        env['INCPATHS']  = env['INCPATHS']  + INCPATHS + f" -I{GITDIR}/build_{VARIANT}/{NAME} "
        env['LINKPATHS'] = env['LINKPATHS'] + LINKPATHS + f" -L{GITDIR}/build_{VARIANT}/{NAME} "

        fuzz.build_cmake(GITDIR, VARIANT, env, CMAKE_FLAGS)

        for main in HARNESSES:
            fuzz.build_exe(main, [f"{GITDIR}/build_{VARIANT}/{NAME}/{NAME}.a"], VARIANT, env)


if __name__ == '__main__':
    libtiff()
    # afl-fuzz -i corpus/tiff -o output bin/libtiff.c.main.elf -- @@
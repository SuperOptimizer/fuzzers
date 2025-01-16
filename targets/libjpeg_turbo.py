import fuzz
from fuzz import ROOTDIR, BUILDDIR
import os

NAME = "libjpeg-turbo"
GITURL = "https://github.com/libjpeg-turbo/libjpeg-turbo.git"
GITDIR = f"{BUILDDIR}/{NAME}"

CMAKE_FLAGS = " -DENABLE_SHARED=FALSE "
LDFLAGS = " -lm -lz -lzstd -ldeflate -llzma -ljpeg -ljbig -lLerc -lwebp "
INCPATHS = f" -I{GITDIR} -I{GITDIR}/{NAME} -I{GITDIR}/src "
LINKPATHS = f" -L{GITDIR} "

HARNESSES = [f'{ROOTDIR}/src/{NAME}.c']

def libjpeg_turbo():
    fuzz.get_lib(GITURL,NAME)
    for VARIANT in fuzz.VARIANTS:

        env = fuzz.get_env(VARIANT)
        env['LDFLAGS']   = env['LDFLAGS']   + LDFLAGS
        env['INCPATHS']  = env['INCPATHS']  + INCPATHS + f" -I{GITDIR}/build_{VARIANT}/{NAME} "
        env['LINKPATHS'] = env['LINKPATHS'] + LINKPATHS + f" -L{GITDIR}/build_{VARIANT}/{NAME} "

        fuzz.build_cmake(GITDIR, VARIANT, env, CMAKE_FLAGS)

        for main in HARNESSES:
            fuzz.build_exe(main, [f"{GITDIR}/build_{VARIANT}/libturbojpeg.a", f"{GITDIR}/build_{VARIANT}/libjpeg.a"], VARIANT, env)


if __name__ == '__main__':
    libjpeg_turbo()
    # afl-fuzz -i corpus/tiff -o output bin/libtiff.c.main.elf -- @@
import fuzz
from fuzz import ROOTDIR, BUILDDIR
import os

NAME = "libtiff"
GITURL = "https://gitlab.com/libtiff/libtiff.git"

HARNESSES = ['src/libtiff.c']
CMAKE_FLAGS = ["-DBUILD_SHARED_LIBS=OFF", "-Dtiff-docs=OFF", "-Dtiff-contrib=OFF", "-Dtiff-tests=OFF", "-Dtiff-tools=OFF"]

def libtiff():
    fuzz.get_lib(GITURL,NAME)
    env = os.environ.copy()
    for variant in fuzz.VARIANTS:
        fuzz.build_lib(NAME, variant, env, CMAKE_FLAGS)
        
        for main in HARNESSES:
            libsrcpath = f"{BUILDDIR}/{NAME}.c"
            libbuildpath = f"{fuzz.variant_dir(NAME, variant)}/libtiff/libtiff.a"
            fuzz.build_exe(main, variant, libsrcpath, libbuildpath, env)


if __name__ == '__main__':
    libtiff()
import fuzz
import os
import subprocess
import shutil

TARGET = "syzkaller"
GITURL = "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"

def syzcaller():
    env = fuzz.get_env(TARGET,"nofuzz",False)

    TARGETDIR = fuzz.expand(env, "{TARGETDIR}")
    fuzz.git_checkout(env,GITURL,"linux")

    # we have multiple kernel variants: none kasan kmsan ubsan kcsan
    os.makedirs(f"{TARGETDIR}/build", exist_ok=True)
    os.makedirs(f"{TARGETDIR}/build_kmsan", exist_ok=True)
    os.makedirs(f"{TARGETDIR}/build_kasan", exist_ok=True)
    os.makedirs(f"{TARGETDIR}/build_ubsan", exist_ok=True)
    os.makedirs(f"{TARGETDIR}/build_kcsan", exist_ok=True)



    shutil.copyfile(f"{TARGETDIR}/.config",f"{TARGETDIR}/linux/.config")
    subprocess.run("make O=../build olddefconfig".split(), cwd=f"{TARGETDIR}/linux")
    subprocess.run("make -j32".split(), cwd=f"{TARGETDIR}/linux")
    #subprocess.run("wget https://raw.githubusercontent.com/google/syzkaller/master/tools/create-image.sh".split(),cwd="/tmp")
    #subprocess.run("chmod +x ./create-image.sh".split(),cwd="/tmp")
    #subprocess.run("sudo ./create-image.sh".split(),cwd="/tmp")



if __name__ == '__main__':
    syzcaller()
    # afl-fuzz -i corpus/tiff -o output bin/libtiff.c.main.elf -- @@
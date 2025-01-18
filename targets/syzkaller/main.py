import fuzz
import os
import subprocess
import shutil

TARGET = "syzkaller"
GITURL = "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"

#doing out of tree builds and stuff with the linux kernel is dumb
#working with the linux kernel being in tree is dumb for my ide
#so we're gonna git checkout 5 times to some temp directory, one for each variant
def syzcaller():
    env = fuzz.get_env(TARGET,"nofuzz",False)
    REALTARGETDIR = fuzz.expand(env,"{TARGETDIR}")
    TARGETDIR = "/home/forrest/tmp/syzkaller"
    if not os.path.exists(TARGETDIR):
        os.makedirs(TARGETDIR)
        fuzz.git_checkout(env,GITURL,f"{TARGETDIR}/linux")
        shutil.copytree(f"{TARGETDIR}/linux",f"{TARGETDIR}/linux_kmsan")
        shutil.copytree(f"{TARGETDIR}/linux",f"{TARGETDIR}/linux_kasan")
        shutil.copytree(f"{TARGETDIR}/linux",f"{TARGETDIR}/linux_ubsan")
        shutil.copytree(f"{TARGETDIR}/linux",f"{TARGETDIR}/linux_kcsan")

    shutil.copyfile(f"{REALTARGETDIR}/.config",f"{TARGETDIR}/linux/.config")
    shutil.copyfile(f"{REALTARGETDIR}/.config.kasan",f"{TARGETDIR}/linux_kasan/.config")
    shutil.copyfile(f"{REALTARGETDIR}/.config.kcsan",f"{TARGETDIR}/linux_kcsan/.config")
    shutil.copyfile(f"{REALTARGETDIR}/.config.kmsan",f"{TARGETDIR}/linux_kmsan/.config")
    shutil.copyfile(f"{REALTARGETDIR}/.config.ubsan",f"{TARGETDIR}/linux_ubsan/.config")

    subprocess.run(f"make LLVM=1 olddefconfig".split(), cwd=f"{TARGETDIR}/linux")
    subprocess.run(f"make LLVM=1  -j32".split(), cwd=f"{TARGETDIR}/linux")

    subprocess.run(f"make LLVM=1 olddefconfig".split(), cwd=f"{TARGETDIR}/linux_kasan")
    subprocess.run(f"make LLVM=1  -j32".split(), cwd=f"{TARGETDIR}/linux_kasan")

    subprocess.run(f"make LLVM=1 olddefconfig".split(), cwd=f"{TARGETDIR}/linux_kcsan")
    subprocess.run(f"make LLVM=1  -j32".split(), cwd=f"{TARGETDIR}/linux_kcsan")

    subprocess.run(f"make LLVM=1 olddefconfig".split(), cwd=f"{TARGETDIR}/linux_kmsan")
    subprocess.run(f"make LLVM=1  -j32".split(), cwd=f"{TARGETDIR}/linux_kmsan")

    subprocess.run(f"make LLVM=1 olddefconfig".split(), cwd=f"{TARGETDIR}/linux_ubsan")
    subprocess.run(f"make LLVM=1  -j32".split(), cwd=f"{TARGETDIR}/linux_ubsan")

    #subprocess.run("wget https://raw.githubusercontent.com/google/syzkaller/master/tools/create-image.sh".split(),cwd="/tmp")
    #subprocess.run("chmod +x ./create-image.sh".split(),cwd="/tmp")
    #subprocess.run("sudo ./create-image.sh".split(),cwd="/tmp")



if __name__ == '__main__':
    syzcaller()
    # afl-fuzz -i corpus/tiff -o output bin/libtiff.c.main.elf -- @@
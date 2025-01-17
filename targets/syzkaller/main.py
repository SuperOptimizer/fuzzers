import fuzz
import os
import subprocess

TARGET = "syzkaller"
GITURL = "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"

CMAKE_FLAGS = " -DBUILD_SHARED_LIBS=OFF -Dtiff-docs=OFF -Dtiff-contrib=OFF -Dtiff-tests=OFF -Dtiff-tools=OFF "
LDFLAGS = " -lm -lz -lzstd -ldeflate -llzma -ljpeg -ljbig -lLerc -lwebp "



def syzcaller():
    env = fuzz.get_env(TARGET,"nofuzz",False)
    fuzz.git_checkout(env,GITURL,"linux")
    subprocess.run("cp .config ./linux".split(), cwd= fuzz.expand(env,"{TARGETDIR}"))
    subprocess.run("make olddefconfig".split(), cwd= fuzz.expand(env,"{TARGETDIR}/linux"))
    subprocess.run("make -j32".split(), cwd= fuzz.expand(env,"{TARGETDIR}/linux"))
    cwd = fuzz.expand(env,"{TARGETDIR}/")
    subprocess.run("cp ./linux/arch/x86/boot/bzImage .".split(), cwd= fuzz.expand(env,"{TARGETDIR}/"))
    subprocess.run("cp ./linux/vmlinux .".split(), cwd= fuzz.expand(env,"{TARGETDIR}/"))
    #subprocess.run("wget https://raw.githubusercontent.com/google/syzkaller/master/tools/create-image.sh".split(),cwd="/tmp")
    #subprocess.run("chmod +x ./create-image.sh".split(),cwd="/tmp")
    #subprocess.run("sudo ./create-image.sh".split(),cwd="/tmp")
    subprocess.run("cp /tmp/bullseye.id_rsa /tmp/bullseye.id_rsa.pub /tmp/bullseye.img .".split(), cwd= fuzz.expand(env,"{TARGETDIR}/"))



if __name__ == '__main__':
    syzcaller()
    # afl-fuzz -i corpus/tiff -o output bin/libtiff.c.main.elf -- @@
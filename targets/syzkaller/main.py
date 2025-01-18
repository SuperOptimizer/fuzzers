import fuzz
import os
import subprocess
import shutil

#subprocess.run("wget https://raw.githubusercontent.com/google/syzkaller/master/tools/create-image.sh".split(),cwd="/tmp")
#subprocess.run("chmod +x ./create-image.sh".split(),cwd="/tmp")
#subprocess.run("sudo ./create-image.sh".split(),cwd="/tmp")
#then sudo chown -R the id pub rsa to the current user!!! very important

TARGET = "syzkaller"
GITURL = "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"

all_flags = '''
CONFIG_KCOV=y
CONFIG_KCOV_INSTRUMENT_ALL=y
CONFIG_KCOV_ENABLE_COMPARISONS=y
CONFIG_DEBUG_FS=y
CONFIG_DEBUG_KMEMLEAK=y
CONFIG_DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT=y
CONFIG_KALLSYMS=y
CONFIG_KALLSYMS_ALL=y
CONFIG_NAMESPACES=y
CONFIG_UTS_NS=y
CONFIG_IPC_NS=y
CONFIG_PID_NS=y
CONFIG_NET_NS=y
CONFIG_CGROUP_PIDS=y
CONFIG_MEMCG=y
CONFIG_USER_NS=y
CONFIG_CONFIGFS_FS=y
CONFIG_SECURITYFS=y
CONFIG_CMDLINE_BOOL=y
CONFIG_CMDLINE="net.ifnames=0"
CONFIG_FAULT_INJECTION=y
CONFIG_FAULT_INJECTION_DEBUG_FS=y
CONFIG_FAULT_INJECTION_USERCOPY=y
CONFIG_FAILSLAB=y
CONFIG_FAIL_PAGE_ALLOC=y
CONFIG_FAIL_MAKE_REQUEST=y
CONFIG_FAIL_IO_TIMEOUT=y
CONFIG_FAIL_FUTEX=y
CONFIG_LOCKDEP=y
CONFIG_PROVE_LOCKING=y
CONFIG_DEBUG_ATOMIC_SLEEP=y
CONFIG_PROVE_RCU=y
CONFIG_DEBUG_VM=y
CONFIG_REFCOUNT_FULL=y
CONFIG_FORTIFY_SOURCE=y
CONFIG_HARDENED_USERCOPY=y
CONFIG_LOCKUP_DETECTOR=y
CONFIG_SOFTLOCKUP_DETECTOR=y
CONFIG_HARDLOCKUP_DETECTOR=y
CONFIG_BOOTPARAM_HARDLOCKUP_PANIC=y
CONFIG_DETECT_HUNG_TASK=y
CONFIG_WQ_WATCHDOG=y
CONFIG_DEFAULT_HUNG_TASK_TIMEOUT=140
CONFIG_RCU_CPU_STALL_TIMEOUT=100
'''

kasan_flags = '''
CONFIG_KASAN=y
CONFIG_KASAN_INLINE=y
CONFIG_KASAN_GENERIC=y
'''

kcsan_flags = '''
CONFIG_KCSAN=y
'''
kmsan_flags = '''
CONFIG_KMSAN=y
'''
ubsan_flags = '''
CONFIG_UBSAN=y
'''


def write_config_flags(config_path, flags_str):
    with open(config_path, 'a') as f:
        f.write(flags_str)


#doing out of tree builds and stuff with the linux kernel is dumb
#working with the linux kernel being in tree is dumb for my ide
#so we're gonna git checkout 5 times to some temp directory, one for each variant



def syzcaller():
    env = fuzz.get_env(TARGET, "nofuzz", False)
    REALTARGETDIR = fuzz.expand(env, "{TARGETDIR}")
    TARGETDIR = "/home/forrest/tmp/syzkaller"
    if not os.path.exists(TARGETDIR):
        os.makedirs(TARGETDIR)
        fuzz.git_checkout(env, GITURL, f"{TARGETDIR}/linux")
        shutil.copytree(f"{TARGETDIR}/linux", f"{TARGETDIR}/linux_kmsan")
        shutil.copytree(f"{TARGETDIR}/linux", f"{TARGETDIR}/linux_kasan")
        shutil.copytree(f"{TARGETDIR}/linux", f"{TARGETDIR}/linux_ubsan")
        shutil.copytree(f"{TARGETDIR}/linux", f"{TARGETDIR}/linux_kcsan")

    for variant in ["", "_kasan", "_kmsan", "_kcsan", "_ubsan"]:
        flags = all_flags
        if variant == "_kasan":
            flags  += kasan_flags
        if variant == "_kmsan":
            flags += kmsan_flags
        if variant == "_kcsan":
            flags += kcsan_flags
        if variant == "_ubsan":
            flags += ubsan_flags
        subprocess.run(f"make mrproper".split(), cwd=f"{TARGETDIR}/linux{variant}")
        subprocess.run(f"make LLVM=1 CC=clang defconfig".split(), cwd=f"{TARGETDIR}/linux{variant}")
        subprocess.run(f"make LLVM=1 CC=clang kvm_guest.config".split(), cwd=f"{TARGETDIR}/linux{variant}")
        write_config_flags(f"{TARGETDIR}/linux{variant}/.config", flags)
        subprocess.run(f"make LLVM=1 CC=clang olddefconfig".split(), cwd=f"{TARGETDIR}/linux{variant}")
        subprocess.run(f"make LLVM=1 CC=clang -j32".split(), cwd=f"{TARGETDIR}/linux{variant}")





if __name__ == '__main__':
    syzcaller()
    # afl-fuzz -i corpus/tiff -o output bin/libtiff.c.main.elf -- @@
import fuzz
import os
import subprocess
import shutil

# cd /tmp
# wget https://raw.githubusercontent.com/google/syzkaller/master/tools/create-image.sh
# chmod +x ./create-image.sh
# sudo bash create-image.sh
# sudo chown -R forrest ./bullseye*
#then sudo chown -R the id pub rsa to the current user!!! very important

TARGET = "syzkaller"
GITURL = "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
SYZKALLER="/home/forrest/syzkaller"

extra_flags = """
CONFIG_CONFIGFS_FS=y
CONFIG_SECURITYFS=y
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
CONFIG_DEBUG_KMEMLEAK=y
CONFIG_KFENCE=y
"""

variant_flags = {
    "": """
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
CONFIG_CMDLINE_BOOL=y
CONFIG_CMDLINE="earlyprintk=serial net.ifnames=0 sysctl.kernel.hung_task_all_cpu_backtrace=1 ima_policy=tcb nf-conntrack-ftp.ports=20000 nf-conntrack-tftp.ports=20000 nf-conntrack-sip.ports=20000 nf-conntrack-irc.ports=20000 nf-conntrack-sane.ports=20000 binder.debug_mask=0 rcupdate.rcu_expedited=1 rcupdate.rcu_cpu_stall_cputime=1 no_hash_pointers page_owner=on sysctl.vm.nr_hugepages=4 sysctl.vm.nr_overcommit_hugepages=4 secretmem.enable=1 sysctl.max_rcu_stall_to_panic=1 msr.allow_writes=off coredump_filter=0xffff root=/dev/sda console=ttyS0 vsyscall=native numa=fake=2 kvm-intel.nested=1 spec_store_bypass_disable=prctl nopcid vivid.n_devs=64 vivid.multiplanar=1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2 netrom.nr_ndevs=32 rose.rose_ndevs=32 smp.csd_lock_timeout=100000 watchdog_thresh=55 workqueue.watchdog_thresh=140 sysctl.net.core.netdev_unregister_timeout_secs=140 dummy_hcd.num=32 max_loop=32 nbds_max=32 panic_on_warn=1"
""",
    "tiny": """""",
    "msan": """""",
    "asan": """""",
    "kcsan": """""",
    "ubsan": """
CONFIG_ARCH_HAS_UBSAN=y
CONFIG_UBSAN=y
CONFIG_UBSAN_TRAP=y
CONFIG_CC_HAS_UBSAN_ARRAY_BOUNDS=y
CONFIG_UBSAN_BOUNDS=y
CONFIG_UBSAN_ARRAY_BOUNDS=y
CONFIG_UBSAN_SHIFT=y
CONFIG_UBSAN_SIGNED_WRAP=y
CONFIG_UBSAN_BOOL=y
CONFIG_UBSAN_ENUM=y
CONFIG_UBSAN_ALIGNMENT=y
"""
}

def write_config_flags(config_path, flags_str):
    with open(config_path, 'a') as f:
        f.write(flags_str)


#doing out of tree builds and stuff with the linux kernel is dumb
#working with the linux kernel being in tree is dumb for my ide
#so we're gonna git checkout 5 times to some temp directory, one for each variant



def syzcaller():
    env = fuzz.get_env(TARGET, "nofuzz", False)
    REALTARGETDIR = fuzz.expand(env,"{TARGETDIR}")
    TARGETDIR = "/home/forrest/tmp/syzkaller"
    if not os.path.exists(TARGETDIR):
        os.makedirs(TARGETDIR)
        fuzz.git_checkout(env, GITURL, f"{TARGETDIR}/linux")
        shutil.copytree(f"{TARGETDIR}/linux", f"{TARGETDIR}/linuxkcsan")
        shutil.copytree(f"{TARGETDIR}/linux", f"{TARGETDIR}/linuxtiny")
        shutil.copytree(f"{TARGETDIR}/linux", f"{TARGETDIR}/linuxmsan")
        shutil.copytree(f"{TARGETDIR}/linux", f"{TARGETDIR}/linuxasan")
        shutil.copytree(f"{TARGETDIR}/linux", f"{TARGETDIR}/linuxubsan")

    for variant in ["","msan","asan","kcsan","ubsan","tiny"]:
        #TODO: when do we need to do a clean build? only when changing CONFIG_?
        #subprocess.run(f"make mrproper".split(), cwd=f"{TARGETDIR}/linux{variant}")

        if variant == "":
            subprocess.run(f"make defconfig".split(), cwd=f"{TARGETDIR}/linux{variant}")
        elif variant == "tiny":
            subprocess.run(f"make tinyconfig".split(), cwd=f"{TARGETDIR}/linux{variant}")
        else:
            conf = {
                "msan":f"/{SYZKALLER}/dashboard/config/linux/upstream-kmsan.config",
                "asan":f"/{SYZKALLER}/dashboard/config/linux/upstream-kasan-badwrites.config",
                "kcsan":f"/{SYZKALLER}/dashboard/config/linux/upstream-kcsan.config",
                "ubsan":f"/{SYZKALLER}/dashboard/config/linux/upstream-leak.config",
            }[variant]
            shutil.copyfile(conf,f"{TARGETDIR}/linux{variant}/.config")

        write_config_flags(f"{TARGETDIR}/linux{variant}/.config", extra_flags)
        write_config_flags(f"{TARGETDIR}/linux{variant}/.config", variant_flags[variant])

        subprocess.run(f"make kvm_guest.config".split(), cwd=f"{TARGETDIR}/linux{variant}")
        subprocess.run(f"make  olddefconfig".split(), cwd=f"{TARGETDIR}/linux{variant}")
        subprocess.run(f"make -j32".split(), cwd=f"{TARGETDIR}/linux{variant}")

        subprocess.run("cp /tmp/bullseye.img /tmp/bullseye.id_rsa.pub /tmp/bullseye.id_rsa . ".split(),cwd=f"{TARGETDIR}/linux{variant}")






if __name__ == '__main__':
    syzcaller()
    # afl-fuzz -i corpus/tiff -o output bin/libtiff.c.main.elf -- @@
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh
sudo bash llvm.sh 20 all
sudo apt-get update
sudo apt-get install -y build-essential python3-dev automake cmake git flex bison libglib2.0-dev libpixman-1-dev python3-setuptools cargo libgtk-3-dev
sudo apt-get install -y gcc-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-plugin-dev libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev
sudo apt-get install -y ninja-build # for QEMU mode
sudo apt-get install -y cpio libcapstone-dev # for Nyx mode
sudo apt-get install -y wget curl # for Frida mode
sudo apt-get install -y python3-pip # for Unicorn mode
git clone https://github.com/AFLplusplus/AFLplusplus
cd AFLplusplus
CC=clang-20 CXX=clang-20 make distrib PERFORMANCE=1 STATIC=1 CODE_COVERAGE=1 LLVM_CONFIG=llvm-config-20
sudo make install

#syzkaller stuff
sudo apt update
sudo apt install make gcc flex bison libncurses-dev libelf-dev libssl-dev build-essential binutils gawk
sudo apt install debootstrap
sudo apt install qemu-system-x86
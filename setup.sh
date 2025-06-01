#wget https://apt.llvm.org/llvm.sh
#chmod +x llvm.sh
#sudo bash llvm.sh 20 all
sudo apt-get update
sudo apt-get install -y build-essential python3-dev automake cmake git flex bison libglib2.0-dev libpixman-1-dev python3-setuptools cargo libgtk-3-dev
sudo apt-get install -y gcc-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-plugin-dev libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev
sudo apt-get install -y ninja-build # for QEMU mode
sudo apt-get install -y cpio libcapstone-dev # for Nyx mode
sudo apt-get install -y wget curl # for Frida mode
sudo apt-get install -y python3-pip # for Unicorn mode
git clone https://github.com/AFLplusplus/AFLplusplus
cd AFLplusplus
CC=clang CXX=clang++ make source-only PERFORMANCE=1 STATIC=1 NO_NYX=1 NO_CORESIGHT=1 NO_UNICORN_ARM64=1 AFL_NO_X86=1
sudo make install


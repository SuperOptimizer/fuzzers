git clone https://github.com/pnggroup/libpng.git
rm -rf libpng/fuzzing_build
mkdir libpng/fuzzing_build

# threads
# -------
# main thread
# cmpcov
# redqueen
# asan
# msan
# ubsan
# cfisan
# tsan
# lsan

# power schedule: fast (default), explore, coe, lin, quad, exploit,  rare
# which you can set with the -p option, e.g., -p explore. See the FAQ for details.

# main thread
cd libpng/fuzzing_build
mkdir mainthread
cd mainthread
cmake ../.. -DPNG_SHARED=OFF -DCMAKE_C_COMPILER=afl-clang-lto -DCMAKE_CXX_COMPILER=afl-clang-lto++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3 -g3 -flto -fsanitize-coverage=trace-cmp -fno-omit-frame-pointer" -DLINK_FLAGS="-O3 -g3 -flto -fsanitize-coverage=trace-cmp -fno-omit-frame-pointer" -DLINK_OPTIONS="-flto -fsanitize-coverage=trace-cmp -fno-omit-frame-pointer"
make -j8
cd ../../..
afl-cc src/main.c -o bin/main_thread -I libpng libpng/fuzzing_build/mainthread/libpng.a -lm -lz -flto -fsanitize=fuzzer -fsanitize-coverage=trace-cmp -fno-omit-frame-pointer -O3

#cmpcov
cd libpng/fuzzing_build
mkdir cmpcov
cd cmpcov
set AFL_LLVM_LAF_ALL=1
export AFL_LLVM_LAF_ALL=1
cmake ../.. -DPNG_SHARED=OFF -DCMAKE_C_COMPILER=afl-clang-lto -DCMAKE_CXX_COMPILER=afl-clang-lto++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3 -g3 -flto -fno-omit-frame-pointer -fsanitize-coverage=trace-cmp " -DLINK_FLAGS="-O3 -g3 -flto  -fno-omit-frame-pointer" -DLINK_OPTIONS="-flto  -fno-omit-frame-pointer"
make -j8
cd ../../..
afl-cc src/main.c -o bin/cmpcov -I libpng libpng/fuzzing_build/cmpcov/libpng.a -lm -lz -flto -fsanitize=fuzzer -fno-omit-frame-pointer -O3
unset AFL_LLVM_LAF_ALL

#redqueen
cd libpng/fuzzing_build
mkdir redqueen
cd redqueen
export AFL_LLVM_CMPLOG=1
set AFL_LLVM_CMPLOG=1
cmake ../.. -DPNG_SHARED=OFF -DCMAKE_C_COMPILER=afl-clang-lto -DCMAKE_CXX_COMPILER=afl-clang-lto++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3 -g3 -flto  -fno-omit-frame-pointer -fsanitize-coverage=trace-cmp " -DLINK_FLAGS="-O3 -g3 -flto -fno-omit-frame-pointer " -DLINK_OPTIONS="-flto -fno-omit-frame-pointer "
make -j8
cd ../../..
afl-cc src/main.c -o bin/redqueen -I libpng libpng/fuzzing_build/redqueen/libpng.a -lm -lz -flto -fsanitize=fuzzer -fno-omit-frame-pointer -O3
unset AFL_LLVM_CMPLOG

#asan
cd libpng/fuzzing_build
mkdir asan
cd asan
export AFL_USE_ASAN=1
set AFL_USE_ASAN=1
cmake ../.. -DPNG_SHARED=OFF -DCMAKE_C_COMPILER=afl-clang-lto -DCMAKE_CXX_COMPILER=afl-clang-lto++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3 -g3 -flto -fsanitize=address -fno-omit-frame-pointer -fsanitize-coverage=trace-cmp " -DLINK_FLAGS="-O3 -g3 -flto  -fsanitize=address" -DLINK_OPTIONS="-flto  -fsanitize=address"
make -j8
cd ../../..
afl-cc src/main.c -o bin/asan -I libpng libpng/fuzzing_build/asan/libpng.a -lm -lz -flto  -fsanitize=fuzzer,address -fno-omit-frame-pointer -O3
unset AFL_USE_ASAN

#msan
cd libpng/fuzzing_build
mkdir msan
cd msan
export AFL_USE_MSAN=1
set AFL_USE_MSAN=1
cmake ../.. -DPNG_SHARED=OFF -DCMAKE_C_COMPILER=afl-clang-lto -DCMAKE_CXX_COMPILER=afl-clang-lto++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3 -g3 -flto -fsanitize=memory -fno-omit-frame-pointer -fsanitize-coverage=trace-cmp " -DLINK_FLAGS="-O3 -g3 -flto  -fsanitize=memory" -DLINK_OPTIONS="-flto  -fsanitize=memory"
make -j8
cd ../../..
afl-cc src/main.c -o bin/msan -I libpng libpng/fuzzing_build/msan/libpng.a -lm -lz -flto  -fsanitize=fuzzer,memory -fno-omit-frame-pointer -O3
unset AFL_USE_MSAN

#ubsan
cd libpng/fuzzing_build
mkdir ubsan
cd ubsan
export AFL_USE_UBSAN=1
set AFL_USE_UBSAN=1
cmake ../.. -DPNG_SHARED=OFF -DCMAKE_C_COMPILER=afl-clang-lto -DCMAKE_CXX_COMPILER=afl-clang-lto++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3 -g3 -flto -fsanitize=undefined -fno-omit-frame-pointer -fsanitize-coverage=trace-cmp " -DLINK_FLAGS="-O3 -g3 -flto  -fsanitize=undefined" -DLINK_OPTIONS="-flto  -fsanitize=undefined"
make -j8
cd ../../..
afl-cc src/main.c -o bin/ubsan -I libpng libpng/fuzzing_build/ubsan/libpng.a -lm -lz -flto  -fsanitize=fuzzer,undefined -fno-omit-frame-pointer -O3
unset AFL_USE_UBSAN

#cfisan
cd libpng/fuzzing_build
mkdir cfisan
cd cfisan
export AFL_USE_CFISAN=1
set AFL_USE_CFISAN=1
cmake ../.. -DPNG_SHARED=OFF -DCMAKE_C_COMPILER=afl-clang-lto -DCMAKE_CXX_COMPILER=afl-clang-lto++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3 -g3 -flto -fsanitize=cfi -fno-omit-frame-pointer -fsanitize-coverage=trace-cmp " -DLINK_FLAGS="-O3 -g3 -flto  -fsanitize=cfi" -DLINK_OPTIONS="-flto  -fsanitize=cfi"
make -j8
cd ../../..
afl-cc src/main.c -o bin/cfisan -I libpng libpng/fuzzing_build/cfisan/libpng.a -lm -lz -flto  -fsanitize=fuzzer,cfi -fno-omit-frame-pointer -O3
unset AFL_USE_CFISAN

#tsan
#cd libpng/fuzzing_build
#mkdir tsan
#cd tsan
#export AFL_USE_TSAN=1
#set AFL_USE_TSAN=1
#cmake ../.. -DPNG_SHARED=OFF -DCMAKE_C_COMPILER=afl-clang-lto -DCMAKE_CXX_COMPILER=afl-clang-lto++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3 -g3 -flto -fsanitize=thread" -DLINK_FLAGS="-O3 -g3 -flto  -fsanitize=thread" -DLINK_OPTIONS="-flto  -fsanitize=thread"
#make -j8
#cd ../../..
#afl-cc src/main.c -o bin/tsan -I libpng libpng/fuzzing_build/tsan/libpng.a -lm -lz -flto  -fsanitize=thread
#unset AFL_USE_TSAN

#lsan
cd libpng/fuzzing_build
mkdir lsan
cd lsan
export AFL_USE_LSAN=1
set AFL_USE_LSAN=1
cmake ../.. -DPNG_SHARED=OFF -DCMAKE_C_COMPILER=afl-clang-lto -DCMAKE_CXX_COMPILER=afl-clang-lto++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3 -g3 -flto -fsanitize=leak -fno-omit-frame-pointer -fsanitize-coverage=trace-cmp " -DLINK_FLAGS="-O3 -g3 -flto  -fsanitize=leak" -DLINK_OPTIONS="-flto  -fsanitize=leak"
make -j8
cd ../../..
afl-cc src/main.c -o bin/lsan -I libpng libpng/fuzzing_build/lsan/libpng.a -lm -lz -flto  -fsanitize=leak -fno-omit-frame-pointer -O3
unset AFL_USE_LSAN

# run the fuzzer
afl-fuzz -i corpus -o output -t 1000 -M main_libpng -- ./bin/main_thread @@
afl-fuzz -i corpus -o output -t 1000 -S cmpcov_libpng -- ./bin/cmpcov @@
afl-fuzz -i corpus -o output -t 1000 -S redqueen_libpng -- ./bin/redqueen @@
afl-fuzz -i corpus -o output -t 1000 -S asan_libpng -- ./bin/asan @@
afl-fuzz -i corpus -o output -t 1000 -S msan_libpng -- ./bin/msan @@
afl-fuzz -i corpus -o output -t 1000 -S ubsan_libpng -- ./bin/ubsan @@
afl-fuzz -i corpus -o output -t 1000 -S cfisan_libpng -- ./bin/cfisan @@
afl-fuzz -i corpus -o output -t 1000 -S lsan_libpng -- ./bin/lsan @@
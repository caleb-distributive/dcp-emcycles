#!/bin/bash

set +e

cd js_build

cp bin/cycles_test cycles_test.bc && emcc --embed-file elephant.xml --embed-file gumbo.xml lib/libcycles_kernel.so lib/libcycles_util.so lib/libcycles_device.so lib/libcycles_bvh.so lib/libcycles_subd.so  lib/libcycles_render.so cycles_test.bc -o cycles_test.html
# cp bin/cycles_test cycles_test.bc && emcc --embed-file elephant.xml --embed-file gumbo.xml lib/libcycles_kernel.so lib/libcycles_util.so lib/libcycles_device.so lib/libcycles_bvh.so lib/libcycles_subd.so  lib/libcycles_render.so cycles_test.bc --llvm-lto 1 -o cycles_test.html
# cp bin/cycles_test cycles_test.bc && emcc --embed-file elephant.xml --embed-file gumbo.xml cycles_test.bc -o cycles_test.html

#!/bin/bash

set +e

rm -f cycles_test.js

pushd js_build

# JavaScript build
cp bin/cycles_test cycles_test.bc && emcc lib/libcycles_kernel.so lib/libcycles_util.so lib/libcycles_device.so lib/libcycles_bvh.so lib/libcycles_subd.so lib/libcycles_render.so cycles_test.bc -O2 -o cycles_test.js

popd

cat cloudrender_init.js js_build/cycles_test.js cloudrender_close.js > ./cloudrender_core.js


#!/bin/bash

# rm -rf js_build

mkdir -p js_build
# {
#     cd js_build && make clean
# } || {
#     echo "COULD NOT CLEAN"
# }
cd js_build && emcmake cmake .. -DCMAKE_CXX_FLAGS='-s SINGLE_FILE=1 -s ALLOW_MEMORY_GROWTH=1' && make && cd .. && ./cat-build.sh

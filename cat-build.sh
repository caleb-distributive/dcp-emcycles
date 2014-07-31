#!/usr/bin/env bash

cat cloudrender_init.js zlib.js png.js js_build/cycles_test.js cloudrender_close.js > ./cloudrender_core.js

touch index.html

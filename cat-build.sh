#!/usr/bin/env bash

cat init.js zlib.js png.js js_build/bin/cycles_test.js close.js > ./emcycles_core.js

js-beautify -f ./emcycles_core.js -o ./emcycles_core.js
sed -i 's/self.location.href/"dcp\/worker"/g' ./emcycles_core.js

#touch index.html

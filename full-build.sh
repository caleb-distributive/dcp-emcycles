#!/bin/bash

# rm -rf js_build

mkdir -p js_build

cd js_build && emconfigure cmake .. && make && cd .. && ./half-build.sh



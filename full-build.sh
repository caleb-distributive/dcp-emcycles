#!/bin/bash


rm -rf js_build && mkdir js_build && cd js_build && emconfigure cmake .. && make

../half-build.sh


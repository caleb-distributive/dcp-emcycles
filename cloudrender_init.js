
if (typeof Module !== 'undefined') var outerModule = Module

;(function (SCENE, INCLUDES) {

Module = outerModule || {}  // It's defined again, by emscripten code

Module.noInitialRun = true

Module.draw_out = Module.draw_out || function (mem, w, h, pix) {
    if (console && console.log) { console.log('draw_out!') }

    Module.imageData = [].slice.call(Module.HEAPU8.subarray(mem, mem + (w * h * 4)))

    if (typeof postMessage == 'function') {
        postMessage({
            image: Module.imageData,
            w: w,
            h: h,
            pix: pix
        });
    }
}

Module.TOTAL_MEMORY = 256 * 1024 * 1024 // 64mb


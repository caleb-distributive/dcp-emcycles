
var crypto = { getRandomValues: function(array) { for (var i = 0; i < array.length; i++) array[i] = (Math.random()*256)|0 } };



exports.render = async function (info, SCENE, INCLUDES, cb=()=>{}) {

  var Module = typeof info !== 'undefined'? info:  {}  // It's defined again, by emscripten code

  /*
  Module.tileH = 30
  Module.tileW = 40
  Module.tileY = 30
  Module.tileX = 40
  /*
  */
  
  Module.noInitialRun = true
  
  Module.draw_out = Module.draw_out || function (mem, w, h, pix) {
      // if (console && console.log) { console.log('draw_out!') }
  
      Module.imageData = [].slice.call(Module.HEAPU8.subarray(mem, mem + (w * h * 4)))
  
      // if (typeof postMessage == 'function') {
      //     postMessage({
      //         image: Module.imageData,
      //         w: w,
      //         h: h,
      //         pix: pix
      //     });
      // }

  }
  
  Module.INITIAL_MEMORY = 256 * 1024 * 1024 // 64mb

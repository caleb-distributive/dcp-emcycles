
(function () {

SCENE = 'elephant.xml'
INCLUDES = ['gumbo.xml']

Module = {
    noInitialRun: true,
    preInit: function () {
        var toDo = INCLUDES.length + 1
        function tryDone() {
            toDo--;
            if (!toDo) Module._main();
        }

        load(SCENE, function () {
            FS.writeFile('scene.xml', this.responseText)
            tryDone()
        })

        INCLUDES.forEach(function (include) {
            load(include, function () {
                FS.writeFile(include, this.responseText)
                tryDone()
            })
        })
    },

    draw_out: function (mem, w, h, pix) {
        Module.imageData = Module.HEAPU8.subarray(mem, mem + (w * h * 4));
        postMessage({
            image: Module.imageData,
            w: w,
            h: h,
            pix: pix
        });
    },

    TOTAL_MEMORY: 256 * 1024 * 1024 // 64mb
}

function load(url, cb) {
    var xhr = new XMLHttpRequest()
    xhr.onload = cb
    xhr.open('get', url, true)
    xhr.send()
}


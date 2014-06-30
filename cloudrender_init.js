
SCENE = 'elephant.xml'
INCLUDES = ['gumbo.xml']

Module = {
    noInitialRun: true,
    preInit: function () {
        var done = INCLUDES.length + 1

        load(SCENE, function () {
            console.log('writing scene.xml')
            FS.writeFile('scene.xml', this.responseText)
            done--
            if(!done) { Module._main() }
        })

        INCLUDES.forEach(function (include) {
            load(include, function () {
                console.log('writing', include)
                FS.writeFile(include, this.responseText)
                done--
                if (!done) { Module._main() }
            })
        })
    }
}

function load(url, cb) {
    var xhr = new XMLHttpRequest()
    xhr.onload = cb
    xhr.open('get', url, true)
    xhr.send()
}


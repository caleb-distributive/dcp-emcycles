
function load(url) {
    var xhr = new XMLHttpRequest()
    xhr.open('get', url, false)
    xhr.send()
    return xhr.responseText
}

if (/\.xml$/.test(SCENE)) {
    SCENE = load(SCENE)
}

FS.writeFile('scene.xml', SCENE)

INCLUDES.forEach(function (include) {
    FS.writeFile(include, load(include))
})

Module._main()

}(
typeof SCENE    === 'undefined' ? 'elephant.xml' : SCENE,
typeof INCLUDES === 'undefined' ? []  : INCLUDES
));

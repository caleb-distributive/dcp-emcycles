    
    return await new Promise(async (_resolve, _reject)=>{
        Module['onRuntimeInitialized'] = async function(){

            FS.writeFile('scene.xml', SCENE)

            INCLUDES.forEach(function (include) {
                FS.writeFile(include, include);
            })

            Module._main()

            while (typeof Module.imageData === 'undefined'){
                await new Promise((resolve, reject)=>{
                    setTimeout(resolve, 100);
                    cb();
                })
            }
            _resolve(Module.imageData);
        };
    });
};

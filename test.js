fs = require('fs');


var SCENE = fs.readFileSync('./elephant.xml').toString('utf8');


async function main(){
    var cycles = require('./emcycles_core');

    var info = {
        tileH: 30,
        tileW: 40,
        tileY: 0,
        tileX: 0
    }

    i = 0;
    
    let data = await cycles.render(
        info,
        SCENE,
        [],
        ()=>{console.log(i);i++},
    ); 
    console.log(render); 
    console.log( typeof data );
    data = Uint8Array.from(data);

    console.log(data.length);
}



main().then(()=>{console.log("DONE")});

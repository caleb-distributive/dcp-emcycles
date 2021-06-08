const process = require('process');
const fs = require('fs');
const { resolve } = require('path');
const SCENE = fs.readFileSync('./elephant.xml').toString('utf8');
const IMAGE_WIDTH = 640;
const IMAGE_HEIGHT = 480;
var job;
const SCHEDULER = 'https://scheduler-v3.distributed.computer'

async function main(){
  
  process.argv.push('--scheduler', SCHEDULER)
  await require('dcp-client').init(process.argv);

  const compute = require('dcp/compute');
  const wallet = require('dcp/wallet');
  const dcpCli = require('dcp/dcp-cli');

  const argv = dcpCli.base([
    '\x1b[33mThis application is for testing.\x1b[37m'
  ].join('\n'))
    .options({
      numworker: {
        describe: 'number of workers',
        type: 'number',
        default: 1
      }
    })
    .argv;


  const numWorkers = argv.numworker;

  const identityKeystore = await dcpCli.getIdentityKeystore();
  wallet.addId(identityKeystore);

  const accountKeystore = await dcpCli.getAccountKeystore();

  console.log("Loaded Keystore");
  
  job = compute.for([...Array(numWorkers).keys()],async function(sim_id, SCENE){
    progress();
    var info = {
      tileH: 480,
      tileW: 640,
      tileY: 0,
      tileX: 0
    };
    let render = require('emcycles_core').render;
    let data = await render(
      info,
      SCENE,
      [],
      progress
    );
    progress();
    return data ;
  },[SCENE]);

  console.log('Deploying Job!');

  job.on('accepted', ()=>{
    console.log('Job accepted....');
  });

  job.on('status', (status)=>{
    console.log('Got a status update: ', status);
  });
  job.on('result', (value) =>{ 
    console.log("result- ", value.result.length);
  });

  job.on('error', (err)=>{
    console.log(err);
  });

  job.on('console', (Output) => {
    console.log(Output.message);
  });

  job.on('uncaughException', (Output) =>{
    console.log(Output);
  });
  
  job.on('ENOFUNDS', (err)=>{
    console.log("ENOFUNDS: ", err);
  });

  job.on('ENOPROGRESS', (err)=>{
    console.log("ENOPROGRESS: ", err);
  });

  job.public.name = 'DCP-emcycles';

  //job.requirements.environment.offscreenCanvas = false;

  job.requires('emcycles_dev_1/emcycles_core');
  let results = await job.exec( compute.marketValue, accountKeystore);
  console.log("Done!");

  const Jimp = require('jimp');
  let imgData = Uint8Array.from( results.values()[0] );
  let outImg  = [];
  for (let i = IMAGE_HEIGHT - 1; i >= 0; i--){
    let row = [];
    for (let j = IMAGE_WIDTH - 1; j >= 0; j--){
      let r = imgData[(i*IMAGE_WIDTH*4) + j*(4) + 0 ];
      let g = imgData[(i*IMAGE_WIDTH*4) + j*(4) + 1 ];
      let b = imgData[(i*IMAGE_WIDTH*4) + j*(4) + 2 ];
      let a = imgData[(i*IMAGE_WIDTH*4) + j*(4) + 3 ];
      if (typeof r === 'undefined'){
        continue;
      }
      let colour = Jimp.rgbaToInt(r, g, b, a);
      row.push( colour );
    }
    outImg.push( row );
  }

    new Jimp( IMAGE_WIDTH, IMAGE_HEIGHT, function(err, img) {
        if (err) throw err;
        outImg.forEach((row, y) => {
          row.forEach((colour, x) => {
            img.setPixelColor( colour, x, y );
          });
        });

        img.write('test.png', (err) => {
          if (err) throw err;
        });
      });
};

main();

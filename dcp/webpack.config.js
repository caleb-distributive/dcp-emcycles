const path = require('path');

module.exports = {
  entry: {
    emcycles_core: './emcycles_core.js',
  },
  output: {
      filename: '[name]' + '_bundled.js',
      path: path.resolve(__dirname,'dist'),
      libraryTarget: 'commonjs2',
  },
  resolve: {
    fallback: {
      'path': false,
      'fs': false
    },
  },
  target: 'webworker'
};

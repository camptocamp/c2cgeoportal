const webpackMerge = require('webpack-merge');
const apps = require('./webpack.apps.js');
const commons = require('ngeo/buildtools/webpack.commons');

let config = commons.config({
  cacheDirectory: '/build/hard-source-cache/[confighash]',
}, '/build/bable-loader-cache/');

const nodeEnv = process.env['NODE_ENV'] || 'development';
switch (nodeEnv) {
  case 'development':
    config = webpackMerge(config, require('ngeo/buildtools/webpack.dev'));
    break;
  case 'production':
    config = webpackMerge(config, require('ngeo/buildtools/webpack.prod')('/build/uglifyjs-plugin-cache/'));
    break;
  default:
    console.log(`The 'NODE_ENV' environment variable is set to an invalid value: ${process.env.NODE_ENV}.` );
    process.exit(2);
}

config = webpackMerge(config, apps);

module.exports = config;

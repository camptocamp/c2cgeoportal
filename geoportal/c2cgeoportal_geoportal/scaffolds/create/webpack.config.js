const webpackMerge = require('webpack-merge');
const commons = require('ngeo/buildtools/webpack.commons');

let config = commons.config;

const nodeEnv = process.env['NODE_ENV'] || 'development';
switch (nodeEnv) {
  case 'development':
    config = webpackMerge(config, require('ngeo/buildtools/webpack.dev'));
    break;
  case 'production':
    config = webpackMerge(config, require('ngeo/buildtools/webpack.prod'));
    break;
  default:
    console.log(`The 'NODE_ENV' environement variable is set to an invalid value: ${process.env.NODE_ENV}.` );
    process.exit(2);
}

config = webpackMerge(config, require('./webpack.apps.js'));

module.exports = config;

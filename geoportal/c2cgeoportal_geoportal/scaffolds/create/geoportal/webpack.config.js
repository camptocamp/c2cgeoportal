const {merge} = require('webpack-merge');
const apps = require('./webpack.apps.js');
const commons = require('./webpack.commons.js');

let config = commons();

const nodeEnv = process.env['NODE_ENV'] || 'development';
switch (nodeEnv) {
  case 'development':
    config = merge(config, require('ngeo/buildtools/webpack.dev')());
    break;
  case 'production':
    config = merge(config, require('ngeo/buildtools/webpack.prod')());
    break;
  default:
    console.log(`The 'NODE_ENV' environment variable is set to an invalid value: ${process.env.NODE_ENV}.`);
    process.exit(2);
}

config = merge(config, apps);

module.exports = config;

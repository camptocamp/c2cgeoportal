const path = require('path');
const ls = require('ngeo/buildtools/ls.js');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const plugins = [];
const entry = {};

// The dev mode will be used for builds on local machine outside docker
const nodeEnv = process.env['NODE_ENV'] || 'development';
const dev = nodeEnv == 'development';

for (const filename of ls(
  path.resolve(__dirname, '{{cookiecutter.package}}_geoportal/static-ngeo/js/apps/*.html.ejs')
)) {
  const name = filename.file.substr(0, filename.file.length - '.html.ejs'.length);
  entry[name] = '{{cookiecutter.package}}/apps/Controller' + name + '.js';
  plugins.push(
    new HtmlWebpackPlugin({
      template: filename.full,
      inject: false,
      chunksSortMode: 'manual',
      filename: name + '.html',
      chunks: [name],
      vars: {
        entry_point: '${VISIBLE_ENTRY_POINT}',
        version: '{{cookiecutter.geomapfish_version}}',
        cache_version: '${CACHE_VERSION}',
      },
    })
  );
}

const noDevServer = process.env['NO_DEV_SERVER'] == 'TRUE';
const devServer = dev && !noDevServer;

console.log('Use dev mode: ' + dev);
console.log('Use dev server mode: ' + devServer);

module.exports = {
  output: {
    path: '/etc/static-ngeo/',
    publicPath: devServer ? '${VISIBLE_ENTRY_POINT}dev/' : '.__ENTRY_POINT__static-ngeo/',
  },
  devServer: {
    publicPath: '${VISIBLE_WEB_PROTOCOL}://${VISIBLE_WEB_HOST}${VISIBLE_ENTRY_POINT}dev/',
    port: 8080,
    host: 'webpack_dev_server',
    hot: true,
  },
  entry: entry,
  plugins: plugins,
  resolve: {
    modules: ['/opt/c2cgeoportal/geoportal/node_modules/'],
    alias: {
      '{{cookiecutter.package}}': path.resolve(
        __dirname,
        '{{cookiecutter.package}}_geoportal/static-ngeo/js'
      ),
      ngeo: '/opt/c2cgeoportal/geoportal/node_modules/ngeo/distlib/src',
      gmf: '/opt/c2cgeoportal/geoportal/node_modules/ngeo/distlib/src',
      gmfapi: '/opt/c2cgeoportal/geoportal/node_modules/ngeo/distlib/srcapi',
    },
  },
};

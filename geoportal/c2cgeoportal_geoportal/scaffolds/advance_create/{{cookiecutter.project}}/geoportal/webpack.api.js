const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');

const destDir = '/etc/static-ngeo/';

module.exports = (env, argv) => {
  const library = argv.library ? argv.library : '{{cookiecutter.package}}';
  return {
    entry: path.resolve(__dirname, '{{cookiecutter.package}}_geoportal/static-ngeo/api/index.js'),
    devtool: 'source-map',
    mode: 'production',
    output: {
      filename: 'api.js',
      path: destDir,
      libraryTarget: 'umd',
      globalObject: 'this',
      libraryExport: 'default',
      library: library,
    },
    optimization: {
      minimizer: [
        new TerserPlugin({
          parallel: true,
          terserOptions: {
            compress: false,
          },
        }),
      ],
    },
    resolve: {
      modules: ['/opt/c2cgeoportal/geoportal/node_modules'],
      alias: {
        api: '/opt/c2cgeoportal/geoportal/node_modules/ngeo/distlib/api/src',
        ngeo: '/opt/c2cgeoportal/geoportal/node_modules/ngeo/distlib/src',
      },
    },
    resolveLoader: {
      modules: ['/usr/lib/node_modules'],
    },
  };
};

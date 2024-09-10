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
          sourceMap: true,
          terserOptions: {
            compress: false,
          },
        }),
      ],
    },
    resolve: {
      modules: [
        '/usr/lib/node_modules',
        '/usr/lib/node_modules/ol/node_modules',
        '/usr/lib/node_modules/proj4/node_modules',
      ],
      alias: {
        api: '/usr/lib/node_modules/ngeo/api/src',
        ngeo: '/usr/lib/node_modules/ngeo/src',
      },
    },
    resolveLoader: {
      modules: ['/usr/lib/node_modules'],
    },
  };
};

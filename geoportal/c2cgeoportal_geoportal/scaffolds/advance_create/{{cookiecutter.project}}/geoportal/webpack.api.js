const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');

const destDir = '/etc/static-ngeo/';

const babelPresets = [
  [
    require.resolve('@babel/preset-env'),
    {
      targets: {
        browsers: ['> 0.7% in CH', '> 0.7% in FR', 'Firefox ESR'],
      },
      modules: false,
      loose: true,
    },
  ],
];

module.exports = (env, argv) => {
  const library = argv.library ? argv.library : '{{cookiecutter.package}}';
  return {
    entry: path.resolve(__dirname, '{{cookiecutter.package}}_geoportal/static-ngeo/api/index.js'),
    devtool: 'source-map',
    mode: 'production',
    module: {
      rules: [
        {
          test: /\.js$/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: babelPresets,
              babelrc: false,
              comments: false,
              plugins: [require.resolve('babel-plugin-angularjs-annotate')],
            },
          },
        },
      ],
    },
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

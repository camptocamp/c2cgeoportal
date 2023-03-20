const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = {
  entry: {
    vendor: ['/tmp/deps.js'],
  },
  output: {
    path: '/opt/',
    filename: '[name].js',
    library: '[name]_[hash]',
  },
  module: {
    rules: [
      {
        test: /.*\.js$/,
        use: {
          loader: 'babel-loader',
          options: {
            babelrc: false,
            comments: false,
            presets: [
              [
                require.resolve('@babel/preset-env'),
                {
                  targets: {
                    browsers: ['last 2 versions', 'Firefox ESR', 'ie 11'],
                  },
                  modules: false,
                  loose: true,
                },
              ],
            ],
          },
        },
      },
    ],
  },
  plugins: [
    new webpack.DllPlugin({
      path: '/opt/vendor-manifest.json',
      name: '[name]_[hash]',
      context: '/usr/lib/node_modules/',
    }),
    new webpack.SourceMapDevToolPlugin({
      filename: '[file].map',
    }),
    new webpack.ProvidePlugin({
      // Make sure that Angular finds jQuery and does not fall back to jqLite
      // See https://github.com/webpack/webpack/issues/582
      'window.jQuery': 'jquery',
      // For Bootstrap
      jQuery: 'jquery',
      // For own scripts
      $: 'jquery',
    }),
  ],
  resolveLoader: {
    modules: ['/usr/lib/node_modules'],
  },
  resolve: {
    modules: ['/usr/lib/node_modules', '/usr/lib/node_modules/d3/node_modules'],
    alias: {
      jsts: 'jsts/org/locationtech/jts',
      olcs: 'ol-cesium/src/olcs',
      'jquery-ui/datepicker': 'jquery-ui/ui/widgets/datepicker', // For angular-ui-date
      proj4: 'proj4/lib',
      rbush: 'ol/node_modules/rbush',
      quickselect: '/usr/lib/node_modules/ol/node_modules/quickselect',
      mgrs: '/usr/lib/node_modules/proj4/node_modules/mgrs',
      'wkt-parser': '/usr/lib/node_modules/proj4/node_modules/wkt-parser',
      lie: '/usr/lib/node_modules/localforage/node_modules/lie',
      immediate: '/usr/lib/node_modules/localforage/node_modules/immediate',
    },
  },
  optimization: {
    minimizer: [
      new TerserPlugin({
        parallel: true,
        sourceMap: true,
      }),
    ],
  },
};

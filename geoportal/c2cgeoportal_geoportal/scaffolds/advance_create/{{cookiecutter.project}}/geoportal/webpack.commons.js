const commons = require('ngeo/buildtools/webpack.commons.js');

const config = commons({
  DllReferencePluginOptions: {
    context: '/usr/lib/',
  },
  browsers: 'defaults, > 0.1% in CH, > 0.1% in FR, Firefox ESR and supports es6-class and not iOS < 10',
});

module.exports = () => config;

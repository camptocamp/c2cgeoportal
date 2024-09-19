const commons = require('ngeo/buildtools/webpack.commons.js');

const config = commons({
  DllReferencePluginOptions: {
    context: '/usr/lib/',
  },
  noTs: true,
});

module.exports = () => config;

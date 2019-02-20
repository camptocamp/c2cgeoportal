const commons = require('ngeo/buildtools/webpack.commons.js');
const SassPlugin = require('ngeo/buildtools/webpack.plugin.js');

const config = commons.config({
  cacheDirectory: '/build/hard-source-cache/[confighash]',
}, '/build/bable-loader-cache/');

for (const plugin of config.plugins) {
  if (plugin instanceof SassPlugin) {
    plugin.options.preReplacements = [
      [new RegExp('\\${VISIBLE_ENTRY_POINT}', 'g'), 'visible-entry-point'],
    ];
    plugin.options.postReplacements = [
      [new RegExp('visible-entry-point', 'g'), '${VISIBLE_ENTRY_POINT}'],
    ];
  }
}

module.exports = {
  config,
};

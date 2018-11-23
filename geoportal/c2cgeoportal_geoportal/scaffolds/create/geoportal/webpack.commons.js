'use strict';

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

for (const rule of config.module.rules) {
  if (rule.use.loader === 'babel-loader') {
    const plugins = [];
    for (const plugin of rule.use.options.plugins) {
      plugins.push(require.resolve(plugin));
    }
    rule.use.options.plugins = plugins;
    const presets = [];
    for (const preset of rule.use.options.presets) {
      presets.push([require.resolve(preset[0]), preset[1]]);
    }
    rule.use.options.presets = presets;
  }
}

module.exports = {
  config,
};

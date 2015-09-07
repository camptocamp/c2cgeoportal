/**
 * @fileoverview This file provides the "app" namespace, which is the
 * application's main namespace. And it defines the application's Angular
 * module.
 */
goog.provide('app');

/**
 * This goog.require is needed because gmfModule.name is defined in 'gmf'.
 * @suppress {extraRequire}
 */
goog.require('gmf');


/**
 * @type {!angular.Module}
 */
app.module = angular.module('app', [gmfModule.name, 'gettext']);

/**
 * @fileoverview This file provides the "app" namespace, which is the
 * application's main namespace. And it defines the application's Angular
 * module.
 */
goog.provide('app');

goog.require('ngeo');


/**
 * @type {!angular.Module}
 */
app.module = angular.module('app', [ngeoModule.name, 'gettext']);

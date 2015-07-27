/**
 * @fileoverview This file defines the controller class for the application's
 * main controller (created using "ng-controller" in the page).
 *
 * In particular, this controller creates the OpenLayers map, and makes it
 * available in the controller for use from other parts (directives) of the
 * application. It also defines the behavior of elements of the HTML page.
 */
goog.provide('app.MainController');



/**
 * @constructor
 * @export
 * @ngInject
 */
app.MainController = function() {

  /**
   * @type {string}
   * @export
   */
  this.lang;

  /**
   * @type {ol.Map}
   * @export
   */
  this.map;
};
app.module.controller('MainController', app.MainController);

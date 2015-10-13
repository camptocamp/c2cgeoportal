/**
 * @fileoverview This file defines the controller class for the application's
 * mobile controller (created using "ng-controller" in the page).
 *
 * In particular, this controller creates the OpenLayers map, and makes it
 * available in the controller for use from other parts (directives) of the
 * application. It also defines the behavior of elements of the HTML page.
 */
goog.provide('app.MobileController');

goog.require('app');
goog.require('ol.Map');
goog.require('ol.View');
goog.require('ol.layer.Tile');
goog.require('ol.source.OSM');


/**
 * @constructor
 * @export
 * @ngInject
 */
app.MobileController = function() {

  /**
   * @type {string}
   * @export
   */
  this.lang;

  /**
   * @type {ol.Map}
   * @export
   */
  this.map = new ol.Map({
    layers: [
      new ol.layer.Tile({
        source: new ol.source.OSM()
      })
    ],
    view: new ol.View({
      center: [0, 0],
      zoom: 4
    })
  });
};
app.module.controller('MobileController', app.MobileController);

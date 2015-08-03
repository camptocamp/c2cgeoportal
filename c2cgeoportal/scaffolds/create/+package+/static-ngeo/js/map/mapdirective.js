/**
 * @fileoverview This file provides the "map" directive.
 *
 * Example:
 *
 * <app-map app-map-map="::mainCtrl.map"><app-map>
 */
goog.provide('app.mapDirective');

goog.require('app');
goog.require('goog.asserts');
goog.require('ngeo.mapDirective');
goog.require('ngeo.Debounce');
goog.require('ngeo.Location');


/**
 * @return {angular.Directive} The Directive Definition Object.
 * @ngInject
 */
app.mapDirective = function() {
  return {
    scope: {
      'map': '=appMapMap'
    },
    bindToController: true,
    controller: 'AppMapController',
    controllerAs: 'ctrl',
    templateUrl: 'map/map.html'
  };
};
app.module.directive('appMap', app.mapDirective);



/**
 * @param {ngeo.Location} ngeoLocation ngeo Location service.
 * @param {ngeo.Debounce} ngeoDebounce ngeo Debounce service.
 * @constructor
 * @ngInject
 */
app.MapController = function(ngeoLocation, ngeoDebounce) {

  /**
   * @type {!ol.Map}
   */
  var map = this['map'];
  goog.asserts.assert(goog.isDef(map));
  var view = map.getView();

  var x = ngeoLocation.getParam('map_x');
  var y = ngeoLocation.getParam('map_y');
  var zoom = ngeoLocation.getParam('map_zoom');

  if (goog.isDef(x) && goog.isDef(y)) {
    view.setCenter([+x, +y]);
  }
  if (goog.isDef(zoom)) {
    view.setZoom(+zoom);
  }

  view.on('propertychange', ngeoDebounce(function() {
    var center = view.getCenter();
    var zoom = view.getZoom();
    ngeoLocation.updateParams({
      'map_zoom': zoom,
      'map_x': Math.round(center[0]),
      'map_y': Math.round(center[1])
    });
  }, 300, /* invokeApply */ true));

};
app.module.controller('AppMapController', app.MapController);

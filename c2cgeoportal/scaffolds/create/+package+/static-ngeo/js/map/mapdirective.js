/**
 * @fileoverview This file provides the "map" directive.
 *
 * Example:
 *
 * <app-map app-map-map="::mainCtrl.map"><app-map>
 */
goog.provide('app.mapDirective');

goog.require('app');


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
 * @constructor
 * @ngInject
 */
app.MapController = function() {


};
app.module.controller('AppMapController', app.MapController);

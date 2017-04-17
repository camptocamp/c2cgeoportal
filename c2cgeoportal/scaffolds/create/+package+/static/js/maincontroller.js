goog.provide('app.MainController');

goog.require('app');
goog.require('ol.Map');


/**
 * @param {angular.Scope} $scope Scope.
 * @constructor
 * @export
 * @ngInject
 */
app.MainController = function($scope) {

  /**
   * @private
   */
  this.scope_ = $scope;

  /**
   * @type {ol.Map}
   * @export
   */
  this.map = null;

  /**
   * @type {string|undefined}
   * @export
   */
  this.lang = undefined;

};


/**
 * @private
 */
app.MainController.prototype.setMap_ = function() {
  // this.map = new ol.Map();
};


app.module.controller('MainController', app.MainController);

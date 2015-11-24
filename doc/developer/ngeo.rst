.. _developer_ngeo:

ngeo
====

--------------------------------------------
Integrate demo apps in c2cgeoportal scaffold
--------------------------------------------

Copy Files
----------

Copy the following files from ngeo:

 * ``contribs/gmf/apps/mobile/index.html``
 * ``contribs/gmf/apps/mobile/js/appmodule.js``
 * ``contribs/gmf/apps/mobile/js/mobile.js``

In the c2cgeoportal scaffold

 * ``c2cgeoportal/scaffolds/create/+package+/templates/mobile.html_tmpl``
 * ``c2cgeoportal/scaffolds/create/+package+/static-ngeo/js/appmodule.js_tmpl``
 * ``c2cgeoportal/scaffolds/create/+package+/static-ngeo/js/mobile.js_tmpl``

Some replacements
-----------------

* app => {{package}}
* nodes files path
* direct service URL => pyramid ``route_url``

In details:

.. code:: diff

   c2cgeoportal/scaffolds/create/+package+/static-ngeo/js/appmodule.js
   @@ -3,7 +3,7 @@
     * application's main namespace. And it defines the application's Angular
     * module.
     */
   -goog.provide('app');
   +goog.provide('{{package}}');

    goog.require('gmf');

   @@ -11,4 +11,4 @@ goog.require('gmf');
    /**
     * @type {!angular.Module}
     */
   -app.module = angular.module('app', [gmfModule.name]);
   +{{package}}.module = angular.module('{{package}}', [gmfModule.name]);


   c2cgeoportal/scaffolds/create/+package+/static-ngeo/js/mobile.js
   @@ -7,10 +7,10 @@
     * This file includes `goog.require`'s for all the components/directives used
     * by the HTML page and the controller to provide the configuration.
     */
   -goog.provide('app.MobileController');
   -goog.provide('app_mobile');
   +goog.provide('{{package}}.MobileController');
   +goog.provide('{{package}}_mobile');

   -goog.require('app');
   +goog.require('{{package}}');
    goog.require('gmf.mapDirective');
    goog.require('gmf.mobileNavDirective');
    goog.require('gmf.proj.EPSG21781');
   @@ -33,7 +33,7 @@ goog.require('ol.source.OSM');
     * @ngInject
     * @export
     */
   -app.MobileController = function(ngeoFeatureOverlayMgr, serverVars) {
   +{{package}}.MobileController = function(ngeoFeatureOverlayMgr, serverVars) {

      /**
       * @type {Array.<gmfx.SearchDirectiveDatasource>}
   @@ -88,7 +88,7 @@ app.MobileController = function(ngeoFeatureOverlayMgr, serverVars) {
    /**
     * @export
     */
   -app.MobileController.prototype.toggleLeftNavVisibility = function() {
   +{{package}}.MobileController.prototype.toggleLeftNavVisibility = function() {
      this.leftNavVisible = !this.leftNavVisible;
    };

   @@ -96,7 +96,7 @@ app.MobileController.prototype.toggleLeftNavVisibility = function() {
    /**
     * @export
     */
   -app.MobileController.prototype.toggleRightNavVisibility = function() {
   +{{package}}.MobileController.prototype.toggleRightNavVisibility = function() {
      this.rightNavVisible = !this.rightNavVisible;
    };

   @@ -105,7 +105,7 @@ app.MobileController.prototype.toggleRightNavVisibility = function() {
     * Hide both navigation menus.
     * @export
     */
   -app.MobileController.prototype.hideNav = function() {
   +{{package}}.MobileController.prototype.hideNav = function() {
      this.leftNavVisible = this.rightNavVisible = false;
    };

   @@ -115,7 +115,7 @@ app.MobileController.prototype.hideNav = function() {
     * otherwise false.
     * @export
     */
   -app.MobileController.prototype.navIsVisible = function() {
   +{{package}}.MobileController.prototype.navIsVisible = function() {
      return this.leftNavVisible || this.rightNavVisible;
    };

   @@ -125,7 +125,7 @@ app.MobileController.prototype.navIsVisible = function() {
     * otherwise false.
     * @export
     */
   -app.MobileController.prototype.leftNavIsVisible = function() {
   +{{package}}.MobileController.prototype.leftNavIsVisible = function() {
      return this.leftNavVisible;
    };

   @@ -135,9 +135,9 @@ app.MobileController.prototype.leftNavIsVisible = function() {
     * otherwise false.
     * @export
     */
   -app.MobileController.prototype.rightNavIsVisible = function() {
   +{{package}}.MobileController.prototype.rightNavIsVisible = function() {
      return this.rightNavVisible;
    };


   -app.module.controller('MobileController', app.MobileController);
   +{{package}}.module.controller('MobileController', {{package}}.MobileController);


   c2cgeoportal/scaffolds/create/+package+/templates/mobile.html_tmpl
   @@ -1,5 +1,5 @@
    <!DOCTYPE html>
   -<html lang="{{mobileCtrl.lang}}" ng-app="app" ng-controller="MobileController as mainCtrl">
   +<html lang="\{\{mobileCtrl.lang\}\}" ng-app="{{package}}" ng-controller="MobileController as mainCtrl">
      <head>
        <title>Mobile Application</title>
        <meta charset="utf-8">
        <meta name="viewport" content="initial-scale=1.0, user-scalable=no, width=device-width">
        <meta name="apple-mobile-web-app-capable" content="yes">
   -    <link rel="stylesheet" href="../../build/mobile.css" type="text/css">
   +% if debug:
   +    <link rel="stylesheet/less" href="${request.static_url('{{package}}:static-ngeo/less/mobile.less')}" type="text/css">
   +% else:
   +    <link rel="stylesheet" href="${request.static_url('{{package}}:static-ngeo/build/mobile.css')}" type="text/css">
   +% endif
        <style>
        #desc {
          display: none;
   @@ -91,15 +91,19 @@
          </div>
        </nav>
        <p id="desc">This example is a mobile application based on ngeo and gmf components.</p>
   -    <script src="../../../../node_modules/jquery/dist/jquery.js"></script>
   -    <script src="../../../../node_modules/angular/angular.js"></script>
   -    <script src="../../../../node_modules/typeahead.js/dist/typeahead.bundle.js"></script>
   -    <script src="http://cdnjs.cloudflare.com/ajax/libs/proj4js/2.2.1/proj4.js" type="text/javascript"></script>
   -    <script src="/@?main=mobile/js/mobile.js"></script>
   -    <script src="../../../../utils/watchwatchers.js"></script>
   +% if debug:
   +    <script src="${request.static_url('%s/jquery/dist/jquery.js' % node_modules_path)}"></script>
   +    <script src="${request.static_url('%s/angular/angular.js' % node_modules_path)}"></script>
   +    <script src="${request.static_url('%s/angular-gettext/dist/angular-gettext.js' % node_modules_path)}"></script>
   +    <script src="${request.static_url('%s/bootstrap/dist/js/bootstrap.js' % node_modules_path)}"></script>
   +    <script src="${request.static_url('%s/proj4/dist/proj4-src.js' % node_modules_path)}"></script>
   +    <script src="${request.static_url('%s/d3/d3.min.js' % node_modules_path)}"></script>
   +    <script src="${request.static_url('%s/typeahead.js/dist/typeahead.bundle.js' % node_modules_path)}"></script>
   +    <script src="${request.static_url('%s/closure/goog/base.js' % closure_library_path)}"></script>
   +    <script src="${request.route_url('deps.js')}"></script>
   +    <script src="${request.static_url('{{package}}:static-ngeo/js/mobile.js')}"></script>
   +    <script src="${request.static_url('{{package}}:static-ngeo/build/templatecache.js')}"></script>
   +    <script src="${request.static_url('%s/utils/watchwatchers.js' % closure_library_path)}"></script>
   +    <script src="${request.static_url('%s/less/dist/less.min.js' % node_modules_path)}"></script>
   +% else:
   +    <script src="${request.static_url('{{package}}:static-ngeo/js/mobile.js')}"></script>
   +% endif
        <script>
          (function() {
   -         var module = angular.module('app');
   +         var module = angular.module('{{package}}');
             var serverVars = {
               serviceUrls: {
   -             fulltextsearch: 'http://geomapfish-demo.camptocamp.net/2.0/wsgi/fulltextsearch?query=%QUERY'
   +             fulltextsearch: '${request.route_url('fulltextsearch', _query={'query':'%QUERY'}) | n}'
               }
             };
             module.constant('serverVars', serverVars);

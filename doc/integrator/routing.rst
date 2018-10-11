.. _integrator_routing:

Routing interface
=================

This section describes how to add the `OSRM routing <http://project-osrm.org/>`_ interface to a c2cgeoprtal application.


Requirements
------------
To add this feature, you need a `OSRM backend server <https://github.com/Project-OSRM/osrm-backend>`_ with version >= 5.8.


Adding the routing interface to the template
--------------------------------------------

For a working example, check the `alternative example desktop app <https://github.com/camptocamp/ngeo/blob/master/contribs/gmf/apps/desktop_alt/index.html>`_ of ngeo.


Add the button to the ``gmf-app-bar``::

  <button ngeo-btn class="btn btn-default" ng-model="mainCtrl.routingfeatureActive"
          data-toggle="tooltip" data-placement="left" data-original-title="{{'Routing'|translate}}">
    <span class="fa fa-map-signs"></span>
  </button>


Then, add the routing component to the ``gmf-app-tools-content`` area::

    <div ng-show="mainCtrl.routingfeatureActive" class="row">
      <div class="col-sm-12">
        <div class="gmf-app-tools-content-heading">
          {{'Routing'|translate}}
          <a class="btn close" ng-click="mainCtrl.routingfeatureActive = false">&times;</a>
        </div>
        <ngeo-routing ngeo-routing-map="mainCtrl.map">
        </ngeo-routing>
      </div>
    </div>

`mainCtrl.routingfeatureActive` and `mainCtrl.map` are part of `gmf.AbstractDesktopController` and do not need to be defined in your interface controller, as long as it extends AbstractDesktopController.


Configuration
-------------

In the same interface template where the button and the component were added, the `ngeoRoutingOptions` and `ngeoNominatimSearchDefaultParams` can be defined. Example::

    var module = angular.module('app');
    module.constant('ngeoRoutingOptions', {
      'backendUrl': 'http://routing.osm.ch/',
      'profiles': [
        {label : 'Car', profile: 'routed-car'},
        {label : 'Bike (City)', profile: 'routed-bike'}
      ]
    });

    module.constant('ngeoNominatimSearchDefaultParams', {
        'countrycodes': 'CH'
    });

backendUrl
^^^^^^^^^^
required, string
URL to an `OSRM backend server instance <https://github.com/Project-OSRM/osrm-backend>`_ with version >= 5.8


profiles
^^^^^^^^
not required, ngeox.RoutingProfile

label: string, label to display in the drop-down-menu for the profile

profile: string, url-path of the profile, example::

    http://routing.osm.ch/routed-bike/route/v1/car/<params>
        ^                |     ^     |    ^
        '                |     '     |    '
    backendUrl           |  profile  | osrm query

If more than one profile are supplied, the component will show a drop-down-menu for the user to select a profile.


ngeoNominatimSearchDefaultParams
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
not required, dictionary of string-parameters

Configures the nominatim search, which is used to search for addresses and features in the routing search fields.
Check the  OpenStreetMap wiki for a `list of all available parameters <https://wiki.openstreetmap.org/wiki/Nominatim#Parameters>`_.

In the example, ``'countrycodes': 'CH'`` restricts the search to Switzerland.

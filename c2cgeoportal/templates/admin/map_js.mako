/**
 * Class: DeleteFeatureControl
 * Control to delete features. It is supposed to be used together
 *      with a <OpenLayers.Control.ModifyFeature> control, which
 *      must be set in the constructor.
 *      The control is activated when a feature is selected with
 *      the <OpenLayers.Control.ModifyFeature> control. Then
 *      a click on the DeleteFeature control deletes the feature.
 *
 * Inherits From:
 *  - <OpenLayers.Control>
 */
DeleteFeatureControl = OpenLayers.Class(OpenLayers.Control, {

    /**
     * Property: type
     * {String} The type of <OpenLayers.Control> -- When added to a
     *     <Control.Panel>, 'type' is used by the panel to determine how to
     *     handle our events.
     */
    type: OpenLayers.Control.TYPE_BUTTON,

    /**
     * Constructor: DeleteFeatureControl
     * Creates a new delete feature control.
     *
     * Parameters:
     * modifyFeatureControl - {<OpenLayers.Control.ModifyFeature>} ModifyFeature control that
     *     is used to select features.
     * options - {Object} Optional object whose properties will be set on the
     *     control.
     */
    initialize: function (modifyFeatureControl, options) {
        this.modifyFeatureControl = modifyFeatureControl;

        modifyFeatureControl.layer.events.register("beforefeaturemodified",
                this, this.handleFeatureSelected);
        modifyFeatureControl.layer.events.register("afterfeaturemodified",
                this, this.handleFeatureUnSelected);

        OpenLayers.Control.prototype.initialize.apply(this, [options]);
    },

    /**
     * Method: handleFeatureSelected
     * Called before a feature is selected with the ModifyFeature control. Activates
     *      the control by changing the 'displayClass' of the DIV.
     */
    handleFeatureSelected : function () {
        this.panel_div.className = this.displayClass + 'ItemActive';
    },

    /**
     * Method: handleFeatureUnSelected
     * Called when a feature is unselected with the ModifyFeature control. Deactivates
     *      the control by changing the 'displayClass' of the DIV.
     */
    handleFeatureUnSelected : function() {
        this.panel_div.className = this.displayClass + 'ItemInactive';
    },

    /**
     * Method: trigger
     * Called when the control is clicked. Deletes the selected
     *      feature.
     */
    trigger: function () {
        if (this.modifyFeatureControl.feature && confirm(OpenLayers.i18n('confirm delete feature'))) {
            var layer = this.modifyFeatureControl.layer;
            var feature = this.modifyFeatureControl.feature;

            var continueRemoving = layer.events.triggerEvent("beforefeatureremoved",
                    {feature: feature});

            if (continueRemoving === false) {
                return;
            }

            layer.removeFeatures([feature], {silent: true});
            feature.state = OpenLayers.State.DELETE;
            layer.events.triggerEvent("featureremoved",
                            {feature: feature});
            this.modifyFeatureControl.unselectFeature(feature);
        }
    },

    CLASS_NAME: "DeleteFeatureControl"
});

var geoformalchemy = {};

geoformalchemy.getRestriction = function (field_name) {
  /* the list of field which are restricted to rectangle */
  var rectangleRestrictedField = ['Role'];

  for (var i=0; i<=rectangleRestrictedField.length; i++) {
      if (field_name.indexOf(rectangleRestrictedField[i]) > -1) {
          return true
      }
  }
  return false;
};

geoformalchemy.init_map = function (
        field_name,
        read_only,
        is_collection,
        geometry_type,
        lon,
        lat,
        zoom,
        base_layer,
        wkt
                           ) {
    var map, layer, vlayer, panelControls;
    var geometry_field = document.getElementById(field_name);
    var wkt_parser = new OpenLayers.Format.WKT();

    layer = base_layer;
    vlayer = new OpenLayers.Layer.Vector("Geometries");

    var restrictRectangle = geoformalchemy.getRestriction(field_name)

    if (read_only) {
        // in read-mode, only show navigation control
        panelControls = [new OpenLayers.Control.Navigation()];
    } else {
        /**
         * When the geometry of a feature changes, then the WKT string of
         * this feature has to be written to a input field. So that
         * when the form is submitted, the data can be read from this
         * input field.
         */
        var update_geometry_field = function (feature) {
            var wkt = null;
            if (feature === null ||
                    ((feature instanceof Array) && (feature.length <= 0))) {
                wkt = '';
            } else {
                wkt = wkt_parser.write(feature);
            }
            geometry_field.value = wkt;
        };

        /**
         * Creates an array containing all features of
         * the vector layer. OpenLayers can not create
         * WKT string from a GeometryCollection, so that is
         * why we are constructing an array of Geometries.
         */
        var get_feature_collection = function () {
            var collection_feature = [];
            for (var i = 0; i < vlayer.features.length; i++) {
                collection_feature.push(vlayer.features[i]);
            }
            return collection_feature;
        };

        /**
         * When a features is modified, update the geometry field.
         */
        var feature_modified_handler = function (event) {
            update_feature(event.feature);
        };

        var update_feature = function (feature) {
            var features = null;
            if (is_collection) {
                features = get_feature_collection();
            } else {
                if (feature.state !== OpenLayers.State.DELETE) {
                    features = feature;
                }
            }
            update_geometry_field(features);
        };

        /**
         * When a features is added, update the geometry field. If the geometry
         * type is 'Collection', construct an array of the already existing
         * features and add the new feature to this array.
         */
        var before_feature_added_handler = function (event) {
            if (is_collection) {
                var collection_feature = get_feature_collection();
                //collection_feature.push(event.feature);

                update_geometry_field(collection_feature);

                return true;
            } else if (vlayer.features.length > 0) {
                // remove old feature(s)
                vlayer.destroyFeatures();
            }

            update_geometry_field(event.feature);

            return true;
        };

        vlayer.events.on({"featuremodified": feature_modified_handler});
        vlayer.events.on({"beforefeatureadded": before_feature_added_handler});
        vlayer.events.on({"afterfeaturemodified": feature_modified_handler});
        vlayer.events.on({"sketchcomplete": feature_modified_handler});

        panelControls = [new OpenLayers.Control.Navigation()];

        if (geometry_type === 'Polygon' || geometry_type === 'Collection') {
            if (restrictRectangle == false) {
                panelControls.push(new OpenLayers.Control.DrawFeature(vlayer,
                         OpenLayers.Handler.Polygon,
                         {
                             'displayClass': 'olControlDrawFeaturePolygon',
                             'handlerOptions': {'holeModifier': 'ctrlKey'}
                         }));
            } else {
                panelControls.push(new OpenLayers.Control.DrawFeature(vlayer,
                         OpenLayers.Handler.RegularPolygon,
                         {'displayClass': 'olControlDrawFeaturePolygon',
                          handlerOptions: {sides: 4, irregular: true}}));
                }
            }

        if (geometry_type === 'Point' || geometry_type === 'Collection') {
            panelControls.push(new OpenLayers.Control.DrawFeature(vlayer,
                     OpenLayers.Handler.Point,
                     {'displayClass': 'olControlDrawFeaturePoint'}));
        }



        if (geometry_type === 'Path' || geometry_type === 'Collection') {
            panelControls.push(new OpenLayers.Control.DrawFeature(vlayer,
                     OpenLayers.Handler.Path,
                     {'displayClass': 'olControlDrawFeaturePath'}));
        }

        if ((geometry_type === 'Polygon' || geometry_type === 'Collection') &&
            restrictRectangle) {
            var controlModifyFeature = new OpenLayers.Control.ModifyFeature(vlayer,
                    {'displayClass': 'olControlModifyFeature',
                     mode: OpenLayers.Control.ModifyFeature.RESHAPE | OpenLayers.Control.ModifyFeature.RESIZE});
        } else {
            var controlModifyFeature = new OpenLayers.Control.ModifyFeature(vlayer,
                    {'displayClass': 'olControlModifyFeature'});
        }

        var controlDeleteFeature = new DeleteFeatureControl(controlModifyFeature,
                {'displayClass': "olControlDeleteFeature"});

        var controlDragFeature = new OpenLayers.Control.DragFeature(vlayer,
                {'displayClass': 'olControlDragFeature',
                 onComplete: function(f, p) {update_feature(f);}})


        panelControls.push(controlDeleteFeature);
        panelControls.push(controlModifyFeature);
        panelControls.push(controlDragFeature);
    }

    map = new OpenLayers.Map('map_' + field_name, {theme: null});

    $('#map_' + field_name).resizable({
        stop: function(event, ui) {
            map.updateSize();
        }
    });

    var toolbar = new OpenLayers.Control.Panel({
        displayClass: 'olControlEditingToolbar',
        defaultControl: panelControls[0]
    });
    toolbar.addControls(panelControls);
    map.addControl(toolbar);

    map.addLayers([layer, vlayer]);

    // try to get the geometry
    if (wkt !== '') {
        var features = wkt_parser.read(wkt);
        if (!(features instanceof Array)) {
            features = [features];
        }
        vlayer.addFeatures(features, {'silent': true});

        /* OpenLayers creates an array of features when the WKT string
         * represents a GeometryCollection. To get the centroid of all
         * features, we have to create a 'real' GeometryCollection.
         */
        var geometry_collection = new OpenLayers.Geometry.Collection();
        for (var i = 0; i < features.length; i++) {
            geometry_collection.addComponents(features[i].geometry);
        }
        var centroid = geometry_collection.getCentroid();

        map.setCenter(new OpenLayers.LonLat(centroid.x, centroid.y), zoom);
    } else {
        map.setCenter(new OpenLayers.LonLat(lon, lat), zoom);
    }
};

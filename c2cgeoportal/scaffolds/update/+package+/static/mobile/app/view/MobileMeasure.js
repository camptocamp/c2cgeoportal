Ext.ns('App.view');
App.view.MobileMeasure = OpenLayers.Class(OpenLayers.Control, {

    button: null,

    /**
     * Property: helpMessageEl
     * {DOMElement}
     */
    helpMessageEl: null,

    /**
     * Property: addPointButton
     * {DOMElement}
     */
    addPointButton: null,

    /**
     * Property: finishButton
     * {DOMElement}
     */
    finishButton: null,

    /**
     * Property: newMeasureButton
     * {DOMElement}
     */
    newMeasureButton: null,

    /**
     * Property: layer
     * {OpenLayers.Layer.Vector}
     */
    layer: null,

    /**
     * Property: origin
     * {OpenLayers.Geometry.Point} First point
     */
    origin: null,

    /**
     * Property: target
     * {OpenLayers.Geometry.Point} End point
     */
    target: null,

    autoActivate: false,

    /**
     * APIProperty: displaySystem
     * {String} Display system for output measurements.  Supported values
     *     are 'english', 'metric', and 'geographic'.  Default is 'metric'.
     */
    displaySystem: 'metric',

    /**
     * Property: displaySystemUnits
     * {Object} Units for various measurement systems.  Values are arrays
     *     of unit abbreviations (from OpenLayers.INCHES_PER_UNIT) in decreasing
     *     order of length.
     */
    displaySystemUnits: {
        geographic: ['dd'],
        english: ['mi', 'ft', 'in'],
        metric: ['km', 'm']
    },

    /**
     * Constructor: MobileMeasure
     *
     * Parameters:
     * options - {Object}
     */
    initialize: function(options) {
        OpenLayers.Control.prototype.initialize.apply(this, [options]);

        this.layer = new OpenLayers.Layer.Vector(this.CLASS_NAME, {
            displayInLayerSwitcher: false,
            calculateInRange: OpenLayers.Function.True,
            styleMap: new OpenLayers.StyleMap({
                'default': OpenLayers.Util.applyDefaults({
                    strokeColor: 'red',
                    graphicName: 'cross',
                    label: "${label}",
                    fontColor: 'red',
                    labelAlign: "lt",
                    labelXOffset: 10,
                    labelYOffset: -10
                }, OpenLayers.Feature.Vector.style['default'])
            })
        });

    },

    draw: function() {
        var div = OpenLayers.Control.prototype.draw.apply(this);

        var measure = document.createElement("a");
        measure.id = "mobileMeasure";
        div.appendChild(measure);
        OpenLayers.Element.addClass(measure, "olButton");
        this.button = measure;

        this.eventsInstance = this.map.events;
        this.eventsInstance.register("buttonclick", this, this.onClick);

        this.helpMessageEl = document.createElement('div');
        this.helpMessageEl.id = 'mobileMeasureHelp';
        this.helpMessageEl.style.display = 'none';
        div.appendChild(this.helpMessageEl);
        return div;
    },

    /**
     * Method: onClick
     * Called when any element with 'olButton' class is clicked.
     *
     * Parameters:
     * evt - {OpenLayers.Event}
     */
    onClick: function(evt) {
        var button = evt.buttonElement;
        switch (button) {
            case this.button:
                if (this.active) {
                    this.deactivate();
                } else {
                    this.activate();
                }
                break;
            case this.addPointButton:
                button.parentNode.removeChild(button);
                this.addFirstPoint();
                break;
            case this.newMeasureButton:
                button.parentNode.removeChild(button);
                this.deactivate();
                this.activate();
                break;
            case this.finishButton:
                button.parentNode.removeChild(button);
                this.map.events.unregister('move', this, this.measure);
                this.helpMessageEl.style.display = 'none';
                break;
        }
    },

    /**
     * Method: showCenter
     * Display target at the center of the screen.
     */
    showCenter: function() {
        var target = document.createElement('div');
        target.id = 'centerCross';
        target.innerHTML = '+';
        this.map.getViewport().appendChild(target);
    },

    /**
     * Method: hideCenter
     * Removes the center target.
     */
    hideCenter: function() {
        var el = document.getElementById("centerCross");
        el && el.parentNode.removeChild(el);
    },

    /**
     * Method: activate
     * Remove any button or message but the control initial button.
     */
    deactivate: function() {
        OpenLayers.Element.removeClass(this.button, 'active');
        this.hideCenter();
        this.active = false;

        this.helpMessageEl.style.display = "none";
        this.addPointButton && this.addPointButton.parentNode && this.addPointButton.parentNode.removeChild(this.addPointButton);
        this.finishButton && this.finishButton.parentNode && this.finishButton.parentNode.removeChild(this.finishButton);
        this.newMeasureButton && this.newMeasureButton.parentNode && this.newMeasureButton.parentNode.removeChild(this.newMeasureButton);

        this.map.removeLayer(this.layer);
        this.map.events.unregister('move', this, this.measure);

        this.layer.removeFeatures(this.layer.features);
        this.origin = null;
        this.line = null;
        this.target = null;
    },

    /**
     * Method: activate
     * Show target on the map and invite user to add first point.
     */
    activate: function() {
        this.showCenter();

        OpenLayers.Element.addClass(this.button, 'active');

        var addPoint = document.createElement('div');
        this.div.appendChild(addPoint);
        OpenLayers.Element.addClass(addPoint, 'olButton');
        addPoint.id = 'addPointButton';

        var msg = this.helpMessageEl;
        msg.innerHTML = OpenLayers.i18n("Move the map to locate starting point");
        msg.style.display = '';

        // hide message as soon as map has moved
        var map = this.map;

        function hide() {
            msg.style.display = 'none';
            map.events.unregister('move', null, hide);
        }
        map.events.register('move', null, hide);

        var button = document.createElement('a');
        button.innerHTML = OpenLayers.i18n('Set starting point');
        addPoint.appendChild(button);
        this.addPointButton = addPoint;

        this.active = true;

        this.map.addLayer(this.layer);
    },

    /**
     * Method: addFirstPoint
     * Adds the first point and waits for map to be panned.
     */
    addFirstPoint: function() {
        this.hideCenter();

        var center = this.map.getCenter();
        this.origin = new OpenLayers.Feature.Vector(
        new OpenLayers.Geometry.Point(center.lon, center.lat), {
            label: ''
        });
        this.layer.addFeatures(this.origin);
        this.map.events.register('move', this, this.measure);

        var div = document.createElement('div');
        this.div.appendChild(div);
        OpenLayers.Element.addClass(div, 'olButton');
        div.id = 'newMeasureButton';

        var button = document.createElement('a');
        div.appendChild(button);
        this.newMeasureButton = div;

        this.helpMessageEl.innerHTML = OpenLayers.i18n("Move the map to measure distance");
        this.helpMessageEl.style.display = '';

        div = document.createElement('div');
        this.div.appendChild(div);
        OpenLayers.Element.addClass(div, 'olButton');
        div.id = 'finishButton';

        button = document.createElement('a');
        button.innerHTML = OpenLayers.i18n('Finish');
        div.appendChild(button);
        this.finishButton = div;
    },

    /**
     * Method: measure
     * Draw a line from first point and current center, display measure.
     */
    measure: function() {
        this.helpMessageEl.style.display = 'none';
        var center = this.map.getCenter();
        if (!this.line) {
            this.target = new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(center.lon, center.lat));
            var geom = new OpenLayers.Geometry.LineString([
            this.origin.geometry,
            this.target.geometry]);
            this.line = new OpenLayers.Feature.Vector(geom, {
                label: ''
            });
            this.layer.addFeatures([
            this.line,
            this.target]);
        } else {
            this.target.geometry.x = center.lon;
            this.target.geometry.y = center.lat;
            var measure = this.getBestLength(this.line.geometry);
            this.target.attributes.label = measure[0].toPrecision(4) + ' ' + measure[1];

            this.line.geometry.clearBounds();
            this.layer.drawFeature(this.line);
            this.target.geometry.clearBounds();
            this.layer.drawFeature(this.target);
        }
    },

    /**
     * Method: destroy
     * Clean up.
     */
    destroy: function() {
        if (this.map) {
            this.map.events.unregister("buttonclick", this, this.onClick);
        }
        OpenLayers.Control.prototype.destroy.apply(this);
    },

    /**
     * Method: getBestLength
     * Based on the <displaySystem> returns the length of a geometry.
     *
     * Parameters:
     * geometry - {<OpenLayers.Geometry>}
     *
     * Returns:
     * {Array([Float, String])}  Returns a two item array containing the
     *     length and the units abbreviation.
     */
    getBestLength: function(geometry) {
        var units = this.displaySystemUnits[this.displaySystem];
        var unit, length;
        for (var i = 0, len = units.length; i < len; ++i) {
            unit = units[i];
            length = this.getLength(geometry, unit);
            if (length > 1) {
                break;
            }
        }
        return [length, unit];
    },

    /**
     * Method: getLength
     *
     * Parameters:
     * geometry - {<OpenLayers.Geometry>}
     * units - {String} Unit abbreviation
     *
     * Returns:
     * {Float} The geometry length in the given units.
     */
    getLength: function(geometry, units) {
        var length, geomUnits;
        if (this.geodesic) {
            length = geometry.getGeodesicLength(this.map.getProjectionObject());
            geomUnits = "m";
        } else {
            length = geometry.getLength();
            geomUnits = this.map.getUnits();
        }
        var inPerDisplayUnit = OpenLayers.INCHES_PER_UNIT[units];
        if (inPerDisplayUnit) {
            var inPerMapUnit = OpenLayers.INCHES_PER_UNIT[geomUnits];
            length *= (inPerMapUnit / inPerDisplayUnit);
        }
        return length;
    },

    CLASS_NAME: "MobileMeasure"
});

/**
 * Copyright (c) 2011-2013 by Camptocamp SA
 *
 * CGXP is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * CGXP is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CGXP. If not, see <http://www.gnu.org/licenses/>.
 */

window.App = App || {};
App.MobileMeasure = OpenLayers.Class(OpenLayers.Control, {

    /**
     * Property: addFirstPointButton
     * {DOMElement}
     */
    buttonsCtn: null,
    
    /**
     * Property: addFirstPointButton
     * {DOMElement}
     */
    activateButton: null,

    /**
     * Property: addFirstPointButton
     * {DOMElement}
     */
    deactivateButton: null,
    
    /**
     * Property: addFirstPointButton
     * {DOMElement}
     */
    addFirstPointButton: null,
    
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
     * Property: helpMessageEl
     * {DOMElement}
     */
    helpMessageEl: null,

    /**
     * Property: layer
     * {OpenLayers.Layer.Vector}
     */
    layer: null,

    /**
     * Property: line
     * {OpenLayers.Geometry.LineString} Measure linestring
     */
    linestring: null,

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
        
        this.buttonsCtn = document.createElement('div');
        this.buttonsCtn.id = 'buttonsCtn';
        this.div.appendChild(this.buttonsCtn);
        
        this.activateButton = this.addButton("activateButton", "", true);
        this.deactivateButton = this.addButton("deactivateButton", "");
        this.newMeasureButton = this.addButton('newMeasureButton', "");
        this.addFirstPointButton = this.addButton('addFirstPointButton', 'Set starting point');
        this.finishButton = this.addButton('finishButton', 'Finish');
        this.addPointButton = this.addButton('addPointButton', '');
        
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
            case this.activateButton:
                this.activate();
                this.showMessage("Move the map to locate starting point");
                break;
            case this.deactivateButton:
                this.deactivate();
                break;
            case this.addFirstPointButton:
                this.hideButton(button);
                this.addFirstPoint();
                this.showMessage("Move the map to measure distance");
                break;
            case this.addPointButton:
                this.addPoint();
                this.showMessage("New point added, you can move again");
                break;
            case this.newMeasureButton:
                this.deactivate();
                this.activate();
                this.showMessage("Move the map to locate starting point");
                break;
            case this.finishButton:
                this.hideButton(this.addPointButton);
                this.hideButton(button);
                this.map.events.unregister('move', this, this.measure);
                this.hideMessage();
                break;
        }
    },

    /**
     * Method: showMessage
     * Display a message to user.
     */
    showMessage: function(message) {
    	this.helpMessageEl.innerHTML = OpenLayers.i18n(message);
        this.helpMessageEl.style.display = '';
    },
    
    /**
     * Method: hideMessage
     * Hide previously showed message.
     */
    hideMessage: function() {
        this.helpMessageEl.style.display = 'none';
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
        this.hideCenter();
        this.showButton(this.activateButton);
        this.hideButton(this.deactivateButton);
        this.hideButton(this.addFirstPointButton);
        this.hideButton(this.addPointButton);
        this.hideButton(this.finishButton);
        this.hideButton(this.newMeasureButton);
        this.helpMessageEl.style.display = "none";

        OpenLayers.Element.addClass(div, 'olButton');
        
        this.map.removeLayer(this.layer);
        this.map.events.unregister('move', this, this.measure);
        this.map.events.unregister('move', this, this.hidemessage);
        this.layer.removeFeatures(this.layer.features);
        this.linetring= null;
        this.target = null;
        this.active = false;
    },

    /**
     * Method: activate
     * Show target on the map and invite user to add first point.
     */
    activate: function() {
        this.showCenter();
        this.hideButton(this.activateButton);
        this.showButton(this.deactivateButton);
        this.showButton(this.addFirstPointButton);
        this.map.events.register('move', this, this.hideMessage);
        this.map.addLayer(this.layer);
        this.active = true;
    },

    /**
     * Method: addFirstPoint
     * Adds the first point and waits for map to be panned.
     */
    addFirstPoint: function() {
        this.hideCenter();
        this.createTarget();
        this.createLineString();
        this.addPoint();
        this.map.events.register('move', this, this.measure);
        this.showButton(this.addPointButton);
        this.showButton(this.finishButton);
        this.showButton(this.newMeasureButton);
    },

    /**
     * Method: addPoint
     * Adds new point as target.
     */
    addPoint: function() {
        this.updateTarget();
        this.target.attributes.label = "";
        this.target.geometry.clearBounds();
        this.layer.drawFeature(this.target);
        this.linestring.geometry.addPoint(this.createTarget().geometry);
        this.measure();
    },

    /**
     * Method: createTarget
     * Adds new point as target.
     */
    createTarget: function() {
        var center = this.map.getCenter();
        this.target = new OpenLayers.Feature.Vector(
            new OpenLayers.Geometry.Point(center.lon, center.lat), {
                label: ''
            });
        this.layer.addFeatures(this.target);
        return this.target;
    },

    /**
     * Method: updateTarget
     * Update target position to the center of the map.
     */
    updateTarget: function() {
        var center = this.map.getCenter();
        this.target.geometry.x = center.lon;
        this.target.geometry.y = center.lat;
    },

    /**
     * Method: createLineString
     * Create the linestring feature.
     */
    createLineString: function() {
        var geom = new OpenLayers.Geometry.LineString([
            this.target.geometry]);
        this.linestring = new OpenLayers.Feature.Vector(geom, {
            label: ''
        });
        this.layer.addFeatures(this.linestring);
    },
    

    /**
     * Method: addButton
     * Create a button with id and text.
     */
    addButton: function(id, text, visible) {
        div = document.createElement('div');
        div.id = id;
        OpenLayers.Element.addClass(div, 'olButton');
        if (!visible) {
            OpenLayers.Element.addClass(div, 'hidden');
        }
        this.buttonsCtn.appendChild(div);
        
        a = document.createElement('a');
        a.innerHTML = OpenLayers.i18n(text);
        div.appendChild(a);
      
        return div;
    },
    
    /**
     * Method: removeButton
     * Remove a button by dom object.
     */
    removeButton: function(button) {
        if (button && button.parentNode) {
            button.parentNode.removeChild(button);
        }
    },
    
    /**
     * Method: showButton
     * Show button to the user.
     */
    showButton: function(button) {
        OpenLayers.Element.removeClass(button, 'hidden');
    },
    
    /**
     * Method: hideButton
     * Hide button to the user.
     */
    hideButton: function(button) {
        OpenLayers.Element.addClass(button, 'hidden');
    },
    
    /**
     * Method: measure
     * Draw a line from first point and current center, display measure.
     */
    measure: function() {
        this.hideMessage();
        this.updateTarget();
        var measure = this.getBestLength(this.linestring.geometry);
        if (measure != undefined) {
            this.target.attributes.label = measure[0].toPrecision(4) + ' ' + measure[1];
        }
        this.linestring.geometry.clearBounds();
        this.layer.drawFeature(this.linestring);
        this.target.geometry.clearBounds();
        this.layer.drawFeature(this.target);
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

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
     * Property: buttonsCtn
     * {DOMElement} Buttons container
     */
    buttonsCtn: null,
    
    /**
     * Property: activateButton
     * {DOMElement}
     */
    activateButton: null,

    /**
     * Property: deactivateButton
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
     * Property: linestring
     * {OpenLayers.Geometry.LineString} Measure linestring
     */
    linestring: null,

    /**
     * Property: lastPoint
     * {OpenLayers.Geometry.Point} Last added point
     */
    lastPoint: null,
    
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
     *     of unit abbreviations (from OpenLayers.INCHES_PER_UNIT)
     *     in decreasing order of length.
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

        var defaultStyle = OpenLayers.Util.applyDefaults({
            fillColor: 'red',
            fillOpacity: 1.0,
            strokeColor: 'red',
            strokeWidth: 0,
            graphicName: 'cross',
            label: "${label}",
            fontColor: 'red',
            labelAlign: "lt",
            labelXOffset: 10,
            labelYOffset: -10
        }, OpenLayers.Feature.Vector.style['default']);

        var lineStyle = OpenLayers.Util.applyDefaults({
            strokeWidth: 2
        }, defaultStyle);
        
        var temporaryStyle = OpenLayers.Util.applyDefaults({
            fillColor: 'blue',
            strokeColor: 'blue',
            fontColor: 'blue'
        }, defaultStyle);
        
        this.layer = new OpenLayers.Layer.Vector(this.CLASS_NAME, {
            displayInLayerSwitcher: false,
            calculateInRange: OpenLayers.Function.True,
            styleMap: new OpenLayers.StyleMap({
                'default': defaultStyle,
                'line': lineStyle,
                'temporary': temporaryStyle
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
        this.addFirstPointButton = this.addButton('addFirstPointButton',
                                                  'Set starting point');
        this.addPointButton = this.addButton('addPointButton',
                                             'Add new point');
        this.finishButton = this.addButton('finishButton', 'Finish');
        
        this.eventsInstance = this.map.events;
        this.eventsInstance.register("buttonclick", this, this.onClick);

        this.helpMessageEl = document.createElement('div');
        this.helpMessageEl.id = 'mobileMeasureHelp';
        this.hideMessage();
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
                break;
            case this.deactivateButton:
                this.deactivate();
                break;
            case this.addFirstPointButton:
                this.addPoint();
                this.hideButton(button);
                this.showButton(this.newMeasureButton);
                this.showMessage("Move the map to next point");
                break;
            case this.addPointButton:
                this.addPoint();
                this.hideButton(button);
                this.showButton(this.finishButton);
                this.showMessage("Finish or move the map to next point");
                break;
            case this.newMeasureButton:
                this.deactivate();
                this.activate();
                break;
            case this.finishButton:
                this.hideMessage();
                this.map.events.unregister('move', this, this.updateTarget);
                this.hideButton(this.finishButton);
                break;
        }
    },

    /**
     * Method: showMessage
     * Display a message to user.
     */
    showMessage: function(message) {
        this.helpMessageEl.innerHTML = OpenLayers.i18n(message);
        OpenLayers.Element.removeClass(this.helpMessageEl, 'hidden');
    },

    /**
     * Method: hideMessage
     * Hide previously showed message.
     */
    hideMessage: function() {
        OpenLayers.Element.addClass(this.helpMessageEl, 'hidden');
    },

    /**
     * Method: deactivate
     * Remove any button or message but the control initial button.
     */
    deactivate: function() {
        this.showButton(this.activateButton);
        this.hideButton(this.deactivateButton);
        this.hideButton(this.addFirstPointButton);
        this.hideButton(this.addPointButton);
        this.hideButton(this.finishButton);
        this.hideButton(this.newMeasureButton);
        this.hideMessage();

        this.map.removeLayer(this.layer);
        this.map.events.unregister('move', this, this.updateTarget);
        this.map.events.unregister('move', this, this.hideMessage);
        this.layer.removeFeatures(this.layer.features);
        this.layer.redraw();
        this.linestring = null;
        this.lastPoint = null;
        this.target = null;
        this.active = false;
    },

    /**
     * Method: activate
     * Show target on the map and invite user to add first point.
     */
    activate: function() {
        this.map.addLayer(this.layer);
        this.map.events.register('move', this, this.hideMessage);
        this.map.events.register('move', this, this.updateTarget);
        this.active = true;
        
        this.updateTarget();
        this.hideButton(this.activateButton);
        this.showButton(this.deactivateButton);
        this.hideButton(this.addPointButton);
        this.showButton(this.addFirstPointButton);
        this.showMessage("Move the map to locate starting point");
    },

    addPoint: function() {
        this.lastPoint = this.target;
        this.target = null;

        var center = this.map.getCenter();
        this.lastPoint.geometry.x = center.lon;
        this.lastPoint.geometry.y = center.lat;

        if (!this.linestring) {
            this.linestring = new OpenLayers.Feature.Vector(
                new OpenLayers.Geometry.LineString([
                    this.lastPoint.geometry
                ]),
                { label: '' }
            );
            this.layer.addFeatures(this.linestring);
        }
        else {
            this.linestring.geometry.addPoint(this.lastPoint.geometry);
            var measure = this.getBestLength(this.linestring.geometry);
            if (measure != undefined && measure[0] != 0) {
                var measure = measure[0].toPrecision(4) + ' ' + measure[1];
                this.lastPoint.attributes.label = measure;
                                                  
            }
        }
        
        this.lastPoint.geometry.clearBounds();
        this.linestring.geometry.clearBounds();
        this.layer.drawFeature(this.linestring, 'line');
        this.layer.drawFeature(this.lastPoint, 'default');
    },

    /**
     * Method: updateTarget
     * Update target position to the center of the map.
     */
    updateTarget: function() {
        var center = this.map.getCenter();
        if (!this.target) {
            if (this.lastPoint) {
                this.lastPoint.attributes.label = '';
                this.layer.drawFeature(this.lastPoint, 'default');
            }
            this.target = new OpenLayers.Feature.Vector(
                new OpenLayers.Geometry.Point(center.lon, center.lat),
                { label: '' }
            );
            this.layer.addFeatures(this.target);
            if (this.linestring) {
                this.linestring.geometry.addPoint(this.target.geometry);
            }
        }
        else {
            this.target.geometry.x = center.lon;
            this.target.geometry.y = center.lat;
        }
        if (this.linestring) {
            var measure = this.getBestLength(this.linestring.geometry);
            if (measure != undefined && measure[0] != 0) {
                var measure = measure[0].toPrecision(4) + ' ' + measure[1];
                this.target.attributes.label = measure;
            }
            this.linestring.geometry.clearBounds();
            this.layer.drawFeature(this.linestring);
            this.showButton(this.addPointButton);
        }
        this.target.geometry.clearBounds();
        this.layer.drawFeature(this.target, 'temporary');

        this.hideButton(this.finishButton);
        if (this.lastPoint) {
            this.showButton(this.addPointButton);
        }
    },
    
    /**
     * Method: addButton
     * Create a button with id and text.
     */
    addButton: function(id, text, visible) {
        var div = document.createElement('div');
        div.id = id;
        OpenLayers.Element.addClass(div, 'olButton');
        if (!visible) {
            OpenLayers.Element.addClass(div, 'hidden');
        }
        this.buttonsCtn.appendChild(div);
        
        var a = document.createElement('a');
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

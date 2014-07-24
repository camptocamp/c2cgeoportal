/**
 * Copyright (c) 2011-2014 by Camptocamp SA
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
App.GeolocateControl = OpenLayers.Class(OpenLayers.Control, {

    autoActivate: true,
    button: null,
    firstGeolocation: false,

    activate: function() {
        if(!OpenLayers.Control.prototype.activate.apply(this, arguments)) {
            return false;
        }
        this.layer = new OpenLayers.Layer.Vector(this.CLASS_NAME, {
            displayInLayerSwitcher: false,
            calculateInRange: OpenLayers.Function.True
        });
        this.touchControl = this.map.getControlsByClass('OpenLayers.Control.TouchNavigation')[0];

        this.circle = new OpenLayers.Feature.Vector(
            null,
            {},
            {
                fillOpacity: 0.1,
                strokeOpacity: 0.6
            }
        );
        this.marker = new OpenLayers.Feature.Vector(
            null,
            {},
            OpenLayers.Util.applyDefaults({
                graphicOpacity: 1,
                graphicWidth: 16,
                graphicHeight: 16
            }, OpenLayers.Feature.Vector.style['default'])
        );

        return true;
    },

    draw: function() {
        var div = OpenLayers.Control.prototype.draw.apply(this);

        var geolocate = document.createElement("a");
        div.appendChild(geolocate);
        OpenLayers.Element.addClass(geolocate, "olButton");
        this.button = geolocate;

        this.eventsInstance = this.map.events;
        this.eventsInstance.register("buttonclick", this, this.onClick);

        this.geolocateControl = new OpenLayers.Control.Geolocate({
            bind: false,
            autoCenter: false,
            watch: true,
            geolocationOptions: {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 7000
            }
        });
        this.geolocateControl.events.on({
            "locationfailed": this.onLocationFailed,
            "locationupdated": this.onLocationUpdated,
            scope: this
        });

        return div;
    },

    onLocationFailed: function(e) {
        if (e.error.code == 1) {
            this.geolocateControl.deactivate();
            this.cancelAutoUpdate();
            alert("This application is not allowed to use your position");
        }
    },

    onLocationUpdated: function(e) {
        this.layer.removeFeatures([this.circle, this.marker]);
        this.circle.geometry = new OpenLayers.Geometry.Polygon.createRegularPolygon(
            e.point,
            e.position.coords.accuracy/2,
            40,
            0
        );
        this.marker.geometry = e.point;
        this.layer.addFeatures([
            this.circle,
            this.marker
        ]);
        this.map.events.unregister('movestart', this, this.cancelAutoUpdate);
        if (this.firstGeolocation) {
            this.map.addLayer(this.layer);
            this.map.zoomToExtent(this.circle.geometry.getBounds());
            this.firstGeolocation = false;
        } else if (this.geolocateControl.autoCenter) {
            this.map.setCenter(new OpenLayers.LonLat(e.point.x, e.point.y));
        }
        this.map.events.register('movestart', this, this.cancelAutoUpdate);
    },

    // cancel auto update if map is drag-panned
    cancelAutoUpdate: function(evt) {
        if (!evt || !evt.zoomChanged) {
            // control is still active, but map doesn't recenter
            this.geolocateControl.autoCenter = false;
            this.touchControl.pinchZoom.preserveCenter = false;
            OpenLayers.Element.removeClass(this.button, 'active');
            this.firstGeolocation = false;
            this.circle.style.fillColor = '#999';
            this.circle.style.strokeColor = '#999';
            this.marker.style.externalGraphic = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAAAXNSR0IArs4c6QAAAAJiS0dEAP+Hj8y/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3AwDDSwgdOrsLgAAARhJREFUKM+FkT1uwkAQhb+1LIi9hkhJYxHlApYotuAWHIAyDXS5AgVXSIeblBzAd6CgcOeKigjFBUkRfgTsbqBYisSRyDxpNMXTSN974sT18eHFXQk9uiggJ2NCAfCMD990mPX90X18RwRs1Kf66JthJ525D4ZpPxw/cgtYIOCBKH4bTyEFD2wiRi0k5ockLcTIJuCB7jXjAF1RQDPWPfDAdBsc/hgONDBd8EGrd7aENAipAwd2rNkh0coZsHyxqvDXuEE7Cp1L1WRTMURIdO4ws5WKEJhf+YWsMJmjmJSlRSIJLpJILGWpJy6H4jhcsKdGndpl71lwHNrCYdJO14N5uWSLh8eWJfNyPWinBhAnnq6U9Yr4r+4zk2Z4mbISFUIAAAAASUVORK5CYII%3D';
            this.layer.redraw();
        }
    },

    onClick: function(evt) {
        var button = evt.buttonElement;
        if (button === this.button) {
            if (this.button.className.indexOf('active') != -1) {
                this.cancelAutoUpdate();
            } else {
                this.map.addControl(this.geolocateControl);
                this.geolocateControl.autoCenter = true;
                this.firstGeolocation = true;
                // force activation, even if already active
                this.geolocateControl.deactivate();
                this.geolocateControl.activate();
                OpenLayers.Element.addClass(this.button, 'active');
                this.touchControl.pinchZoom.preserveCenter = true;
                this.circle.style.fillColor = '#4C7FB2';
                this.circle.style.strokeColor = '#4C7FB2';
                this.marker.style.externalGraphic = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAAK/INwWK6QAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAGYSURBVHjapFNLisJAEK2E4Cf+QDeieAHBRZjxFh7ACyTewoW3MF7AA3iHLDKDO1euFNFF4sIfGn9Tr0alF+LA2PDSTdWrl9Srjna9XumdpUGg5X6rsSqjyWgwrFtsyBgw+ozRndh1PsjA4XK5UL1eJ9/3bcMwOoVCoZjP5ymdTgtxs9lYy+XSCsPQPp1Obeb2mCs5EeAgeZ5nm6bpVioVyuVykjyfz7Ink0kql8sQLE6nU5e5CPfw0G/EqqZpnVKpRKlUSgSfATlwwEXNQ+B4PDaz2WwRb+LzS4ADLmoeAqzeyGQydDgc/hQAB1zUPDzghDWfz2m73RL7IATs8XhcPEDRbrej9XotO1pBjSoghq1WKwqC4OXcY7EYJRIJqVEFhqxqcW8Y2UsBjPb2BUN1jAN+s4UkOyyOP1t8R6Q1fCVq1Cn0F7zQBtQBuK3iHgcHXNSo92AURVF7MpnQfr+XPmEgdvWMHDjgokYdI9VqtR677IzH48VsNpOJ6LouwBkx5MAB996m/EyfLfdfP9NX1/kVeGf9CDAAGzQxvrg3al4AAAAASUVORK5CYII%3D';
                this.layer.redraw();
            }
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

    CLASS_NAME: "Geolocate"
});

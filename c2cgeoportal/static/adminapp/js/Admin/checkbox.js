/*
Copyright (c) 2011-2016 by Camptocamp SA
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of the FreeBSD Project.
*/


// define a adminapp namespace in jQuery and all related methodes
(function($){
    $.fn.adminapp = function(){};

    /**
     * find an element in the dom whose id match str and not contained in ignoreList
     */

    $.fn.adminapp.findList = function(str, fieldList, ignoreList) {
        ignoreList = (typeof(ignoreList) == "undefined") ? [] : ignoreList;
        var list = [];

        // get all el with id attr
        list = fieldList.filter("[id]");
        // find els with id containing searched str
        list = list.filter(function(index) {
            if (this.id.indexOf("-" + str) > -1) {
                return this;
            }
        });
        // remove ignored els
        list = list.filter(function(index) {
            if (ignoreList.length > 0) {
                for (var j=0; j<ignoreList.length; j++) {
                    if (this.id.indexOf(ignoreList[j]) == -1) {
                        return this;
                    }
                }
            } else {
                return this;
            }
        });

        return list;
    };

    /**
     * find an element in the dom whose id match str and not contained in ignoreList
     */
    $.fn.adminapp.findField = function(str, ignoreList) {
        var result = this.findList(str, this.fieldList, ignoreList);
        if (result.length == 0) {
            result = this.findList(str, this.selectList, ignoreList);
        }
        return result;
    };

    /**
     * find an element in the dom whose id match str and not contained in ignoreList
     */
    $.fn.adminapp.findSelect = function(str, ignoreList) {
        return this.findList(str, this.selectList, ignoreList);
    };

    /**
     * attach toogleAddress event on the secondary address checkbox
     */
    $.fn.adminapp.bindEventOnAddress = function(el) {
        var chk = $('#' + el.id);
        chk.bind('click', function(event) {
            $.fn.adminapp.toogleAddress(event.target);
        });
    };

    /**
     * attach toogle restrictionarea event on the secondary "public" checkbox
     */
    $.fn.adminapp.bindEventOnLayer = function(lt) {
        var chk = $('#' + lt.id);
        chk.bind('change', function(event) {
            $.fn.adminapp.toogleLayerType(event.target);
        });
    };

    /**
     * attach toogle internal WMS on Base Layer.
     */
    $.fn.adminapp.bindEventOnLayerGroup = function(wmsi, bl) {
        wmsi.bind('change', function(event) {
            $.fn.adminapp.toogleBaseLayer(wmsi, bl);
        });
    };

    /**
     * show / hide secondary address input fields
     */
    $.fn.adminapp.toogleAddress = function(el) {
        var els = $.fn.adminapp.findField('b_', [el.id]);
        /* this code can be used to show/hide block instead of enabling/disabling inputs
        var d = 'block';
        */
        var state = false;
        if (!el.checked) {
            //d = 'none';
            state = true;
        }

        if (state) {
            $.fn.adminapp.resetField(els);
            els.addClass('disabledinput');
        } else {
            els.removeClass('disabledinput');
        }
        // reset value and set readonly
        els.attr('readOnly', state);
        // can NOT use disabled as FA expect the field to be in request
        // els.attr('disabled', state);
    };

    /**
     * show / hide restrictionArea input fields
     */
    $.fn.adminapp.toogleRestrictionAreas = function(el) {
        var els = $.fn.adminapp.findField('restrictionareas', [el.id]);
        var state = el.value == "internal WMS" || el.value == "WMTS";
        if (state) {
            els.removeClass('disabledinput');
        } else {
            // reset value
            $.fn.adminapp.resetField(els);

            els.addClass('disabledinput');
        }
        // set readonly
        els.attr('readOnly', !state);
        els.attr('disabled', !state);
    };

    /**
     * show / hide unneeded fields
     */
    $.fn.adminapp.toogleLayerType = function(el) {
        var state = el.value;
        var fields = [];
        if (state == "internal WMS") {
            fields = ["legend_rule"];
        }
        else if (state == "external WMS") {
            fields = ["url", "style", "image_type", "legend_rule", "is_single_tile"];
        }
        else if (state == "WMTS") {
            fields = ["url", "style", "dimensions", "matrixSet", "wms_url",
                      "wms_layers", "query_layers"];
        }

        var change = function(field, fields) {
            var e = $.fn.adminapp.findField(field, [el.id]);
            var state = jQuery.inArray(field, fields) >= 0;
            if (state) {
                e.removeClass('disabledinput');
            }
            else {
                e.addClass('disabledinput');
            }
            e.attr('readOnly', !state);
            if (e[0].tagName != "INPUT") {
                e.attr('disabled', !state);
            }
        };

        change("url", fields);
        change("image_type", fields);
        change("style", fields);
        change("dimensions", fields);
        change("matrix_set", fields);
        change("wms_url", fields);
        change("wms_layers", fields);
        change("query_layers", fields);
        change("is_single_tile", fields);
        change("legend_rule", fields);

        enablePrivateOption = state == "internal WMS" || state == "WMTS"
        var e = $.fn.adminapp.findField("public",  [el.id]);
        e.attr('readOnly', !enablePrivateOption);
        if (enablePrivateOption) {
            e.removeClass('disabledinput');
        }
        else {
            e.addClass('disabledinput');
            e.attr('checked', true);
        }
        this.toogleRestrictionAreas(el);
        // true should be send ...
        //e.attr('disabled', !internalWMS);
    };

    $.fn.adminapp.toogleBaseLayer = function(wmsi, bl) {
        var state = wmsi[0].checked;
        if (state) {
            // reset value
            $.fn.adminapp.resetField(bl);

            bl.addClass('disabledinput');
        } else {
            bl.removeClass('disabledinput');
        }
        // set readonly
        bl.attr('readOnly', state);
        bl.attr('disabled', state);
    };

    /**
     * get the parent div containing on input field
     */
    $.fn.adminapp.getParentBLock = function(el) {
        var p = el.parentNode;
        while (p.nodeName.toLowerCase() != 'div') {
            p = p.parentNode;
        }
        return p;
    };

    /**
     * reset input value or state
     */
    $.fn.adminapp.resetField = function(el) {
        for (var i = 0 ; i < el.length ; i++) {
            switch (el[i].type) {
              case 'checkbox':
                  el[i].checked = false;
                  break;
              case 'radio':
                  break;
              default:
                  el[i].value = '';
            }
        }
    };

    $.fn.adminapp.syncField = function(el) {
        var cbl = $.fn.adminapp.checkboxcorrespondance[el.target.id];
        for (var i = 0, len = cbl.length ; i < len ; i++) {
            cbl[i].checked = el.target.checked;
        }
    };

})(jQuery);

$(document).ready(function(){

    // store all fields
    $.fn.adminapp.fieldList = $("input");
    $.fn.adminapp.selectList = $("select");

    // attach event on User.b_company to show/hide secondary address fields (b_*)
    var f = $.fn.adminapp.findField('b_company');
    if (f.length > 0) {
        $.fn.adminapp.bindEventOnAddress(f[0]);
        // init state
        $.fn.adminapp.toogleAddress(f[0]);
    }

    // attach event on Layer.public to show/hide restrictionareas
    var lt = $.fn.adminapp.findSelect('layer_type');
    //Select('layerType');
    if (lt.length > 0) {
        // restrictionareas
        $.fn.adminapp.bindEventOnLayer(lt[0]);
        // init state
        $.fn.adminapp.toogleRestrictionAreas(lt[0]);
        $.fn.adminapp.toogleLayerType(lt[0]);
    }

    /**
     * When a layer(or group) is display more than one time
     * this will sync the state on all tree items.
     */

    // store field correspondence
    // this is used to have two times the same layer in a tree,
    // than when we check or uncheck one, the other should do the same
    $.fn.adminapp.checkboxcorrespondance = {};
    var checkboxtrees = $(".checkboxtree");
    for (var i = 0, leni = checkboxtrees.length ; i < leni ; i++) {
        var checkboxlist = $("#" + checkboxtrees[i].id + " input");
        for (var j = 0, lenj = checkboxlist.length ; j < lenj ; j++) {
            if (checkboxlist[j].id) {
                var samenamecheckbox = $("#" + checkboxtrees[i].id + " input[value=" + checkboxlist[j].value + ']');
                if (samenamecheckbox.length > 1) {
                    $.fn.adminapp.checkboxcorrespondance[checkboxlist[j].id] = samenamecheckbox;
                    $("#" + checkboxlist[j].id).bind('change', $.fn.adminapp.syncField);
                }
            }
        }
    }

    var wmsi = $.fn.adminapp.findField('is_internal_wms')
    var bl = $.fn.adminapp.findField('is_base_layer')
    if (wmsi.length > 0 && bl.length > 0) {
        $.fn.adminapp.bindEventOnLayerGroup(wmsi, bl);
        // init state
        $.fn.adminapp.toogleBaseLayer(wmsi, bl);
    }

    // make read only for Chrome
    var e = $(":checkbox");
    e.click(function(evt) {
        if ($(evt.target).hasClass('disabledinput')) {
            evt.preventDefault();
        }
    });
});

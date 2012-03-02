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
            if (this.id.indexOf(str) > -1) {
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
        return this.findList(str, this.fieldList, ignoreList);
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
    $.fn.adminapp.bindEventOnLayer = function(pl, lt) {
        var chk = $('#' + pl.id);
        chk.bind('click', function(event) {
            $.fn.adminapp.toogleRestrictionAreas(event.target);
        }); 
        chk = $('#' + lt.id);
        chk.bind('change', function(event) {
            $.fn.adminapp.toogleLayerType(event.target);
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

        for (var i=0; i<els.length; i++) {
            /*
            var p = $.fn.adminapp.getParentBLock(els[i]);
            p.style.display = d;
            */
            if (state) {
                $(els[i]).addClass('disabledinput');
            } else {
                $(els[i]).removeClass('disabledinput');            
            }
            // can NOT use disabled as FA expect the field to be in request
            //els[i].disabled = state;
            // reset value and set readonly
            $.fn.adminapp.resetField(els[i]);
            els[i].readOnly = state;
        }
        
    };

    /**
     * show / hide restrictionArea input fields
     */
    $.fn.adminapp.toogleRestrictionAreas = function(el) {
        var els = $.fn.adminapp.findField('restrictionareas', [el.id]);        
        var state = el.checked;
        for (var i=0; i<els.length; i++) {
            if (state) {
                // reset value
                $.fn.adminapp.resetField(els[i]);

                $(els[i]).addClass('disabledinput');
            } else {
                $(els[i]).removeClass('disabledinput');            
            }
            // set readonly
            els[i].readOnly = state;
        }
    };

    /**
     * show / hide unneeded fields
     */
    $.fn.adminapp.toogleLayerType = function(el) {
        var state = el.value;
        var fields = [];
        if (state == "internal WMS") {
            fields = ["legendRule"];
        }
        else if (state == "external WMS") {
            fields = ["url", "isSingleTile"];
        }
        else if (state == "internal WMTS") {
            fields = ["legendImage"];
        }
        else if (state == "external WMTS") {
            fields = ["url", "serverResolutions", "maxExtent", "legendImage"];
        }

        var change = function(field, fields) {
            var e = $.fn.adminapp.findField(field, [el.id]);
            if (jQuery.inArray(field, fields) >= 0) {
                $(e[0]).removeClass('disabledinput');
            }
            else {
                $(e[0]).addClass('disabledinput');
            }
            e[0].readOnly = state;
        };

        change("url", fields);
        change("serverResolutions", fields);
        change("maxExtent", fields);
        change("isSingleTile", fields);
        change("legendImage", fields);
        change("legendRule", fields);
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
        switch (el.type) {
          case 'checkbox':
              el.checked = false;
              break;
          case 'radio':
              break;
          default:
              el.value = '';
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

    // attach event on User.b_company to show/hide secondare address fields (b_*)
    var f = $.fn.adminapp.findField('b_company');
    if (f.length > 0) {        
        $.fn.adminapp.bindEventOnAddress(f[0]);
        // init state
        $.fn.adminapp.toogleAddress(f[0]);
    }

    // attach event on Layer.public to show/hide restrictionareas
    var pl = $.fn.adminapp.findField('public');
    var lt = $.fn.adminapp.findSelect('layerType');
    //Select('layerType');
    if (pl.length > 0 && lt.length > 0) {        
        //restrictionareas
        $.fn.adminapp.bindEventOnLayer(pl[0], lt[0]);
        // init state
        $.fn.adminapp.toogleRestrictionAreas(pl[0]);
        $.fn.adminapp.toogleLayerType(lt[0]);
    }

    /**
     * When a layer(or group) is display more than one time
     * this will sync the state on all tree items.
     */

    // store field correspondance
    $.fn.adminapp.checkboxcorrespondance = {};
    var checkboxtrees = $(".checkboxtree");
    for (var i = 0, leni = checkboxtrees.length ; i < leni ; i++) {
        var checkboxlist = $("#" + checkboxtrees[i].id + " input");
        for (var j = 0, lenj = checkboxlist.length ; j < lenj ; j++) {
            if (checkboxlist[j].id) {
                var samenamecheckbox = $("input[value=" + checkboxlist[j].value + ']');
                if (samenamecheckbox.length > 1) {
                    $.fn.adminapp.checkboxcorrespondance[checkboxlist[j].id] = samenamecheckbox;
                    $("#" + checkboxlist[j].id).bind('change', $.fn.adminapp.syncField);
                }
            }
        }
    }
});

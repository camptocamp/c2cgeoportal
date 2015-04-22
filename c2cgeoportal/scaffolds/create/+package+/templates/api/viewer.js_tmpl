<%doc>
This file defines the GXP viewer and its plugins for the Extended API.
</%doc>
        var viewer = new gxp.Viewer({
            portalConfig: {
                renderTo: config.div,
                ctCls: 'x-map',
                height: Ext.get(config.div).getHeight(),
                layout: "fit",
                items: [config.id]
            },
            tools: [
            {
                ptype: "cgxp_mapopacityslider"
            },
            {
                ptype: "gxp_zoomtoextent",
                actionTarget: "map.tbar",
                closest: true,
                extent: [420000, 30000, 900000, 350000]
            },
            {
                ptype: "cgxp_zoom",
                actionTarget: "map.tbar",
                toggleGroup: "maptools"
            },
            {
                ptype: "cgxp_fulltextsearch",
                actionTarget: "map.tbar",
                url: "${request.route_url('fulltextsearch') | n}"
            },
            {
                ptype: "cgxp_menushortcut",
                actionTarget: "map.tbar",
                type: '->'
            },
            {
                ptype: "cgxp_legend",
                id: "legendPanel",
                toggleGroup: "maptools",
                actionTarget: "map.tbar"
            }],
            sources: {
                "olsource": {
                    ptype: "gxp_olsource"
                }
            },
            map: config
        });

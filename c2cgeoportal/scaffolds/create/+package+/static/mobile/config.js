// Here integrator can set up the layers
var App = App || {};
App.searchUrl = "${request.route_url('fulltextsearch', path='')}";

App.map = new OpenLayers.Map({
    theme: null,
    maxExtent: new OpenLayers.Bounds(515000, 180000, 580000, 230000),
    projection: new OpenLayers.Projection("EPSG:21781"),
    units: "m",
    resolutions: [250,100,50,20,10,5,2.5,2,1.5,1,0.5,0.25,0.125,0.0625],
    controls: [
        new OpenLayers.Control.TouchNavigation({
            dragPanOptions: {
                interval: 1,
                enableKinetic: true
            }
        }),
        new OpenLayers.Control.Attribution(),
        new OpenLayers.Control.ScaleLine()
    ],
    layers: [
        new OpenLayers.Layer.TMS(
            OpenLayers.i18n('Plan de ville'),
            ['http://tile1-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile2-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile3-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile4-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile5-sitn.ne.ch/tilecache_new/tilecache.cgi/'],
            {  
                layername: 'plan_ville_c2c',
                ref: 'plan',
                type:'png; mode=24bit',
                serverResolutions: [250,100,50,20,10,5,2.5,2,1.5,1,0.5,0.25,0.125,0.0625],
                tileOrigin: new OpenLayers.LonLat(420000,30000),
                transitionEffect: 'resize'
            }
        ),
        new OpenLayers.Layer.TMS(
            OpenLayers.i18n('Plan cadastral'),
            ['http://tile1-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile2-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile3-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile4-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile5-sitn.ne.ch/tilecache_new/tilecache.cgi/'],
            {  
                layername: 'plan_cadastral_c2c',
                ref: 'plan_cadastral',
                type:'png; mode=24bit',
                serverResolutions: [250,100,50,20,10,5,2.5,2,1.5,1,0.5,0.25,0.125,0.0625],
                tileOrigin: new OpenLayers.LonLat(420000,30000),
                transitionEffect: 'resize'
            }
        ),
        new OpenLayers.Layer.TMS(
            OpenLayers.i18n('Orthophoto'),
            ['http://tile1-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile2-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile3-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile4-sitn.ne.ch/tilecache_new/tilecache.cgi/', 'http://tile5-sitn.ne.ch/tilecache_new/tilecache.cgi/'],
            {  
                layername: 'ortho2011',
                ref: 'ortho',
                type:'png; mode=24bit',
                serverResolutions: [250,100,50,20,10,5,2.5,2,1.5,1,0.5,0.25,0.125,0.0625],
                tileOrigin: new OpenLayers.LonLat(420000,30000),
                transitionEffect: 'resize'
            }
        )
    ]
});

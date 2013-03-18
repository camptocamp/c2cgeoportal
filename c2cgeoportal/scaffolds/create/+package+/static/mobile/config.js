/*
 * This file represents the customization point for the application integrator.
 *
 * After execution of this script an OpenLayers map filled with layers should
 * be available in App.map.
 *
 * This file also contains translations for the application strings.
 */

OpenLayers.Lang.en = {
    "summits": "Summits",
    "huts": "Huts",
    "sites": "Sites",
    "users": "Users",

    // base layer switcher picker (you shouldn't remove this)
    'layer_switcher.cancel': 'Cancel',
    'layer_switcher.done': 'Done',

    // login/logout
    'loginButtonText': 'Log in',
    'welcomeText': '<p>You are {username}.</p>',
    'logoutButtonText': 'Log out',
    'loginLabel': 'Login',
    'passwordLabel': 'Password',
    'loginSubmitButtonText': 'Submit',
    'loginCancelButtonText': 'Cancel',

    // redirect to standard application
    'redirect_msg': "You're using the mobile version. Check out the" +
        " <a href='${'${url}'}'>standard version</a>.",
    'close': "Close"
};
OpenLayers.Lang.fr = {
    "summits": "Sommets",
    "huts": "Cabanes",
    "sites": "Sites",
    "users": "Utilisateurs",

    // base layer switcher picker (you shouldn't remove this)
    'layer_switcher.cancel': 'Annuler',
    'layer_switcher.done': 'OK',

    // login/logout
    'loginButtonText': 'Me connecter',
    'welcomeText': '<p>Vous êtes {username}.</p>',
    'logoutButtonText': 'Me déconnecter',
    'loginLabel': 'Nom',
    'passwordLabel': 'Mot de passe',
    'loginSubmitButtonText': 'Me connecter',
    'loginCancelButtonText': 'Annuler',

    // redirect to standard application
    'redirect_msg': "Vous utilisez la version pour mobile. Vous pouvez aussi" +
        " consulter la <a href='${'${url}'}'>version standard</a>.",
    'close': "Fermer"
};
OpenLayers.Lang.de = {
    "summits": "Gipfel",
    "huts": "Hütten",
    "sites": "Sehenswürdigkeiten",
    "users": "Benutzer",

    // base layer switcher picker (you shouldn't remove this)
    'layer_switcher.cancel': 'Abbrechen',
    'layer_switcher.done': 'OK',

    // login/logout
    'loginButtonText': 'Log in',
    'welcomeText': '<p>Sie sind {username}.</p>',
    'logoutButtonText': 'Log out',
    'loginLabel': 'Login',
    'passwordLabel': 'Passwort',
    'loginSubmitButtonText': 'OK',
    'loginCancelButtonText': 'Abbrechen',

    // redirect to standard application
    'redirect_msg': "Sie benutzen die mobile Version. Sie können auch" +
        " die <a href='${'${url}'}'>Standardversion</a> benutzen.",
    'close': "Schliessen"
};
OpenLayers.Lang.setCode("${lang}");

// App.info includes information that is needed by internal
// components, such as the Login view component.
App.info = '${info | n}';

// define the map and layers
App.map = new OpenLayers.Map({
    fallThrough: true, // required for longpress queries
    theme: null,
    projection: 'EPSG:900913',
    controls: [
        new OpenLayers.Control.TouchNavigation({
            dragPanOptions: {
                interval: 1,
                enableKinetic: true
            }
        }),
        new OpenLayers.Control.Attribution(),
        new OpenLayers.Control.ScaleLine({geodesic: true})
    ],
    layers: [
        new OpenLayers.Layer.OSM("OpenStreetMap", null, {
            transitionEffect: 'resize'
        }),
        new OpenLayers.Layer.OSM(
            "Cycle Map",
            [
                "http://a.tile.opencyclemap.org/cycle/${'${z}/${x}/${y}'}.png",
                "http://b.tile.opencyclemap.org/cycle/${'${z}/${x}/${y}'}.png",
                "http://c.tile.opencyclemap.org/cycle/${'${z}/${x}/${y}'}.png"
            ],
            {
                transitionEffect: 'resize'
            }
        ),
        new OpenLayers.Layer.OSM(
            "Transport Map",
            [
                "http://a.tile2.opencyclemap.org/transport/${'${z}/${x}/${y}'}.png",
                "http://b.tile2.opencyclemap.org/transport/${'${z}/${x}/${y}'}.png",
                "http://c.tile2.opencyclemap.org/transport/${'${z}/${x}/${y'}}.png"
            ],
            {
                transitionEffect: 'resize'
            }

        ),
        new OpenLayers.Layer.WMS(
            "Summits",
            "http://www.camptocamp.org/cgi-bin/c2corg_wms",
            {
                layers: ['summits'],
                transparent: true
            },
            {
                allLayers: ['summits', "huts", "sites", "users"],
                singleTile: true,
                ratio: 1
            }
        )
    ]
});

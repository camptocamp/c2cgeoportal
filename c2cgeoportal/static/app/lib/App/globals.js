Ext.namespace("App");

App.setGlobals = function() {
    // OpenLayers
    OpenLayers.Number.thousandsSeparator = ' ';
    OpenLayers.IMAGE_RELOAD_ATTEMPTS = 5;
    OpenLayers.DOTS_PER_INCH = 72;
    OpenLayers.ImgPath = App["OpenLayers.ImgPath"];

    // Ext
    Ext.BLANK_IMAGE_URL = App["Ext.BLANK_IMAGE_URL"];
    Ext.QuickTips.init();

    // Apply same language than on the server side
    OpenLayers.Lang.setCode(App["lang"]);
};

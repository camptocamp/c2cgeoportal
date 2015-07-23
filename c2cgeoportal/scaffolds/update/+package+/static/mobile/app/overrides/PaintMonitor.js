Ext.define('App.overrides.PaintMonitor', {
    override: 'Ext.util.PaintMonitor',

    uses: [
        'Ext.env.Browser',
        'Ext.env.OS',
        'Ext.util.paintmonitor.CssAnimation',
        'Ext.util.paintmonitor.OverflowChange'
    ],

    constructor: function(config) {
        return new Ext.util.paintmonitor.CssAnimation(config);
    }

}, function () {
    // <debug>
    console.info("Ext.util.PaintMonitor temp. fix is active");
    // </debug>
});

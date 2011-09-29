/**
 * Class ToolButton
 * An {Ext.Button} with specific configuration
 *
 * This type of button takes at least the following config options:
 * window : a {App.ToolButton} to show when the button is clicked.
 */
Ext.namespace('App');
App.ToolButton = function(config) {
    // call parent constructor
    App.ToolButton.superclass.constructor.call(this, config);
};
Ext.extend(App.ToolButton, Ext.Button, {
    initComponent: function() {
        App.ToolButton.superclass.initComponent.call(this, arguments);

        this.on('toggle', function(button) {
            if (button.pressed) {
                this.window.show();
                // we suppose the button is in a toolbar
                var toolbar = this.ownerCt;
                this.window.anchorTo(toolbar.getEl(), 'tr-br');
            } else {
                this.window.hide();
            }
        });
        this.window.on('hide', function() {
            this.toggle(false);
        }, this);
    }
});

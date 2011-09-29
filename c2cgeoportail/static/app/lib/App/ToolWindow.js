/**
 * Class ToolWindow
 * An {Ext.Window} with specific configuration
 */
Ext.namespace('App');
App.ToolWindow = function(config) {

    this.renderTo = Ext.getBody();
    this.closeAction = 'hide';
    this.unstyled = true;
    this.resizable = false;
    this.shadow = false;
    this.cls = 'toolwindow';
    // call parent constructor
    App.ToolWindow.superclass.constructor.call(this, config);
};
Ext.extend(App.ToolWindow, Ext.Window, {});

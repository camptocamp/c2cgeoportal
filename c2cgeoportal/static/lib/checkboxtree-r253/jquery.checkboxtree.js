/*!
 * jQuery CheckboxTree
 *
 * @author Valerio Galano <v.galano@daredevel.it>
 *
 * @see http://checkboxtree.daredevel.it
 *
 * @version 0.6
 */
$.widget("daredevel.checkboxTree", {

/**
 * Add a new node as children of passed one
 *
 * @private
 *
 * @param parentLi node under which new node will be attached
 */
    /*    _addNode: function(parentLi) {
     input = $('<input/>', {
     type: 'checkbox'
     });

     label = $('<label/>', {
     html: 'new'
     });

     span = $('<span/>', {
     html: ''
     });

     li = $('<li/>', {
     class: 'leaf'
     });

     li.append(span).append(input).append(label);

     if (parentLi.hasClass('leaf')) {
     ul = $('<ul/>');
     span = $('<span/>', {
     html: '-'
     });
     parentLi.append(ul.append(li)).removeClass('leaf').addClass('expanded');
     span.prependTo(parentLi);
     } else {
     parentLi.find('ul:first').append(li);
     }
     },*/

    /**
     * Check if all descendant of passed node are checked
     *
     * @private
     *
     * @param li node
     *
     * @return true if all descendant checked
     */
    _allDescendantChecked: function(li) {
        return (li.find('li input:checkbox:not(:checked)').length == 0);
    },

    /**
     * Initialize plugin
     *
     * @private
     */
    _create: function() {

        var t = this;

        // setup collapse engine tree
        if (this.options.collapsable) {

            // build collapse engine's anchors
            this.options.collapseAnchor = (this.options.collapseImage.length > 0) ? '<img src="' + this.options.collapseImage + '" />' : '';
            this.options.expandAnchor = (this.options.expandImage.length > 0) ? '<img src="' + this.options.expandImage + '" />' : '';
            this.options.leafAnchor = (this.options.leafImage.length > 0) ? '<img src="' + this.options.leafImage + '" />' : '';

            // initialize leafs
            this.element.find("li:not(:has(ul))").each(function() {
                $(this).prepend($('<span />'));
                t._markAsLeaf($(this));
            });

            // initialize checked nodes
            this.element.find("li:has(ul):has(input:checkbox:checked)").each(function() {
                $(this).prepend($('<span />'));
                t.options.initializeChecked == 'collapsed' ? t.collapse($(this)) : t.expand($(this));
            });

            // initialize unchecked nodes
            this.element.find("li:has(ul):not(:has(input:checkbox:checked))").each(function() {
                $(this).prepend($('<span />'));
                t.options.initializeUnchecked == 'collapsed' ? t.collapse($(this)) : t.expand($(this));
            });

            // bind collapse/expand event
            this.element.find('li span').live("click", function() {
                var li = $(this).parents("li:first");

                if (li.hasClass('collapsed')) {
                    t.expand(li);
                } else

                if (li.hasClass('expanded')) {
                    t.collapse(li);
                }
            });

            // bind collapse all element event
            $(this.options.collapseAllElement).bind("click", function() {
                t.collapseAll();
            });

            // bind expand all element event
            $(this.options.expandAllElement).bind("click", function() {
                t.expandAll();
            });

            // bind collapse on uncheck event
            if (this.options.onUncheck.node == 'collapse') {
                this.element.find('input:checkbox:not(:checked)').live("click", function() {
                    t.collapse($(this).parents("li:first"));
                });
            } else

            // bind expand on uncheck event
            if (this.options.onUncheck.node == 'expand') {
                this.element.find('input:checkbox:not(:checked)').live("click", function() {
                    t.expand($(this).parents("li:first"));
                });
            }

            // bind collapse on check event
            if (this.options.onCheck.node == 'collapse') {
                this.element.find('input:checkbox:checked').live("click", function() {
                    t.collapse($(this).parents("li:first"));
                });
            } else

            // bind expand on check event
            if (this.options.onCheck.node == 'expand') {
                this.element.find('input:checkbox:checked').live("click", function() {
                    t.expand($(this).parents("li:first"));
                });
            }
        }

        // bind node uncheck event
        this.element.find('input:checkbox:not(:checked)').live('click', function() {
            var li = $(this).parents('li:first');
            t.uncheck(li);
        });

        // bind node check event
        this.element.find('input:checkbox:checked').live('click', function() {
            var li = $(this).parents('li:first');
            t.check(li);
        });

        // add essential css class
        this.element.addClass('ui-widget-daredevel-checkboxTree');

        // add jQueryUI css widget class
        this.element.addClass('ui-widget ui-widget-content');

    },

    /**
     * Check ancestors on passed node
     *
     * Don't use check() method because we won't trigger onCheck events
     *
     * @private
     *
     * @param li node
     */
    _checkAncestors: function(li) {
        li.parentsUntil(".ui-widget").filter('li').find('input:checkbox:first:not(:checked)').prop('checked', true).change();
    },

    /**
     * Check descendants on passed node
     *
     * Don't use check() method because we won't trigger onCheck events
     *
     * @private
     *
     * @param li node
     */
    _checkDescendants: function(li) {
        li.find('li input:checkbox:not(:checked)').prop('checked', true).change();
    },

    /**
     * Check nodes that are neither ancestors or descendants of passed node
     *
     * Don't use check() method because we won't trigger onCheck events
     *
     * @private
     *
     * @param li node
     */
    _checkOthers: function(li) {
        var t = this;
        li.addClass('exclude');
        li.parents('li').addClass('exclude');
        li.find('li').addClass('exclude');
        $(this.element).find('li').each(function() {
            if (!$(this).hasClass('exclude')) {
                $(this).find('input:checkbox:first:not(:checked)').prop('checked', true).change();
            }
        });
        $(this.element).find('li').removeClass('exclude');
    },

    /**
     * Destroy plugin
     *
     * @private
     */
    _destroy: function() {
        this.element.removeClass(this.options.cssClass);

        $.Widget.prototype.destroy.call(this);
    },

    /**
     * Check if passed node is a root
     *
     * @private
     *
     * @param li node to check
     */
    _isRoot: function(li) {
        var parents = li.parentsUntil('.ui-widget-daredevel-checkboxTree');
        return 0 == parents.length;
    },

    /**
     * Mark node as collapsed
     *
     * @private
     *
     * @param li node to mark
     */
    _markAsCollapsed: function(li) {
        if (this.options.expandAnchor.length > 0) {
            li.children("span").html(this.options.expandAnchor);
        } else
        if (this.options.collapseUiIcon.length > 0) {
            li.children("span").removeClass(this.options.expandUiIcon).addClass('ui-icon ' + this.options.collapseUiIcon);
        }
        li.removeClass("expanded").addClass("collapsed");
    },

    /**
     * Mark node as expanded
     *
     * @private
     *
     * @param li node to mark
     */
    _markAsExpanded: function(li) {
        if (this.options.collapseAnchor.length > 0) {
            li.children("span").html(this.options.collapseAnchor);
        } else
        if (this.options.expandUiIcon.length > 0) {
            li.children("span").removeClass(this.options.collapseUiIcon).addClass('ui-icon ' + this.options.expandUiIcon);
        }
        li.removeClass("collapsed").addClass("expanded");
    },

    /**
     * Mark node as leaf
     *
     * @private
     *
     * @param li  node to mark
     */
    _markAsLeaf: function(li) {
        if (this.options.leafAnchor.length > 0) {
            li.children("span").html(this.options.leafAnchor);
        } else
        if (this.options.leafUiIcon.length > 0) {
            li.children("span").addClass('ui-icon ' + this.options.leafUiIcon);
        }
        li.addClass("leaf");
    },

    /**
     * Return parent li of the passed li
     *
     * @private
     *
     * @param li node
     *
     * @return parent li
     */
    _parentNode: function(li) {
        return li.parents('li:first');
    },

    /**
     * Uncheck ancestors of passed node
     *
     * Don't use uncheck() method because we won't trigger onUncheck events
     *
     * @private
     *
     * @param li node
     */
    _uncheckAncestors: function(li) {
        li.parentsUntil(".ui-widget").filter('li').find('input:checkbox:first:checked').prop('checked', false).change();
    },

    /**
     * Uncheck descendants of passed node
     *
     * Don't use uncheck() method because we won't trigger onUncheck events
     *
     * @private
     *
     * @param li node
     */
    _uncheckDescendants: function(li) {
        li.find('li input:checkbox:checked').prop('checked', false).change();
    },

    /**
     * Uncheck nodes that are neither ancestors or descendants of passed node
     *
     * Don't use uncheck() method because we won't trigger onUncheck events
     *
     * @private
     *
     * @param li node
     */
    _uncheckOthers: function(li) {
        li.addClass('exclude');
        li.parents('li').addClass('exclude');
        li.find('li').addClass('exclude');
        $(this.element).find('li').each(function() {
            if (!$(this).hasClass('exclude')) {
                $(this).find('input:checkbox:first:checked').prop('checked', false).change();
            }
        });
        $(this.element).find('li').removeClass('exclude');
    },

    /**
     * Check node
     *
     * @public
     *
     * @param li node to check
     */
    check: function(li) {

        li.find('input:checkbox:first:not(:checked)').prop('checked', true).change();

        // handle others
        if (this.options.onCheck.others == 'check') {
            this._checkOthers(li);
        } else

        if (this.options.onCheck.others == 'uncheck') {
            this._uncheckOthers(li);
        }

        // handle descendants
        if (this.options.onCheck.descendants == 'check') {
            this._checkDescendants(li);
        } else

        if (this.options.onCheck.descendants == 'uncheck') {
            this._uncheckDescendants(li);
        }

        // handle ancestors
        if (this.options.onCheck.ancestors == 'check') {
            this._checkAncestors(li);
        } else

        if (this.options.onCheck.ancestors == 'uncheck') {
            this._uncheckAncestors(li);
        } else

        if (this.options.onCheck.ancestors == 'checkIfFull') {
            if (!this._isRoot(li) && this._allDescendantChecked(this._parentNode(li))) {
                this.check(this._parentNode(li));
            }
        }
    },

    /**
     * Check all tree elements
     *
     * Don't use check() method so it won't trigger onCheck events
     *
     * @public
     */
    checkAll: function() {
        $(this.element).find('input:checkbox:not(:checked)').prop('checked', true).change();
    },

    /**
     * Collapse node
     *
     * @public
     *
     * @param li node to collapse
     */
    collapse: function(li) {
        if (li.hasClass('collapsed') || (li.hasClass('leaf'))) {
            return;
        }

        var t = this;

        li.children("ul").hide(this.options.collapseEffect, {}, this.options.collapseDuration);

        setTimeout(function() {
            t._markAsCollapsed(li, t.options);
        }, t.options.collapseDuration);

        t._trigger('collapse', li);
    },

    /**
     * Collapse all nodes of the tree
     *
     * @private
     */
    collapseAll: function() {
        var t = this;
        $(this.element).find('li.expanded').each(function() {
            t.collapse($(this));
        });
    },

    /**
     * Expand node
     *
     * @public
     *
     * @param li node to expand
     */
    expand: function(li) {
        if (li.hasClass('expanded') || (li.hasClass('leaf'))) {
            return;
        }

        var t = this;

        li.children("ul").show(t.options.expandEffect, {}, t.options.expandDuration);

        setTimeout(function() {
            t._markAsExpanded(li, t.options);
        }, t.options.expandDuration);

        t._trigger('expand', li);
    },

    /**
     * Expand all nodes of the tree
     *
     * @public
     */
    expandAll: function() {
        var t = this;
        $(this.element).find('li.collapsed').each(function() {
            t.expand($(this));
        });
    },

    /**
     * Uncheck node
     *
     * @public
     *
     * @param li node to uncheck
     */
    uncheck: function(li) {

        li.find('input:checkbox:first:checked').prop('checked', false).change();

        // handle others
        if (this.options.onUncheck.others == 'check') {
            this._checkOthers(li);
        } else

        if (this.options.onUncheck.others == 'uncheck') {
            this._uncheckOthers(li);
        }

        // handle descendants
        if (this.options.onUncheck.descendants == 'check') {
            this._checkDescendants(li);
        } else

        if (this.options.onUncheck.descendants == 'uncheck') {
            this._uncheckDescendants(li);
        }

        // handle ancestors
        if (this.options.onUncheck.ancestors == 'check') {
            this._checkAncestors(li);
        } else

        if (this.options.onUncheck.ancestors == 'uncheck') {
            this._uncheckAncestors(li);
        }

    },

    /**
     * Uncheck all tree elements
     *
     * Don't use uncheck() method so it won't trigger onUncheck events
     *
     * @public
     */
    uncheckAll: function() {
        $(this.element).find('input:checkbox:checked').prop('checked', false).change();
    },

    /**
     * Default options values
     */
    options: {
        /**
         * Defines if tree has collapse capability.
         */
        collapsable: true,
        /**
         * Defines an element of DOM that, if clicked, trigger collapseAll() method.
         * Value can be either a jQuery object or a selector string.
         * @deprecated will be removed in jquery 0.6.
         */
        collapseAllElement: '',
        /**
         * Defines duration of collapse effect in ms.
         * Works only if collapseEffect is not null.
         */
        collapseDuration: 500,
        /**
         * Defines the effect used for collapse node.
         */
        collapseEffect: 'blind',
        /**
         * Defines URL of image used for collapse anchor.
         * @deprecated will be removed in jquery 0.6.
         */
        collapseImage: '',
        /**
         * Defines jQueryUI icon class used for collapse anchor.
         */
        collapseUiIcon: 'ui-icon-triangle-1-e',
//            dataSourceType: '',
//            dataSourceUrl: '',
        /**
         * Defines an element of DOM that, if clicked, trigger expandAll() method.
         * Value can be either a jQuery object or a selector string.
         * @deprecated will be removed in jquery 0.6.
         */
        expandAllElement: '',
        /**
         * Defines duration of expand effect in ms.
         * Works only if expandEffect is not null.
         */
        expandDuration: 500,
        /**
         * Defines the effect used for expand node.
         */
        expandEffect: 'blind',
        /**
         * Defines URL of image used for expand anchor.
         * @deprecated will be removed in jquery 0.6.
         */
        expandImage: '',
        /**
         * Defines jQueryUI icon class used for expand anchor.
         */
        expandUiIcon: 'ui-icon-triangle-1-se',
        /**
         * Defines if checked node are collapsed or not at tree initializing.
         */
        initializeChecked: 'expanded', // or 'collapsed'
        /**
         * Defines if unchecked node are collapsed or not at tree initializing.
         */
        initializeUnchecked: 'expanded', // or 'collapsed'
        /**
         * Defines URL of image used for leaf anchor.
         * @deprecated will be removed in jquery 0.6.
         */
        leafImage: '',
        /**
         * Defines jQueryUI icon class used for leaf anchor.
         */
        leafUiIcon: '',
        /**
         * Defines which actions trigger when a node is checked.
         * Actions are triggered in the following order:
         * 1) node
         * 2) others
         * 3) descendants
         * 4) ancestors
         */
        onCheck: {
            /**
             * Defines action to perform on ancestors of the checked node.
             * Available values: null, 'check', 'uncheck', 'checkIfFull'.
             */
            ancestors: 'check',
            /**
             * Defines action to perform on descendants of the checked node.
             * Available values: null, 'check', 'uncheck'.
             */
            descendants: 'check',
            /**
             * Defines action to perform on checked node.
             * Available values: null, 'collapse', 'expand'.
             */
            node: '',
            /**
             * Defines action to perform on each other node (checked one excluded).
             * Available values: null, 'check', 'uncheck'.
             */
            others: ''
        },
        /**
         * Defines which actions trigger when a node is unchecked.
         * Actions are triggered in the following order:
         * 1) node
         * 2) others
         * 3) descendants
         * 4) ancestors
         */
        onUncheck: {
            /**
             * Defines action to perform on ancestors of the unchecked node.
             * Available values: null, 'check', 'uncheck'.
             */
            ancestors: '',
            /**
             * Defines action to perform on descendants of the unchecked node.
             * Available values: null, 'check', 'uncheck'.
             */
            descendants: 'uncheck',
            /**
             * Defines action to perform on unchecked node.
             * Available values: null, 'collapse', 'expand'.
             */
            node: '',
            /**
             * Defines action to perform on each other node (unchecked one excluded).
             * Available values: null, 'check', 'uncheck'.
             */
            others: ''
        }
    }

    /*
     function descendants(li) {
     return li.find('li :checkbox:checkbox');
     }

     function checkParent(li){
     parentNode(li).find(':checkbox:first:not(:checked)').each(function(){
     check(this.element.parent('li:first'), this.options);
     });
     }
     //*/
});

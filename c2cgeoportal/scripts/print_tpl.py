# -*- coding: utf-8 -*-

import os, getopt
from mako.template import Template
from mako.lookup import TemplateLookup


def main():
    """ This function build the print configuration file config.yaml using
    mako.
    The file is created in the folder print/.
    If the file print/templates/print.mako doesnt exists, the build is not 
    executed    
    """

    base_template = 'print/templates/print.mako'
    if os.path.exists(base_template):
        print "building print template"

        # DONT! add a trailing / to the lookup path, mako cant find templates otherwise
        mylookup = TemplateLookup(directories=['print/templates'])
        mytemplate = Template(filename=base_template, lookup=mylookup)

        #print mytemplate.render()
        print_template = open('print/config.yaml', 'w+')
        print_template.write(mytemplate.render().encode('UTF-8'))                    
        print_template.close() 

        print "finished building print template"
    else:
        print "no print template found, ignoring"

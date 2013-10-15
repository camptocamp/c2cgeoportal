# -*- coding: utf-8 -*-
## the leading / is needed to tell mako to look for the template using the provided TemplateLookup
<%inherit file="/A4_landscape.mako" />

## using a trailing \ to prevent new line from being inserted by mako
<%def name="title()">\
2 Inheriting A4 landscape\
</%def>

<%def name="block_logo()">
            - !text
              text: 'Put another logo here'
              fontSize: 6
</%def>

<%def name="block_text_misc()">
            - !text
              text: 'Here some other miscellaneous text'
              fontSize: 6
</%def>

# -*- coding: utf-8 -*-
## the leading / is needed to tell mako to look for the template using the provided TemplateLookup
<%inherit file="/A3_landscape.mako" />

## the backslash tell mako To Not write a new line at the end
<%def name="title()">\
2 Inheriting A3 landscape\
</%def>

<%def name="block_logo()">
        - !columns
          absoluteX: 648
          absoluteY: 88
          width: 124
          config:
            cells:
              - padding: 1
          items:
            - !text
              text: 'Put another logo here'
              fontSize: 10
</%def>

<%def name="block_text_misc()">
        - !columns
          absoluteX: 51
          absoluteY: 104
          width: 250
          config:
            cells:
              - padding: 8
          items:
            - !text
              text: 'Here some other miscellaneous text'
              fontSize: 10
</%def>
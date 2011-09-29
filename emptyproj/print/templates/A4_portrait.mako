# -*- coding: utf-8 -*-
  #===========================================================================
  ${self.title()}:
  #===========================================================================
    metaData:
      title: '<%text>$</%text>{title}'

    #-------------------------------------------------------------------------
    mainPage:
      pageSize: A4
      rotation: true
      items:
        - !map
          condition: showMap
          width: 511
          height: 692
          absoluteX: 51
          absoluteY: 808
        - !columns
          condition: showAttr
          absoluteX: 61
          absoluteY: 808
          width: 491
          config:
              borderWidth: 0.2
              borderColor: black
          items:
            - !attributes
              source: table
              tableConfig: 
                cells: 
                  - padding: 2
                    backgroundColor: #ffffff
                    borderWidthRight: 1
                    borderWidthBottom: 1
                    borderColor: black  
              columnDefs:
                col0:
                  header: !text
                    text: '<%text>$</%text>{col0}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col0}'
                        fontSize: 8
                        backgroundColor: #ffffff
                        borderColorBottom: #ffffff
                        borderWidthBottom: 1
                col1:
                  header: !text
                    text: '<%text>$</%text>{col1}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col1}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col2:
                  header: !text
                    text: '<%text>$</%text>{col2}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col2}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col3:
                  header: !text
                    text: '<%text>$</%text>{col3}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col3}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col4:
                  header: !text
                    text: '<%text>$</%text>{col4}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col4}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col5:
                  header: !text
                    text: '<%text>$</%text>{col5}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col5}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col6:
                  header: !text
                    text: '<%text>$</%text>{col6}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col6}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col7:
                  header: !text
                    text: '<%text>$</%text>{col7}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col7}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col8:
                  header: !text
                    text: '<%text>$</%text>{col8}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col8}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col9:
                  header: !text
                    text: '<%text>$</%text>{col9}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col9}'
                        fontSize: 8
                        backgroundColor: #ffffff
        - !columns
          condition: showScale
          absoluteX: 60
          absoluteY: 132
          width: 500
          items:
            - !scalebar
              maxSize: 200
              type: bar_sub
              intervals: 5
              textDirection: up
              barDirection: up
              align: left
              barSize: 3
              lineWidth: 0.3
              fontSize: 5
              labelDistance: 2
              barBgColor: #FFFFFF
        - !columns
          condition: showNorth
          absoluteX: 146
          absoluteY: 99
          width: 100
          items:
            - !image
              align: center
              maxWidth: 49
              url: '<%text>$</%text>{configDir}/north.png'
              rotation: '<%text>$</%text>{rotation}'
        - !columns
          absoluteX: 224
          absoluteY: 85
          width: 124
          config:
            cells:
              - padding: 1
          items:
${self.block_logo()}
        - !columns
          condition: showMapframe
          absoluteX: 51
          absoluteY: 808
          width: 511
          config:
            borderWidth: 0.8
            cells:
              - padding: 346
          items:
            - !text
              text: ' '
        # map border bottom only (for query result page)
        - !columns
          condition: showMapframeQueryresult
          absoluteX: 51
          absoluteY: 808
          width: 511
          config:
            borderWidthBottom: 0.8
            cells:
              - padding: 346
          items:
            - !text
              text: ' '
        - !columns
          absoluteX: 51
          absoluteY: 116
          width: 118
          config:
            cells:
              - padding: 8
          items:
${self.block_text_misc()}
        # Border arround north
        - !columns
          condition: showNorth
          absoluteX: 168
          absoluteY: 116
          width: 55
          config:
            borderWidthLeft: 0.8
            borderWidthRight: 0.8
            cells:
              - padding: 45
          items:
            - !text
              text: ' '
        # Format label
        - !columns
          absoluteX: 346
          absoluteY: 116
          width: 55
          config:
            borderWidthLeft: 0.4
            borderWidthRight: 0.4
            cells:
              - padding: 5
                paddingTop: 9
                paddingBottom: 75
          items:
            - !text
              text: 'Format'
              fontSize: 6
        # Format
        - !columns
          absoluteX: 401
          absoluteY: 116
          width: 51
          config:
            borderWidthRight: 0.4
            cells:
              - padding: 5
                paddingTop: 9
                paddingBottom: 75
          items:
            - !text
              text: 'A4'
              fontSize: 6
        # update label
        - !columns
          absoluteX: 346
          absoluteY: 94
          width: 55
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: 'Valid from'
              fontSize: 6
        # update
        - !columns
          absoluteX: 401
          absoluteY: 94
          width: 51
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: '31.12.2008'
              fontSize: 6
        # Date label
        - !columns
          absoluteX: 346
          absoluteY: 72
          width: 55
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: 'Production'
              fontSize: 6
        # Date
        - !columns
          absoluteX: 401
          absoluteY: 72
          width: 51
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: '<%text>$</%text>{now dd.MM.yyyy}'
              fontSize: 6
        # User label
        - !columns
          absoluteX: 346
          absoluteY: 49
          width: 55
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: 'In production till'
              fontSize: 6
        # User
        - !columns
          absoluteX: 401
          absoluteY: 49
          width: 51
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: ' '
              fontSize: 6
        # Title
        - !columns
          absoluteX: 450
          absoluteY: 118
          width: 118
          config:
            cells:
              - padding: 8
          items:
            - !text
              text: '<%text>$</%text>{title}'
              fontSize: 10
        # Comment
        - !columns
          absoluteX: 450
          absoluteY: 95
          width: 118
          config:
            cells:
              - padding: 8
          items:
            - !text
              text: '<%text>$</%text>{comment}'
              fontSize: 7
        # Scale
        - !columns
          condition: showScalevalue
          absoluteX: 450
          absoluteY: 116
          width: 118
          config:
            cells:
              - padding: 8
                paddingTop: 75
          items:
            - !text
              text: '1:<%text>$</%text>{scale}'
              fontSize: 10
        # Border
        - !columns
          absoluteX: 51
          absoluteY: 116
          width: 511
          config:
            borderWidth: 0.8
            borderWidthTop: 0
            cells:
              - padding: 39
          items:
            - !text
              text: ' '

## the backslash tell mako To Not write a new line at the end
<%def name="title()">\
1 A4 portrait\
</%def>

<%def name="block_logo()">
            - !text
              text: 'Put your logo here'
              fontSize: 6
</%def>

<%def name="block_text_misc()">
            - !text
              text: 'Here some miscellaneous text'
              fontSize: 6
</%def>
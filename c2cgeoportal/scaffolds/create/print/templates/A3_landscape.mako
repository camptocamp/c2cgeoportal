# -*- coding: utf-8 -*-
## start of global template code
  #===========================================================================
  ${self.title()}:
  #===========================================================================
    metaData:
      title: '<%text>$</%text>{title}'

    #-------------------------------------------------------------------------
    mainPage:
      pageSize: A3
      rotation: true
      landscape: true
      items:
${self.block_logo()}
        - !map
          condition: showMap
          width: 1100
          height: 704
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
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col0}'
                        fontSize: 5
                        backgroundColor: #ffffff
                        borderColorBottom: #ffffff
                        borderWidthBottom: 1
                col1:
                  header: !text
                    text: '<%text>$</%text>{col1}'
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col1}'
                        fontSize: 5
                        backgroundColor: #ffffff
                col2:
                  header: !text
                    text: '<%text>$</%text>{col2}'
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col2}'
                        fontSize: 5
                        backgroundColor: #ffffff
                col3:
                  header: !text
                    text: '<%text>$</%text>{col3}'
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col3}'
                        fontSize: 5
                        backgroundColor: #ffffff
                col4:
                  header: !text
                    text: '<%text>$</%text>{col4}'
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col4}'
                        fontSize: 5
                        backgroundColor: #ffffff
                col5:
                  header: !text
                    text: '<%text>$</%text>{col5}'
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col5}'
                        fontSize: 5
                        backgroundColor: #ffffff
                col6:
                  header: !text
                    text: '<%text>$</%text>{col6}'
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col6}'
                        fontSize: 5
                        backgroundColor: #ffffff
                col7:
                  header: !text
                    text: '<%text>$</%text>{col7}'
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col7}'
                        fontSize: 5
                        backgroundColor: #ffffff
                col8:
                  header: !text
                    text: '<%text>$</%text>{col8}'
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col8}'
                        fontSize: 5
                        backgroundColor: #ffffff
                col9:
                  header: !text
                    text: '<%text>$</%text>{col9}'
                    fontSize: 6
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col9}'
                        fontSize: 5
                        backgroundColor: #ffffff
        - !columns
          condition: showScale
          absoluteX: 60
          absoluteY: 120
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
              fontSize: 8
              labelDistance: 4
              barBgColor: #FFFFFF
        - !columns
          condition: showNorth
          absoluteX: 557
          absoluteY: 92
          width: 100
          items:
            - !image
              align: center
              maxWidth: 49
              url: '<%text>$</%text>{configDir}/north.png'
              rotation: '<%text>$</%text>{rotation}'
        # map border
        - !columns
          condition: showMapframe
          absoluteX: 51
          absoluteY: 808
          width: 1100
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
          width: 1100
          config:
            borderWidthBottom: 0.8
            cells:
              - padding: 346
          items:
            - !text
              text: ' '
${self.block_text_misc()}
        # left text block separator
        - !columns
          absoluteX: 300
          absoluteY: 104
          width: 10
          config:
            borderWidthLeft: 0.8
            cells:
              - padding: 39
          items:
            - !text
              text: ' '
        # north block border
        - !columns
          condition: showNorth
          absoluteX: 567
          absoluteY: 104
          width: 80
          config:
            borderWidthLeft: 0.8
            borderWidthRight: 0.8
            cells:
              - padding: 33
          items:
            - !text
              text: ' '
        # legend separator
        - !columns
          absoluteX: 850
          absoluteY: 104
          width: 60
          config:
            borderWidthLeft: 0.4
            borderWidthRight: 0.4
            cells:
              - padding: 5
                paddingTop: 9
                paddingBottom: 63
          items:
            - !text
              text: 'Format'
              fontSize: 6
        - !columns
          absoluteX: 910
          absoluteY: 104
          width: 45
          config:
            borderWidthRight: 0.4
            cells:
              - padding: 5
                paddingTop: 9
                paddingBottom: 63
          items:
            - !text
              text: 'A4'
              fontSize: 6
        - !columns
          absoluteX: 850
          absoluteY: 78
          width: 60
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: 'Production'
              fontSize: 6
        - !columns
          absoluteX: 910
          absoluteY: 78
          width: 45
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: '<%text>$</%text>{now dd.MM.yyyy}'
              fontSize: 6
        - !columns
          absoluteX: 850
          absoluteY: 52
          width: 60
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: 'In production till'
              fontSize: 6
        - !columns
          absoluteX: 910
          absoluteY: 52
          width: 45
          config:
            borderWidthTop: 0.4
            cells:
              - padding: 5
                paddingTop: 9
          items:
            - !text
              text: ' '
              fontSize: 6
        - !columns
          absoluteX: 955
          absoluteY: 104
          width: 195
          config:
            cells:
              - padding: 8
          items:
            - !text
              text: '<%text>$</%text>{title}'
              fontSize: 9
        - !columns
          absoluteX: 955
          absoluteY: 90
          width: 195
          config:
            cells:
              - padding: 8
          items:
            - !text
              text: '<%text>$</%text>{comment}'
              fontSize: 9
        - !columns
          condition: showScalevalue
          absoluteX: 955
          absoluteY: 116
          width: 195
          config:
            cells:
              - padding: 8
                paddingTop: 72
          items:
            - !text
              text: '1:<%text>$</%text>{scale}'
              fontSize: 9
        - !columns
          absoluteX: 51
          absoluteY: 104
          width: 1100
          config:
            borderWidth: 0.8
            borderWidthTop: 0
            cells:
              - padding: 33
          items:
            - !text
              text: ' '

## end of global template code
## start of block specific code

## the backslash tell mako To Not write a new line at the end
<%def name="title()">\
2 A3 landscape\
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
              text: 'Put your logo here'
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
              text: 'Here some miscellaneous text'
              fontSize: 10
</%def>
## end of block specific code
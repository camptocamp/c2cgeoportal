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
      landscape: true
      items:
        - !map
          condition: showMap
          width: 774
          height: 450
          absoluteX: 40
          absoluteY: 480

        # Date
        - !columns
          absoluteX: 100
          absoluteY: 523
          width: 80
          items:
            - !text
              text: 'Date: <%text>$</%text>{now dd.MM.yyyy}'
              fontSize: 7
        # show logo
        - !columns
          absoluteX: 44
          absoluteY: 563
          width: 161
          items:
${self.block_logo()}
        # Border around date and logo
        - !columns
          absoluteX: 40
          absoluteY: 571
          width: 168
          config:
            #borderWidthBottom: 0.8
            borderWidthRight: 0.8
            cells:
              - padding: 25
          items:
            - !text
              text: ' '
        # Title
        - !columns
          absoluteX: 215
          absoluteY: 569
          width: 430
          items:
            - !text
              text: '<%text>$</%text>{title}'
              fontSize: 11
        # Comment
        - !columns
          absoluteX: 215
          absoluteY: 556
          width: 430
          items:
            - !text
              text: '<%text>$</%text>{comment}'
              fontSize: 7
        # show auszug
        - !columns
          absoluteX: 215
          absoluteY: 545
          width: 430
          items:
            - !text
              text: 'Some text 1'
              fontSize: 9
        - !columns
          absoluteX: 215
          absoluteY: 533
          width: 430
          items:
            - !text
              text: 'Some text 2'
              fontSize: 7
        - !columns
          absoluteX: 215
          absoluteY: 525
          width: 430
          items:
            - !text
              text: 'Some text 3'
              fontSize: 7
        # Border arround auszug
        - !columns
          absoluteX: 210
          absoluteY: 571
          width: 449
          config:
            borderWidthRight: 0.8
            #borderWidthBottom: 0.8
            cells:
              - padding: 25
          items:
            - !text
              text: ' '
        # show north
        - !columns
          condition: showNorth
          absoluteX: 658
          absoluteY: 559
          width: 45
          items:
            - !image
              align: center
              maxWidth: 25
              url: '<%text>$</%text>{configDir}/north.png'
              rotation: '<%text>$</%text>{rotation}'
        # Border arround north
        - !columns
          condition: showNorth
          absoluteX: 659
          absoluteY: 571
          width: 45
          config:
            borderWidthRight: 0.8
            #borderWidthBottom: 0.8
            cells:
              - paddingTop: 25
              - paddingBottom: 25
          items:
            - !text
              text: ' '
        # Scalevalue
        - !columns
          condition: showScalevalue
          absoluteX: 682
          absoluteY: 560
          width: 125
          config:
            cells:
              - padding: 10
                paddingLeft: 30
          items:
            - !text
              text: 'Scale 1:<%text>$</%text>{scale}'
              fontSize: 7
        # show scale
        - !columns
          condition: showScale
          absoluteX: 711
          absoluteY: 532
          width: 90
          items:
            - !scalebar
              type: line
              minSize: 90
              maxSize: 90
              intervals: 3
              textDirection: up
              barDirection: up
              align: left
              barSize: 3
              lineWidth: 0.8
              fontSize: 6
              labelDistance: 2
              barBgColor: #FFFFFF
        # Border arround scale
        - !columns
          condition: showScalevalue
          absoluteX: 704
          absoluteY: 571
          width: 110
          config:
            #borderWidthBottom: 0.8
            cells:
              - padding: 25
          items:
            - !text
              text: ' '
        # info
        - !columns
          absoluteX: 50
          absoluteY: 505
          width: 754
          items:
            - !text
              text: 'Some text 4'
              fontSize: 8

        # border info top
        - !columns
          absoluteX: 40
          absoluteY: 509.8
          width: 774
          config:
            borderWidthTop: 0.8
          items:
            - !text
              text: ' '

        # show mapframe
        - !columns
          condition: showMapframe
          absoluteX: 40
          absoluteY: 480
          width: 774
          config:
            borderWidth: 0.8
            borderWidthTop: 0
            cells:
              - padding: 219
          items:
            - !text
              text: ' '
        # map border bottom only (for query result page)
        # - !columns
          # condition: showMapframeQueryresult
          # absoluteX: 40
          # absoluteY: 480
          # width: 774
          # config:
            # borderWidthBottom: 0.8
            # cells:
              # - padding: 219
          # items:
            # - !text
              # text: ' '

        # Border
        - !columns
          absoluteX: 40
          absoluteY: 571
          width: 774
          config:
            borderWidth: 0.8
            #borderWidthBottom: 0
            cells:
              - padding: 40
          items:
            - !text
              text: ' '

        - !columns
          condition: showAttr
          absoluteX: 40
          absoluteY: 450
          width: 774
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
                col10:
                  header: !text
                    text: '<%text>$</%text>{col10}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col10}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col11:
                  header: !text
                    text: '<%text>$</%text>{col11}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col11}'
                        fontSize: 8
                        backgroundColor: #ffffff  
                col12:
                  header: !text
                    text: '<%text>$</%text>{col12}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col12}'
                        fontSize: 8
                        backgroundColor: #ffffff
                col13:
                  header: !text
                    text: '<%text>$</%text>{col13}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col13}'
                        fontSize: 8
                        backgroundColor: #ffffff 
                col14:
                  header: !text
                    text: '<%text>$</%text>{col14}'
                    font: Helvetica-Bold
                    fontSize: 8
                    backgroundColor: #ffffff
                  cell: !columns
                    items:
                      - !text
                        text: '<%text>$</%text>{col14}'
                        fontSize: 8
                        backgroundColor: #ffffff   

    lastPage:
      pageSize: A4
      landscape: true
      items:
         - !columns
          condition: legends
          absoluteX: 45
          absoluteY: 571
          width: 750
          items:
            - !legends
              horizontalAlignment: left
              inline: false
              defaultScale: 0.5
              maxHeight: 500
              maxWidth: 700
              iconMaxHeight: 0
              iconMaxWidth: 0
              columnMargin: 5
              classIndentation: 3
              classSpace: 5
              layerSpace: 5
              backgroundColor: white
              layerFontSize: 8

<%def name="title()">\
2 A4 landscape\
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

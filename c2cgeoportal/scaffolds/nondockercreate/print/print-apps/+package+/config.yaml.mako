throwErrorOnExtraParameters: true

templates:
    1 A4 portrait: !template
        reportTemplate: A4_Portrait.jrxml
        attributes:
            title: !string &title
                default: ""
            comments: !string &comments
                default: ""
            debug: !boolean &debug
                default: false
            legend: !legend &legend {}
            northArrow: !northArrow &northArrow
                size: 40
                default:
                    graphic: "file:///north.svg"
            scalebar: !scalebar &scalebar
                width: 150
                height: 20
                default:
                     fontSize: 8
            map: !map &map
                maxDpi: 254
                dpiSuggestions: [254]
                zoomLevels: !zoomLevels
                    scales: [100, 250, 500, 2500, 5000, 10000, 25000, 50000, 100000, 500000]
                width: 555
                height: 675
            datasource: !datasource &datasource
                attributes:
                    title: !string {}
                    table: !table {}

        processors: &processors
        - !reportBuilder # compile all reports in current directory
            directory: '.'
        - !configureHttpRequests &configureHttpRequests
            httpProcessors:
            - !mapUri
                mapping:
                    (https?)://${__import__('re').escape(host)}/(.*): "http://127.0.0.1/$2"
            - !forwardHeaders
                matchers:
                - !localMatch {}
                headers:
                - Cookie
                - Host
            - !forwardHeaders
                headers:
                - Referer
            - !restrictUris
                matchers:
                - !localMatch
                  pathRegex: /${__import__('re').escape(instanceid)}/wsgi/mapserv_proxy
                - !localMatch
                  pathRegex: /${__import__('re').escape(instanceid)}/tiles/.*
                - !localMatch
                  reject: true
                - !ipMatch
                  ip: 10.0.0.0
                  mask: 255.0.0.0
                  reject: true
                - !ipMatch
                  ip: 172.16.0.0
                  mask: 255.240.0.0
                  reject: true
                - !ipMatch
                  ip: 192.168.0.0
                  mask: 255.255.0.0
                  reject: true
                - !acceptAll {}
        - !prepareLegend
            template: legend.jrxml
        - !createNorthArrow {}
        - !createScalebar {}
        - !createMap {}
        - !createDataSource
            processors:
            - !prepareTable
                dynamic: true
                columns:
                    icon: !urlImage
                        urlExtractor: (.*)
                        urlGroup: 1

    2 A4 landscape: !template
        reportTemplate: A4_Landscape.jrxml
        attributes:
            title: *title
            comments: *comments
            debug: *debug
            legend: *legend
            northArrow: *northArrow
            scalebar: *scalebar
            map: !map
                <<: *map
                width: 800
                height: 441
            datasource: *datasource
        processors: *processors

    3 A3 portrait: !template
        reportTemplate: A3_Portrait.jrxml
        attributes:
            title: *title
            comments: *comments
            debug: *debug
            legend: *legend
            northArrow: *northArrow
            scalebar: *scalebar
            map: !map
               <<: *map
               width: 800
               height: 1000
            datasource: *datasource
        processors: *processors

    4 A3 landscape: !template
        reportTemplate: A3_Landscape.jrxml
        attributes:
            title: *title
            comments: *comments
            debug: *debug
            legend: *legend
            northArrow: *northArrow
            scalebar: *scalebar
            map: !map
                <<: *map
                width: 1150
                height: 673
            datasource: *datasource
        processors: *processors

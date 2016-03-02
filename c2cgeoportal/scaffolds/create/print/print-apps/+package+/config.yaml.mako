throwErrorOnExtraParameters: true

templates:
    1 A4 portrait: !template
        reportTemplate: A4_Portrait.jrxml
        attributes:
            title: !string
                default: ""
            comments: !string
                default: ""
            debug: !boolean
                default: false
            legend: !legend {}
            northArrow: !northArrow
                size: 40
                default:
                    graphic: "file:///north.svg"
            scalebar: !scalebar
                width: 150
                height: 20
                default:
                     fontSize: 8
            map: !map
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
                matchers:
                - !dnsMatch
                    host: ${host}
                mapping:
                    (https?)://${host}/(.*): "http://127.0.0.1/$2"
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
                  pathRegex: "/${instanceid}/wsgi/mapserv_proxy"
                - !localMatch
                  pathRegex: "/${instanceid}/tiles/.*"
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

#    A4 landscape: !template
#        reportTemplate: A4_Landscape.jrxml
#        attributes: &attributes
#            title: !string
#                default: ""
#            comments: !string
#                default: ""
#            debug: !boolean
#                default: false
#            legend: !legend {}
#            northArrow: !northArrow
#                size: 40
#                default:
#                    graphic: "file:///north.svg"
#            scalebar: !scalebar
#                width: 150
#                height: 20
#                default:
#                     fontSize: 8
#            map: !map
#                maxDpi: 254
#                dpiSuggestions: [254]
#                zoomLevels: !zoomLevels
#                    scales: [100, 250, 500, 2500, 5000, 10000, 25000, 50000, 100000, 500000]
#                width: 555
#                height: 675
#            datasource: !datasource *datasource
#        processors: *processors

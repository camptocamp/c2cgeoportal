grids:
    # grid name, I just recommends to add the min resolution because it's common to not generate all the layers at the same resolution.
    swissgrid_05:
        # resolutions [required]
        resolutions: [1000, 500, 250, 100, 50, 20, 10, 5, 2, 1, 0.5]
        # bbox [required]
        bbox: [420000, 30000, 900000, 350000]
        # srs [required]
        srs: EPSG:21781

caches:
    local:
        type: filesystem
        folder: /var/sig/tiles
        wmtscapabilities_file: ${wmtscapabilities_path}
        # for GetCapabilities
        http_url: https://%(host)s/tiles/
        hosts:
        - wmts0.<host>
        - wmts1.<host>
        - wmts2.<host>
        - wmts3.<host>
        - wmts4.<host>
    s3:
        type: s3
        bucket: tiles
        folder: ''
        # for GetCapabilities
        http_url: https://%(host)s/%(bucket)s/%(folder)s/
        cache_control: 'public, max-age=14400'
        hosts:
        - wmts0.<host>

# this defines some defaults values for all the layers
defaults:
    layer: &layer
        type: wms
        grid: swissgrid_05
        # The minimum resolution to seed, useful to use with mapcache, optional.
        # min_resolution_seed: 1
        # the URL of the WMS server to used
        url: http://localhost${entry_point}mapserv
        # Set the headers to get the right virtual host, and don't get any cached result
        headers:
            Host: ${host}
            Cache-Control: no-cache, no-store
            Pragma: no-cache
        # file name extension
        extension: png
        # the bbox there we want to generate tiles
        #bbox: [493000, 114000, 586000, 204000]

        # mime type used for the WMS request and the WMTS capabilities generation
        mime_type: image/png
        wmts_style: default
        # the WMTS dimensions definition [default to []]
        #dimensions:
        #    -   name: DATE
        #        # the default value for the WMTS capabilities
        #        default: '2012'
        #        # the generated values
        #        generate: ['2012']
        #        # all the available values in the WMTS capabilities
        #        values: ['2012']
        # the meta tiles definition [default to off]
        meta: on
        # the meta tiles size [default to 8]
        meta_size: 8
        # the meta tiles buffer [default to 128]
        meta_buffer: 128
        # connexion an sql to get geometries (in column named geom) where we want to generate tiles
        # Warn: too complex result can slow down the application
#    connection: user=www-data password=www-data dbname=<db> host=localhost
#    geoms:
#        -   sql: <column> AS geom FROM <table>
        # size and hash used to detect empty tiles and metatiles [optional, default to None]
        empty_metatile_detection:
            size: 740
            hash: 3237839c217b51b8a9644d596982f342f8041546
        empty_tile_detection:
            size: 921
            hash: 1e3da153be87a493c4c71198366485f290cad43c

layers:
    plan:
        <<: *layer
        layers: plan
    ortho:
        <<: *layer
        layers: ortho
        extension: jpeg
        mime_type: image/jpeg
        # no buffer needed on rater sources
        meta_buffer: 0
        empty_metatile_detection:
            size: 66163
            hash: a9d16a1794586ef92129a2fb41a739451ed09914
        empty_tile_detection:
            size: 1651
            hash: 2892fea0a474228f5d66a534b0b5231d923696da

generation:
    default_cache: local
    # used to allowed only a specific user to generate tiles (for rights issue)
    authorised_user: www-data

    # maximum allowed consecutive errors, after it exit [default to 10]
    maxconsecutive_errors: 10

apache:
    location: ${entry_point}tiles

mapcache:
    config_file: apache/mapcache.xml
    location: ${entry_point}mapcache
    memcache_host: localhost
    memcache_port: 11211

process:
    optipng_test:
    -   cmd: optipng -o7 -simulate %(in)s
    optipng:
    -   cmd: optipng %(args)s -q -zc9 -zm8 -zs3 -f5 %(in)s
        arg:
            default: '-q'
            quiet: '-q'
    jpegoptim:
    -   cmd: jpegoptim %(args)s --strip-all --all-normal -m 90 %(in)s
        arg:
            default: '-q'
            quiet: '-q'

openlayers:
    # srs, center_x, center_y [required]
    srs: EPSG:21781
    center_x: 600000
    center_y: 200000

metadata:
    title: Some title
    abstract: Some abstract
    servicetype: OGC WMTS
    keywords:
    - some
    - keywords
    fees: None
    access_constraints: None

provider:
    name: The provider name
    url: The provider URL
    contact:
        name: The contact name
        position: The position name
        info:
            phone:
                voice: +41 11 222 33 44
                fax: +41 11 222 33 44
            address:
                delivery: Address delivery
                city: Berne
                area: BE
                postal_code: 3000
                country: Switzerland
                email: info@example.com

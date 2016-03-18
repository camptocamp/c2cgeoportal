#
# MapServer Mapfile
#
# Test requests:
#
# WMS GetCapabilities:
# /mapserv?service=wms&version=1.1.1&request=getcapabilities
#
# WMS GetMap:
# /mapserv?service=wms&version=1.1.1&request=getmap&bbox=-180,-90,180,90&layers=countries&width=600&height=400&srs=EPSG:4326&format=image/png
#
# WMS GetFeatureInfo:
# /mapserv?service=wms&version=1.1.1&request=getfeatureinfo&bbox=-180,-90,180,90&layers=countries&query_layers=countries&width=600&height=400&srs=EPSG:4326&format=image/png&x=180&y=90&info_format=application/vnd.ogc.gml
#

MAP
    NAME "geoportal"

    # For Windows users: uncomment this line and adapt it to your
    # own mapserver's nad folder (use regular slash "/")
    # CONFIG "PROJ_LIB" "C:/path/to/ms4w/proj/nad"

    EXTENT 420000 30000 900000 350000 ##
    UNITS METERS

    # RESOLUTION and DEFRESOLUTION default to 96. If you
    # change RESOLUTION to some other value, also change
    # DEFRESOLUTION. See
    # http://mapserver.org/development/rfc/ms-rfc-55.html
    RESOLUTION 96 ## Also set in Openlayers especially for legends
    DEFRESOLUTION 96

    # MAXSIZE shouldn't be less than 5000 for MF print on A3
    MAXSIZE 5000

    SHAPEPATH '/var/sig/c2cgeoportal'

    IMAGECOLOR 255 255 255
    STATUS ON

    FONTSET "fonts.conf"
    #SYMBOLSET "symbole.sym"

    OUTPUTFORMAT
        NAME jpeg
        DRIVER "AGG/JPEG"
        MIMETYPE "image/jpeg"
        IMAGEMODE RGB
        EXTENSION "jpeg"
        FORMATOPTION "QUALITY=75,PROGRESSIVE=TRUE"
    END

    OUTPUTFORMAT
        NAME png
        DRIVER AGG/PNG
        MIMETYPE "image/png"
        IMAGEMODE RGBA
        EXTENSION "png"
        FORMATOPTION "INTERLACE=OFF"
        FORMATOPTION "QUANTIZE_DITHER=OFF"
        FORMATOPTION "QUANTIZE_FORCE=ON"
        FORMATOPTION "QUANTIZE_COLORS=256"
    END

    PROJECTION
        "init=epsg:21781"
    END

    WEB
        METADATA
            "wms_title" "changeme"
            "wms_abstract" "changeme"
            "wms_onlineresource" "http://${host}/${instanceid}/wsgi/mapserv_proxy"
            "wms_srs" "EPSG:21781"
            "wms_encoding" "UTF-8"
            "wms_enable_request" "*"
            "wfs_enable_request" "!*"
            "wfs_encoding" "UTF-8"
        END
    END

    LEGEND
        LABEL
            ENCODING "UTF-8"
            TYPE TRUETYPE
            FONT "Arial"
            SIZE 9
        END
    END

    # restricted access layer
    LAYER
        NAME 'layer_name'
        TYPE POLYGON
        TEMPLATE fooOnlyForWMSGetFeatureInfo # For GetFeatureInfo
        EXTENT 420000 30000 900000 350000
        CONNECTIONTYPE postgis
        PROCESSING "CLOSE_CONNECTION=DEFER" # For performance
        CONNECTION "${mapserver_connection}"
        # Example data for secured layer by restriction area
        DATA "geometrie FROM (SELECT geo.* FROM geodata.table AS geo WHERE ST_Contains((${mapfile_data_subselect} 'layer_name'), ST_SetSRID(geo.geometrie, 21781))) as foo using unique id using srid=21781"
        # Example data for secured layer by role (without any area)
        #DATA "geometrie FROM (SELECT geo.geom as geom FROM geodata.table AS geo WHERE %role_id% IN (${mapfile_data_noarea_subselect} 'layer_name')) as foo USING UNIQUE gid USING srid=21781"
        # Example data for public layer
        #DATA "geometrie FROM (SELECT geo.geom as geom FROM geodata.table AS geo) AS foo USING UNIQUE gid USING srid=21781"
        METADATA
            "wms_title" "layer_name" # For WMS
            "wms_srs" "EPSG:21781" # For WMS

            "wfs_enable_request" "*" # Enable WFS for this layer
            "gml_include_items" "all" # For GetFeatureInfo and WFS GetFeature (QueryBuilder)
            "ows_geom_type" "polygon" # For returning geometries in GetFeatureInfo
            "ows_geometries" "geom" # For returning geometries in GetFeatureInfo

            "wms_metadataurl_href" "http://www.example.com/bar" # For metadata URL
            "wms_metadataurl_format" "text/html" # For metadata URL
            "wms_metadataurl_type" "TC211" # For metadata URL

            ${mapserver_layer_metadata} # For secured layers
        END
        VALIDATION
            ${mapserver_layer_validation} # For secured layers
        END
        STATUS ON
        PROJECTION
          "init=epsg:21781"
        END
        TOLERANCE 10
        TOLERANCEUNITS pixels
        CLASS
            NAME "countries"
            OUTLINECOLOR 0 0 0
        END
    END

    # raster layer (with a tile index)
    LAYER
        NAME 'topo'
        GROUP 'plan'
        TYPE RASTER
        STATUS ON
        PROCESSING "RESAMPLE=AVERAGE"
        TILEINDEX "raster/topo"
        TILEITEM "LOCATION"
        MINSCALEDENOM 25000
    END
END

MAP
    NAME "c2cgeoportail"

    EXTENT 420000 40500 839000 306400
    UNITS dd

    # MAXSIZE should not be less than 4000 for MF print
    MAXSIZE 4000

    SHAPEPATH ''

    IMAGECOLOR 255 255 255
    STATUS ON

    #FONTSET "fonts.conf"
    #SYMBOLSET "symbole.sym"

    OUTPUTFORMAT
        NAME jpeg
        DRIVER "AGG/JPEG"
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
    END

    PROJECTION
        "init=epsg:21781"
    END

    WEB
        METADATA
            "wms_title" "changeme"
            "wms_abstract" "changeme"
            "wms_onlineresource" "changeme"
            "wms_encoding" "UTF-8"
            "wms_enable_request" "*"
            "ows_title" "changeme"
            "ows_enable_request" "*"
            "ows_encoding" "UTF-8"
        END
    END

    SYMBOL
        NAME "square"
        TYPE vector
        POINTS
            0 0
            0 1
            1 1
            1 0
            0 0
        END
        FILLED true
    END

    LAYER
        NAME "testpoint_unprotected"
        GROUP "testpoint_group"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        METADATA
            "wms_title" "countries"
            # gml_ settings for GetFeatureInfo
            "gml_include_items" "all"
            "gml_exclude_items" "id"
            "gml_geometries" "the_geom"
            "gml_the_geom_type" "point"
            "gml_types" "auto"
            "gml_featureid" "id"
        END
        DUMP TRUE # for GetFeatureInfo
        TEMPLATE "template"
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            NAME "testpoint_unprotected"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "testpoint_protected"
        GROUP "testpoint_group"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from (SELECT tp.* FROM main.testpoint AS tp, ${mapserver_join_tables} WHERE ST_Contains(${mapserver_join_area}, ST_GeomFromText(ST_AsText(tp.the_geom), 21781)) AND ${mapserver_join_where} 'testpoint_protected') as foo using unique id using srid=21781"
        METADATA
            "wms_title" "countries"
            # gml_ settings for GetFeatureInfo
            "gml_include_items" "all"
            "gml_exclude_items" "id"
            "gml_geometries" "the_geom"
            "gml_the_geom_type" "point"

            ${mapserver_layer_metadata}
        END
        VALIDATION
            ${mapserver_layer_validation}
        END
        DUMP TRUE # for GetFeatureInfo
        TEMPLATE "template"
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            NAME "testpoint_protected"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "testpoint_protected_2"
        GROUP "testpoint_group_2"
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from (SELECT tp.* FROM main.testpoint AS tp, ${mapserver_join_tables} WHERE ST_Contains(${mapserver_join_area}, ST_GeomFromText(ST_AsText(tp.the_geom), 21781)) AND ${mapserver_join_where} 'testpoint_protected_2') as foo using unique id using srid=21781"
        METADATA
            "wms_title" "countries"
            # gml_ settings for GetFeatureInfo
            "gml_include_items" "all"
            "gml_exclude_items" "id"
            "gml_geometries" "the_geom"
            "gml_the_geom_type" "point"

            ${mapserver_layer_metadata}
        END
        DUMP TRUE # for GetFeatureInfo
        TEMPLATE "template"
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            NAME "testpoint_protected"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "testpoint_protected_query_with_collect"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from (SELECT tp.* FROM main.testpoint AS tp WHERE ST_Contains((${mapfile_data_subselect} 'testpoint_protected_query_with_collect'), ST_SetSRID(tp.the_geom, 21781))) as foo using unique id using srid=21781"
        METADATA
            "wms_title" "countries"
            # gml_ settings for GetFeatureInfo
            "gml_include_items" "all"
            "gml_exclude_items" "id"
            "gml_geometries" "the_geom"
            "gml_the_geom_type" "point"

            ${mapserver_layer_metadata}
        END
        VALIDATION
            ${mapserver_layer_validation}
        END
        DUMP TRUE # for GetFeatureInfo
        TEMPLATE "template"
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            NAME "testpoint_protected"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "testpoint_substitution"
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom FROM (SELECT * FROM main.testpoint WHERE name='%s_name%') AS test USING UNIQUE id USING srid=21781"
        METADATA
            "wms_title" "countries"
            # gml_ settings for GetFeature
            "gml_include_items" "all"
            "gml_exclude_items" "id"
            "gml_geometries" "the_geom"
            "gml_the_geom_type" "point"
            "gml_types" "auto"

            "s_name_validation_pattern" "^[a-z]*$$"
            "default_s_name" "foo"
        END
        VALIDATION
            "s_name" "^[a-z]*$"
            "default_s_name" "foo"
        END
        DUMP TRUE # for GetFeatureInfo
        TEMPLATE "template"
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            NAME "testpoint_substitution"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "testpoint_column_restriction"
        TYPE POINT
        EXTENT 420000 40500 839000 306400
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom FROM (SELECT the_geom, id, %s_cols% FROM main.testpoint) AS test USING UNIQUE id USING srid=21781"
        METADATA
            "wms_title" "countries"
            # gml_ settings for GetFeature
            "gml_include_items" "all"
            "gml_exclude_items" "id"
            "gml_geometries" "the_geom"
            "gml_the_geom_type" "point"
            "gml_types" "auto"

            "s_cols_validation_pattern" "^[a-z,]*$$"
            "default_s_cols" "name"
        END
        VALIDATION
            "s_cols" "^[a-z,]*$"
            "default_s_cols" "name"
        END
        DUMP TRUE # for GetFeatureInfo
        TEMPLATE "template"
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            NAME "testpoint_column_restriction"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "test_wmsfeatures"
        GROUP "test_wmsfeaturesgroup"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        METADATA
            "wms_title" "countries"
            # gml_ settings for GetFeatureInfo
            "gml_include_items" "all"
            "gml_exclude_items" "id"
            "gml_geometries" "the_geom"
            "gml_the_geom_type" "point"
            "gml_types" "auto"
            "wms_metadataurl_href" "http://example.com/wmsfeatures.metadata"
            "wms_metadataurl_format" "text/plain"
            "wms_metadataurl_type" "TC211"
        END
        DUMP TRUE # for GetFeatureInfo
        TEMPLATE "template"
        MINSCALEDENOM 5000
        MAXSCALEDENOM 25000
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            NAME "test_wmsfeatures"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "test_wmstime"
        GROUP "test_wmstimegroup"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        METADATA
            "wms_title" "time"
            "wms_timeextent" "2000/2010/P1Y"
            "wms_timeitem" "date"
            "wms_timedefault" "2000"
        END
        PROJECTION
           "init=epsg:21781"
        END
        MINSCALEDENOM 5000
        MAXSCALEDENOM 25000
        CLASS
            NAME "test_wmstime"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "test_wmstime2"
        GROUP "test_wmstimegroup"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        METADATA
            "wms_title" "time"
            "wms_timeextent" "2015/2020/P1Y"
            "wms_timeitem" "date"
            "wms_timedefault" "2015"
        END
        PROJECTION
           "init=epsg:21781"
        END
        MINSCALEDENOM 5000
        MAXSCALEDENOM 25000
        CLASS
            NAME "testpoint_unprotected"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "__test_public_layer"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        METADATA
        END
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "__test_private_layer"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

% for n in range(10):
    LAYER
        NAME "__test_private_layer${n}"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        PROJECTION
           "init=epsg:21781"
        END
    END
% endfor

    LAYER
        NAME "__test_public_layer_bis"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "__test_private_layer_bis"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

    LAYER
        NAME "__test_layer_internal_wms"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        PROJECTION
           "init=epsg:21781"
        END
        FEATURE
          WKT "POINT(0 0)"
        END
        CLASS
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END

% for name, hasMin, hasMax in [("noscale", False, False), ("minscale", True, False), ("maxscale", False, True), ("boothscale", True, True)]:
    LAYER
        NAME "test_${name}"
        EXTENT 420000 40500 839000 306400
        TYPE POINT
        STATUS ON
        CONNECTIONTYPE postgis
        CONNECTION "user=${dbuser} password=${dbpassword} dbname=${db} host=${dbhost}"
        DATA "the_geom from main.testpoint using unique id using srid=21781"
        METADATA
            "wms_title" "countries"
            # gml_ settings for GetFeatureInfo
            "gml_include_items" "all"
            "gml_exclude_items" "id"
            "gml_geometries" "the_geom"
            "gml_the_geom_type" "point"
            "gml_types" "auto"
            "wms_metadataurl_href" "http://example.com/wmsfeatures.metadata"
            "wms_metadataurl_format" "text/plain"
            "wms_metadataurl_type" "TC211"
        END
        DUMP TRUE # for GetFeatureInfo
        TEMPLATE "template"
% if hasMin:
        MINSCALEDENOM 5000
% endif
% if hasMax:
        MAXSCALEDENOM 25000
% endif
        PROJECTION
           "init=epsg:21781"
        END
        CLASS
            NAME "test_wmsfeatures"
            STYLE
                SYMBOL "square"
                SIZE 16
                COLOR 0 0 0
                OUTLINECOLOR 0 0 0
            END
        END
    END
% endfor
END

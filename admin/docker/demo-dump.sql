--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.10
-- Dumped by pg_dump version 9.5.10

-- Started on 2017-12-06 14:59:27 CET

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET search_path = main, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;


CREATE SCHEMA main AUTHORIZATION "www-data";


-- Function: main.on_role_name_change()

-- DROP FUNCTION main.on_role_name_change();

CREATE OR REPLACE FUNCTION main.on_role_name_change()
  RETURNS trigger AS
$BODY$
BEGIN
IF NEW.name <> OLD.name THEN
UPDATE main."user" SET role_name = NEW.name WHERE role_name = OLD.name;
END IF;
RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

ALTER FUNCTION main.on_role_name_change() OWNER TO "www-data";

--
-- TOC entry 199 (class 1259 OID 89527)
-- Name: alembic_version; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE alembic_version OWNER TO "www-data";

--
-- TOC entry 200 (class 1259 OID 89530)
-- Name: dimension; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE dimension (
    id integer NOT NULL,
    name character varying,
    value character varying,
    description character varying,
    layer_id integer NOT NULL
);


ALTER TABLE dimension OWNER TO "www-data";

--
-- TOC entry 201 (class 1259 OID 89536)
-- Name: functionality; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE functionality (
    id integer NOT NULL,
    name character varying NOT NULL,
    value character varying NOT NULL,
    description character varying
);


ALTER TABLE functionality OWNER TO "www-data";

--
-- TOC entry 202 (class 1259 OID 89542)
-- Name: functionality_id_seq; Type: SEQUENCE; Schema: main; Owner: www-data
--

CREATE SEQUENCE functionality_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE functionality_id_seq OWNER TO "www-data";

--
-- TOC entry 3724 (class 0 OID 0)
-- Dependencies: 202
-- Name: functionality_id_seq; Type: SEQUENCE OWNED BY; Schema: main; Owner: www-data
--

ALTER SEQUENCE functionality_id_seq OWNED BY functionality.id;


--
-- TOC entry 203 (class 1259 OID 89544)
-- Name: interface; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE interface (
    id integer NOT NULL,
    name character varying,
    description character varying
);


ALTER TABLE interface OWNER TO "www-data";

--
-- TOC entry 204 (class 1259 OID 89550)
-- Name: interface_id_seq; Type: SEQUENCE; Schema: main; Owner: www-data
--

CREATE SEQUENCE interface_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE interface_id_seq OWNER TO "www-data";

--
-- TOC entry 3725 (class 0 OID 0)
-- Dependencies: 204
-- Name: interface_id_seq; Type: SEQUENCE OWNED BY; Schema: main; Owner: www-data
--

ALTER SEQUENCE interface_id_seq OWNED BY interface.id;


--
-- TOC entry 205 (class 1259 OID 89552)
-- Name: interface_layer; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE interface_layer (
    interface_id integer NOT NULL,
    layer_id integer NOT NULL
);


ALTER TABLE interface_layer OWNER TO "www-data";

--
-- TOC entry 206 (class 1259 OID 89555)
-- Name: interface_theme; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE interface_theme (
    interface_id integer NOT NULL,
    theme_id integer NOT NULL
);


ALTER TABLE interface_theme OWNER TO "www-data";

--
-- TOC entry 207 (class 1259 OID 89558)
-- Name: layer; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE layer (
    id integer NOT NULL,
    public boolean,
    geo_table character varying,
    exclude_properties character varying
);


ALTER TABLE layer OWNER TO "www-data";

--
-- TOC entry 208 (class 1259 OID 89564)
-- Name: layer_restrictionarea; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE layer_restrictionarea (
    layer_id integer NOT NULL,
    restrictionarea_id integer NOT NULL
);


ALTER TABLE layer_restrictionarea OWNER TO "www-data";

--
-- TOC entry 209 (class 1259 OID 89567)
-- Name: layer_wms; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE layer_wms (
    id integer NOT NULL,
    ogc_server_id integer NOT NULL,
    layer character varying NOT NULL,
    style character varying,
    time_mode character varying DEFAULT 'disabled'::character varying NOT NULL,
    time_widget character varying DEFAULT 'slider'::character varying NOT NULL
);


ALTER TABLE layer_wms OWNER TO "www-data";

--
-- TOC entry 210 (class 1259 OID 89575)
-- Name: layer_wmts; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE layer_wmts (
    id integer NOT NULL,
    url character varying NOT NULL,
    layer character varying NOT NULL,
    style character varying,
    matrix_set character varying,
    image_type character varying(10) NOT NULL
);


ALTER TABLE layer_wmts OWNER TO "www-data";

--
-- TOC entry 211 (class 1259 OID 89581)
-- Name: layergroup; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE layergroup (
    id integer NOT NULL,
    is_expanded boolean,
    is_internal_wms boolean,
    is_base_layer boolean
);


ALTER TABLE layergroup OWNER TO "www-data";

--
-- TOC entry 212 (class 1259 OID 89584)
-- Name: layergroup_treeitem; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE layergroup_treeitem (
    treegroup_id integer NOT NULL,
    treeitem_id integer NOT NULL,
    id integer NOT NULL,
    ordering integer,
    description character varying
);


ALTER TABLE layergroup_treeitem OWNER TO "www-data";

--
-- TOC entry 213 (class 1259 OID 89590)
-- Name: layergroup_treeitem_id_seq; Type: SEQUENCE; Schema: main; Owner: www-data
--

CREATE SEQUENCE layergroup_treeitem_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE layergroup_treeitem_id_seq OWNER TO "www-data";

--
-- TOC entry 3726 (class 0 OID 0)
-- Dependencies: 213
-- Name: layergroup_treeitem_id_seq; Type: SEQUENCE OWNED BY; Schema: main; Owner: www-data
--

ALTER SEQUENCE layergroup_treeitem_id_seq OWNED BY layergroup_treeitem.id;


--
-- TOC entry 214 (class 1259 OID 89592)
-- Name: layerv1; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE layerv1 (
    id integer NOT NULL,
    is_checked boolean,
    icon character varying,
    layer_type character varying(12),
    url character varying,
    image_type character varying(10),
    style character varying,
    dimensions character varying,
    matrix_set character varying,
    wms_url character varying,
    wms_layers character varying,
    query_layers character varying,
    kml character varying,
    is_single_tile boolean,
    legend boolean,
    legend_image character varying,
    legend_rule character varying,
    is_legend_expanded boolean,
    min_resolution double precision,
    max_resolution double precision,
    disclaimer character varying,
    identifier_attribute_field character varying,
    time_mode character varying(8),
    time_widget character varying(10),
    layer character varying
);


ALTER TABLE layerv1 OWNER TO "www-data";

--
-- TOC entry 215 (class 1259 OID 89598)
-- Name: metadata; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE metadata (
    id integer NOT NULL,
    name character varying,
    value character varying,
    description character varying,
    item_id integer NOT NULL
);


ALTER TABLE metadata OWNER TO "www-data";

--
-- TOC entry 216 (class 1259 OID 89604)
-- Name: ogc_server; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE ogc_server (
    id integer NOT NULL,
    name character varying NOT NULL,
    description character varying,
    url character varying NOT NULL,
    url_wfs character varying,
    type character varying NOT NULL,
    image_type character varying NOT NULL,
    auth character varying NOT NULL,
    wfs_support boolean DEFAULT false,
    is_single_tile boolean DEFAULT false
);


ALTER TABLE ogc_server OWNER TO "www-data";

--
-- TOC entry 217 (class 1259 OID 89612)
-- Name: restricted_role_theme; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE restricted_role_theme (
    role_id integer NOT NULL,
    theme_id integer NOT NULL
);


ALTER TABLE restricted_role_theme OWNER TO "www-data";

--
-- TOC entry 218 (class 1259 OID 89615)
-- Name: restrictionarea; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE restrictionarea (
    id integer NOT NULL,
    name character varying,
    description character varying,
    readwrite boolean,
    area public.geometry(Polygon,21781)
);


ALTER TABLE restrictionarea OWNER TO "www-data";

--
-- TOC entry 219 (class 1259 OID 89621)
-- Name: restrictionarea_id_seq; Type: SEQUENCE; Schema: main; Owner: www-data
--

CREATE SEQUENCE restrictionarea_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE restrictionarea_id_seq OWNER TO "www-data";

--
-- TOC entry 3727 (class 0 OID 0)
-- Dependencies: 219
-- Name: restrictionarea_id_seq; Type: SEQUENCE OWNED BY; Schema: main; Owner: www-data
--

ALTER SEQUENCE restrictionarea_id_seq OWNED BY restrictionarea.id;


--
-- TOC entry 220 (class 1259 OID 89623)
-- Name: role; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE role (
    id integer NOT NULL,
    name character varying NOT NULL,
    description character varying,
    extent public.geometry,
    CONSTRAINT enforce_dims_extent CHECK ((public.st_ndims(extent) = 2)),
    CONSTRAINT enforce_geotype_extent CHECK (((public.geometrytype(extent) = 'POLYGON'::text) OR (extent IS NULL))),
    CONSTRAINT enforce_srid_extent CHECK ((public.st_srid(extent) = 21781))
);


ALTER TABLE role OWNER TO "www-data";

--
-- TOC entry 221 (class 1259 OID 89632)
-- Name: role_functionality; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE role_functionality (
    role_id integer NOT NULL,
    functionality_id integer NOT NULL
);


ALTER TABLE role_functionality OWNER TO "www-data";

--
-- TOC entry 222 (class 1259 OID 89635)
-- Name: role_id_seq; Type: SEQUENCE; Schema: main; Owner: www-data
--

CREATE SEQUENCE role_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE role_id_seq OWNER TO "www-data";

--
-- TOC entry 3728 (class 0 OID 0)
-- Dependencies: 222
-- Name: role_id_seq; Type: SEQUENCE OWNED BY; Schema: main; Owner: www-data
--

ALTER SEQUENCE role_id_seq OWNED BY role.id;


--
-- TOC entry 223 (class 1259 OID 89637)
-- Name: role_restrictionarea; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE role_restrictionarea (
    role_id integer NOT NULL,
    restrictionarea_id integer NOT NULL
);


ALTER TABLE role_restrictionarea OWNER TO "www-data";

--
-- TOC entry 224 (class 1259 OID 89640)
-- Name: server_ogc_id_seq; Type: SEQUENCE; Schema: main; Owner: www-data
--

CREATE SEQUENCE server_ogc_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE server_ogc_id_seq OWNER TO "www-data";

--
-- TOC entry 3729 (class 0 OID 0)
-- Dependencies: 224
-- Name: server_ogc_id_seq; Type: SEQUENCE OWNED BY; Schema: main; Owner: www-data
--

ALTER SEQUENCE server_ogc_id_seq OWNED BY ogc_server.id;


--
-- TOC entry 225 (class 1259 OID 89642)
-- Name: theme; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE theme (
    id integer NOT NULL,
    icon character varying,
    ordering integer,
    public boolean
);


ALTER TABLE theme OWNER TO "www-data";

--
-- TOC entry 226 (class 1259 OID 89648)
-- Name: theme_functionality; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE theme_functionality (
    theme_id integer NOT NULL,
    functionality_id integer NOT NULL
);


ALTER TABLE theme_functionality OWNER TO "www-data";

--
-- TOC entry 227 (class 1259 OID 89651)
-- Name: treegroup; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE treegroup (
    id integer NOT NULL
);


ALTER TABLE treegroup OWNER TO "www-data";

--
-- TOC entry 228 (class 1259 OID 89654)
-- Name: treeitem; Type: TABLE; Schema: main; Owner: www-data
--

CREATE TABLE treeitem (
    type character varying(10) NOT NULL,
    id integer NOT NULL,
    name character varying NOT NULL,
    metadata_url character varying,
    description character varying
);


ALTER TABLE treeitem OWNER TO "www-data";

--
-- TOC entry 229 (class 1259 OID 89660)
-- Name: treeitem_id_seq; Type: SEQUENCE; Schema: main; Owner: www-data
--

CREATE SEQUENCE treeitem_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE treeitem_id_seq OWNER TO "www-data";

--
-- TOC entry 3730 (class 0 OID 0)
-- Dependencies: 229
-- Name: treeitem_id_seq; Type: SEQUENCE OWNED BY; Schema: main; Owner: www-data
--

ALTER SEQUENCE treeitem_id_seq OWNED BY treeitem.id;


--
-- TOC entry 232 (class 1259 OID 89672)
-- Name: ui_metadata_id_seq; Type: SEQUENCE; Schema: main; Owner: www-data
--

CREATE SEQUENCE ui_metadata_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE ui_metadata_id_seq OWNER TO "www-data";

--
-- TOC entry 3731 (class 0 OID 0)
-- Dependencies: 232
-- Name: ui_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: main; Owner: www-data
--

ALTER SEQUENCE ui_metadata_id_seq OWNED BY metadata.id;


--
-- TOC entry 233 (class 1259 OID 89674)
-- Name: wmts_dimension_id_seq; Type: SEQUENCE; Schema: main; Owner: www-data
--

CREATE SEQUENCE wmts_dimension_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE wmts_dimension_id_seq OWNER TO "www-data";

--
-- TOC entry 3732 (class 0 OID 0)
-- Dependencies: 233
-- Name: wmts_dimension_id_seq; Type: SEQUENCE OWNED BY; Schema: main; Owner: www-data
--

ALTER SEQUENCE wmts_dimension_id_seq OWNED BY dimension.id;


CREATE SCHEMA main_static AUTHORIZATION "www-data";


SET search_path = main_static, pg_catalog;

--
-- TOC entry 234 (class 1259 OID 89676)
-- Name: alembic_version; Type: TABLE; Schema: main_static; Owner: www-data
--

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE alembic_version OWNER TO "www-data";

--
-- TOC entry 237 (class 1259 OID 89687)
-- Name: user; Type: TABLE; Schema: main_static; Owner: www-data
--

CREATE TABLE "user" (
    type character varying(10) NOT NULL,
    id integer NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL,
    email character varying NOT NULL,
    is_password_changed boolean,
    role_name character varying,
    temp_password character varying
);


ALTER TABLE "user" OWNER TO "www-data";

--
-- TOC entry 238 (class 1259 OID 89693)
-- Name: user_id_seq; Type: SEQUENCE; Schema: main_static; Owner: www-data
--

CREATE SEQUENCE user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_id_seq OWNER TO "www-data";

--
-- TOC entry 3735 (class 0 OID 0)
-- Dependencies: 238
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: main_static; Owner: www-data
--

ALTER SEQUENCE user_id_seq OWNED BY "user".id;


SET search_path = main, pg_catalog;

--
-- TOC entry 3462 (class 2604 OID 89695)
-- Name: id; Type: DEFAULT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY dimension ALTER COLUMN id SET DEFAULT nextval('wmts_dimension_id_seq'::regclass);


--
-- TOC entry 3463 (class 2604 OID 89696)
-- Name: id; Type: DEFAULT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY functionality ALTER COLUMN id SET DEFAULT nextval('functionality_id_seq'::regclass);


--
-- TOC entry 3464 (class 2604 OID 89697)
-- Name: id; Type: DEFAULT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY interface ALTER COLUMN id SET DEFAULT nextval('interface_id_seq'::regclass);


--
-- TOC entry 3467 (class 2604 OID 89698)
-- Name: id; Type: DEFAULT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layergroup_treeitem ALTER COLUMN id SET DEFAULT nextval('layergroup_treeitem_id_seq'::regclass);


--
-- TOC entry 3468 (class 2604 OID 89699)
-- Name: id; Type: DEFAULT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY metadata ALTER COLUMN id SET DEFAULT nextval('ui_metadata_id_seq'::regclass);


--
-- TOC entry 3471 (class 2604 OID 89700)
-- Name: id; Type: DEFAULT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY ogc_server ALTER COLUMN id SET DEFAULT nextval('server_ogc_id_seq'::regclass);


--
-- TOC entry 3472 (class 2604 OID 89701)
-- Name: id; Type: DEFAULT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY restrictionarea ALTER COLUMN id SET DEFAULT nextval('restrictionarea_id_seq'::regclass);


--
-- TOC entry 3473 (class 2604 OID 89702)
-- Name: id; Type: DEFAULT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY role ALTER COLUMN id SET DEFAULT nextval('role_id_seq'::regclass);


--
-- TOC entry 3477 (class 2604 OID 89703)
-- Name: id; Type: DEFAULT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY treeitem ALTER COLUMN id SET DEFAULT nextval('treeitem_id_seq'::regclass);


SET search_path = main_static, pg_catalog;

--
-- TOC entry 3478 (class 2604 OID 89706)
-- Name: id; Type: DEFAULT; Schema: main_static; Owner: www-data
--

ALTER TABLE ONLY "user" ALTER COLUMN id SET DEFAULT nextval('user_id_seq'::regclass);


SET search_path = main, pg_catalog;

--
-- TOC entry 3684 (class 0 OID 89527)
-- Dependencies: 199
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO alembic_version VALUES ('d8ef99bc227e');


--
-- TOC entry 3685 (class 0 OID 89530)
-- Dependencies: 200
-- Data for Name: dimension; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO dimension VALUES (1, 'Time', '20141003', NULL, 120);
INSERT INTO dimension VALUES (2, 'DIM1', 'default', NULL, 132);
INSERT INTO dimension VALUES (4, 'ELEVATION', '0', NULL, 132);
INSERT INTO dimension VALUES (5, 'ELEVATION', '0', NULL, 133);
INSERT INTO dimension VALUES (3, 'DIM1', 'default', NULL, 133);
INSERT INTO dimension VALUES (12, 'DIM1', 'default', NULL, 182);
INSERT INTO dimension VALUES (13, 'ELEVATION', '0', NULL, 182);


--
-- TOC entry 3686 (class 0 OID 89536)
-- Dependencies: 201
-- Data for Name: functionality; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO functionality VALUES (5, 'default_basemap', 'blank', NULL);
INSERT INTO functionality VALUES (1, 'default_basemap', 'asitvd.fond_couleur', NULL);
INSERT INTO functionality VALUES (2, 'default_basemap', 'asitvd.fond_gris', NULL);
INSERT INTO functionality VALUES (6, 'location', '"Lausanne": [535436, 155243, 539476, 150443]', NULL);
INSERT INTO functionality VALUES (7, 'location', '"Pully": [539606, 152493, 541106, 150443]', NULL);
INSERT INTO functionality VALUES (8, 'location', '"Vevey": [551755, 149340, 555995, 145060]', NULL);
INSERT INTO functionality VALUES (10, 'default_theme', 'Cadastre', NULL);
INSERT INTO functionality VALUES (9, 'default_basemap', 'OSM map', NULL);
INSERT INTO functionality VALUES (11, 'default_basemap', 'OSM map WMS', NULL);


--
-- TOC entry 3736 (class 0 OID 0)
-- Dependencies: 202
-- Name: functionality_id_seq; Type: SEQUENCE SET; Schema: main; Owner: www-data
--

SELECT pg_catalog.setval('functionality_id_seq', 13, true);


--
-- TOC entry 3688 (class 0 OID 89544)
-- Dependencies: 203
-- Data for Name: interface; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO interface VALUES (2, 'mobile', NULL);
INSERT INTO interface VALUES (3, 'edit', NULL);
INSERT INTO interface VALUES (4, 'routing', NULL);
INSERT INTO interface VALUES (1, 'desktop', NULL);


--
-- TOC entry 3737 (class 0 OID 0)
-- Dependencies: 204
-- Name: interface_id_seq; Type: SEQUENCE SET; Schema: main; Owner: www-data
--

SELECT pg_catalog.setval('interface_id_seq', 4, true);


--
-- TOC entry 3690 (class 0 OID 89552)
-- Dependencies: 205
-- Data for Name: interface_layer; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO interface_layer VALUES (1, 95);
INSERT INTO interface_layer VALUES (2, 95);
INSERT INTO interface_layer VALUES (3, 95);
INSERT INTO interface_layer VALUES (4, 95);
INSERT INTO interface_layer VALUES (1, 12);
INSERT INTO interface_layer VALUES (3, 12);
INSERT INTO interface_layer VALUES (4, 12);
INSERT INTO interface_layer VALUES (1, 48);
INSERT INTO interface_layer VALUES (3, 48);
INSERT INTO interface_layer VALUES (4, 48);
INSERT INTO interface_layer VALUES (1, 50);
INSERT INTO interface_layer VALUES (3, 50);
INSERT INTO interface_layer VALUES (4, 50);
INSERT INTO interface_layer VALUES (1, 51);
INSERT INTO interface_layer VALUES (3, 51);
INSERT INTO interface_layer VALUES (4, 51);
INSERT INTO interface_layer VALUES (1, 53);
INSERT INTO interface_layer VALUES (3, 53);
INSERT INTO interface_layer VALUES (4, 53);
INSERT INTO interface_layer VALUES (1, 54);
INSERT INTO interface_layer VALUES (3, 54);
INSERT INTO interface_layer VALUES (4, 54);
INSERT INTO interface_layer VALUES (1, 55);
INSERT INTO interface_layer VALUES (3, 55);
INSERT INTO interface_layer VALUES (4, 55);
INSERT INTO interface_layer VALUES (1, 56);
INSERT INTO interface_layer VALUES (3, 56);
INSERT INTO interface_layer VALUES (4, 56);
INSERT INTO interface_layer VALUES (1, 57);
INSERT INTO interface_layer VALUES (3, 57);
INSERT INTO interface_layer VALUES (4, 57);
INSERT INTO interface_layer VALUES (1, 58);
INSERT INTO interface_layer VALUES (3, 58);
INSERT INTO interface_layer VALUES (4, 58);
INSERT INTO interface_layer VALUES (1, 59);
INSERT INTO interface_layer VALUES (3, 59);
INSERT INTO interface_layer VALUES (4, 59);
INSERT INTO interface_layer VALUES (1, 60);
INSERT INTO interface_layer VALUES (3, 60);
INSERT INTO interface_layer VALUES (4, 60);
INSERT INTO interface_layer VALUES (1, 61);
INSERT INTO interface_layer VALUES (3, 61);
INSERT INTO interface_layer VALUES (4, 61);
INSERT INTO interface_layer VALUES (1, 62);
INSERT INTO interface_layer VALUES (3, 62);
INSERT INTO interface_layer VALUES (4, 62);
INSERT INTO interface_layer VALUES (1, 65);
INSERT INTO interface_layer VALUES (3, 65);
INSERT INTO interface_layer VALUES (4, 65);
INSERT INTO interface_layer VALUES (1, 71);
INSERT INTO interface_layer VALUES (3, 71);
INSERT INTO interface_layer VALUES (4, 71);
INSERT INTO interface_layer VALUES (1, 70);
INSERT INTO interface_layer VALUES (3, 70);
INSERT INTO interface_layer VALUES (4, 70);
INSERT INTO interface_layer VALUES (1, 69);
INSERT INTO interface_layer VALUES (3, 69);
INSERT INTO interface_layer VALUES (4, 69);
INSERT INTO interface_layer VALUES (1, 74);
INSERT INTO interface_layer VALUES (3, 74);
INSERT INTO interface_layer VALUES (4, 74);
INSERT INTO interface_layer VALUES (1, 77);
INSERT INTO interface_layer VALUES (3, 77);
INSERT INTO interface_layer VALUES (4, 77);
INSERT INTO interface_layer VALUES (1, 78);
INSERT INTO interface_layer VALUES (3, 78);
INSERT INTO interface_layer VALUES (4, 78);
INSERT INTO interface_layer VALUES (1, 79);
INSERT INTO interface_layer VALUES (3, 79);
INSERT INTO interface_layer VALUES (4, 79);
INSERT INTO interface_layer VALUES (1, 80);
INSERT INTO interface_layer VALUES (3, 80);
INSERT INTO interface_layer VALUES (4, 80);
INSERT INTO interface_layer VALUES (1, 11);
INSERT INTO interface_layer VALUES (3, 11);
INSERT INTO interface_layer VALUES (4, 11);
INSERT INTO interface_layer VALUES (1, 81);
INSERT INTO interface_layer VALUES (3, 81);
INSERT INTO interface_layer VALUES (4, 81);
INSERT INTO interface_layer VALUES (1, 86);
INSERT INTO interface_layer VALUES (3, 86);
INSERT INTO interface_layer VALUES (4, 86);
INSERT INTO interface_layer VALUES (1, 67);
INSERT INTO interface_layer VALUES (3, 67);
INSERT INTO interface_layer VALUES (4, 67);
INSERT INTO interface_layer VALUES (2, 12);
INSERT INTO interface_layer VALUES (2, 48);
INSERT INTO interface_layer VALUES (2, 50);
INSERT INTO interface_layer VALUES (2, 51);
INSERT INTO interface_layer VALUES (2, 53);
INSERT INTO interface_layer VALUES (2, 54);
INSERT INTO interface_layer VALUES (2, 55);
INSERT INTO interface_layer VALUES (2, 56);
INSERT INTO interface_layer VALUES (2, 57);
INSERT INTO interface_layer VALUES (2, 58);
INSERT INTO interface_layer VALUES (2, 59);
INSERT INTO interface_layer VALUES (2, 60);
INSERT INTO interface_layer VALUES (2, 61);
INSERT INTO interface_layer VALUES (2, 62);
INSERT INTO interface_layer VALUES (2, 65);
INSERT INTO interface_layer VALUES (2, 71);
INSERT INTO interface_layer VALUES (2, 70);
INSERT INTO interface_layer VALUES (2, 69);
INSERT INTO interface_layer VALUES (2, 74);
INSERT INTO interface_layer VALUES (2, 77);
INSERT INTO interface_layer VALUES (2, 78);
INSERT INTO interface_layer VALUES (2, 79);
INSERT INTO interface_layer VALUES (2, 80);
INSERT INTO interface_layer VALUES (2, 11);
INSERT INTO interface_layer VALUES (2, 81);
INSERT INTO interface_layer VALUES (2, 86);
INSERT INTO interface_layer VALUES (2, 67);
INSERT INTO interface_layer VALUES (1, 98);
INSERT INTO interface_layer VALUES (3, 98);
INSERT INTO interface_layer VALUES (4, 98);
INSERT INTO interface_layer VALUES (2, 98);
INSERT INTO interface_layer VALUES (1, 99);
INSERT INTO interface_layer VALUES (3, 99);
INSERT INTO interface_layer VALUES (4, 99);
INSERT INTO interface_layer VALUES (2, 99);
INSERT INTO interface_layer VALUES (1, 100);
INSERT INTO interface_layer VALUES (3, 100);
INSERT INTO interface_layer VALUES (4, 100);
INSERT INTO interface_layer VALUES (2, 100);
INSERT INTO interface_layer VALUES (1, 101);
INSERT INTO interface_layer VALUES (3, 101);
INSERT INTO interface_layer VALUES (4, 101);
INSERT INTO interface_layer VALUES (2, 101);
INSERT INTO interface_layer VALUES (1, 102);
INSERT INTO interface_layer VALUES (3, 102);
INSERT INTO interface_layer VALUES (4, 102);
INSERT INTO interface_layer VALUES (2, 102);
INSERT INTO interface_layer VALUES (1, 103);
INSERT INTO interface_layer VALUES (3, 103);
INSERT INTO interface_layer VALUES (4, 103);
INSERT INTO interface_layer VALUES (2, 103);
INSERT INTO interface_layer VALUES (1, 104);
INSERT INTO interface_layer VALUES (3, 104);
INSERT INTO interface_layer VALUES (4, 104);
INSERT INTO interface_layer VALUES (2, 104);
INSERT INTO interface_layer VALUES (1, 105);
INSERT INTO interface_layer VALUES (3, 105);
INSERT INTO interface_layer VALUES (4, 105);
INSERT INTO interface_layer VALUES (2, 105);
INSERT INTO interface_layer VALUES (1, 106);
INSERT INTO interface_layer VALUES (3, 106);
INSERT INTO interface_layer VALUES (4, 106);
INSERT INTO interface_layer VALUES (2, 106);
INSERT INTO interface_layer VALUES (1, 107);
INSERT INTO interface_layer VALUES (3, 107);
INSERT INTO interface_layer VALUES (4, 107);
INSERT INTO interface_layer VALUES (2, 107);
INSERT INTO interface_layer VALUES (1, 108);
INSERT INTO interface_layer VALUES (3, 108);
INSERT INTO interface_layer VALUES (4, 108);
INSERT INTO interface_layer VALUES (2, 108);
INSERT INTO interface_layer VALUES (1, 109);
INSERT INTO interface_layer VALUES (3, 109);
INSERT INTO interface_layer VALUES (4, 109);
INSERT INTO interface_layer VALUES (2, 109);
INSERT INTO interface_layer VALUES (1, 110);
INSERT INTO interface_layer VALUES (3, 110);
INSERT INTO interface_layer VALUES (4, 110);
INSERT INTO interface_layer VALUES (2, 110);
INSERT INTO interface_layer VALUES (1, 111);
INSERT INTO interface_layer VALUES (3, 111);
INSERT INTO interface_layer VALUES (4, 111);
INSERT INTO interface_layer VALUES (2, 111);
INSERT INTO interface_layer VALUES (1, 112);
INSERT INTO interface_layer VALUES (3, 112);
INSERT INTO interface_layer VALUES (4, 112);
INSERT INTO interface_layer VALUES (2, 112);
INSERT INTO interface_layer VALUES (1, 113);
INSERT INTO interface_layer VALUES (3, 113);
INSERT INTO interface_layer VALUES (4, 113);
INSERT INTO interface_layer VALUES (2, 113);
INSERT INTO interface_layer VALUES (1, 114);
INSERT INTO interface_layer VALUES (3, 114);
INSERT INTO interface_layer VALUES (4, 114);
INSERT INTO interface_layer VALUES (2, 114);
INSERT INTO interface_layer VALUES (1, 115);
INSERT INTO interface_layer VALUES (3, 115);
INSERT INTO interface_layer VALUES (4, 115);
INSERT INTO interface_layer VALUES (2, 115);
INSERT INTO interface_layer VALUES (1, 116);
INSERT INTO interface_layer VALUES (3, 116);
INSERT INTO interface_layer VALUES (4, 116);
INSERT INTO interface_layer VALUES (2, 116);
INSERT INTO interface_layer VALUES (1, 117);
INSERT INTO interface_layer VALUES (3, 117);
INSERT INTO interface_layer VALUES (4, 117);
INSERT INTO interface_layer VALUES (2, 117);
INSERT INTO interface_layer VALUES (1, 118);
INSERT INTO interface_layer VALUES (3, 118);
INSERT INTO interface_layer VALUES (4, 118);
INSERT INTO interface_layer VALUES (2, 118);
INSERT INTO interface_layer VALUES (1, 119);
INSERT INTO interface_layer VALUES (3, 119);
INSERT INTO interface_layer VALUES (4, 119);
INSERT INTO interface_layer VALUES (2, 119);
INSERT INTO interface_layer VALUES (1, 120);
INSERT INTO interface_layer VALUES (3, 120);
INSERT INTO interface_layer VALUES (4, 120);
INSERT INTO interface_layer VALUES (2, 120);
INSERT INTO interface_layer VALUES (1, 121);
INSERT INTO interface_layer VALUES (3, 121);
INSERT INTO interface_layer VALUES (4, 121);
INSERT INTO interface_layer VALUES (2, 121);
INSERT INTO interface_layer VALUES (1, 122);
INSERT INTO interface_layer VALUES (3, 122);
INSERT INTO interface_layer VALUES (4, 122);
INSERT INTO interface_layer VALUES (2, 122);
INSERT INTO interface_layer VALUES (1, 123);
INSERT INTO interface_layer VALUES (3, 123);
INSERT INTO interface_layer VALUES (4, 123);
INSERT INTO interface_layer VALUES (2, 123);
INSERT INTO interface_layer VALUES (1, 124);
INSERT INTO interface_layer VALUES (3, 124);
INSERT INTO interface_layer VALUES (4, 124);
INSERT INTO interface_layer VALUES (2, 124);
INSERT INTO interface_layer VALUES (1, 125);
INSERT INTO interface_layer VALUES (2, 125);
INSERT INTO interface_layer VALUES (3, 125);
INSERT INTO interface_layer VALUES (4, 125);
INSERT INTO interface_layer VALUES (1, 126);
INSERT INTO interface_layer VALUES (2, 126);
INSERT INTO interface_layer VALUES (3, 126);
INSERT INTO interface_layer VALUES (4, 126);
INSERT INTO interface_layer VALUES (1, 128);
INSERT INTO interface_layer VALUES (2, 128);
INSERT INTO interface_layer VALUES (3, 128);
INSERT INTO interface_layer VALUES (4, 128);
INSERT INTO interface_layer VALUES (1, 129);
INSERT INTO interface_layer VALUES (2, 129);
INSERT INTO interface_layer VALUES (3, 129);
INSERT INTO interface_layer VALUES (4, 129);
INSERT INTO interface_layer VALUES (1, 130);
INSERT INTO interface_layer VALUES (2, 130);
INSERT INTO interface_layer VALUES (3, 130);
INSERT INTO interface_layer VALUES (4, 130);
INSERT INTO interface_layer VALUES (1, 132);
INSERT INTO interface_layer VALUES (2, 132);
INSERT INTO interface_layer VALUES (3, 132);
INSERT INTO interface_layer VALUES (4, 132);
INSERT INTO interface_layer VALUES (1, 133);
INSERT INTO interface_layer VALUES (2, 133);
INSERT INTO interface_layer VALUES (3, 133);
INSERT INTO interface_layer VALUES (4, 133);
INSERT INTO interface_layer VALUES (1, 134);
INSERT INTO interface_layer VALUES (2, 134);
INSERT INTO interface_layer VALUES (3, 134);
INSERT INTO interface_layer VALUES (4, 134);
INSERT INTO interface_layer VALUES (1, 138);
INSERT INTO interface_layer VALUES (2, 138);
INSERT INTO interface_layer VALUES (3, 138);
INSERT INTO interface_layer VALUES (4, 138);
INSERT INTO interface_layer VALUES (1, 139);
INSERT INTO interface_layer VALUES (2, 139);
INSERT INTO interface_layer VALUES (3, 139);
INSERT INTO interface_layer VALUES (4, 139);
INSERT INTO interface_layer VALUES (1, 140);
INSERT INTO interface_layer VALUES (2, 140);
INSERT INTO interface_layer VALUES (3, 140);
INSERT INTO interface_layer VALUES (4, 140);
INSERT INTO interface_layer VALUES (1, 141);
INSERT INTO interface_layer VALUES (2, 141);
INSERT INTO interface_layer VALUES (3, 141);
INSERT INTO interface_layer VALUES (4, 141);
INSERT INTO interface_layer VALUES (1, 143);
INSERT INTO interface_layer VALUES (2, 143);
INSERT INTO interface_layer VALUES (3, 143);
INSERT INTO interface_layer VALUES (4, 143);
INSERT INTO interface_layer VALUES (1, 144);
INSERT INTO interface_layer VALUES (2, 144);
INSERT INTO interface_layer VALUES (3, 144);
INSERT INTO interface_layer VALUES (4, 144);
INSERT INTO interface_layer VALUES (1, 147);
INSERT INTO interface_layer VALUES (2, 147);
INSERT INTO interface_layer VALUES (3, 147);
INSERT INTO interface_layer VALUES (4, 147);
INSERT INTO interface_layer VALUES (1, 150);
INSERT INTO interface_layer VALUES (2, 150);
INSERT INTO interface_layer VALUES (3, 150);
INSERT INTO interface_layer VALUES (4, 150);
INSERT INTO interface_layer VALUES (1, 151);
INSERT INTO interface_layer VALUES (2, 151);
INSERT INTO interface_layer VALUES (3, 151);
INSERT INTO interface_layer VALUES (4, 151);
INSERT INTO interface_layer VALUES (1, 152);
INSERT INTO interface_layer VALUES (2, 152);
INSERT INTO interface_layer VALUES (3, 152);
INSERT INTO interface_layer VALUES (4, 152);
INSERT INTO interface_layer VALUES (1, 154);
INSERT INTO interface_layer VALUES (3, 154);
INSERT INTO interface_layer VALUES (1, 155);
INSERT INTO interface_layer VALUES (3, 155);
INSERT INTO interface_layer VALUES (1, 156);
INSERT INTO interface_layer VALUES (3, 156);
INSERT INTO interface_layer VALUES (1, 157);
INSERT INTO interface_layer VALUES (3, 157);
INSERT INTO interface_layer VALUES (1, 158);
INSERT INTO interface_layer VALUES (3, 158);
INSERT INTO interface_layer VALUES (1, 159);
INSERT INTO interface_layer VALUES (3, 159);
INSERT INTO interface_layer VALUES (1, 160);
INSERT INTO interface_layer VALUES (3, 160);
INSERT INTO interface_layer VALUES (1, 161);
INSERT INTO interface_layer VALUES (3, 161);
INSERT INTO interface_layer VALUES (1, 162);
INSERT INTO interface_layer VALUES (3, 162);
INSERT INTO interface_layer VALUES (1, 163);
INSERT INTO interface_layer VALUES (3, 163);
INSERT INTO interface_layer VALUES (2, 170);
INSERT INTO interface_layer VALUES (3, 170);
INSERT INTO interface_layer VALUES (4, 170);
INSERT INTO interface_layer VALUES (1, 170);
INSERT INTO interface_layer VALUES (2, 171);
INSERT INTO interface_layer VALUES (3, 171);
INSERT INTO interface_layer VALUES (4, 171);
INSERT INTO interface_layer VALUES (1, 171);
INSERT INTO interface_layer VALUES (2, 172);
INSERT INTO interface_layer VALUES (3, 172);
INSERT INTO interface_layer VALUES (4, 172);
INSERT INTO interface_layer VALUES (1, 172);
INSERT INTO interface_layer VALUES (2, 173);
INSERT INTO interface_layer VALUES (3, 173);
INSERT INTO interface_layer VALUES (4, 173);
INSERT INTO interface_layer VALUES (1, 173);
INSERT INTO interface_layer VALUES (2, 175);
INSERT INTO interface_layer VALUES (3, 175);
INSERT INTO interface_layer VALUES (4, 175);
INSERT INTO interface_layer VALUES (1, 175);
INSERT INTO interface_layer VALUES (2, 177);
INSERT INTO interface_layer VALUES (3, 177);
INSERT INTO interface_layer VALUES (4, 177);
INSERT INTO interface_layer VALUES (1, 177);
INSERT INTO interface_layer VALUES (2, 178);
INSERT INTO interface_layer VALUES (3, 178);
INSERT INTO interface_layer VALUES (4, 178);
INSERT INTO interface_layer VALUES (1, 178);
INSERT INTO interface_layer VALUES (2, 179);
INSERT INTO interface_layer VALUES (3, 179);
INSERT INTO interface_layer VALUES (4, 179);
INSERT INTO interface_layer VALUES (1, 179);
INSERT INTO interface_layer VALUES (2, 180);
INSERT INTO interface_layer VALUES (3, 180);
INSERT INTO interface_layer VALUES (4, 180);
INSERT INTO interface_layer VALUES (1, 180);
INSERT INTO interface_layer VALUES (2, 181);
INSERT INTO interface_layer VALUES (3, 181);
INSERT INTO interface_layer VALUES (4, 181);
INSERT INTO interface_layer VALUES (1, 181);
INSERT INTO interface_layer VALUES (2, 182);
INSERT INTO interface_layer VALUES (3, 182);
INSERT INTO interface_layer VALUES (4, 182);
INSERT INTO interface_layer VALUES (1, 182);
INSERT INTO interface_layer VALUES (2, 184);
INSERT INTO interface_layer VALUES (3, 184);
INSERT INTO interface_layer VALUES (4, 184);
INSERT INTO interface_layer VALUES (1, 184);


--
-- TOC entry 3691 (class 0 OID 89555)
-- Dependencies: 206
-- Data for Name: interface_theme; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO interface_theme VALUES (1, 38);
INSERT INTO interface_theme VALUES (1, 37);
INSERT INTO interface_theme VALUES (1, 29);
INSERT INTO interface_theme VALUES (1, 64);
INSERT INTO interface_theme VALUES (1, 73);
INSERT INTO interface_theme VALUES (3, 38);
INSERT INTO interface_theme VALUES (3, 37);
INSERT INTO interface_theme VALUES (3, 29);
INSERT INTO interface_theme VALUES (3, 64);
INSERT INTO interface_theme VALUES (3, 73);
INSERT INTO interface_theme VALUES (4, 38);
INSERT INTO interface_theme VALUES (4, 37);
INSERT INTO interface_theme VALUES (4, 29);
INSERT INTO interface_theme VALUES (4, 64);
INSERT INTO interface_theme VALUES (4, 73);
INSERT INTO interface_theme VALUES (2, 64);
INSERT INTO interface_theme VALUES (1, 5);
INSERT INTO interface_theme VALUES (2, 5);
INSERT INTO interface_theme VALUES (3, 5);
INSERT INTO interface_theme VALUES (4, 5);
INSERT INTO interface_theme VALUES (1, 92);
INSERT INTO interface_theme VALUES (2, 92);
INSERT INTO interface_theme VALUES (3, 92);
INSERT INTO interface_theme VALUES (4, 92);
INSERT INTO interface_theme VALUES (1, 91);
INSERT INTO interface_theme VALUES (2, 91);
INSERT INTO interface_theme VALUES (3, 91);
INSERT INTO interface_theme VALUES (4, 91);
INSERT INTO interface_theme VALUES (2, 73);
INSERT INTO interface_theme VALUES (2, 38);
INSERT INTO interface_theme VALUES (2, 37);
INSERT INTO interface_theme VALUES (2, 29);
INSERT INTO interface_theme VALUES (1, 4);
INSERT INTO interface_theme VALUES (2, 4);
INSERT INTO interface_theme VALUES (3, 4);
INSERT INTO interface_theme VALUES (4, 4);
INSERT INTO interface_theme VALUES (1, 3);
INSERT INTO interface_theme VALUES (2, 3);
INSERT INTO interface_theme VALUES (3, 3);
INSERT INTO interface_theme VALUES (4, 3);
INSERT INTO interface_theme VALUES (1, 2);
INSERT INTO interface_theme VALUES (2, 2);
INSERT INTO interface_theme VALUES (3, 2);
INSERT INTO interface_theme VALUES (4, 2);
INSERT INTO interface_theme VALUES (2, 168);
INSERT INTO interface_theme VALUES (3, 168);
INSERT INTO interface_theme VALUES (4, 168);
INSERT INTO interface_theme VALUES (1, 168);
INSERT INTO interface_theme VALUES (2, 176);
INSERT INTO interface_theme VALUES (3, 176);
INSERT INTO interface_theme VALUES (4, 176);
INSERT INTO interface_theme VALUES (1, 176);


--
-- TOC entry 3692 (class 0 OID 89558)
-- Dependencies: 207
-- Data for Name: layer; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO layer VALUES (98, true, NULL, NULL);
INSERT INTO layer VALUES (99, true, NULL, NULL);
INSERT INTO layer VALUES (100, true, NULL, NULL);
INSERT INTO layer VALUES (101, true, NULL, NULL);
INSERT INTO layer VALUES (102, true, NULL, NULL);
INSERT INTO layer VALUES (103, true, NULL, NULL);
INSERT INTO layer VALUES (104, true, NULL, NULL);
INSERT INTO layer VALUES (106, true, NULL, NULL);
INSERT INTO layer VALUES (107, true, NULL, NULL);
INSERT INTO layer VALUES (108, true, NULL, NULL);
INSERT INTO layer VALUES (109, true, NULL, NULL);
INSERT INTO layer VALUES (110, true, NULL, NULL);
INSERT INTO layer VALUES (111, true, 'edit.line', NULL);
INSERT INTO layer VALUES (112, true, 'edit.polygon', NULL);
INSERT INTO layer VALUES (113, true, 'edit.point', NULL);
INSERT INTO layer VALUES (114, true, NULL, NULL);
INSERT INTO layer VALUES (115, true, NULL, NULL);
INSERT INTO layer VALUES (116, true, NULL, NULL);
INSERT INTO layer VALUES (117, true, NULL, NULL);
INSERT INTO layer VALUES (118, true, NULL, NULL);
INSERT INTO layer VALUES (119, true, NULL, NULL);
INSERT INTO layer VALUES (120, true, NULL, NULL);
INSERT INTO layer VALUES (122, false, NULL, NULL);
INSERT INTO layer VALUES (123, true, NULL, NULL);
INSERT INTO layer VALUES (124, true, NULL, NULL);
INSERT INTO layer VALUES (125, false, NULL, NULL);
INSERT INTO layer VALUES (126, true, NULL, NULL);
INSERT INTO layer VALUES (134, true, NULL, NULL);
INSERT INTO layer VALUES (48, true, NULL, NULL);
INSERT INTO layer VALUES (50, true, NULL, NULL);
INSERT INTO layer VALUES (51, true, NULL, NULL);
INSERT INTO layer VALUES (53, true, NULL, NULL);
INSERT INTO layer VALUES (54, true, NULL, NULL);
INSERT INTO layer VALUES (55, true, NULL, NULL);
INSERT INTO layer VALUES (56, true, NULL, NULL);
INSERT INTO layer VALUES (57, true, NULL, NULL);
INSERT INTO layer VALUES (58, true, NULL, NULL);
INSERT INTO layer VALUES (59, true, NULL, NULL);
INSERT INTO layer VALUES (60, true, NULL, NULL);
INSERT INTO layer VALUES (61, true, NULL, NULL);
INSERT INTO layer VALUES (62, true, NULL, NULL);
INSERT INTO layer VALUES (65, true, NULL, NULL);
INSERT INTO layer VALUES (69, true, 'edit.point', NULL);
INSERT INTO layer VALUES (74, true, NULL, NULL);
INSERT INTO layer VALUES (77, true, NULL, NULL);
INSERT INTO layer VALUES (78, true, NULL, NULL);
INSERT INTO layer VALUES (79, true, NULL, NULL);
INSERT INTO layer VALUES (80, true, NULL, NULL);
INSERT INTO layer VALUES (81, true, NULL, NULL);
INSERT INTO layer VALUES (86, true, NULL, NULL);
INSERT INTO layer VALUES (67, true, NULL, NULL);
INSERT INTO layer VALUES (95, false, NULL, NULL);
INSERT INTO layer VALUES (12, false, NULL, NULL);
INSERT INTO layer VALUES (11, false, NULL, NULL);
INSERT INTO layer VALUES (128, true, NULL, NULL);
INSERT INTO layer VALUES (129, true, NULL, NULL);
INSERT INTO layer VALUES (130, true, NULL, NULL);
INSERT INTO layer VALUES (133, false, NULL, NULL);
INSERT INTO layer VALUES (132, false, NULL, NULL);
INSERT INTO layer VALUES (138, true, NULL, NULL);
INSERT INTO layer VALUES (139, true, NULL, NULL);
INSERT INTO layer VALUES (140, true, NULL, NULL);
INSERT INTO layer VALUES (70, true, 'edit.line', NULL);
INSERT INTO layer VALUES (71, true, 'edit.polygon', NULL);
INSERT INTO layer VALUES (141, true, NULL, NULL);
INSERT INTO layer VALUES (144, true, NULL, NULL);
INSERT INTO layer VALUES (143, true, NULL, NULL);
INSERT INTO layer VALUES (147, true, NULL, NULL);
INSERT INTO layer VALUES (150, true, NULL, NULL);
INSERT INTO layer VALUES (151, true, NULL, NULL);
INSERT INTO layer VALUES (152, true, NULL, NULL);
INSERT INTO layer VALUES (121, true, NULL, NULL);
INSERT INTO layer VALUES (105, false, NULL, NULL);
INSERT INTO layer VALUES (154, true, NULL, NULL);
INSERT INTO layer VALUES (155, true, NULL, NULL);
INSERT INTO layer VALUES (156, true, NULL, NULL);
INSERT INTO layer VALUES (157, true, NULL, NULL);
INSERT INTO layer VALUES (158, true, NULL, NULL);
INSERT INTO layer VALUES (159, true, NULL, NULL);
INSERT INTO layer VALUES (160, true, NULL, NULL);
INSERT INTO layer VALUES (161, true, NULL, NULL);
INSERT INTO layer VALUES (163, true, NULL, NULL);
INSERT INTO layer VALUES (162, true, NULL, NULL);
INSERT INTO layer VALUES (170, true, NULL, NULL);
INSERT INTO layer VALUES (171, true, NULL, NULL);
INSERT INTO layer VALUES (172, true, NULL, NULL);
INSERT INTO layer VALUES (173, true, NULL, NULL);
INSERT INTO layer VALUES (175, true, NULL, NULL);
INSERT INTO layer VALUES (177, true, NULL, NULL);
INSERT INTO layer VALUES (178, true, NULL, NULL);
INSERT INTO layer VALUES (179, true, NULL, NULL);
INSERT INTO layer VALUES (180, true, NULL, NULL);
INSERT INTO layer VALUES (181, true, NULL, NULL);
INSERT INTO layer VALUES (182, true, NULL, NULL);
INSERT INTO layer VALUES (184, true, NULL, NULL);


--
-- TOC entry 3693 (class 0 OID 89564)
-- Dependencies: 208
-- Data for Name: layer_restrictionarea; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO layer_restrictionarea VALUES (71, 5);
INSERT INTO layer_restrictionarea VALUES (70, 5);
INSERT INTO layer_restrictionarea VALUES (69, 5);
INSERT INTO layer_restrictionarea VALUES (12, 8);
INSERT INTO layer_restrictionarea VALUES (12, 6);
INSERT INTO layer_restrictionarea VALUES (122, 8);
INSERT INTO layer_restrictionarea VALUES (122, 6);
INSERT INTO layer_restrictionarea VALUES (111, 5);
INSERT INTO layer_restrictionarea VALUES (112, 5);
INSERT INTO layer_restrictionarea VALUES (113, 5);
INSERT INTO layer_restrictionarea VALUES (12, 9);
INSERT INTO layer_restrictionarea VALUES (122, 9);
INSERT INTO layer_restrictionarea VALUES (12, 10);
INSERT INTO layer_restrictionarea VALUES (122, 10);
INSERT INTO layer_restrictionarea VALUES (59, 7);
INSERT INTO layer_restrictionarea VALUES (105, 7);


--
-- TOC entry 3694 (class 0 OID 89567)
-- Dependencies: 209
-- Data for Name: layer_wms; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO layer_wms VALUES (111, 2, 'line', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (112, 2, 'polygon', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (115, 3, 'ch.swisstopo.dreiecksvermaschung', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (116, 3, 'ch.swisstopo.geologie-gravimetrischer_atlas', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (117, 3, 'ch.swisstopo.geologie-geotechnik-gk500-lithologie_hauptgruppen', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (118, 3, 'ch.swisstopo.geologie-geotechnik-gk500-gesteinsklassierung', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (139, 2, 'osm_open', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (123, 2, 'alpine_hut', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (122, 2, 'firestations', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (121, 2, 'hospitals', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (144, 2, 'osm_time', NULL, 'value', 'datepicker');
INSERT INTO layer_wms VALUES (143, 2, 'osm_time', NULL, 'value', 'slider');
INSERT INTO layer_wms VALUES (126, 2, 'osm_time', NULL, 'range', 'datepicker');
INSERT INTO layer_wms VALUES (124, 2, 'fuel', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (110, 2, 'osm_time', NULL, 'range', 'slider');
INSERT INTO layer_wms VALUES (114, 2, 'osm_scale', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (113, 2, 'point', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (109, 2, 'osm', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (106, 2, 'post_office', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (105, 2, 'police', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (103, 2, 'parking', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (104, 2, 'place_of_worship', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (101, 2, 'bus_stop', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (100, 2, 'bank', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (99, 2, 'cinema', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (98, 2, 'information', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (108, 2, 'tourism_activity', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (107, 2, 'sustenance', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (102, 2, 'entertainment', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (147, 2, 'osm_time2', NULL, 'range', 'datepicker');
INSERT INTO layer_wms VALUES (140, 2, 'bank', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (150, 2, 'half_query', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (151, 2, 'srtm', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (152, 2, 'aster', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (141, 2, 'sustenance,entertainment', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (154, 2, 'point', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (155, 2, 'line', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (156, 2, 'point', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (157, 2, 'line', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (158, 2, 'polygon', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (159, 2, 'line', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (160, 2, 'line', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (161, 2, 'polygon', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (162, 2, 'polygon', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (163, 2, 'polygon', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (170, 2, 'polygon', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (171, 2, 'polygon', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (172, 2, 'line', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (173, 2, 'point', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (175, 2, 'default', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (177, 2, 'osm_time_year_mounth', NULL, 'range', 'slider');
INSERT INTO layer_wms VALUES (178, 2, 'osm_time_year_mounth', NULL, 'value', 'slider');
INSERT INTO layer_wms VALUES (179, 2, 'osm_time_mount_year', NULL, 'range', 'slider');
INSERT INTO layer_wms VALUES (180, 2, 'osm_time_mount_year', NULL, 'value', 'slider');
INSERT INTO layer_wms VALUES (181, 4, 'osm_open', NULL, 'disabled', 'slider');
INSERT INTO layer_wms VALUES (184, 2, 'osm_time_mount_year', NULL, 'range', 'slider');


--
-- TOC entry 3695 (class 0 OID 89575)
-- Dependencies: 210
-- Data for Name: layer_wmts; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO layer_wmts VALUES (125, 'https://ows.asitvd.ch/wmts/1.0.0/WMTSCapabilities.xml', 'asitvd.fond_pourortho', NULL, NULL, 'image/jpeg');
INSERT INTO layer_wmts VALUES (120, 'https://wmts.geo.admin.ch/1.0.0/WMTSCapabilities.xml?lang=fr', 'ch.astra.ausnahmetransportrouten', 'ch.astra.ausnahmetransportrouten', '21781_26', 'image/jpeg');
INSERT INTO layer_wmts VALUES (119, 'https://wmts.geo.admin.ch/1.0.0/WMTSCapabilities.xml?lang=fr', 'ch.are.alpenkonvention', NULL, '21781_26', 'image/jpeg');
INSERT INTO layer_wmts VALUES (133, 'https://ows.asitvd.ch/wmts/1.0.0/WMTSCapabilities.xml', 'asitvd.fond_couleur', NULL, NULL, 'image/jpeg');
INSERT INTO layer_wmts VALUES (132, 'https://ows.asitvd.ch/wmts/1.0.0/WMTSCapabilities.xml', 'asitvd.fond_gris', NULL, NULL, 'image/jpeg');
INSERT INTO layer_wmts VALUES (134, 'config://local/tiles/1.0.0/WMTSCapabilities.xml', 'map', NULL, NULL, 'image/jpeg');
INSERT INTO layer_wmts VALUES (182, 'https://ows.asitvd.ch/wmts/1.0.0/WMTSCapabilities.xml', 'asitvd.fond_gris_sans_labels', NULL, '2056', 'image/png');


--
-- TOC entry 3696 (class 0 OID 89581)
-- Dependencies: 211
-- Data for Name: layergroup; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO layergroup VALUES (6, true, true, false);
INSERT INTO layergroup VALUES (7, true, true, false);
INSERT INTO layergroup VALUES (8, true, true, false);
INSERT INTO layergroup VALUES (9, true, true, false);
INSERT INTO layergroup VALUES (35, true, true, false);
INSERT INTO layergroup VALUES (36, true, true, false);
INSERT INTO layergroup VALUES (63, false, true, false);
INSERT INTO layergroup VALUES (66, false, true, false);
INSERT INTO layergroup VALUES (72, true, true, false);
INSERT INTO layergroup VALUES (93, false, true, false);
INSERT INTO layergroup VALUES (30, true, false, false);
INSERT INTO layergroup VALUES (68, true, true, false);
INSERT INTO layergroup VALUES (94, true, true, false);
INSERT INTO layergroup VALUES (131, false, true, false);
INSERT INTO layergroup VALUES (135, false, true, false);
INSERT INTO layergroup VALUES (136, false, true, false);
INSERT INTO layergroup VALUES (137, false, true, false);
INSERT INTO layergroup VALUES (145, false, true, false);
INSERT INTO layergroup VALUES (146, false, true, false);
INSERT INTO layergroup VALUES (153, false, false, false);
INSERT INTO layergroup VALUES (164, false, true, false);
INSERT INTO layergroup VALUES (165, false, true, false);
INSERT INTO layergroup VALUES (166, false, true, false);
INSERT INTO layergroup VALUES (167, false, true, false);
INSERT INTO layergroup VALUES (169, false, true, false);
INSERT INTO layergroup VALUES (174, false, false, false);
INSERT INTO layergroup VALUES (183, false, true, false);


--
-- TOC entry 3697 (class 0 OID 89584)
-- Dependencies: 212
-- Data for Name: layergroup_treeitem; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO layergroup_treeitem VALUES (30, 77, 191, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 78, 192, 1, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 79, 193, 2, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 80, 194, 3, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 81, 195, 4, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 86, 196, 5, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 95, 197, -1, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 67, 199, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (5, 6, 128, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (73, 72, 133, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (38, 35, 135, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (37, 36, 136, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (29, 30, 137, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (4, 7, 138, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (3, 8, 139, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (2, 9, 140, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (91, 94, 142, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (93, 55, 151, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (66, 65, 60, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (36, 48, 152, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (36, 57, 153, 1, NULL);
INSERT INTO layergroup_treeitem VALUES (36, 55, 154, 2, NULL);
INSERT INTO layergroup_treeitem VALUES (35, 55, 155, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (9, 53, 157, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (6, 11, 76, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (7, 54, 161, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (7, 58, 162, 1, NULL);
INSERT INTO layergroup_treeitem VALUES (92, 93, 169, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (7, 100, 211, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (93, 101, 212, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (36, 101, 213, 2, NULL);
INSERT INTO layergroup_treeitem VALUES (36, 103, 216, 1, NULL);
INSERT INTO layergroup_treeitem VALUES (7, 104, 217, 1, NULL);
INSERT INTO layergroup_treeitem VALUES (8, 108, 222, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (66, 109, 223, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 115, 229, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 116, 230, 1, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 117, 231, 2, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 118, 232, 3, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 119, 233, 4, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 120, 234, 5, NULL);
INSERT INTO layergroup_treeitem VALUES (36, 124, 238, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (30, 125, 240, -1, NULL);
INSERT INTO layergroup_treeitem VALUES (135, 102, 255, 2, NULL);
INSERT INTO layergroup_treeitem VALUES (135, 99, 254, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (131, 134, 252, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (131, 129, 271, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (64, 66, 9, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (64, 68, 10, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (64, 63, 11, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (137, 102, 265, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (137, 56, 266, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (137, 61, 267, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (137, 107, 268, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (145, 110, 276, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 74, 200, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 114, 228, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 138, 262, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 139, 263, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 140, 274, 50, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 145, 280, 60, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 141, 281, 70, NULL);
INSERT INTO layergroup_treeitem VALUES (146, 126, 284, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (64, 146, 286, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 120, 287, 80, NULL);
INSERT INTO layergroup_treeitem VALUES (9, 123, 237, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 51, 202, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 59, 204, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 60, 205, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 99, 210, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 105, 218, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 106, 219, 50, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 126, 241, 70, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 137, 269, 80, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 11, 295, 90, NULL);
INSERT INTO layergroup_treeitem VALUES (63, 121, 296, 100, NULL);
INSERT INTO layergroup_treeitem VALUES (146, 147, 288, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (146, 114, 289, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (146, 139, 290, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (146, 140, 291, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (146, 141, 292, 50, NULL);
INSERT INTO layergroup_treeitem VALUES (146, 150, 297, 60, NULL);
INSERT INTO layergroup_treeitem VALUES (131, 132, 298, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (131, 133, 299, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (146, 151, 300, 70, NULL);
INSERT INTO layergroup_treeitem VALUES (146, 152, 301, 80, NULL);
INSERT INTO layergroup_treeitem VALUES (153, 115, 302, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (153, 116, 303, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (153, 117, 304, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (153, 118, 305, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (64, 153, 306, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (6, 12, 77, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (6, 121, 235, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (6, 122, 236, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (35, 50, 156, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (35, 98, 209, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (35, 101, 214, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (164, 154, 307, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (164, 155, 308, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (72, 71, 73, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (72, 70, 74, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (72, 69, 75, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (72, 111, 225, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (72, 112, 226, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (72, 113, 227, 50, NULL);
INSERT INTO layergroup_treeitem VALUES (165, 156, 318, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (165, 157, 319, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (165, 158, 320, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (166, 159, 321, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (166, 161, 322, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (167, 160, 323, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (167, 162, 324, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (73, 164, 325, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (73, 165, 326, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (73, 166, 327, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (73, 167, 328, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (164, 163, 316, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (169, 111, 329, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (169, 112, 330, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (169, 113, 331, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (168, 169, 332, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (169, 170, 333, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (169, 171, 334, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (169, 172, 335, 50, NULL);
INSERT INTO layergroup_treeitem VALUES (169, 173, 336, 60, NULL);
INSERT INTO layergroup_treeitem VALUES (8, 48, 160, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (8, 124, 239, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (9, 108, 221, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (9, 50, 293, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (9, 98, 294, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (64, 174, 342, 50, NULL);
INSERT INTO layergroup_treeitem VALUES (174, 134, 341, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (131, 175, 343, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (176, 174, 344, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (145, 143, 278, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (145, 144, 279, 20, NULL);
INSERT INTO layergroup_treeitem VALUES (145, 126, 283, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (145, 177, 345, 40, NULL);
INSERT INTO layergroup_treeitem VALUES (145, 178, 346, 50, NULL);
INSERT INTO layergroup_treeitem VALUES (145, 179, 347, 60, NULL);
INSERT INTO layergroup_treeitem VALUES (145, 180, 348, 70, NULL);
INSERT INTO layergroup_treeitem VALUES (174, 118, 338, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (174, 139, 339, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (174, 147, 349, 30, NULL);
INSERT INTO layergroup_treeitem VALUES (68, 181, 353, 90, NULL);
INSERT INTO layergroup_treeitem VALUES (131, 182, 354, 50, NULL);
INSERT INTO layergroup_treeitem VALUES (183, 139, 355, 0, NULL);
INSERT INTO layergroup_treeitem VALUES (183, 147, 356, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (176, 183, 357, 10, NULL);
INSERT INTO layergroup_treeitem VALUES (64, 183, 358, 60, NULL);
INSERT INTO layergroup_treeitem VALUES (145, 184, 360, 80, NULL);


--
-- TOC entry 3738 (class 0 OID 0)
-- Dependencies: 213
-- Name: layergroup_treeitem_id_seq; Type: SEQUENCE SET; Schema: main; Owner: www-data
--

SELECT pg_catalog.setval('layergroup_treeitem_id_seq', 360, true);


--
-- TOC entry 3699 (class 0 OID 89592)
-- Dependencies: 214
-- Data for Name: layerv1; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO layerv1 VALUES (50, true, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Informations', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'information');
INSERT INTO layerv1 VALUES (51, true, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Cinémas', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'cinema');
INSERT INTO layerv1 VALUES (54, true, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Banques', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'bank');
INSERT INTO layerv1 VALUES (55, false, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Arrêt de bus', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'bus_stop');
INSERT INTO layerv1 VALUES (57, false, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Parking', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'parking');
INSERT INTO layerv1 VALUES (65, false, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, true, NULL, NULL, '© les contributeurs d’OSM', 'display_name', 'disabled', 'slider', 'osm');
INSERT INTO layerv1 VALUES (58, true, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Lieux de culte', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'place_of_worship');
INSERT INTO layerv1 VALUES (59, true, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Postes de police', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'police');
INSERT INTO layerv1 VALUES (60, true, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Offices de poste', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'post_office');
INSERT INTO layerv1 VALUES (67, true, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Dans les temps', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'name', 'range', 'slider', 'osm_time');
INSERT INTO layerv1 VALUES (70, true, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Line', false, NULL, NULL, NULL, 'name', 'disabled', 'slider', 'line');
INSERT INTO layerv1 VALUES (71, true, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Polygon', false, NULL, NULL, NULL, 'name', 'disabled', 'slider', 'polygon');
INSERT INTO layerv1 VALUES (69, true, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Point', false, NULL, NULL, NULL, 'name', 'disabled', 'slider', 'point');
INSERT INTO layerv1 VALUES (74, true, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'OSM', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'osm_scale');
INSERT INTO layerv1 VALUES (77, false, NULL, 'external WMS', 'http://wms.geo.admin.ch?lang=fr', 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, NULL, NULL, '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 'disabled', 'slider', 'ch.swisstopo.dreiecksvermaschung');
INSERT INTO layerv1 VALUES (78, false, NULL, 'external WMS', 'http://wms.geo.admin.ch?lang=fr', 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, NULL, NULL, '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 'disabled', 'slider', 'ch.swisstopo.geologie-gravimetrischer_atlas');
INSERT INTO layerv1 VALUES (79, true, NULL, 'external WMS', 'http://wms.geo.admin.ch?lang=fr', 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, NULL, NULL, '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 'disabled', 'slider', 'ch.swisstopo.geologie-geotechnik-gk500-lithologie_hauptgruppen');
INSERT INTO layerv1 VALUES (80, false, NULL, 'external WMS', 'http://wms.geo.admin.ch?lang=fr', 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, NULL, NULL, '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 'disabled', 'slider', 'ch.swisstopo.geologie-geotechnik-gk500-gesteinsklassierung');
INSERT INTO layerv1 VALUES (81, false, NULL, 'WMTS', 'http://wmts.geo.admin.ch/1.0.0/WMTSCapabilities.xml?lang=fr', 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, 100, 1000, '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 'disabled', 'slider', 'ch.are.alpenkonvention');
INSERT INTO layerv1 VALUES (86, false, NULL, 'WMTS', 'http://wmts.geo.admin.ch/1.0.0/WMTSCapabilities.xml?lang=fr', 'image/jpeg', 'ch.astra.ausnahmetransportrouten', '{"Time": "20141003"}', '21781_26', NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, NULL, NULL, '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 'disabled', 'slider', 'ch.astra.ausnahmetransportrouten');
INSERT INTO layerv1 VALUES (11, true, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, true, false, NULL, 'Hôpital', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'hospitals');
INSERT INTO layerv1 VALUES (12, false, NULL, 'internal WMS', NULL, 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, true, false, NULL, 'Casernes de pompiers', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'firestations');
INSERT INTO layerv1 VALUES (48, true, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Station service', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'fuel');
INSERT INTO layerv1 VALUES (95, true, NULL, 'WMTS', 'http://ows.asitvd.ch/wmts/1.0.0/WMTSCapabilities.xml', 'image/jpeg', NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, 1, 100, '© <a href=''http://asitvd.ch''>ASIT VD</a>, Contributeurs d’<a href=''http://www.openstreetmap.org/copyright''>OpenStreetMap</a>', NULL, 'disabled', 'slider', 'asitvd.fond_pourortho');
INSERT INTO layerv1 VALUES (128, true, NULL, 'WMTS', 'https://geomapfish-demo.camptocamp.net/2.0/tiles/1.0.0/WMTSCapabilities.xml', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, NULL, NULL, NULL, NULL, 'disabled', 'slider', 'map');
INSERT INTO layerv1 VALUES (130, true, NULL, 'WMTS', 'http://ows.asitvd.ch/wmts/1.0.0/WMTSCapabilities.xml', NULL, NULL, '{ "DIM1": "default", "ELEVATION": "0" }', NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, NULL, NULL, NULL, NULL, 'disabled', 'slider', 'asitvd.fond_gris');
INSERT INTO layerv1 VALUES (129, true, NULL, 'WMTS', 'http://ows.asitvd.ch/wmts/1.0.0/WMTSCapabilities.xml', NULL, NULL, '{ "DIM1": "default", "ELEVATION": "0" }', NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, NULL, NULL, NULL, NULL, 'disabled', 'slider', 'asitvd.fond_couleur');
INSERT INTO layerv1 VALUES (138, true, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, NULL, false, NULL, NULL, NULL, NULL, 'disabled', 'slider', 'osm_open');
INSERT INTO layerv1 VALUES (56, true, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Cafés', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'entertainment');
INSERT INTO layerv1 VALUES (61, true, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Restaurant', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'sustenance');
INSERT INTO layerv1 VALUES (53, true, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Hôtel', false, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'accommodation');
INSERT INTO layerv1 VALUES (62, true, NULL, 'internal WMS', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, NULL, 'Musée', true, NULL, NULL, '© les contributeurs d’OpenStreetMap', 'display_name', 'disabled', 'slider', 'tourisme_information');


--
-- TOC entry 3700 (class 0 OID 89598)
-- Dependencies: 215
-- Data for Name: metadata; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO metadata VALUES (7, 'legend', 'true', NULL, 98);
INSERT INTO metadata VALUES (9, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 98);
INSERT INTO metadata VALUES (12, 'legend', 'true', NULL, 99);
INSERT INTO metadata VALUES (14, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 99);
INSERT INTO metadata VALUES (17, 'legend', 'true', NULL, 100);
INSERT INTO metadata VALUES (19, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 100);
INSERT INTO metadata VALUES (21, 'legend', 'true', NULL, 101);
INSERT INTO metadata VALUES (23, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 101);
INSERT INTO metadata VALUES (26, 'legend', 'true', NULL, 102);
INSERT INTO metadata VALUES (28, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 102);
INSERT INTO metadata VALUES (30, 'legend', 'true', NULL, 103);
INSERT INTO metadata VALUES (32, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 103);
INSERT INTO metadata VALUES (35, 'legend', 'true', NULL, 104);
INSERT INTO metadata VALUES (37, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 104);
INSERT INTO metadata VALUES (40, 'legend', 'true', NULL, 105);
INSERT INTO metadata VALUES (42, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 105);
INSERT INTO metadata VALUES (45, 'legend', 'true', NULL, 106);
INSERT INTO metadata VALUES (47, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 106);
INSERT INTO metadata VALUES (50, 'legend', 'true', NULL, 107);
INSERT INTO metadata VALUES (52, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 107);
INSERT INTO metadata VALUES (55, 'legend', 'true', NULL, 108);
INSERT INTO metadata VALUES (57, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 108);
INSERT INTO metadata VALUES (59, 'legend', 'true', NULL, 109);
INSERT INTO metadata VALUES (64, 'legend', 'true', NULL, 110);
INSERT INTO metadata VALUES (66, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 110);
INSERT INTO metadata VALUES (69, 'legend', 'true', NULL, 111);
INSERT INTO metadata VALUES (73, 'legend', 'true', NULL, 112);
INSERT INTO metadata VALUES (78, 'legend', 'true', NULL, 113);
INSERT INTO metadata VALUES (82, 'legend', 'true', NULL, 114);
INSERT INTO metadata VALUES (84, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 114);
INSERT INTO metadata VALUES (86, 'legend', 'true', NULL, 115);
INSERT INTO metadata VALUES (87, 'disclaimer', '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 115);
INSERT INTO metadata VALUES (88, 'legend', 'true', NULL, 116);
INSERT INTO metadata VALUES (89, 'disclaimer', '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 116);
INSERT INTO metadata VALUES (91, 'legend', 'true', NULL, 117);
INSERT INTO metadata VALUES (92, 'disclaimer', '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 117);
INSERT INTO metadata VALUES (93, 'legend', 'true', NULL, 118);
INSERT INTO metadata VALUES (94, 'disclaimer', '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 118);
INSERT INTO metadata VALUES (95, 'legend', 'true', NULL, 119);
INSERT INTO metadata VALUES (98, 'disclaimer', '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 119);
INSERT INTO metadata VALUES (99, 'legend', 'true', NULL, 120);
INSERT INTO metadata VALUES (100, 'disclaimer', '<a href="http://www.geo.admin.ch/">Données publiques de l''infrastructure fédérale de données géographiques (IFDG)</a>', NULL, 120);
INSERT INTO metadata VALUES (102, 'legend', 'false', NULL, 121);
INSERT INTO metadata VALUES (104, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 121);
INSERT INTO metadata VALUES (106, 'legend', 'false', NULL, 122);
INSERT INTO metadata VALUES (108, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 122);
INSERT INTO metadata VALUES (111, 'legend', 'true', NULL, 123);
INSERT INTO metadata VALUES (113, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 123);
INSERT INTO metadata VALUES (60, 'isLegendExpanded', 'true', NULL, 109);
INSERT INTO metadata VALUES (6, 'isChecked', 'true', NULL, 98);
INSERT INTO metadata VALUES (11, 'isChecked', 'true', NULL, 99);
INSERT INTO metadata VALUES (16, 'isChecked', 'true', NULL, 100);
INSERT INTO metadata VALUES (25, 'isChecked', 'true', NULL, 102);
INSERT INTO metadata VALUES (34, 'isChecked', 'true', NULL, 104);
INSERT INTO metadata VALUES (39, 'isChecked', 'true', NULL, 105);
INSERT INTO metadata VALUES (44, 'isChecked', 'true', NULL, 106);
INSERT INTO metadata VALUES (49, 'isChecked', 'true', NULL, 107);
INSERT INTO metadata VALUES (54, 'isChecked', 'true', NULL, 108);
INSERT INTO metadata VALUES (63, 'isChecked', 'true', NULL, 110);
INSERT INTO metadata VALUES (68, 'isChecked', 'true', NULL, 111);
INSERT INTO metadata VALUES (72, 'isChecked', 'true', NULL, 112);
INSERT INTO metadata VALUES (77, 'isChecked', 'true', NULL, 113);
INSERT INTO metadata VALUES (81, 'isChecked', 'true', NULL, 114);
INSERT INTO metadata VALUES (101, 'isChecked', 'true', NULL, 121);
INSERT INTO metadata VALUES (110, 'isChecked', 'true', NULL, 123);
INSERT INTO metadata VALUES (115, 'isChecked', 'true', NULL, 124);
INSERT INTO metadata VALUES (10, 'identifierAttributeField', 'display_name', NULL, 98);
INSERT INTO metadata VALUES (15, 'identifierAttributeField', 'display_name', NULL, 99);
INSERT INTO metadata VALUES (20, 'identifierAttributeField', 'display_name', NULL, 100);
INSERT INTO metadata VALUES (24, 'identifierAttributeField', 'display_name', NULL, 101);
INSERT INTO metadata VALUES (29, 'identifierAttributeField', 'display_name', NULL, 102);
INSERT INTO metadata VALUES (33, 'identifierAttributeField', 'display_name', NULL, 103);
INSERT INTO metadata VALUES (38, 'identifierAttributeField', 'display_name', NULL, 104);
INSERT INTO metadata VALUES (43, 'identifierAttributeField', 'display_name', NULL, 105);
INSERT INTO metadata VALUES (48, 'identifierAttributeField', 'display_name', NULL, 106);
INSERT INTO metadata VALUES (53, 'identifierAttributeField', 'display_name', NULL, 107);
INSERT INTO metadata VALUES (58, 'identifierAttributeField', 'display_name', NULL, 108);
INSERT INTO metadata VALUES (62, 'identifierAttributeField', 'display_name', NULL, 109);
INSERT INTO metadata VALUES (67, 'identifierAttributeField', 'name', NULL, 110);
INSERT INTO metadata VALUES (97, 'maxResolution', '1000.0', NULL, 119);
INSERT INTO metadata VALUES (96, 'minResolution', '100.0', NULL, 119);
INSERT INTO metadata VALUES (76, 'metadataUrl', 'static:///htdocs/example.html', NULL, 113);
INSERT INTO metadata VALUES (116, 'legend', 'true', NULL, 124);
INSERT INTO metadata VALUES (118, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 124);
INSERT INTO metadata VALUES (121, 'legend', 'true', NULL, 125);
INSERT INTO metadata VALUES (125, 'legend', 'true', NULL, 126);
INSERT INTO metadata VALUES (8, 'legendRule', 'Informations', NULL, 98);
INSERT INTO metadata VALUES (13, 'legendRule', 'Cinémas', NULL, 99);
INSERT INTO metadata VALUES (18, 'legendRule', 'Banques', NULL, 100);
INSERT INTO metadata VALUES (27, 'legendRule', 'Cafés', NULL, 102);
INSERT INTO metadata VALUES (65, 'legendRule', 'Dans les temps', NULL, 110);
INSERT INTO metadata VALUES (70, 'legendRule', 'Line', NULL, 111);
INSERT INTO metadata VALUES (74, 'legendRule', 'Polygon', NULL, 112);
INSERT INTO metadata VALUES (79, 'legendRule', 'Point', NULL, 113);
INSERT INTO metadata VALUES (83, 'legendRule', 'OSM', NULL, 114);
INSERT INTO metadata VALUES (107, 'legendRule', 'Casernes de pompiers', NULL, 122);
INSERT INTO metadata VALUES (126, 'legendRule', 'Dans les temps', NULL, 126);
INSERT INTO metadata VALUES (120, 'isChecked', 'true', NULL, 125);
INSERT INTO metadata VALUES (71, 'identifierAttributeField', 'name', NULL, 111);
INSERT INTO metadata VALUES (51, 'legendRule', 'Restaurant', NULL, 107);
INSERT INTO metadata VALUES (46, 'legendRule', 'Office de poste', NULL, 106);
INSERT INTO metadata VALUES (41, 'legendRule', 'Poste de police', NULL, 105);
INSERT INTO metadata VALUES (56, 'legendRule', 'Musée', NULL, 108);
INSERT INTO metadata VALUES (112, 'legendRule', 'Hôtel', NULL, 123);
INSERT INTO metadata VALUES (31, 'legendRule', 'Parking', NULL, 103);
INSERT INTO metadata VALUES (22, 'legendRule', 'Arrêt de bus', NULL, 101);
INSERT INTO metadata VALUES (36, 'legendRule', 'Autre lieux de culte', NULL, 104);
INSERT INTO metadata VALUES (103, 'legendRule', 'Hôpital', NULL, 121);
INSERT INTO metadata VALUES (75, 'identifierAttributeField', 'name', NULL, 112);
INSERT INTO metadata VALUES (80, 'identifierAttributeField', 'name', NULL, 113);
INSERT INTO metadata VALUES (85, 'identifierAttributeField', 'display_name', NULL, 114);
INSERT INTO metadata VALUES (105, 'identifierAttributeField', 'display_name', NULL, 121);
INSERT INTO metadata VALUES (109, 'identifierAttributeField', 'display_name', NULL, 122);
INSERT INTO metadata VALUES (114, 'identifierAttributeField', 'display_name', NULL, 123);
INSERT INTO metadata VALUES (119, 'identifierAttributeField', 'display_name', NULL, 124);
INSERT INTO metadata VALUES (127, 'identifierAttributeField', 'name', NULL, 126);
INSERT INTO metadata VALUES (123, 'maxResolution', '100.0', NULL, 125);
INSERT INTO metadata VALUES (122, 'minResolution', '1.0', NULL, 125);
INSERT INTO metadata VALUES (124, 'disclaimer', '© <a href=''http://asitvd.ch''>ASIT VD</a>, Contributeurs d’<a href=''http://www.openstreetmap.org/copyright''>OpenStreetMap</a>', NULL, 125);
INSERT INTO metadata VALUES (151, 'wmsLayers', 'ch.are.alpenkonvention', NULL, 119);
INSERT INTO metadata VALUES (152, 'queryLayers', 'ch.astra.ausnahmetransportrouten', NULL, 120);
INSERT INTO metadata VALUES (157, 'disclaimer', 'Editing theme', NULL, 72);
INSERT INTO metadata VALUES (158, 'disclaimer', 'Editing theme', NULL, 73);
INSERT INTO metadata VALUES (159, 'isExpanded', 'true', NULL, 6);
INSERT INTO metadata VALUES (160, 'isExpanded', 'true', NULL, 7);
INSERT INTO metadata VALUES (161, 'isExpanded', 'true', NULL, 8);
INSERT INTO metadata VALUES (162, 'isExpanded', 'true', NULL, 9);
INSERT INTO metadata VALUES (164, 'isExpanded', 'true', NULL, 30);
INSERT INTO metadata VALUES (165, 'isExpanded', 'true', NULL, 35);
INSERT INTO metadata VALUES (166, 'isExpanded', 'true', NULL, 36);
INSERT INTO metadata VALUES (167, 'isExpanded', 'true', NULL, 68);
INSERT INTO metadata VALUES (168, 'isExpanded', 'true', NULL, 72);
INSERT INTO metadata VALUES (169, 'isExpanded', 'true', NULL, 94);
INSERT INTO metadata VALUES (170, 'isLegendExpanded', 'true', NULL, 86);
INSERT INTO metadata VALUES (171, 'isLegendExpanded', 'true', NULL, 77);
INSERT INTO metadata VALUES (172, 'isLegendExpanded', 'true', NULL, 48);
INSERT INTO metadata VALUES (173, 'metadataUrl', 'static:///htdocs/example.html', NULL, 48);
INSERT INTO metadata VALUES (174, 'identifierAttributeField', 'last_update_timestamp', NULL, 71);
INSERT INTO metadata VALUES (175, 'legendRule', 'Dans les temps', NULL, 147);
INSERT INTO metadata VALUES (176, 'identifierAttributeField', 'name', NULL, 147);
INSERT INTO metadata VALUES (61, 'disclaimer', '© les contributeurs d’OpenStreetMap', NULL, 109);
INSERT INTO metadata VALUES (179, 'wmsLayers', 'ch.are.alpenkonvention', NULL, 81);
INSERT INTO metadata VALUES (180, 'wmsLayers', 'ch.astra.ausnahmetransportrouten', NULL, 86);
INSERT INTO metadata VALUES (177, 'serverOGC', 'Main PNG', NULL, 128);
INSERT INTO metadata VALUES (181, 'serverOGC', 'WMS CH topo fr', NULL, 81);
INSERT INTO metadata VALUES (182, 'serverOGC', 'WMS CH topo fr', NULL, 86);
INSERT INTO metadata VALUES (184, 'lastUpdateDateColumn', 'last_update_timestamp', NULL, 71);
INSERT INTO metadata VALUES (185, 'lastUpdateUserColumn', 'last_update_user', NULL, 71);
INSERT INTO metadata VALUES (134, 'thumbnail', 'static://static/img/cadastre.jpeg', NULL, 132);
INSERT INTO metadata VALUES (133, 'thumbnail', 'static://static/img/cadastre.jpeg', NULL, 133);
INSERT INTO metadata VALUES (132, 'thumbnail', 'static://static/img/cadastre.jpeg', NULL, 134);
INSERT INTO metadata VALUES (186, 'snappingConfig', '{}', NULL, 155);
INSERT INTO metadata VALUES (188, 'snappingConfig', '{}', NULL, 163);
INSERT INTO metadata VALUES (187, 'snappingConfig', '{}', NULL, 154);
INSERT INTO metadata VALUES (195, 'snappingConfig', '{"vertex": false}', NULL, 162);
INSERT INTO metadata VALUES (194, 'snappingConfig', '{"vertex": false}', NULL, 160);
INSERT INTO metadata VALUES (193, 'snappingConfig', '{"edge": false}', NULL, 161);
INSERT INTO metadata VALUES (192, 'snappingConfig', '{"edge": false}', NULL, 159);
INSERT INTO metadata VALUES (191, 'snappingConfig', '{"tolerance": 50}', NULL, 156);
INSERT INTO metadata VALUES (190, 'snappingConfig', '{"tolerance": 50}', NULL, 157);
INSERT INTO metadata VALUES (189, 'snappingConfig', '{"tolerance": 50}', NULL, 158);
INSERT INTO metadata VALUES (178, 'queryLayers', 'buildings,buildings15,buildings16,buildings17,buildings18', 'Only buildings', 128);
INSERT INTO metadata VALUES (196, 'ogcServer', 'Main PNG', NULL, 134);
INSERT INTO metadata VALUES (198, 'copyable', 'true', NULL, 170);
INSERT INTO metadata VALUES (199, 'copyable', 'true', NULL, 172);
INSERT INTO metadata VALUES (200, 'copyable', 'true', NULL, 173);
INSERT INTO metadata VALUES (209, 'thumbnail', 'static://static/img/cadastre.jpeg', NULL, 175);
INSERT INTO metadata VALUES (212, 'opacity', '0.8', NULL, 120);
INSERT INTO metadata VALUES (213, 'opacity', '0.654321', NULL, 66);
INSERT INTO metadata VALUES (211, 'opacity', '0.25', NULL, 118);
INSERT INTO metadata VALUES (214, 'timeAttribute', 'timestamp', NULL, 147);
INSERT INTO metadata VALUES (216, 'timeAttribute', 'timestamp', NULL, 110);
INSERT INTO metadata VALUES (217, 'timeAttribute', 'timestamp', NULL, 144);
INSERT INTO metadata VALUES (218, 'timeAttribute', 'timestamp', NULL, 143);
INSERT INTO metadata VALUES (219, 'timeAttribute', 'timestamp', NULL, 126);
INSERT INTO metadata VALUES (203, 'enumeratedAttributes', 'type', NULL, 139);
INSERT INTO metadata VALUES (204, 'directedFilterAttributes', 'name,type,timestamp', NULL, 138);
INSERT INTO metadata VALUES (205, 'directedFilterAttributes', 'name,type,timestamp', NULL, 134);
INSERT INTO metadata VALUES (207, 'directedFilterAttributes', 'Classification_des_roches', NULL, 118);
INSERT INTO metadata VALUES (215, 'directedFilterAttributes', 'name,type,timestamp', NULL, 147);
INSERT INTO metadata VALUES (197, 'wmsLayers', 'buildings_query', NULL, 134);
INSERT INTO metadata VALUES (154, 'maxResolution', '1000', NULL, 119);
INSERT INTO metadata VALUES (153, 'minResolution', '10', NULL, 119);
INSERT INTO metadata VALUES (221, 'disclaimer', 'This is a test disclaimer, to test metadata addition.', NULL, 2);
INSERT INTO metadata VALUES (117, 'legendRule', 'Station à votre service.', NULL, 124);
INSERT INTO metadata VALUES (222, 'disclaimer', 'Test for a disclaimer to test metadata', NULL, 36);


--
-- TOC entry 3701 (class 0 OID 89604)
-- Dependencies: 216
-- Data for Name: ogc_server; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO ogc_server VALUES (3, 'WMS CH topo fr', NULL, 'https://wms.geo.admin.ch?lang=fr', NULL, 'mapserver', 'image/png', 'No auth', false, false);
INSERT INTO ogc_server VALUES (2, 'Main PNG', 'default source for internal image/png', 'config://internal/mapserv', NULL, 'mapserver', 'image/png', 'Standard auth', true, false);
INSERT INTO ogc_server VALUES (1, 'Main Jpeg', 'default source for internal image/jpeg', 'config://internal/mapserv', NULL, 'mapserver', 'image/jpeg', 'Standard auth', true, false);
INSERT INTO ogc_server VALUES (4, 'Main no WFS', NULL, 'config://internal/mapserv', NULL, 'mapserver', 'image/png', 'Standard auth', false, false);


--
-- TOC entry 3702 (class 0 OID 89612)
-- Dependencies: 217
-- Data for Name: restricted_role_theme; Type: TABLE DATA; Schema: main; Owner: www-data
--



--
-- TOC entry 3703 (class 0 OID 89615)
-- Dependencies: 218
-- Data for Name: restrictionarea; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO restrictionarea VALUES (5, 'Edit', NULL, true, NULL);
INSERT INTO restrictionarea VALUES (7, 'No area', NULL, false, NULL);
INSERT INTO restrictionarea VALUES (8, 'Full', NULL, false, '0103000020155500000100000005000000C8FDA77D9C1C2041664417390BE612415B6BF262ECC7174144C0DEE49C4DEE405A4AC4FF745D2C41D03671BC04E7FC40B67FE1FEE4062841C4993E5675271341C8FDA77D9C1C2041664417390BE61241');
INSERT INTO restrictionarea VALUES (6, 'Lausanne', NULL, false, '0103000020155500000100000005000000B794C4CC55082041C8560660875E0341B0F0877F4ECE1F41E8EF98BE1D0E02412AA6A6FA51A7204147749D3B4A5E0241040531EBB89B20418BEA30078AA30341B794C4CC55082041C8560660875E0341');
INSERT INTO restrictionarea VALUES (9, 'northwest', NULL, false, '010300002015550000010000001200000030C6B741648B2141881D03F0969E1041F21711D1237624412D0B82F95DF21141AF36043EA4CF2541BF75A47FA5B0124126476759CAD62641EF3E2AD4E6BA10411771213225F325419E19C518F9BF0D4184BD352C8CD724419E29458678A60B411C9350F87E442341ED68B47B55C70A419A01FBAE86B522416832B924FC88084139282F9BB6322241DB85194E13A8044193B935A595F02141407CA26EF22B014177405D36B74421419B1DFFF7FB5B0041ACCB89A9456C2041E63F39F9C7BF02419178418CA6AB2041245C1EC2972C04413AFCA4EE7B952041F862029BDE8E05410A4FECEC354020415D95FEB36792054102FCCCDA04C91F41E49E908322BE054188FD94E773E11F41CC9F8C155E98084130C6B741648B2141881D03F0969E1041');
INSERT INTO restrictionarea VALUES (10, 'bern', NULL, false, '01030000201555000001000000060000004E0106F9E47A21414C248C5965830A41BE7980381B05234184DF6B7B61550A41CCA8829C762D2341A3662FB123300641C6573A1EDB6021412E8DBD54299A054146563FF253B82141C08B2E84844C08414E0106F9E47A21414C248C5965830A41');


--
-- TOC entry 3739 (class 0 OID 0)
-- Dependencies: 219
-- Name: restrictionarea_id_seq; Type: SEQUENCE SET; Schema: main; Owner: www-data
--

SELECT pg_catalog.setval('restrictionarea_id_seq', 10, true);


--
-- TOC entry 3705 (class 0 OID 89623)
-- Dependencies: 220
-- Data for Name: role; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO role VALUES (8, 'northwest', NULL, '0103000020155500000100000005000000C2D3617A13E71E412090D5C8F8F9004154D466AD1EFE1E41266D28F2AE8D0C41604D4A47514E24414658B06A7D820C411E5101BE785624418D3F0C9599EE0041C2D3617A13E71E412090D5C8F8F90041');
INSERT INTO role VALUES (9, 'bern', NULL, NULL);
INSERT INTO role VALUES (1, 'role_admin', NULL, '0103000020155500000100000005000000278B98D3B74B204111908E548D8B0241F8BD5951CD4B20416D9A74EB1EAA0241765F4436A34020419E8B37DD9DAA0241019989418D4020411AB2A24B0C8C0241278B98D3B74B204111908E548D8B0241');
INSERT INTO role VALUES (6, 'demo', NULL, '01030000201555000001000000050000001C501B36E553204199E90766706B024136D4340244542041190F325578F402414AF798AEA47E2041D22D9AD7B6F20241DD2BB5CB4D7E204184360594AE6902411C501B36E553204199E90766706B0241');


--
-- TOC entry 3706 (class 0 OID 89632)
-- Dependencies: 221
-- Data for Name: role_functionality; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO role_functionality VALUES (6, 6);
INSERT INTO role_functionality VALUES (6, 7);
INSERT INTO role_functionality VALUES (6, 8);
INSERT INTO role_functionality VALUES (6, 9);
INSERT INTO role_functionality VALUES (1, 9);
INSERT INTO role_functionality VALUES (6, 10);
INSERT INTO role_functionality VALUES (1, 10);


--
-- TOC entry 3740 (class 0 OID 0)
-- Dependencies: 222
-- Name: role_id_seq; Type: SEQUENCE SET; Schema: main; Owner: www-data
--

SELECT pg_catalog.setval('role_id_seq', 10, true);


--
-- TOC entry 3708 (class 0 OID 89637)
-- Dependencies: 223
-- Data for Name: role_restrictionarea; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO role_restrictionarea VALUES (6, 6);
INSERT INTO role_restrictionarea VALUES (1, 5);
INSERT INTO role_restrictionarea VALUES (6, 5);
INSERT INTO role_restrictionarea VALUES (1, 7);
INSERT INTO role_restrictionarea VALUES (6, 7);
INSERT INTO role_restrictionarea VALUES (1, 8);
INSERT INTO role_restrictionarea VALUES (8, 9);
INSERT INTO role_restrictionarea VALUES (9, 10);
INSERT INTO role_restrictionarea VALUES (1, 6);
INSERT INTO role_restrictionarea VALUES (1, 9);
INSERT INTO role_restrictionarea VALUES (1, 10);


--
-- TOC entry 3741 (class 0 OID 0)
-- Dependencies: 224
-- Name: server_ogc_id_seq; Type: SEQUENCE SET; Schema: main; Owner: www-data
--

SELECT pg_catalog.setval('server_ogc_id_seq', 4, true);


--
-- TOC entry 3710 (class 0 OID 89642)
-- Dependencies: 225
-- Data for Name: theme; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO theme VALUES (73, 'static:///img/edit.png', 100, true);
INSERT INTO theme VALUES (64, 'static:///img/osm.png', 100, true);
INSERT INTO theme VALUES (38, 'static:///img/enseignement.jpeg', 100, true);
INSERT INTO theme VALUES (37, 'static:///img/transports.jpeg', 100, true);
INSERT INTO theme VALUES (29, 'static:///img/cadastre.jpeg', 100, true);
INSERT INTO theme VALUES (5, 'static:///img/administration.jpeg', 100, true);
INSERT INTO theme VALUES (4, 'static:///img/patrimoine.jpeg', 100, true);
INSERT INTO theme VALUES (3, 'static:///img/gestion_eaux.jpeg', 100, true);
INSERT INTO theme VALUES (2, 'static:///img/paysage.jpeg', 100, true);
INSERT INTO theme VALUES (91, 'static:///img/equipement.jpeg', 100, true);
INSERT INTO theme VALUES (92, 'static:///img/enseignement2.jpeg', 100, true);
INSERT INTO theme VALUES (168, 'static:///img/edit.png', 100, true);
INSERT INTO theme VALUES (176, 'static:///img/filters.png', 100, true);


--
-- TOC entry 3711 (class 0 OID 89648)
-- Dependencies: 226
-- Data for Name: theme_functionality; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO theme_functionality VALUES (64, 9);
INSERT INTO theme_functionality VALUES (29, 5);


--
-- TOC entry 3712 (class 0 OID 89651)
-- Dependencies: 227
-- Data for Name: treegroup; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO treegroup VALUES (2);
INSERT INTO treegroup VALUES (3);
INSERT INTO treegroup VALUES (4);
INSERT INTO treegroup VALUES (5);
INSERT INTO treegroup VALUES (6);
INSERT INTO treegroup VALUES (7);
INSERT INTO treegroup VALUES (8);
INSERT INTO treegroup VALUES (9);
INSERT INTO treegroup VALUES (29);
INSERT INTO treegroup VALUES (30);
INSERT INTO treegroup VALUES (35);
INSERT INTO treegroup VALUES (36);
INSERT INTO treegroup VALUES (37);
INSERT INTO treegroup VALUES (38);
INSERT INTO treegroup VALUES (63);
INSERT INTO treegroup VALUES (64);
INSERT INTO treegroup VALUES (66);
INSERT INTO treegroup VALUES (68);
INSERT INTO treegroup VALUES (72);
INSERT INTO treegroup VALUES (73);
INSERT INTO treegroup VALUES (91);
INSERT INTO treegroup VALUES (92);
INSERT INTO treegroup VALUES (93);
INSERT INTO treegroup VALUES (94);
INSERT INTO treegroup VALUES (131);
INSERT INTO treegroup VALUES (135);
INSERT INTO treegroup VALUES (136);
INSERT INTO treegroup VALUES (137);
INSERT INTO treegroup VALUES (145);
INSERT INTO treegroup VALUES (146);
INSERT INTO treegroup VALUES (153);
INSERT INTO treegroup VALUES (164);
INSERT INTO treegroup VALUES (165);
INSERT INTO treegroup VALUES (166);
INSERT INTO treegroup VALUES (167);
INSERT INTO treegroup VALUES (168);
INSERT INTO treegroup VALUES (169);
INSERT INTO treegroup VALUES (174);
INSERT INTO treegroup VALUES (176);
INSERT INTO treegroup VALUES (183);


--
-- TOC entry 3713 (class 0 OID 89654)
-- Dependencies: 228
-- Data for Name: treeitem; Type: TABLE DATA; Schema: main; Owner: www-data
--

INSERT INTO treeitem VALUES ('theme', 2, 'Paysage', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 3, 'Gestion des eaux', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 5, 'Administration', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 8, 'Gestion des eaux', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 9, 'Paysage', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 66, 'Group', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 63, 'Layers', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 72, 'Edit', 'http://example.com/camptocamp', NULL);
INSERT INTO treeitem VALUES ('theme', 73, 'Edit', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 50, 'information', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 51, 'cinema', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 54, 'bank', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 55, 'bus_stop', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 57, 'parking', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 58, 'place_of_worship', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 59, 'police', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 60, 'post_office', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 65, 'osm', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 67, 'osm_time', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 70, 'line', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 71, 'polygon', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 69, 'point', 'http://example.com/camptocamp', NULL);
INSERT INTO treeitem VALUES ('layerv1', 74, 'osm_scale', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 77, 'ch.swisstopo.dreiecksvermaschung', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 78, 'ch.swisstopo.geologie-gravimetrischer_atlas', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 79, 'ch.swisstopo.geologie-geotechnik-gk500-lithologie_hauptgruppen', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 80, 'ch.swisstopo.geologie-geotechnik-gk500-gesteinsklassierung', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 81, 'ch.are.alpenkonvention', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 86, 'ch.astra.ausnahmetransportrouten', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 11, 'hospitals', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 12, 'firestations', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 37, 'Transport', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 29, 'Cadastre', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 4, 'Patrimoine', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 91, 'Equipement', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 92, 'Enseignement', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 7, 'Patrimoine', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 30, 'Cadastre', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 36, 'Transport', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 93, 'Enseignement', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 94, 'Equipement', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 48, 'fuel', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 95, 'asitvd.fond_pourortho', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wmts', 120, 'ch.astra.ausnahmetransportrouten', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wmts', 125, 'asitvd.fond_pourortho', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 128, 'map', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 130, 'asitvd.fond_gris', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 129, 'asitvd.fond_couleur', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 131, 'background', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wmts', 132, 'asitvd.fond_gris', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wmts', 133, 'asitvd.fond_couleur', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 135, 'test', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 136, 'test2', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 98, 'information', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 99, 'cinema', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 100, 'bank', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 101, 'bus_stop', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 103, 'parking', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 104, 'place_of_worship', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 105, 'police', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 106, 'post_office', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 109, 'osm', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 111, 'line', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 112, 'polygon', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 114, 'osm_scale', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 115, 'ch.swisstopo.dreiecksvermaschung', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 116, 'ch.swisstopo.geologie-gravimetrischer_atlas', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 117, 'ch.swisstopo.geologie-geotechnik-gk500-lithologie_hauptgruppen', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 118, 'ch.swisstopo.geologie-geotechnik-gk500-gesteinsklassierung', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 121, 'hospitals', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 122, 'firestations', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 124, 'fuel', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 38, 'Enseignement 2', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 138, 'osm_open', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 139, 'osm_open', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 140, 'Layer with very very very very very long name', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 113, 'point', 'http://example.com/camptocamp', NULL);
INSERT INTO treeitem VALUES ('l_wms', 141, 'two_layers', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 126, 'osm_time_r_dp', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 143, 'osm_time_v_s', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 144, 'osm_time_v_dp', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 145, 'osm_time', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 110, 'osm_time_r_s', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 147, 'osm_time_r_dp_2', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 146, 'OSM functions', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 68, 'OSM functions mixed', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 107, 'sustenance', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 102, 'entertainment', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 56, 'entertainment', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 61, 'sustenance', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 123, 'accommodation', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 53, 'accommodation', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 137, 'Loisirs', NULL, NULL);
INSERT INTO treeitem VALUES ('layerv1', 62, 'tourisme_information', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 154, 'point snap', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 108, 'tourism_activity', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 150, 'Half query', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 151, 'srtm', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 152, 'aster', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 155, 'line snap', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 153, 'External', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 6, 'Administration', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 35, 'Enseignement 2', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 157, 'line snap tolerance', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 158, 'polygon snap tolerance', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 159, 'line snap no edge', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 160, 'line snap no vertex', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 161, 'polygon snap no edge', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 162, 'polygon snap no vertex', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 163, 'polygon snap', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 164, 'Snapping', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 165, 'Snapping tollerance', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 166, 'Snapping no edge', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 167, 'Snapping no vertex', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 168, 'ObjectEditing', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 169, 'ObjectEditing', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 170, 'Multi-Polygon Query pas éditable mais queryable', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 171, 'Multi-Polygon Query2 pas éditable mais queryable', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 172, 'Multi-Line pas éditable mais queryable', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 173, 'Multi-Point pas éditable mais queryable', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wmts', 134, 'OSM map', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 175, 'OSM map WMS', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 176, 'Filters', NULL, NULL);
INSERT INTO treeitem VALUES ('theme', 64, 'Demo', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 181, 'no_wfs', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 174, 'Filters mixed', NULL, NULL);
INSERT INTO treeitem VALUES ('group', 183, 'Filters', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wmts', 182, 'Test aus Olten', NULL, 'Test change something in layer');
INSERT INTO treeitem VALUES ('l_wms', 156, 'point snap tolerance', NULL, 'Test change something in layer');
INSERT INTO treeitem VALUES ('l_wms', 179, 'osm_time_r_month_year', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 178, 'osm_time_d_year_month', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 177, 'osm_time_r_year_month', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 180, 'osm_time_v_month_year', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wms', 184, 'Long time layer name, very very very long', NULL, NULL);
INSERT INTO treeitem VALUES ('l_wmts', 119, 'Alpen Konvention', 'http://google.fr', NULL);


--
-- TOC entry 3742 (class 0 OID 0)
-- Dependencies: 229
-- Name: treeitem_id_seq; Type: SEQUENCE SET; Schema: main; Owner: www-data
--

SELECT pg_catalog.setval('treeitem_id_seq', 184, true);


--
-- TOC entry 3743 (class 0 OID 0)
-- Dependencies: 232
-- Name: ui_metadata_id_seq; Type: SEQUENCE SET; Schema: main; Owner: www-data
--

SELECT pg_catalog.setval('ui_metadata_id_seq', 222, true);


--
-- TOC entry 3744 (class 0 OID 0)
-- Dependencies: 233
-- Name: wmts_dimension_id_seq; Type: SEQUENCE SET; Schema: main; Owner: www-data
--

SELECT pg_catalog.setval('wmts_dimension_id_seq', 13, true);


SET search_path = main_static, pg_catalog;

--
-- TOC entry 3717 (class 0 OID 89676)
-- Dependencies: 234
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: main_static; Owner: www-data
--

INSERT INTO alembic_version VALUES ('5472fbc19f39');


--
-- TOC entry 3718 (class 0 OID 89687)
-- Dependencies: 237
-- Data for Name: user; Type: TABLE DATA; Schema: main_static; Owner: www-data
--

INSERT INTO "user" VALUES ('user', 5, 'demobern', '89e495e7941cf9e40e6980d14a16bf023ccd4c91', 'info@camptocamp.com', false, 'bern', NULL);
INSERT INTO "user" VALUES ('user', 6, 'demonorthwest', '89e495e7941cf9e40e6980d14a16bf023ccd4c91', 'info@camptocamp.com', false, 'northwest', NULL);
INSERT INTO "user" VALUES ('user', 1, 'admin', 'ea05895d9eed5496a7d8e4786d50b3bb2942d20b', 'stephane.brunner@camptocamp.com', true, 'role_admin', '4f6a0231426ea5823d90c65adbca7360d6266223');
INSERT INTO "user" VALUES ('user', 2, 'demo', '89e495e7941cf9e40e6980d14a16bf023ccd4c91', 'stephane.brunner@camptocamp.com', true, 'demo', '070552038784c5ce92ef4680056865ed82279358');
INSERT INTO "user" VALUES ('user', 4, 'adube', '92a6d9f1bfc29df22266b760c4d389ca5899842a', 'adube@mapgears.com', false, 'demo', NULL);
INSERT INTO "user" VALUES ('user', 8, 'demotest', 'da39a3ee5e6b4b0d3255bfef95601890afd80709', 'DEMO@DEMO.CH', false, 'bern', NULL);


--
-- TOC entry 3745 (class 0 OID 0)
-- Dependencies: 238
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: main_static; Owner: www-data
--

SELECT pg_catalog.setval('user_id_seq', 8, true);


SET search_path = main, pg_catalog;

--
-- TOC entry 3482 (class 2606 OID 91279)
-- Name: functionality_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY functionality
    ADD CONSTRAINT functionality_pkey PRIMARY KEY (id);


--
-- TOC entry 3486 (class 2606 OID 91281)
-- Name: interface_layer_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY interface_layer
    ADD CONSTRAINT interface_layer_pkey PRIMARY KEY (interface_id, layer_id);


--
-- TOC entry 3484 (class 2606 OID 91283)
-- Name: interface_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY interface
    ADD CONSTRAINT interface_pkey PRIMARY KEY (id);


--
-- TOC entry 3488 (class 2606 OID 91285)
-- Name: interface_theme_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY interface_theme
    ADD CONSTRAINT interface_theme_pkey PRIMARY KEY (interface_id, theme_id);


--
-- TOC entry 3490 (class 2606 OID 91287)
-- Name: layer2_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer
    ADD CONSTRAINT layer2_pkey PRIMARY KEY (id);


--
-- TOC entry 3492 (class 2606 OID 91289)
-- Name: layer_restrictionarea_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer_restrictionarea
    ADD CONSTRAINT layer_restrictionarea_pkey PRIMARY KEY (layer_id, restrictionarea_id);


--
-- TOC entry 3494 (class 2606 OID 91291)
-- Name: layer_wms_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer_wms
    ADD CONSTRAINT layer_wms_pkey PRIMARY KEY (id);


--
-- TOC entry 3496 (class 2606 OID 91293)
-- Name: layer_wmts_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer_wmts
    ADD CONSTRAINT layer_wmts_pkey PRIMARY KEY (id);


--
-- TOC entry 3498 (class 2606 OID 91295)
-- Name: layergroup_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layergroup
    ADD CONSTRAINT layergroup_pkey PRIMARY KEY (id);


--
-- TOC entry 3500 (class 2606 OID 91297)
-- Name: layergroup_treeitem_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layergroup_treeitem
    ADD CONSTRAINT layergroup_treeitem_pkey PRIMARY KEY (id);


--
-- TOC entry 3502 (class 2606 OID 91299)
-- Name: layerv1_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layerv1
    ADD CONSTRAINT layerv1_pkey PRIMARY KEY (id);


--
-- TOC entry 3506 (class 2606 OID 91301)
-- Name: name_unique_ogc_server; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY ogc_server
    ADD CONSTRAINT name_unique_ogc_server UNIQUE (name);


--
-- TOC entry 3510 (class 2606 OID 91303)
-- Name: restricted_role_theme_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY restricted_role_theme
    ADD CONSTRAINT restricted_role_theme_pkey PRIMARY KEY (role_id, theme_id);


--
-- TOC entry 3512 (class 2606 OID 91305)
-- Name: restrictionarea_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY restrictionarea
    ADD CONSTRAINT restrictionarea_pkey PRIMARY KEY (id);


--
-- TOC entry 3519 (class 2606 OID 91307)
-- Name: role_functionality_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY role_functionality
    ADD CONSTRAINT role_functionality_pkey PRIMARY KEY (role_id, functionality_id);


--
-- TOC entry 3515 (class 2606 OID 91309)
-- Name: role_name_key; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY role
    ADD CONSTRAINT role_name_key UNIQUE (name);


--
-- TOC entry 3517 (class 2606 OID 91311)
-- Name: role_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY role
    ADD CONSTRAINT role_pkey PRIMARY KEY (id);


--
-- TOC entry 3521 (class 2606 OID 91313)
-- Name: role_restrictionarea_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY role_restrictionarea
    ADD CONSTRAINT role_restrictionarea_pkey PRIMARY KEY (role_id, restrictionarea_id);


--
-- TOC entry 3508 (class 2606 OID 91315)
-- Name: server_ogc_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY ogc_server
    ADD CONSTRAINT server_ogc_pkey PRIMARY KEY (id);


--
-- TOC entry 3525 (class 2606 OID 91317)
-- Name: theme_functionality_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY theme_functionality
    ADD CONSTRAINT theme_functionality_pkey PRIMARY KEY (theme_id, functionality_id);


--
-- TOC entry 3523 (class 2606 OID 91319)
-- Name: theme_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY theme
    ADD CONSTRAINT theme_pkey PRIMARY KEY (id);


--
-- TOC entry 3527 (class 2606 OID 91321)
-- Name: treegroup_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY treegroup
    ADD CONSTRAINT treegroup_pkey PRIMARY KEY (id);


--
-- TOC entry 3529 (class 2606 OID 91323)
-- Name: treeitem_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY treeitem
    ADD CONSTRAINT treeitem_pkey PRIMARY KEY (id);


--
-- TOC entry 3531 (class 2606 OID 91327)
-- Name: type_name_unique_treeitem; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY treeitem
    ADD CONSTRAINT type_name_unique_treeitem UNIQUE (type, name);


--
-- TOC entry 3504 (class 2606 OID 91329)
-- Name: ui_metadata_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT ui_metadata_pkey PRIMARY KEY (id);


--
-- TOC entry 3480 (class 2606 OID 91331)
-- Name: wmts_dimension_pkey; Type: CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY dimension
    ADD CONSTRAINT wmts_dimension_pkey PRIMARY KEY (id);


SET search_path = main_static, pg_catalog;

--
-- TOC entry 3533 (class 2606 OID 91335)
-- Name: user_pkey; Type: CONSTRAINT; Schema: main_static; Owner: www-data
--

ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- TOC entry 3535 (class 2606 OID 91337)
-- Name: user_username_key; Type: CONSTRAINT; Schema: main_static; Owner: www-data
--

ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


SET search_path = main, pg_catalog;

--
-- TOC entry 3513 (class 1259 OID 91338)
-- Name: idx_role_extent; Type: INDEX; Schema: main; Owner: www-data
--

CREATE INDEX idx_role_extent ON role USING gist (extent);


--
-- TOC entry 3562 (class 2620 OID 91342)
-- Name: on_role_name_change; Type: TRIGGER; Schema: main; Owner: www-data
--

CREATE TRIGGER on_role_name_change AFTER UPDATE ON role FOR EACH ROW EXECUTE PROCEDURE on_role_name_change();


--
-- TOC entry 3536 (class 2606 OID 91343)
-- Name: dimension_layer_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY dimension
    ADD CONSTRAINT dimension_layer_id_fkey FOREIGN KEY (layer_id) REFERENCES layer(id);


--
-- TOC entry 3537 (class 2606 OID 91348)
-- Name: interface_layer_interface_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY interface_layer
    ADD CONSTRAINT interface_layer_interface_id_fkey FOREIGN KEY (interface_id) REFERENCES interface(id);


--
-- TOC entry 3538 (class 2606 OID 91353)
-- Name: interface_layer_layer_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY interface_layer
    ADD CONSTRAINT interface_layer_layer_id_fkey FOREIGN KEY (layer_id) REFERENCES layer(id) ON DELETE CASCADE;


--
-- TOC entry 3539 (class 2606 OID 91358)
-- Name: interface_theme_interface_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY interface_theme
    ADD CONSTRAINT interface_theme_interface_id_fkey FOREIGN KEY (interface_id) REFERENCES interface(id);


--
-- TOC entry 3540 (class 2606 OID 91363)
-- Name: interface_theme_theme_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY interface_theme
    ADD CONSTRAINT interface_theme_theme_id_fkey FOREIGN KEY (theme_id) REFERENCES theme(id);


--
-- TOC entry 3541 (class 2606 OID 91368)
-- Name: layer_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer
    ADD CONSTRAINT layer_id_fkey FOREIGN KEY (id) REFERENCES treeitem(id) ON DELETE CASCADE;


--
-- TOC entry 3542 (class 2606 OID 91373)
-- Name: layer_restrictionarea_layer_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer_restrictionarea
    ADD CONSTRAINT layer_restrictionarea_layer_id_fkey FOREIGN KEY (layer_id) REFERENCES layer(id);


--
-- TOC entry 3543 (class 2606 OID 91378)
-- Name: layer_restrictionarea_restrictionarea_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer_restrictionarea
    ADD CONSTRAINT layer_restrictionarea_restrictionarea_id_fkey FOREIGN KEY (restrictionarea_id) REFERENCES restrictionarea(id);


--
-- TOC entry 3544 (class 2606 OID 91383)
-- Name: layer_wms_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer_wms
    ADD CONSTRAINT layer_wms_id_fkey FOREIGN KEY (id) REFERENCES layer(id) ON DELETE CASCADE;


--
-- TOC entry 3545 (class 2606 OID 91388)
-- Name: layer_wms_server_ogc_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer_wms
    ADD CONSTRAINT layer_wms_server_ogc_id_fkey FOREIGN KEY (ogc_server_id) REFERENCES ogc_server(id);


--
-- TOC entry 3546 (class 2606 OID 91393)
-- Name: layer_wmts_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layer_wmts
    ADD CONSTRAINT layer_wmts_id_fkey FOREIGN KEY (id) REFERENCES layer(id) ON DELETE CASCADE;


--
-- TOC entry 3547 (class 2606 OID 91398)
-- Name: layergroup_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layergroup
    ADD CONSTRAINT layergroup_id_fkey FOREIGN KEY (id) REFERENCES treegroup(id) ON DELETE CASCADE;


--
-- TOC entry 3548 (class 2606 OID 91403)
-- Name: layergroup_treeitem_treegroup_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layergroup_treeitem
    ADD CONSTRAINT layergroup_treeitem_treegroup_id_fkey FOREIGN KEY (treegroup_id) REFERENCES treegroup(id);


--
-- TOC entry 3549 (class 2606 OID 91408)
-- Name: layergroup_treeitem_treeitem_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layergroup_treeitem
    ADD CONSTRAINT layergroup_treeitem_treeitem_id_fkey FOREIGN KEY (treeitem_id) REFERENCES treeitem(id) ON DELETE CASCADE;


--
-- TOC entry 3550 (class 2606 OID 91413)
-- Name: layerv1_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY layerv1
    ADD CONSTRAINT layerv1_id_fkey FOREIGN KEY (id) REFERENCES layer(id) ON DELETE CASCADE;


--
-- TOC entry 3552 (class 2606 OID 91418)
-- Name: restricted_role_theme_role_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY restricted_role_theme
    ADD CONSTRAINT restricted_role_theme_role_id_fkey FOREIGN KEY (role_id) REFERENCES role(id);


--
-- TOC entry 3553 (class 2606 OID 91423)
-- Name: restricted_role_theme_theme_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY restricted_role_theme
    ADD CONSTRAINT restricted_role_theme_theme_id_fkey FOREIGN KEY (theme_id) REFERENCES theme(id);


--
-- TOC entry 3554 (class 2606 OID 91428)
-- Name: role_functionality_functionality_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY role_functionality
    ADD CONSTRAINT role_functionality_functionality_id_fkey FOREIGN KEY (functionality_id) REFERENCES functionality(id) ON DELETE CASCADE;


--
-- TOC entry 3555 (class 2606 OID 91433)
-- Name: role_functionality_role_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY role_functionality
    ADD CONSTRAINT role_functionality_role_id_fkey FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE;


--
-- TOC entry 3556 (class 2606 OID 91438)
-- Name: role_restrictionarea_restrictionarea_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY role_restrictionarea
    ADD CONSTRAINT role_restrictionarea_restrictionarea_id_fkey FOREIGN KEY (restrictionarea_id) REFERENCES restrictionarea(id);


--
-- TOC entry 3557 (class 2606 OID 91443)
-- Name: role_restrictionarea_role_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY role_restrictionarea
    ADD CONSTRAINT role_restrictionarea_role_id_fkey FOREIGN KEY (role_id) REFERENCES role(id);


--
-- TOC entry 3559 (class 2606 OID 91448)
-- Name: theme_functionality_functionality_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY theme_functionality
    ADD CONSTRAINT theme_functionality_functionality_id_fkey FOREIGN KEY (functionality_id) REFERENCES functionality(id) ON DELETE CASCADE;


--
-- TOC entry 3560 (class 2606 OID 91453)
-- Name: theme_functionality_theme_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY theme_functionality
    ADD CONSTRAINT theme_functionality_theme_id_fkey FOREIGN KEY (theme_id) REFERENCES theme(id) ON DELETE CASCADE;


--
-- TOC entry 3558 (class 2606 OID 91458)
-- Name: theme_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY theme
    ADD CONSTRAINT theme_id_fkey FOREIGN KEY (id) REFERENCES treegroup(id) ON DELETE CASCADE;


--
-- TOC entry 3561 (class 2606 OID 91463)
-- Name: treegroup_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY treegroup
    ADD CONSTRAINT treegroup_id_fkey FOREIGN KEY (id) REFERENCES treeitem(id) ON DELETE CASCADE;


--
-- TOC entry 3551 (class 2606 OID 91478)
-- Name: ui_metadata_item_id_fkey; Type: FK CONSTRAINT; Schema: main; Owner: www-data
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT ui_metadata_item_id_fkey FOREIGN KEY (item_id) REFERENCES treeitem(id) ON DELETE CASCADE;


SET search_path = main_static, pg_catalog;

--
-- TOC entry 3733 (class 0 OID 0)
-- Dependencies: 234
-- Name: alembic_version; Type: ACL; Schema: main_static; Owner: www-data
--

REVOKE ALL ON TABLE alembic_version FROM PUBLIC;
REVOKE ALL ON TABLE alembic_version FROM "www-data";
GRANT ALL ON TABLE alembic_version TO "www-data";


--
-- TOC entry 3734 (class 0 OID 0)
-- Dependencies: 237
-- Name: user; Type: ACL; Schema: main_static; Owner: www-data
--

REVOKE ALL ON TABLE "user" FROM PUBLIC;
REVOKE ALL ON TABLE "user" FROM "www-data";
GRANT ALL ON TABLE "user" TO "www-data";


-- Completed on 2017-12-06 14:59:27 CET

--
-- PostgreSQL database dump complete
--


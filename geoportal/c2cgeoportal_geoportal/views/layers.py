# Copyright (c) 2012-2024, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

import json
import logging
import os
from collections.abc import Generator
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypedDict, cast

import geoalchemy2.elements
import geojson.geometry
import pyramid.request
import pyramid.response
import shapely.geometry
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sqlalchemy.orm.query
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, to_shape
from geojson.feature import Feature, FeatureCollection
from papyrus.protocol import Protocol, create_filter
from papyrus.xsd import XSDGenerator
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPException,
    HTTPForbidden,
    HTTPInternalServerError,
    HTTPNotFound,
)
from pyramid.view import view_config
from shapely import unary_union
from shapely.errors import TopologicalError
from sqlalchemy import Enum, Numeric, String, Text, Unicode, UnicodeText, exc, func
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound  # type: ignore[attr-defined]
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.util import class_mapper
from sqlalchemy.sql import and_, or_

from c2cgeoportal_commons import models
from c2cgeoportal_geoportal.lib import get_roles_id
from c2cgeoportal_geoportal.lib.caching import get_region
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers
from c2cgeoportal_geoportal.lib.dbreflection import _AssociationProxy, get_class, get_table

if TYPE_CHECKING:
    from c2cgeoportal_commons.models import main  # pylint: disable=ungrouped-imports.useless-suppression


_LOG = logging.getLogger(__name__)
_CACHE_REGION = get_region("std")


class _BaseCallback:
    def __init__(self, layer: "main.Layer"):
        self.layer = layer

    def update(self, request: pyramid.request.Request, obj: Any) -> None:
        last_update_date = Layers.get_metadata(self.layer, "lastUpdateDateColumn")
        if last_update_date is not None:
            setattr(obj, last_update_date, datetime.now())

        last_update_user = Layers.get_metadata(self.layer, "lastUpdateUserColumn")
        if last_update_user is not None:
            setattr(obj, last_update_user, request.user.id)

    def _get_geometry_check_base_query(
        self, request: pyramid.request.Request
    ) -> sqlalchemy.orm.query.RowReturningQuery[tuple[int]]:
        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            Layer,
            RestrictionArea,
            Role,
        )

        assert models.DBSession is not None
        allowed = models.DBSession.query(func.count(RestrictionArea.id))  # pylint: disable=not-callable
        allowed = allowed.join(RestrictionArea.roles)
        allowed = allowed.join(RestrictionArea.layers)
        allowed = allowed.filter(RestrictionArea.readwrite.is_(True))
        allowed = allowed.filter(Role.id.in_(get_roles_id(request)))
        allowed = allowed.filter(Layer.id == self.layer.id)
        return allowed


class _InsertCallback(_BaseCallback):
    def __call__(self, request: pyramid.request.Request, feature: Feature, obj: Any) -> None:
        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            RestrictionArea,
        )

        assert models.DBSession is not None

        geom = feature.geometry
        if geom and not isinstance(geom, geojson.geometry.Default):
            shape = shapely.geometry.shape(geom)
            srid = Layers._get_geom_col_info(self.layer)[1]
            spatial_elt = from_shape(shape, srid=srid)
            allowed = self._get_geometry_check_base_query(request)
            allowed = allowed.filter(
                or_(RestrictionArea.area.is_(None), RestrictionArea.area.ST_Contains(spatial_elt))
            )
            if allowed.scalar() == 0:
                raise HTTPForbidden()

            # Check if geometry is valid
            if Layers._get_validation_setting(self.layer, request):
                Layers._validate_geometry(spatial_elt)

        self.update(request, obj)


class _UpdateCallback(_BaseCallback):
    def __call__(self, request: pyramid.request.Request, feature: Feature, obj: Any) -> None:
        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            RestrictionArea,
        )

        assert models.DBSession is not None

        # we need both the "original" and "new" geometry to be
        # within the restriction area
        geom_attr, srid = Layers._get_geom_col_info(self.layer)
        geom_attr = getattr(obj, geom_attr)
        geom = feature.geometry
        allowed = self._get_geometry_check_base_query(request)
        allowed = allowed.filter(
            or_(RestrictionArea.area.is_(None), RestrictionArea.area.ST_Contains(geom_attr))
        )
        spatial_elt = None
        if geom and not isinstance(geom, geojson.geometry.Default):
            shape = shapely.geometry.shape(geom)
            spatial_elt = from_shape(shape, srid=srid)
            allowed = allowed.filter(
                or_(RestrictionArea.area.is_(None), RestrictionArea.area.ST_Contains(spatial_elt))
            )
        if allowed.scalar() == 0:
            raise HTTPForbidden()

        # Check is geometry is valid
        if Layers._get_validation_setting(self.layer, request):
            Layers._validate_geometry(spatial_elt)

        self.update(request, obj)


class _DeleteCallback(_BaseCallback):
    def __call__(self, request: pyramid.request.Request, obj: Any) -> None:
        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            RestrictionArea,
        )

        geom_attr = getattr(obj, Layers._get_geom_col_info(self.layer)[0])
        allowed = self._get_geometry_check_base_query(request)
        allowed = allowed.filter(
            or_(RestrictionArea.area.is_(None), RestrictionArea.area.ST_Contains(geom_attr))
        )
        if allowed.scalar() == 0:
            raise HTTPForbidden()


class Layers:
    """
    All the layers view (editing).

    Mapfish protocol implementation
    """

    def __init__(self, request: pyramid.request.Request):
        self.request = request
        self.settings = self._get_settings(request)
        self.layers_enum_config = self.settings.get("enum", {})

    @staticmethod
    def _get_settings(request: pyramid.request.Request) -> dict[str, Any]:
        return cast(dict[str, Any], request.registry.settings.get("layers", {}))

    @staticmethod
    def _get_geom_col_info(layer: "main.Layer") -> tuple[str, int]:
        """
        Return information about the layer's geometry column.

        Namely a ``(name, srid)`` tuple, where ``name`` is the name of the geometry column,
        and ``srid`` its srid.

        This function assumes that the names of geometry attributes in the mapped class are the same as those
        of geometry columns.
        """
        mapped_class = get_layer_class(layer)
        for p in class_mapper(mapped_class).iterate_properties:
            if not isinstance(p, ColumnProperty):
                continue
            col = p.columns[0]
            if isinstance(col.type, Geometry):
                return col.name, col.type.srid
        raise HTTPInternalServerError(f'Failed getting geometry column info for table "{layer.geo_table!s}".')

    @staticmethod
    def _get_layer(layer_id: int) -> "main.Layer":
        """Return a ``Layer`` object for ``layer_id``."""
        from c2cgeoportal_commons.models.main import Layer  # pylint: disable=import-outside-toplevel

        assert models.DBSession is not None

        layer_id = int(layer_id)
        try:
            query = models.DBSession.query(Layer, Layer.geo_table)
            query = query.filter(Layer.id == layer_id)
            layer, geo_table = query.one()
        except NoResultFound:
            raise HTTPNotFound(f"Layer {layer_id:d} not found") from None
        except MultipleResultsFound:
            raise HTTPInternalServerError(f"Too many layers found with id {layer_id:d}") from None
        if not geo_table:
            raise HTTPNotFound(f"Layer {layer_id:d} has no geo table")
        return cast("main.Layer", layer)

    def _get_layers_for_request(self) -> Generator["main.Layer", None, None]:
        """
        Get a generator function that yields ``Layer`` objects.

        Based on the layer ids found in the ``layer_id`` matchdict.
        """
        try:
            layer_ids = (
                int(layer_id) for layer_id in self.request.matchdict["layer_id"].split(",") if layer_id
            )
            for layer_id in layer_ids:
                yield self._get_layer(layer_id)
        except ValueError:
            raise HTTPBadRequest(  # pylint: disable=raise-missing-from
                f"A Layer id in '{self.request.matchdict['layer_id']}' is not an integer"
            )

    def _get_layer_for_request(self) -> "main.Layer":
        """Return a ``Layer`` object for the first layer id found in the ``layer_id`` matchdict."""
        return next(self._get_layers_for_request())

    def _get_protocol_for_layer(self, layer: "main.Layer") -> Protocol:
        """Return a papyrus ``Protocol`` for the ``Layer`` object."""
        cls = get_layer_class(layer)
        geom_attr = self._get_geom_col_info(layer)[0]

        return Protocol(
            models.DBSession,
            cls,
            geom_attr,
            before_insert=_InsertCallback(layer),
            before_update=_UpdateCallback(layer),
            before_delete=_DeleteCallback(layer),
        )

    def _get_protocol_for_request(self) -> Protocol:
        """Return a papyrus ``Protocol`` for the first layer id found in the ``layer_id`` matchdict."""
        layer = self._get_layer_for_request()
        return self._get_protocol_for_layer(layer)

    def _proto_read(self, layer: "main.Layer") -> FeatureCollection:
        """Read features for the layer based on the self.request."""

        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            Layer,
            RestrictionArea,
            Role,
        )

        assert models.DBSession is not None

        proto = self._get_protocol_for_layer(layer)
        if layer.public:
            return proto.read(self.request)
        user = self.request.user
        if user is None:
            raise HTTPForbidden()
        cls = proto.mapped_class
        geom_attr = proto.geom_attr
        ras = models.DBSession.query(RestrictionArea.area, RestrictionArea.area.ST_SRID())
        ras = ras.join(RestrictionArea.roles)
        ras = ras.join(RestrictionArea.layers)
        ras = ras.filter(Role.id.in_(get_roles_id(self.request)))
        ras = ras.filter(Layer.id == layer.id)
        collect_ra = []
        use_srid = -1
        for ra, srid in ras.all():
            if ra is None:
                return proto.read(self.request)
            use_srid = srid
            collect_ra.append(to_shape(ra))
        if not collect_ra:
            raise HTTPForbidden()

        filter1_ = create_filter(self.request, cls, geom_attr)
        ra = unary_union(collect_ra)
        filter2_ = func.ST_Contains(from_shape(ra, use_srid), getattr(cls, geom_attr))
        filter_ = filter2_ if filter1_ is None else and_(filter1_, filter2_)

        feature = proto.read(self.request, filter=filter_)
        if isinstance(feature, HTTPException):
            raise feature
        return feature

    @view_config(route_name="layers_read_many", renderer="geojson")  # type: ignore
    def read_many(self) -> FeatureCollection:
        set_common_headers(self.request, "layers", Cache.PRIVATE_NO)

        features = []
        for layer in self._get_layers_for_request():
            for f in self._proto_read(layer).features:
                f.properties["__layer_id__"] = layer.id
                features.append(f)

        return FeatureCollection(features)

    @view_config(route_name="layers_read_one", renderer="geojson")  # type: ignore
    def read_one(self) -> Feature:
        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            Layer,
            RestrictionArea,
            Role,
        )

        assert models.DBSession is not None

        set_common_headers(self.request, "layers", Cache.PRIVATE_NO)

        layer = self._get_layer_for_request()
        protocol = self._get_protocol_for_layer(layer)
        feature_id = self.request.matchdict.get("feature_id")
        feature = protocol.read(self.request, id=feature_id)
        if not isinstance(feature, Feature):
            return feature
        if layer.public:
            return feature
        if self.request.user is None:
            raise HTTPForbidden()
        geom = feature.geometry
        if not geom or isinstance(geom, geojson.geometry.Default):
            return feature
        shape = shapely.geometry.shape(geom)
        srid = self._get_geom_col_info(layer)[1]
        spatial_elt = from_shape(shape, srid=srid)
        allowed = models.DBSession.query(func.count(RestrictionArea.id))  # pylint: disable=not-callable
        allowed = allowed.join(RestrictionArea.roles)
        allowed = allowed.join(RestrictionArea.layers)
        allowed = allowed.filter(Role.id.in_(get_roles_id(self.request)))
        allowed = allowed.filter(Layer.id == layer.id)
        allowed = allowed.filter(
            or_(RestrictionArea.area.is_(None), RestrictionArea.area.ST_Contains(spatial_elt))
        )
        if allowed.scalar() == 0:
            raise HTTPForbidden()

        return feature

    @view_config(route_name="layers_count", renderer="string")  # type: ignore
    def count(self) -> int:
        set_common_headers(self.request, "layers", Cache.PRIVATE_NO)

        protocol = self._get_protocol_for_request()
        count = protocol.count(self.request)
        if isinstance(count, HTTPException):
            raise count
        return cast(int, count)

    @view_config(route_name="layers_create", renderer="geojson")  # type: ignore
    def create(self) -> FeatureCollection | None:
        set_common_headers(self.request, "layers", Cache.PRIVATE_NO)

        if self.request.user is None:
            raise HTTPForbidden()

        self.request.response.cache_control.no_cache = True

        protocol = self._get_protocol_for_request()
        try:
            features = protocol.create(self.request)
            if isinstance(features, HTTPException):
                raise features
            return features
        except TopologicalError as e:
            self.request.response.status_int = 400
            return {"error_type": "validation_error", "message": str(e)}
        except exc.IntegrityError as e:
            _LOG.error(str(e))
            assert e.orig is not None
            self.request.response.status_int = 400
            return {"error_type": "integrity_error", "message": str(e.orig.diag.message_primary)}  # type: ignore[attr-defined]

    @view_config(route_name="layers_update", renderer="geojson")  # type: ignore
    def update(self) -> Feature:
        set_common_headers(self.request, "layers", Cache.PRIVATE_NO)

        if self.request.user is None:
            raise HTTPForbidden()

        self.request.response.cache_control.no_cache = True

        feature_id = self.request.matchdict.get("feature_id")
        protocol = self._get_protocol_for_request()
        try:
            feature = protocol.update(self.request, feature_id)
            if isinstance(feature, HTTPException):
                raise feature
            return cast(Feature, feature)
        except TopologicalError as e:
            self.request.response.status_int = 400
            return {"error_type": "validation_error", "message": str(e)}
        except exc.IntegrityError as e:
            _LOG.error(str(e))
            assert e.orig is not None
            self.request.response.status_int = 400
            return {"error_type": "integrity_error", "message": str(e.orig.diag.message_primary)}  # type: ignore[attr-defined]

    @staticmethod
    def _validate_geometry(geom: geoalchemy2.elements.WKBElement | None) -> None:
        assert models.DBSession is not None

        if geom is not None:
            simple = models.DBSession.query(func.ST_IsSimple(func.ST_GeomFromEWKB(geom))).scalar()
            if not simple:
                raise TopologicalError("Not simple")
            valid = models.DBSession.query(func.ST_IsValid(func.ST_GeomFromEWKB(geom))).scalar()
            if not valid:
                reason = models.DBSession.query(func.ST_IsValidReason(func.ST_GeomFromEWKB(geom))).scalar()
                raise TopologicalError(reason)

    @staticmethod
    def get_metadata(layer: "main.Layer", key: str, default: str | None = None) -> str | None:
        metadata = layer.get_metadata(key)
        if len(metadata) == 1:
            metadata = metadata[0]
            return metadata.value
        return default

    @classmethod
    def _get_validation_setting(cls, layer: "main.Layer", request: pyramid.request.Request) -> bool:
        # The validation UIMetadata is stored as a string, not a boolean
        should_validate = cls.get_metadata(layer, "geometryValidation", None)
        if should_validate:
            return should_validate.lower() != "false"
        return cast(bool, cls._get_settings(request).get("geometry_validation", False))

    @view_config(route_name="layers_delete")  # type: ignore
    def delete(self) -> pyramid.response.Response:
        if self.request.user is None:
            raise HTTPForbidden()

        feature_id = self.request.matchdict.get("feature_id")
        protocol = self._get_protocol_for_request()
        response = protocol.delete(self.request, feature_id)
        if isinstance(response, HTTPException):
            raise response
        set_common_headers(self.request, "layers", Cache.PRIVATE_NO, response=response)
        return response

    @view_config(route_name="layers_metadata", renderer="xsd")  # type: ignore
    def metadata(self) -> pyramid.response.Response:
        set_common_headers(self.request, "layers", Cache.PRIVATE)

        layer = self._get_layer_for_request()
        if not layer.public and self.request.user is None:
            raise HTTPForbidden()

        return get_layer_class(layer, with_last_update_columns=True)

    @view_config(route_name="layers_enumerate_attribute_values", renderer="json")  # type: ignore
    def enumerate_attribute_values(self) -> dict[str, Any]:
        set_common_headers(self.request, "layers", Cache.PUBLIC)

        if self.layers_enum_config is None:
            raise HTTPInternalServerError("Missing configuration")
        layername = self.request.matchdict["layer_name"]
        fieldname = self.request.matchdict["field_name"]
        # TODO check if layer is public or not

        return cast(dict[str, Any], self._enumerate_attribute_values(layername, fieldname))

    @_CACHE_REGION.cache_on_arguments()
    def _enumerate_attribute_values(self, layername: str, fieldname: str) -> dict[str, Any]:
        if layername not in self.layers_enum_config:
            raise HTTPBadRequest(f"Unknown layer: {layername!s}")

        layerinfos = self.layers_enum_config[layername]
        if fieldname not in layerinfos["attributes"]:
            raise HTTPBadRequest(f"Unknown attribute: {fieldname!s}")
        dbsession_name = layerinfos.get("dbsession", "dbsession")
        dbsession = models.DBSessions.get(dbsession_name)
        if dbsession is None:
            raise HTTPInternalServerError(
                f"No dbsession found for layer '{layername!s}' ({dbsession_name!s})"
            )
        values = sorted(self.query_enumerate_attribute_values(dbsession, layerinfos, fieldname))
        enum = {"items": [{"value": value[0]} for value in values]}
        return enum

    @staticmethod
    def query_enumerate_attribute_values(
        dbsession: sqlalchemy.orm.scoped_session[sqlalchemy.orm.Session],
        layerinfos: dict[str, Any],
        fieldname: str,
    ) -> set[tuple[str, ...]]:
        attrinfos = layerinfos["attributes"][fieldname]
        table = attrinfos["table"]
        layertable = get_table(table, session=dbsession())
        column = attrinfos.get("column_name", fieldname)
        attribute = getattr(layertable.columns, column)
        # For instance if `separator` is a "," we consider that the column contains a
        # comma separate list of values e.g.: "value1,value2".
        if "separator" in attrinfos:
            separator = attrinfos["separator"]
            attribute = func.unnest(func.string_to_array(func.string_agg(attribute, separator), separator))
        return set(cast(list[tuple[str, ...]], dbsession.query(attribute).order_by(attribute).all()))


def get_layer_class(layer: "main.Layer", with_last_update_columns: bool = False) -> type:
    """
    Get the SQLAlchemy class to edit a GeoMapFish layer.

    Keyword Arguments:

        layer: The GeoMapFish layer
        with_last_update_columns: False to just have a class to access to the table and be able to
           modify the last_update_columns, True to have a correct class to build the UI
           (without the hidden column).

    Returns: SQLAlchemy class
    """

    assert layer.geo_table is not None

    # Exclude the columns used to record the last features update
    exclude = [] if layer.exclude_properties is None else layer.exclude_properties.split(",")
    if with_last_update_columns:
        last_update_date = Layers.get_metadata(layer, "lastUpdateDateColumn")
        if last_update_date is not None:
            exclude.append(last_update_date)
        last_update_user = Layers.get_metadata(layer, "lastUpdateUserColumn")
        if last_update_user is not None:
            exclude.append(last_update_user)

    m = Layers.get_metadata(layer, "editingAttributesOrder")
    attributes_order = m.split(",") if m else None
    m = Layers.get_metadata(layer, "readonlyAttributes")
    readonly_attributes = m.split(",") if m else None
    m = Layers.get_metadata(layer, "editingEnumerations")
    enumerations_config = json.loads(m) if m else None

    primary_key = Layers.get_metadata(layer, "geotablePrimaryKey")
    cls = get_class(
        str(layer.geo_table.format(**os.environ)),
        exclude_properties=exclude,
        primary_key=primary_key,
        attributes_order=attributes_order,
        enumerations_config=enumerations_config,
        readonly_attributes=readonly_attributes,
    )

    mapper = class_mapper(cls)
    column_properties = [p.key for p in mapper.iterate_properties if isinstance(p, ColumnProperty)]

    for attribute_name in attributes_order or []:
        if attribute_name not in column_properties:
            table = mapper.mapped_table
            _LOG.warning(
                'Attribute "%s" does not exists in table "%s.%s".\n'
                'Please correct metadata "editingAttributesOrder" in layer "%s" (id=%s).\n'
                "Available attributes are: %s.",
                attribute_name,
                table.schema,
                table.name,
                layer.name,
                layer.id,
                ", ".join(column_properties),
            )

    return cast(type, cls)


class ColumnProperties(TypedDict, total=False):
    """Collected metadata information related to an editing attribute."""

    name: str
    type: str
    nillable: bool
    srid: int
    enumeration: list[str]
    restriction: str
    maxLength: int  # noqa
    fractionDigits: int  # noqa
    totalDigits: int  # noqa


def get_layer_metadata(layer: "main.Layer") -> list[ColumnProperties]:
    """Get the metadata related to a layer."""

    assert models.DBSession is not None

    cls = get_layer_class(layer, with_last_update_columns=True)
    edit_columns: list[ColumnProperties] = []

    for column_property in class_mapper(cls).iterate_properties:
        if isinstance(column_property, ColumnProperty):
            if len(column_property.columns) != 1:
                raise NotImplementedError

            column = column_property.columns[0]

            # Exclude columns that are primary keys
            if not column.primary_key:
                properties: ColumnProperties = _convert_column_type(column.type)
                properties["name"] = column.key

                if column.nullable:
                    properties["nillable"] = True
                edit_columns.append(properties)
        else:
            for k, p in cls.__dict__.items():
                if not isinstance(p, _AssociationProxy):
                    continue

                relationship_property = class_mapper(cls).get_property(p.target)
                target_cls = relationship_property.argument
                query = models.DBSession.query(getattr(target_cls, p.value_attr))
                properties = {}
                if column.nullable:
                    properties["nillable"] = True

                properties["name"] = k
                properties["restriction"] = "enumeration"
                properties["type"] = "xsd:string"
                properties["enumeration"] = []
                for value in query:  # pylint: disable=not-an-iterable
                    properties["enumeration"].append(value[0])

                edit_columns.append(properties)
    return edit_columns


def _convert_column_type(column_type: object) -> ColumnProperties:
    # SIMPLE_XSD_TYPES
    for cls, xsd_type in XSDGenerator.SIMPLE_XSD_TYPES.items():
        if isinstance(column_type, cls):
            return {"type": xsd_type}

    # Geometry type
    if isinstance(column_type, Geometry):
        geometry_type = column_type.geometry_type
        if geometry_type in XSDGenerator.SIMPLE_GEOMETRY_XSD_TYPES:
            xsd_type = XSDGenerator.SIMPLE_GEOMETRY_XSD_TYPES[geometry_type]
            return {"type": xsd_type, "srid": int(column_type.srid)}
        if geometry_type == "GEOMETRY":
            xsd_type = "gml:GeometryPropertyType"
            return {"type": xsd_type, "srid": int(column_type.srid)}

        raise NotImplementedError(
            f"The geometry type '{geometry_type}' is not supported, supported types: "
            f"{','.join(XSDGenerator.SIMPLE_GEOMETRY_XSD_TYPES)}"
        )

    # Enumeration type
    if isinstance(column_type, Enum):
        restriction: ColumnProperties = {}
        restriction["restriction"] = "enumeration"
        restriction["type"] = "xsd:string"
        restriction["enumeration"] = column_type.enums
        return restriction

    # String type
    if isinstance(column_type, (String, Text, Unicode, UnicodeText)):
        if column_type.length is None:
            return {"type": "xsd:string"}
        return {"type": "xsd:string", "maxLength": int(column_type.length)}

    # Numeric Type
    if isinstance(column_type, Numeric):
        xsd_type2: ColumnProperties = {"type": "xsd:decimal"}
        if column_type.scale is None and column_type.precision is None:
            return xsd_type2

        if column_type.scale is not None:
            xsd_type2["fractionDigits"] = int(column_type.scale)
        if column_type.precision is not None:
            xsd_type2["totalDigits"] = int(column_type.precision)
        return xsd_type2

    raise NotImplementedError(
        f"The type '{type(column_type).__name__}' is not supported, supported types: "
        "Geometry, Enum, String, Text, Unicode, UnicodeText, Numeric"
    )

.. _integrator_wmstime:

WMSTime Layer
=============

c2cgeoportal supports `WMS Time layers <http://mapserver.org/ogc/wms_time.html>`_.

When the time is enabled for a layer group, a time widget (a slider or datepicker)
is added to this group in the layer tree which enables changing the layer time.

Configuration
-------------

Most of the configuration is automatically extracted from the mapfile. But there
is also some configuration to do in the administration interface.

Mapfile
~~~~~~~

In the mapfile, a WMS Time layer is configured with the help of the layer
metadata:

* ``wms_timeextent``
* ``wms_timeitem``
* ``wms_timedefault``

c2cgeoportal uses the ``wms_timeextent`` to configure the slider. Two different
formats are supported to define the time:

* ``min/max/interval``
* ``value1,value2,value3,...``

The format ``min/max/interval`` allows specifying a time range by giving a start
date, an end date and an interval between the time stops.

The format ``value1,value2,value3,...`` allows specifying a time range by
listing discrete values.

The dates (``min``, ``max`` and ``valueN``) could be specified using any of the
following formats:

* ``YYYY``
* ``YYYY-MM``
* ``YYYY-MM-DD``
* ``YYYY-MM-DDTHH:MM:SSTZ`` (TZ is an optional timezone, i.e. "Z" or "+0100")

The format used for the dates in the mapfile determines both the resolution used
for the slider and the format of the time parameter used for the GetMap
requests. For example when a layer has monthly data, the ``YYYY-MM`` should be
used in the mapfile to make sure that only months and years are displayed in the
slider tip and passed to the GetMap request.

The interval (``interval``) has to be defined regarding international standard
ISO 8601 and its duration/time intervals definition (see
`ISO 8601 Durations / Time intervals <http://en.wikipedia.org/wiki/ISO_8601#Durations>`_).

Some examples for the interval definition:

* An interval of one year: ``P1Y``
* An interval of six months: ``P6M``

For more information please refer to the `MapServer documentation
<http://mapserver.org/ogc/wms_time.html>`_.

Admin interface
~~~~~~~~~~~~~~~

Most of the configuration is done in the mapfile as described in the above
section. However the time widget must be configured via the admin interface.
Two different widget types are available: A time slider and a datepicker
widget. The preferred widget can be selected in the admin interface (field
``Time widget``).

Besides, the time mode can be changed. The time mode is one of:

* ``value``
* ``range``
* ``disabled``

The ``value`` mode displays a widget to select a single time or date. For a
slider widget, a slider with a single thumb will be displayed. If datepicker is
selected as widget, a single datepicker will be shown to select a single date.
The WMS Time layer will display data that is relative to the selected time or date.

The ``range`` mode displays a widget to select a time range. For a slider widget,
a slider with two thumbs is shown. For the datepicker widget, two datepicker
fields are displayed to select the start and end date.
In mode ``range`` the layer will display data that is relative to the defined range.

The ``disabled`` mode hides the time widget. No time parameter will be sent
to the GetMap request in this case.

Merging configurations
----------------------

The previous section describes the time configuration for a single layer.
However there could be multiple WMS Time layers in a group. In such a case, you
need to be aware of some limitations that apply to the configuration of the WMS
Time layers of the same group.

Some of those limitations apply to the mapfile:

* The WMS Time layers of a same group must all be configured with either a
  list of discrete values or an interval. It is not possible to mix the two
  different types of definition within the same group,
* If the WMS Time layers of a group use the ``min/max/interval``, they must
  all use the same interval.

There is also a limitation that applies to the admin interface: all the WMS Time
layers of a group should be configured to use the same widget and the same time mode
(``single`` or ``range``) except for layers with time mode ``disabled`` that can be mixed
within others.

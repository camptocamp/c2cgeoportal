# Copyright (c) 2018-2023, Camptocamp SA
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

import gc
import sys
from collections.abc import Generator

import prometheus_client.core
import prometheus_client.registry
from c2cwsgiutils import broadcast
from c2cwsgiutils.debug import get_size

from c2cgeoportal_geoportal.lib.caching import MEMORY_CACHE_DICT
from c2cgeoportal_geoportal.views.raster import Raster


class MemoryCacheSizeCollector(prometheus_client.registry.Collector):
    """Get the memory used by the cache."""

    def __init__(self, all_: bool = False):
        super().__init__()
        self.all = all_

    def collect(self) -> Generator[prometheus_client.core.GaugeMetricFamily, None, None]:
        gauge = prometheus_client.core.GaugeMetricFamily(
            "c2cgeoportal_memory_cache_bytes",
            "Memory used by cache",
            labels=["pid", "hostname", "key"],
            unit="bytes",
        )

        elements = _get_memory_cache(all_=self.all)
        assert elements is not None
        for elem in elements:
            if elem is not None:
                for key, value in elem["values"]:
                    gauge.add_metric([str(elem["pid"]), str(elem["hostname"]), key], value)
        yield gauge


@broadcast.decorator(expect_answers=True, timeout=15)
def _get_memory_cache(all_: bool) -> dict[str, list[tuple[str, int]]]:
    values = [(key, get_size(value)) for key, value in list(MEMORY_CACHE_DICT.items())] if all_ else []
    values.append(("total", get_size(MEMORY_CACHE_DICT)))
    return {"values": values}


class RasterDataSizeCollector(prometheus_client.registry.Collector):
    """Get the memory used by Raster data cache."""

    def collect(self) -> Generator[prometheus_client.core.GaugeMetricFamily, None, None]:
        gauge = prometheus_client.core.GaugeMetricFamily(
            "c2cgeoportal_raster_data_bytes",
            "Memory used by raster",
            labels=["pid", "hostname", "key"],
            unit="bytes",
        )

        elements = _get_raster_data()
        assert elements is not None
        for elem in elements:
            for key, value in elem["values"]:
                gauge.add_metric([str(elem["pid"]), str(elem["hostname"]), key], value)
        yield gauge


@broadcast.decorator(expect_answers=True, timeout=15)
def _get_raster_data() -> dict[str, list[tuple[str, float]]]:
    return {"values": [(key, get_size(value)) for key, value in list(Raster.data.items())]}


class TotalPythonObjectMemoryCollector(prometheus_client.registry.Collector):
    """Get the memory used by Python objects."""

    def collect(self) -> Generator[prometheus_client.core.GaugeMetricFamily, None, None]:
        gauge = prometheus_client.core.GaugeMetricFamily(
            "c2cgeoportal_total_python_object_memory_bytes",
            "Memory used by Python objects",
            labels=["pid", "hostname"],
            unit="bytes",
        )

        object_size = _get_python_object_size()
        assert object_size is not None
        for val in object_size:
            if val is not None:
                gauge.add_metric([str(val["pid"]), str(val["hostname"])], val["value"])
        yield gauge


@broadcast.decorator(expect_answers=True, timeout=15)
def _get_python_object_size() -> dict[str, float]:
    return {"value": sum(sys.getsizeof(o) for o in gc.get_objects())}

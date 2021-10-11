# Copyright (c) 2018-2021, Camptocamp SA
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
from typing import Any, Dict, List, Tuple

from c2cwsgiutils import broadcast
from c2cwsgiutils.debug import get_size
from c2cwsgiutils.metrics import Provider

from c2cgeoportal_geoportal.lib.caching import MEMORY_CACHE_DICT
from c2cgeoportal_geoportal.views.raster import Raster


class MemoryCacheSizeProvider(Provider):
    """Get the memory used by the cache."""

    def __init__(self, all_: bool = False):
        super().__init__("pod_process_memory_cache_kb", "Used memory cache")
        self.all = all_

    def get_data(self) -> List[Tuple[Dict[str, Any], float]]:
        elements = _get_memory_cache(all_=self.all)
        assert elements is not None
        result = []
        for elem in elements:
            if elem is not None:
                for value in elem["values"]:
                    value[0]["pid"] = str(elem["pid"])
                    value[0]["hostname"] = elem["hostname"]
                    result.append(value)
        return result


@broadcast.decorator(expect_answers=True, timeout=15)
def _get_memory_cache(all_: bool) -> Dict[str, List[Tuple[Dict[str, Any], float]]]:
    values = (
        [({"key": key}, get_size(value) / 1024) for key, value in list(MEMORY_CACHE_DICT.items())]
        if all_
        else []
    )
    values.append(({"key": "total"}, get_size(MEMORY_CACHE_DICT) / 1024))
    return {"values": values}


class RasterDataSizeProvider(Provider):
    """Get the memory used by Raster data cache."""

    def __init__(self) -> None:
        super().__init__("pod_process_raster_data_kb", "Memory used by raster")

    def get_data(self) -> List[Tuple[Dict[str, Any], float]]:
        elements = _get_raster_data()
        assert elements is not None
        result = []
        for elem in elements:
            for value in elem["values"]:
                value[0]["pid"] = str(elem["pid"])
                value[0]["hostname"] = str(elem["hostname"])
                result.append(value)
        return result


@broadcast.decorator(expect_answers=True, timeout=15)
def _get_raster_data() -> Dict[str, List[Tuple[Dict[str, str], float]]]:
    return {"values": [({"key": key}, get_size(value) / 1024) for key, value in list(Raster.data.items())]}


class TotalPythonObjectMemoryProvider(Provider):
    """Get the memory used by Python objects."""

    def __init__(self) -> None:
        super().__init__("total_python_object_memory_kb", "Memory used by raster")

    def get_data(self) -> List[Tuple[Dict[str, str], float]]:
        object_size = _get_python_object_size()
        assert object_size is not None
        return [
            ({"pid": str(val["pid"]), "hostname": str(val["hostname"])}, val["value"])
            for val in object_size
            if val is not None
        ]


@broadcast.decorator(expect_answers=True, timeout=15)
def _get_python_object_size() -> Dict[str, float]:
    return {"value": sum(sys.getsizeof(o) / 1024 for o in gc.get_objects())}

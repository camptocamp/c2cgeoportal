# Copyright (c) 2011-2024, Camptocamp SA
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


import os
from typing import Any

import yaml
from lingva.extractors import Extractor, Message


class GeomapfishConfigExtractor(Extractor):  # type: ignore
    """GeoMapFish config extractor (raster layers, and print templates)."""

    extensions = [".yaml"]

    def __call__(
        self,
        filename: str,
        options: dict[str, Any],
        fileobj: dict[str, Any] | None = None,
        lineno: int = 0,
    ) -> list[Message]:
        del options, fileobj, lineno

        print(f"Running {self.__class__.__name__} on {filename}")

        with open(filename, encoding="utf8") as config_file:
            data = config_file.read()
            settings = yaml.load(
                data.replace("{{cookiecutter.geomapfish_main_version}}", os.environ["MAJOR_VERSION"]),
                Loader=yaml.SafeLoader,
            )

        admin_interface = settings.get("vars", {}).get("admin_interface", {})

        available_metadata = []
        for elem in admin_interface.get("available_metadata", []):
            if "description" in elem:
                location = f"admin_interface/available_metadata/{elem.get('name', '')}"
                available_metadata.append(
                    Message(None, elem["description"].strip(), None, [], "", "", (filename, location))
                )

        available_functionalities = []
        for elem in admin_interface.get("available_functionalities", []):
            if "description" in elem:
                location = f"admin_interface/available_functionalities/{elem.get('name', '')}"
                available_functionalities.append(
                    Message(None, elem["description"].strip(), None, [], "", "", (filename, location))
                )

        return available_metadata + available_functionalities

# Copyright (c) 2019-2024, Camptocamp SA
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


import logging
from typing import Any, cast

from c2c.template.config import config as configuration
from c2cwsgiutils.loader import Loader as BaseLoader

from c2cgeoportal_geoportal.lib.i18n import available_locale_names

_LOG = logging.getLogger(__name__)


class Loader(BaseLoader):
    """The Pyramid configuration loader."""

    def get_wsgi_app_settings(
        self, name: str | None = None, defaults: dict[str, str] | None = None
    ) -> dict[str, Any]:
        settings = cast(dict[str, Any], super().get_wsgi_app_settings(name, defaults))
        app_cfg = settings.get("app.cfg")
        if app_cfg is not None:
            configuration.init(app_cfg)
        settings.update(configuration.get_config())  # type: ignore[arg-type]
        if "available_locale_names" not in settings:
            settings["available_locale_names"] = available_locale_names()
        return settings

    def __repr__(self) -> str:
        """Get the object representation."""
        return f'c2cgeoportal_geoportal.lib.loader.Loader(uri="{self.uri}")'

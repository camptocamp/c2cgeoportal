# -*- coding: utf-8 -*-

# Copyright (c) 2019-2021, Camptocamp SA
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
from typing import Dict

import c2cwsgiutils.pyramid_logging
from c2c.template.config import config as configuration
from plaster_pastedeploy import Loader as BaseLoader

from c2cgeoportal_geoportal.lib.i18n import available_locale_names

LOG = logging.getLogger(__name__)


class Loader(BaseLoader):
    def _get_defaults(self, defaults: Dict[str, str] = None) -> Dict[str, str]:
        env: Dict[str, str] = c2cwsgiutils.pyramid_logging.get_defaults()
        d: Dict[str, str] = {key: env[key].replace("%", "%%") for key in env}
        if defaults:
            d.update(defaults)
        return super()._get_defaults(d)

    def get_wsgi_app_settings(self, name: str = None, defaults: Dict[str, str] = None) -> Dict:
        settings = super().get_wsgi_app_settings(name, defaults)
        configuration.init(settings.get("app.cfg"))
        settings.update(configuration.get_config())
        if "available_locale_names" not in settings:
            settings["available_locale_names"] = available_locale_names()
        return settings

    def __repr__(self) -> str:
        return 'c2cgeoportal_geoportal.lib.loader.Loader(uri="{0}")'.format(self.uri)

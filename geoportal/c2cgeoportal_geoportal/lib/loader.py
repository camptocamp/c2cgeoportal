import os
from typing import Dict
from plaster_pastedeploy import Loader as BaseLoader

from c2c.template.config import config as configuration


class Loader(BaseLoader):

    def _get_defaults(self, defaults: Dict[str, str] = None) -> Dict[str, str]:
        d = {
            "VISIBLE_ENTRY_POINT": "cli",
            "LOG_LEVEL": "INFO",
            "C2CGEOPORTAL_LOG_LEVEL": "WARN",
            "GUNICORN_LOG_LEVEL": "INFO",
            "GUNICORN_ACCESS_LOG_LEVEL": "INFO",
            "SQL_LOG_LEVEL": "INFO",
            "OTHER_LOG_LEVEL": "INFO",
            "LOG_HOST": "localhost",
            "LOG_PORT": "0",
        }  # type: Dict[str, str]
        d.update(os.environ)
        if defaults:
            d.update(defaults)
        return super()._get_defaults(d)

    def get_wsgi_app_settings(self, name: str = None, defaults: Dict[str, str] = None) -> Dict:
        settings = super().get_wsgi_app_settings(name, defaults)
        configuration.init(settings.get('app.cfg'))
        settings.update(configuration.get_config())
        return settings

    def __repr__(self) -> str:
        return 'c2cgeoportal_geoportal.lib.loader.Loader(uri="{0}")'.format(self.uri)

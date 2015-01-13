from pyramid.paster import get_app
from logging.config import fileConfig

configfile = "${directory}/${'development' if development else 'production'}.ini"
fileConfig(configfile)
application = get_app(configfile, 'main')

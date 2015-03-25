import site

site.addsitedir("${python_path}")

from pyramid.paster import get_app, setup_logging

configfile = "${directory}/${'development' if development == 'TRUE' else 'production'}.ini"
setup_logging(configfile)
application = get_app(configfile, 'main')

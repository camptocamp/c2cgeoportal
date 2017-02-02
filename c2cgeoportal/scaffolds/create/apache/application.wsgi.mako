import site
import sys
import re
import os
from logging.config import fileConfig

reload(sys)
sys.setdefaultencoding('utf-8')

% if docker == 'TRUE':
root = "/app"
% else:
site.addsitedir("${python_path}")
root = "${directory}"
% endif


# Remove site packages
regex = re.compile("^/usr/lib/python.\../dist-packages$")
sys.path = [p for p in sys.path if regex.match(p) is None]

from pyramid.paster import get_app

configfile = os.path.join(root, "${'development' if development == 'TRUE' else 'production'}.ini")

# Load the logging config without using pyramid to be able to use environment variables in there.
vars = dict(__file__=configfile, here=os.path.dirname(configfile))
vars.update(os.environ)
fileConfig(configfile, defaults=vars)

application = get_app(configfile, 'main')

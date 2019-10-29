import re

import colander

# Custom url validator that allow c2cgeoportal static urls.
URL_REGEX = r"(?:{}|^(:?static|config)://\S+$)".format(colander.URL_REGEX)
url = colander.Regex(URL_REGEX, msg=colander._("Must be a URL"), flags=re.IGNORECASE)

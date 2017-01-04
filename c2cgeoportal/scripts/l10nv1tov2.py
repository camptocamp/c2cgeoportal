# -*- coding: utf-8 -*-

# Copyright (c) 2014-2017, Camptocamp SA
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


import sys
import json
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser(
        prog=sys.argv[0], add_help=True,
        description="Tool used to migrate the localisation v1 to v2.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""The source file should be wheel formated as:
OpenLayers.Util.extend(OpenLayers.Lang.<lang>, {
    ...
});

Carful, It will truncate the destination file!

After running this script you can do:
touch <package>/locale/<package>-client.pot
and build your application to merge the old localisation with the new one.
""",
    )

    parser.add_argument(
        "lang",
        help="the language to translate"
    )
    parser.add_argument(
        "json_v1",
        help="the JSON l10n file from the version 1"
    )
    parser.add_argument(
        "po_v2",
        help="the po file for the version 2"
    )
    options = parser.parse_args()

    with open(options.json_v1) as src:
        lines = src.readlines()
        while lines[-1].strip() == "":
            lines = lines[0:-1]

        jsonlines = ["console.log(JSON.stringify({"]
        jsonlines += lines[1:-1]
        jsonlines.append("}))")

        json_ = subprocess.check_output(["node", "-e", " ".join(jsonlines)])
        source = json.loads(json_)

    with open(options.po_v2, "w+") as destination:
        destination.write(u"""msgid ""
msgstr ""
"Last-Translator: Imported from {0!s}\\n"
"Language: {1!s}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"
""".format(options.json_v1, options.lang))
        for key, value in source.items():
            if isinstance(value, basestring):
                destination.write((u"""
msgid "{0!s}"
msgstr "{1!s}"
""".format(key, value.replace('"', '\\"'))).encode("utf-8"),
                )

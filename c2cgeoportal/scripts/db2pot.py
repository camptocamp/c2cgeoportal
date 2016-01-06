# -*- coding: utf-8 -*-

# Copyright (c) 2014-2016, Camptocamp SA
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

# Inspired by https://github.com/Geoportail-Luxembourg/geoportailv3/blob/
# ff62dbb42d798d599ec9f96672cac9de72f13d8b/geoportailv3/utils/db_to_pot.py


import codecs
from os import path
from pyramid.paster import bootstrap


def main():  # pragma: nocover
    env = bootstrap("development.ini")

    from c2cgeoportal.models import DBSession, TreeItem

    package = env["registry"].settings["package"]
    directory = "%s/locale/" % package
    destination = path.join(directory, "%s-db.pot" % package)

    w = codecs.open(destination, "wt", encoding="utf-8")
    w.write(
        u'''#, fuzzy
        msgid ""
        msgstr ""
        "MIME-Version: 1.0\\n"
        "Content-Type: text/plain; charset=utf-8\\n"
        "Content-Transfer-Encoding: 8bit\\n"

        '''
    )

    treeitems = DBSession.query(TreeItem.item_type, TreeItem.id, TreeItem.name)
    for type, id, name in treeitems:
        w.write(
            u'''#: %(type)s.%(id)s
            msgid "%(name)s"
            msgstr ""

            ''' % {
                "type": type,
                "id": id,
                "name": name,
            }
        )
    print("DB Pot file updated: %s" % destination)

# -*- coding: utf-8 -*-

# Copyright (c) 2020-2024, Camptocamp SA
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


import datetime
import re
import subprocess

from pylint.checkers import BaseChecker
from pylint.interfaces import IRawChecker


class CopyrightChecker(BaseChecker):
    """
    Check the first line for copyright notice
    """

    __implements__ = IRawChecker

    name = "copyright"
    msgs = {
        "W9902": (
            "Your file ahould have the copyright notice: 'Copyright (c) %s, Camptocamp SA'",
            "missing-copyright",
            (),
        ),
        "W9903": ("Error in copyright plugin: %s", "error-in-copyright", ()),
    }
    options = ()
    copyright_re = re.compile(
        r"Copyright \(c\) ([0-9][0-9][0-9][0-9])(-[0-9][0-9][0-9][0-9])?, Camptocamp SA".encode()
    )

    def process_module(self, node):
        try:
            commits_date = (
                subprocess.check_output(["git", "log", "--pretty=format:%ci", node.file]).decode().split("\n")
            )
            first_year = int(commits_date[-1][0:4])
            last_year = commits_date[0][0:4]
            copyright_re = re.compile(
                r"Copyright \(c\) ([0-9][0-9][0-9][0-9]-)?{}, Camptocamp SA".format(last_year).encode()
            )
            with node.stream() as stream:
                ok = False
                lines = False
                line_no = 0
                for current_line_no, line in enumerate(stream):
                    lines = True
                    match = copyright_re.search(line)
                    if match:
                        first_file_year = int(last_year if match.group(1) is None else match.group(1)[:-1])
                        if first_file_year <= first_year:
                            ok = True
                        else:
                            line_no = current_line_no
                        break
                    match = self.copyright_re.search(line)
                    if match:
                        file_first_year = int(match.group(1))
                        first_year = min(first_year, file_first_year)
                        break
                if not ok and lines:
                    self.add_message(
                        "missing-copyright",
                        line=line_no,
                        args=(
                            (
                                str(first_year)
                                if first_year == datetime.date.today().year
                                else "{}-{}".format(first_year, datetime.date.today().year)
                            ),
                        ),
                    )
        except Exception as e:
            self.add_message("error-in-copyright", line=0, args=(str(e),))


def register(linter):
    """
    required method to auto register this checker
    """
    linter.register_checker(CopyrightChecker(linter))

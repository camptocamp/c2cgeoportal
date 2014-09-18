# -*- coding: utf-8 -*-

# Copyright (c) 2012-2014, Camptocamp SA
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


from unittest import TestCase
from pyramid import testing


class TestIncludeme(TestCase):

    def setUp(self):  # noqa
        self.config = testing.setUp(
            # the c2cgeoportal includeme function requires a number
            # of settings
            settings={
                'sqlalchemy.url': 'postgresql://u:p@h/d',
                'srid': 3857,
                'schema': 'main',
                'parentschema': '',
                'default_max_age': 86400,
                'app.cfg': 'c2cgeoportal/tests/config.yaml'
            })

    def test_set_user_validator_directive(self):
        import c2cgeoportal
        self.config.include(c2cgeoportal.includeme)
        self.failUnless(
            self.config.set_user_validator.im_func.__docobj__ is
            c2cgeoportal.set_user_validator
        )

    def test_default_user_validator(self):
        import c2cgeoportal
        self.config.include(c2cgeoportal.includeme)
        self.assertEqual(self.config.registry.validate_user,
                         c2cgeoportal.default_user_validator)

    def test_user_validator_overwrite(self):
        import c2cgeoportal
        self.config.include(c2cgeoportal.includeme)

        def custom_validator(username, password):
            return False  # pragma: nocover
        self.config.set_user_validator(custom_validator)
        self.assertEqual(self.config.registry.validate_user,
                         custom_validator)

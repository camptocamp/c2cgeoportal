# -*- coding: utf-8 -*-

# Copyright (c) 2016, Camptocamp SA
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
from c2cgeoportal import stats


class FakeRequest:
    def __init__(self, reset):
        self.params = {"reset": reset}


class TestMemoryBackend(TestCase):
    def setUp(self):
        self.backend = stats._MemoryBackend()
        stats.BACKENDS = [self.backend]

    def tearDown(self):
        stats.BACKENDS = []

    def test_get_no_stats(self):
        self.assertEqual(self.backend.get_stats(FakeRequest(reset=False)), {"timers": {}})

    def test_timer_key_before(self):
        measure = stats.timer(["toto", "tutu"])
        measure.stop()
        values = self.backend.get_stats(FakeRequest(reset=False))
        self.assertIn("timers", values)
        self.assertIn("toto/tutu", values["timers"])
        self.assertEqual(1, values["timers"]["toto/tutu"]["nb"])

        measure = stats.timer(["toto", "tutu"])
        measure.stop()
        values = self.backend.get_stats(FakeRequest(reset=False))
        self.assertEqual(2, values["timers"]["toto/tutu"]["nb"])

    def test_timer_key_after(self):
        measure = stats.timer()
        measure.stop(["toto", "tutu"])
        values = self.backend.get_stats(FakeRequest(reset=False))
        self.assertIn("timers", values)
        self.assertIn("toto/tutu", values["timers"])
        self.assertEqual(1, values["timers"]["toto/tutu"]["nb"])

    def test_context(self):
        with stats.timer_context(["toto", "tutu"]):
            pass
        values = self.backend.get_stats(FakeRequest(reset=False))
        self.assertIn("timers", values)
        self.assertIn("toto/tutu", values["timers"])
        self.assertEqual(1, values["timers"]["toto/tutu"]["nb"])

    def test_reset(self):
        with stats.timer_context(["toto", "tutu"]):
            pass
        values = self.backend.get_stats(FakeRequest(reset="1"))
        self.assertIn("timers", values)
        self.assertIn("toto/tutu", values["timers"])
        self.assertEqual(1, values["timers"]["toto/tutu"]["nb"])

        self.assertEqual(self.backend.get_stats(FakeRequest(reset=False)), {"timers": {}})

    def test_simplify_sql(self):
        self.assertEqual(stats._simplify_sql("SELECT a,b,c FROM blah\nWHERE a IN (%(x)s,%(y)s)"),
                         "SELECT FROM blah WHERE a IN (?)")
        self.assertEqual(stats._simplify_sql("INSERT INTO blah (a,b,c) VALUES (1,2,3)"),
                         "INSERT INTO blah")

        self.assertEqual(stats._simplify_sql("UPDATE blah SET a=1, b=2 WHERE c=%(x)s"),
                         "UPDATE blah SET WHERE c=?")

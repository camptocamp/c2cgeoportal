# Copyright (c) 2026, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access


from unittest import TestCase
from unittest.mock import patch

from pyramid import testing

from tests.functional import create_dummy_request
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestFeedbackView(TestCase):
    def teardown_method(self, _) -> None:
        testing.tearDown()

        import transaction

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import Feedback

        assert DBSession is not None
        DBSession.query(Feedback).delete()
        transaction.commit()

    @staticmethod
    def _create_request(params=None):
        if params is None:
            params = {}
        request = create_dummy_request(
            additional_settings={
                "feedback": {
                    "email_from": "test@example.com",
                    "email_subject": "Test feedback",
                    "email_body": "Instance: {instance}\nID: {id_feedback}",
                },
            }
        )
        request.params = params
        return request

    def test_missing_params(self) -> None:
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.feedback import feedback_post

        request = self._create_request({})
        with self.assertRaises(HTTPBadRequest):
            feedback_post(request)

    def test_missing_user_agent(self) -> None:
        from pyramid.httpexceptions import HTTPBadRequest

        from c2cgeoportal_geoportal.views.feedback import feedback_post

        request = self._create_request(
            {
                "permalink": "https://example.com/view",
                "email": "user@example.com",
                "email_optional": "admin@example.com",
                "feedback": "Great app!",
            }
        )
        with self.assertRaises(HTTPBadRequest):
            feedback_post(request)

    def test_success(self) -> None:
        from c2cgeoportal_geoportal.views.feedback import feedback_post

        request = self._create_request(
            {
                "permalink": "https://example.com/view?theme=Demo",
                "user_agent": "Mozilla/5.0",
                "application": "viewer",
                "email": "user@example.com",
                "email_optional": "",
                "feedback": "Great app!",
            }
        )
        result = feedback_post(request)
        assert result == {"success": True}

    def test_success_with_email(self) -> None:
        from c2cgeoportal_geoportal.views.feedback import feedback_post

        request = self._create_request(
            {
                "permalink": "https://example.com/view?theme=Demo",
                "user_agent": "Mozilla/5.0",
                "application": "viewer",
                "email": "user@example.com",
                "email_optional": "admin@example.com",
                "feedback": "Great app!",
            }
        )
        with patch("c2cgeoportal_geoportal.views.feedback.send_email_config") as mock_send:
            result = feedback_post(request)
            assert result == {"success": True}
            mock_send.assert_called_once()
            _, kwargs = mock_send.call_args
            assert kwargs["instance"] == "https://example.com/view"
            assert kwargs["user_agent"] == "Mozilla/5.0"
            assert kwargs["application"] == "viewer"
            assert kwargs["permalink"] == "https://example.com/view?theme=Demo"
            assert kwargs["user_email"] == "user@example.com"
            assert kwargs["text"] == "Great app!"

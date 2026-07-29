import logging
from typing import Any

import pyramid.request
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config

from c2cgeoportal_commons.lib.email_ import send_email_config
from c2cgeoportal_commons.models import DBSession
from c2cgeoportal_commons.models.static import Feedback
from c2cgeoportal_geoportal.lib.common_headers import Cache, set_common_headers

_LOG = logging.getLogger(__name__)


@view_config(route_name="feedback", renderer="json")  # type: ignore[untyped-decorator]
def feedback_post(request: pyramid.request.Request) -> dict[str, Any]:
    """Handle feedback form submission."""
    if (
        "permalink" not in request.params
        or "user_agent" not in request.params
        or "application" not in request.params
        or "email" not in request.params
        or "email_optional" not in request.params
        or "feedback" not in request.params
    ):
        raise HTTPBadRequest(detail="parameter missing")

    new_feedback = Feedback()
    new_feedback.user_agent = request.params["user_agent"]
    new_feedback.application = request.params["application"]
    new_feedback.permalink = request.params["permalink"]
    new_feedback.email = request.params["email"]
    new_feedback.text = request.params["feedback"]
    assert DBSession is not None
    DBSession.add(new_feedback)
    DBSession.flush()

    instance = request.params["permalink"].split("?")[0]
    email = request.params.get("email_optional", "")
    if email != "":
        send_email_config(
            request.registry.settings,
            "feedback",
            email,
            instance=instance,
            id_feedback=str(new_feedback.id_feedback),
            user_agent=new_feedback.user_agent or "",
            application=new_feedback.application or "",
            permalink=new_feedback.permalink or "",
            user_email=new_feedback.email or "",
            text=new_feedback.text or "",
        )

    set_common_headers(request, "feedback", Cache.PRIVATE_NO)
    return {"success": True}

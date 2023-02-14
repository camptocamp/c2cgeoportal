# Copyright (c) 2023-2023, Camptocamp SA
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
from typing import Any, Dict, Optional, Union

import pytz
from c2cgeoform.views.abstract_views import AbstractViews
from pyramid.httpexceptions import HTTPFound

from c2cgeoportal_commons.models import Base
from c2cgeoportal_commons.models.main import Log, LogAction


class LoggedViews(AbstractViews):  # type: ignore
    """Extension of AbstractViews which log actions in a table."""

    _log_model = Log  # main.Log or static.Log
    _name_field = "name"

    def save(self) -> Union[HTTPFound, Dict[str, Any]]:
        response = super().save()

        if isinstance(response, HTTPFound):
            self._create_log(
                action=LogAction.INSERT if self._is_new() else LogAction.UPDATE,
                obj=self._obj,
            )

        return response

    def delete(self) -> Dict[str, Any]:
        obj = self._get_object()

        response = super().delete()

        self._create_log(LogAction.DELETE, obj)

        return response  # type: ignore

    def _create_log(
        self,
        action: LogAction,
        obj: Base,
        element_url_table: Optional[str] = None,
    ) -> None:
        log = self._log_model(
            date=datetime.datetime.now(pytz.utc),
            action=action,
            element_type=self._model.__tablename__,
            element_id=getattr(obj, self._id_field),
            element_name=getattr(obj, self._name_field),
            element_url_table=element_url_table or self._request.matchdict.get("table", None),
            username=self._request.user.username,
        )
        self._request.dbsession.add(log)

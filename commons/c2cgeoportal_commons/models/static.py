# Copyright (c) 2011-2021, Camptocamp SA
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


import crypt
import logging
from datetime import datetime
from hashlib import sha1
from hmac import compare_digest as compare_hash
from typing import Any, List, Optional

import pytz
import sqlalchemy.schema
from c2c.template.config import config
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref, relationship
from sqlalchemy.types import Boolean, DateTime, Integer, String, Unicode

from c2cgeoportal_commons.lib.literal import Literal
from c2cgeoportal_commons.models import Base, _
from c2cgeoportal_commons.models.main import Role

try:
    from c2cgeoform.ext.deform_ext import RelationSelect2Widget
    from colander import Email, drop
    from deform.widget import DateTimeInputWidget, HiddenWidget
except ModuleNotFoundError:
    drop = None

    class GenericClass:
        """Generic class."""

        def __init__(self, *args: Any, **kwargs: Any):
            pass

    Email = GenericClass
    HiddenWidget = GenericClass
    DateTimeInputWidget = GenericClass
    CollenderGeometry = GenericClass
    RelationSelect2Widget = GenericClass


LOG = logging.getLogger(__name__)

_schema: str = config["schema_static"] or "static"

# association table user <> role
user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", Integer, ForeignKey(_schema + ".user.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, primary_key=True),
    schema=_schema,
)


class User(Base):  # type: ignore
    """The user table representation."""

    __tablename__ = "user"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {
        "title": _("User"),
        "plural": _("Users"),
        "description": Literal(
            _(
                """
            <div class="help-block">
                <p>Each user may have from 1 to n roles, but each user has a default role from
                    which are taken some settings. The default role (defined through the
                    "Settings from role" selection) has an influence on the role extent and on some
                    functionalities regarding their configuration.</p>

                <p>Role extents for users can only be set in one role, because the application
                    is currently not able to check multiple extents for one user, thus it is the
                    default role which defines this unique extent.</p>

                <p>Any functionality specified as <b>single</b> can be defined only once per user.
                    Hence, these functionalities have to be defined in the default role.</p>

                <p>By default, functionalities are not specified as <b>single</b>. Currently, the
                    following functionalities are of <b>single</b> type:</p>

                <ul>
                    <li><code>default_basemap</code></li>
                    <li><code>default_theme</code></li>
                    <li><code>preset_layer_filter</code></li>
                    <li><code>open_panel</code></li>
                </ul>

                <p>Any other functionality (with <b>single</b> not set or set to <code>false</code>) can
                    be defined in any role linked to the user.</p>
                <hr>
            </div>
                """
            )
        ),
    }
    __c2cgeoform_config__ = {"duplicate": True}
    item_type = Column(
        "type", String(10), nullable=False, info={"colanderalchemy": {"widget": HiddenWidget()}}
    )
    __mapper_args__ = {"polymorphic_on": item_type, "polymorphic_identity": "user"}

    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    username = Column(
        Unicode,
        unique=True,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Username"),
                "description": _("Name used for authentication (must be unique)."),
            }
        },
    )
    _password = Column("password", Unicode, nullable=False, info={"colanderalchemy": {"exclude": True}})
    temp_password = Column(
        "temp_password", Unicode, nullable=True, info={"colanderalchemy": {"exclude": True}}
    )
    tech_data = Column(MutableDict.as_mutable(HSTORE), info={"colanderalchemy": {"exclude": True}})
    email = Column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Email"),
                "description": _(
                    "Used to send emails to the user, for example in case of password recovery."
                ),
                "validator": Email(),
            }
        },
    )
    is_password_changed = Column(
        Boolean,
        default=False,
        info={
            "colanderalchemy": {
                "title": _("The user changed his password"),
                "description": _("Indicates if user has changed his password."),
            }
        },
    )

    settings_role_id = Column(
        Integer,
        info={
            "colanderalchemy": {
                "title": _("Settings from role"),
                "description": _("Used to get some settings for the user (not for permissions)."),
                "widget": RelationSelect2Widget(
                    Role, "id", "name", order_by="name", default_value=("", _("- Select -"))
                ),
            }
        },
    )

    settings_role = relationship(
        Role,
        foreign_keys="User.settings_role_id",
        primaryjoin="Role.id==User.settings_role_id",
        info={"colanderalchemy": {"title": _("Settings role"), "exclude": True}},
    )

    roles = relationship(
        Role,
        secondary=user_role,
        secondaryjoin=Role.id == user_role.c.role_id,
        backref=backref(
            "users",
            order_by="User.username",
            info={
                "colanderalchemy": {
                    "title": _("Users"),
                    "description": _("Users granted with this role."),
                    "exclude": True,
                }
            },
        ),
        info={
            "colanderalchemy": {
                "title": _("Roles"),
                "description": _("Roles granted to the user."),
                "exclude": True,
            }
        },
    )

    last_login = Column(
        DateTime(timezone=True),
        info={
            "colanderalchemy": {
                "title": _("Last login"),
                "description": _("Date of the user's last login."),
                "missing": drop,
                "widget": DateTimeInputWidget(readonly=True),
            }
        },
    )

    expire_on = Column(
        DateTime(timezone=True),
        info={
            "colanderalchemy": {
                "title": _("Expiration date"),
                "description": _("After this date the user will not be able to login anymore."),
            }
        },
    )

    deactivated = Column(
        Boolean,
        default=False,
        info={
            "colanderalchemy": {
                "title": _("Deactivated"),
                "description": _("Deactivate a user without removing it completely."),
            }
        },
    )

    def __init__(  # nosec
        self,
        username: str = "",
        password: str = "",
        email: str = "",
        is_password_changed: bool = False,
        settings_role: Optional[Role] = None,
        roles: Optional[List[Role]] = None,
        expire_on: Optional[datetime] = None,
        deactivated: bool = False,
    ) -> None:
        self.username = username
        self.password = password
        self.tech_data = {}
        self.email = email
        self.is_password_changed = is_password_changed
        if settings_role:
            self.settings_role = settings_role
        self.roles = roles or []
        self.expire_on = expire_on
        self.deactivated = deactivated

    @property
    def password(self) -> str:
        """Get the password."""
        return self._password  # type: ignore

    @password.setter
    def password(self, password: str) -> None:
        """Encrypt password on the fly."""
        self._password = self.__encrypt_password(password)

    def set_temp_password(self, password: str) -> None:
        """Encrypt password on the fly."""
        self.temp_password = self.__encrypt_password(password)

    @staticmethod
    def __encrypt_password_legacy(password: str) -> str:
        """Hash the given password with SHA1."""
        return sha1(password.encode("utf8")).hexdigest()  # nosec

    @staticmethod
    def __encrypt_password(password: str) -> str:
        return crypt.crypt(password, crypt.METHOD_SHA512)

    def validate_password(self, passwd: str) -> bool:
        """
        Check the password against existing credentials. this method _MUST_ return a boolean.

        @param passwd: the password that was provided by the user to
        try and authenticate. This is the clear text version that we will
        need to match against the (possibly) encrypted one in the database.
        """
        if self._password.startswith("$"):
            # new encryption method
            if compare_hash(self._password, crypt.crypt(passwd, self._password)):
                return True
        else:
            # legacy encryption method
            if compare_hash(self._password, self.__encrypt_password_legacy(passwd)):
                # convert to the new encryption method
                self._password = self.__encrypt_password(passwd)
                return True

        if (
            self.temp_password is not None
            and self.temp_password != ""  # nosec
            and compare_hash(self.temp_password, crypt.crypt(passwd, self.temp_password))
        ):
            self._password = self.temp_password
            self.temp_password = None
            self.is_password_changed = False
            return True
        return False

    def expired(self) -> bool:
        return self.expire_on is not None and self.expire_on < datetime.now(pytz.utc)

    def update_last_login(self) -> None:
        self.last_login = datetime.now(pytz.utc)

    def __str__(self) -> str:
        return self.username or ""


class Shorturl(Base):  # type: ignore
    """The shorturl table representation."""

    __tablename__ = "shorturl"
    __table_args__ = {"schema": _schema}
    id = Column(Integer, primary_key=True)
    url = Column(Unicode)
    ref = Column(String(20), index=True, unique=True, nullable=False)
    creator_email = Column(Unicode(200))
    creation = Column(DateTime)
    last_hit = Column(DateTime)
    nb_hits = Column(Integer)


class OAuth2Client(Base):  # type: ignore
    """The oauth2_client table representation."""

    __tablename__ = "oauth2_client"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("OAuth2 Client"), "plural": _("OAuth2 Clients")}
    __c2cgeoform_config__ = {"duplicate": True}
    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    client_id = Column(
        Unicode,
        unique=True,
        info={
            "colanderalchemy": {
                "title": _("Client ID"),
                "description": _("The client identifier as e.-g. 'qgis'."),
            }
        },
    )
    secret = Column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Secret"),
                "description": _("The secret."),
            }
        },
    )
    redirect_uri = Column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Redirect URI"),
                "description": _(
                    """
                    URI where user should be redirected after authentication
                    as e.-g. 'http://127.0.0.1:7070/' in case of QGIS desktop.
                    """
                ),
            }
        },
    )


class OAuth2BearerToken(Base):  # type: ignore
    """The oauth2_bearertoken table representation."""

    __tablename__ = "oauth2_bearertoken"
    __table_args__ = (
        sqlalchemy.schema.UniqueConstraint("client_id", "user_id"),
        {
            "schema": _schema,
        },
    )
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey(_schema + ".oauth2_client.id", ondelete="CASCADE"), nullable=False)
    client = relationship(OAuth2Client)
    user_id = Column(Integer, ForeignKey(_schema + ".user.id", ondelete="CASCADE"), nullable=False)
    user = relationship(User)
    access_token = Column(Unicode(100), unique=True)
    refresh_token = Column(Unicode(100), unique=True)
    expire_at = Column(DateTime(timezone=True))  # in one hour


class OAuth2AuthorizationCode(Base):  # type: ignore
    """The oauth2_authorizationcode table representation."""

    __tablename__ = "oauth2_authorizationcode"
    __table_args__ = (
        sqlalchemy.schema.UniqueConstraint("client_id", "user_id"),
        {
            "schema": _schema,
        },
    )
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey(_schema + ".oauth2_client.id", ondelete="CASCADE"), nullable=False)
    client = relationship(OAuth2Client)
    user_id = Column(Integer, ForeignKey(_schema + ".user.id", ondelete="CASCADE"), nullable=False)
    user = relationship(User)
    redirect_uri = Column(Unicode)
    code = Column(Unicode(100), unique=True)
    expire_at = Column(DateTime(timezone=True))  # in 10 minutes

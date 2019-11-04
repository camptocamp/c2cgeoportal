# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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


import logging
from datetime import datetime
from hashlib import sha1
import pytz
from typing import List

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import Integer, Boolean, Unicode, String, DateTime

import colander
from deform.widget import HiddenWidget, DateTimeInputWidget
from c2cgeoform.ext import deform_ext

from c2c.template.config import config
from c2cgeoportal_commons.models import Base, _
from c2cgeoportal_commons.models.main import Role


LOG = logging.getLogger(__name__)

_schema = config['schema_static']  # type: str

# association table user <> role
user_role = Table(
    'user_role',
    Base.metadata,
    Column('user_id', Integer, ForeignKey(_schema + '.user.id'), primary_key=True),
    Column('role_id', Integer, primary_key=True),
    schema=_schema
)


class User(Base):
    __tablename__ = 'user'
    __table_args__ = {'schema': _schema}
    __colanderalchemy_config__ = {
        'title': _('User'),
        'plural': _('Users')
    }
    __c2cgeoform_config__ = {
        'duplicate': True
    }
    item_type = Column('type', String(10), nullable=False, info={
        'colanderalchemy': {
            'widget': HiddenWidget()
        }
    })
    __mapper_args__ = {
        'polymorphic_on': item_type,
        'polymorphic_identity': 'user',
    }

    id = Column(Integer, primary_key=True, info={
        'colanderalchemy': {
            'widget': HiddenWidget()
        }
    })
    username = Column(Unicode, unique=True, nullable=False, info={
        'colanderalchemy': {
            'title': _('Username')
        }
    })
    _password = Column('password', Unicode, nullable=False,
                       info={'colanderalchemy': {'exclude': True}})
    temp_password = Column('temp_password', Unicode, nullable=True,
                           info={'colanderalchemy': {'exclude': True}})
    email = Column(Unicode, nullable=False, info={
        'colanderalchemy': {
            'title': _('Email'),
            'validator': colander.Email()
        }
    })
    is_password_changed = Column(Boolean, default=False,
                                 info={'colanderalchemy': {'exclude': True}})

    settings_role_id = Column(Integer, info={
        'colanderalchemy': {
            'title': _('Settings from role'),
            'description': 'Only used for settings not for permissions',
            'widget': deform_ext.RelationSelect2Widget(
                Role,
                'id',
                'name',
                order_by='name',
                default_value=('', _('- Select -'))
            )
        }
    })

    settings_role = relationship(
        Role,
        foreign_keys='User.settings_role_id',
        primaryjoin='Role.id==User.settings_role_id',
        info={
            'colanderalchemy': {
                'title': _('Settings role'),
                'exclude': True
            }
        })

    roles = relationship(
        Role,
        secondary=user_role,
        secondaryjoin=Role.id == user_role.c.role_id,
        backref=backref('users', info={'colanderalchemy': {'exclude': True}}),
        info={
            'colanderalchemy': {
                'title': _('Roles'),
                'exclude': True
            }
        }
    )

    last_login = Column(DateTime(timezone=True), info={
        'colanderalchemy': {
            'title': _('Last login'),
            'missing': colander.drop,
            'widget': DateTimeInputWidget(readonly=True)
        }
    })

    expire_on = Column(DateTime(timezone=True), info={
        'colanderalchemy': {
            'title': _('Expiration date')
        }
    })

    deactivated = Column(Boolean, default=False, info={
        'colanderalchemy': {
            'title': _('Deactivated')
        }
    })

    def __init__(
        self, username: str = '', password: str = '', email: str = '', is_password_changed: bool = False,
        settings_role: Role = None, roles: List[Role] = [], expire_on: datetime = None,
        deactivated: bool = False
    ) -> None:
        self.username = username
        self.password = password
        self.email = email
        self.is_password_changed = is_password_changed
        if settings_role:
            self.settings_role = settings_role
        self.roles = roles
        self.expire_on = expire_on
        self.deactivated = deactivated

    @property
    def password(self) -> str:
        """returns password"""
        return self._password  # pragma: no cover

    @password.setter
    def password(self, password: str) -> None:
        """encrypts password on the fly."""
        self._password = self.__encrypt_password(password)

    def set_temp_password(self, password: str) -> None:
        """encrypts password on the fly."""
        self.temp_password = self.__encrypt_password(password)

    @staticmethod
    def __encrypt_password(password: str) -> str:
        """Hash the given password with SHA1."""
        return sha1(password.encode('utf8')).hexdigest()

    def validate_password(self, passwd: str) -> bool:
        """Check the password against existing credentials.
        this method _MUST_ return a boolean.

        @param passwd: the password that was provided by the user to
        try and authenticate. This is the clear text version that we will
        need to match against the (possibly) encrypted one in the database.
        @type password: string
        """
        if self._password == self.__encrypt_password(passwd):
            return True
        if \
                self.temp_password is not None and \
                self.temp_password != '' and \
                self.temp_password == self.__encrypt_password(passwd):
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
        return self.username or ''  # pragma: no cover


class Shorturl(Base):
    __tablename__ = 'shorturl'
    __table_args__ = {'schema': _schema}
    id = Column(Integer, primary_key=True)
    url = Column(Unicode)
    ref = Column(String(20), index=True, unique=True, nullable=False)
    creator_email = Column(Unicode(200))
    creation = Column(DateTime)
    last_hit = Column(DateTime)
    nb_hits = Column(Integer)

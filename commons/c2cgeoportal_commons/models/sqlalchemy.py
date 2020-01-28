# -*- coding: utf-8 -*-

# Copyright (c) 2012-2020, Camptocamp SA
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
import json
from typing import Any, Optional, Type

from sqlalchemy.engine import Dialect
from sqlalchemy.types import VARCHAR, TypeDecorator, UserDefinedType


# get from https://docs.sqlalchemy.org/en/latest/orm/extensions/
# mutable.html#establishing-mutability-on-scalar-column-values
class JSONEncodedDict(TypeDecorator):
    """
    Represents an immutable structure as a json-encoded string.
    """

    impl = VARCHAR

    @staticmethod
    def process_bind_param(value: Optional[dict], _: Dialect) -> Optional[str]:
        return json.dumps(value) if value is not None else None

    @staticmethod
    def process_result_value(value: Optional[str], _: Dialect) -> Optional[dict]:
        return json.loads(value) if value is not None else None

    @property
    def python_type(self) -> Type:
        return dict

    @staticmethod
    def process_literal_param(value: str, dialect: Any) -> str:
        del dialect
        return json.dumps(value)


class TsVector(UserDefinedType):
    """ A custom type for PostgreSQL's tsvector type. """

    def get_col_spec(self) -> str:  # pylint: disable=no-self-use
        return "TSVECTOR"

    @property
    def python_type(self) -> Type:
        return dict

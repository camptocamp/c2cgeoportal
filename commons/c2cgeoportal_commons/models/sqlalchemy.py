# Copyright (c) 2012-2024, Camptocamp SA
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
from typing import Any

from sqlalchemy.engine import Dialect
from sqlalchemy.types import VARCHAR, TypeDecorator, UserDefinedType


# get from https://docs.sqlalchemy.org/en/latest/orm/extensions/
# mutable.html#establishing-mutability-on-scalar-column-values
class JSONEncodedDict(TypeDecorator[Any]):
    """Represent an immutable structure as a json-encoded string."""

    impl = VARCHAR

    def process_bind_param(self, value: dict[str, Any] | None, _: Dialect) -> str | None:
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value: str | None, _: Dialect) -> dict[str, Any] | None:
        return json.loads(value) if value is not None else None

    @property
    def python_type(self) -> type[Any]:
        return dict

    def process_literal_param(self, value: Any | None, dialect: Any) -> str:
        assert isinstance(value, str)
        del dialect
        return json.dumps(value)


class TsVector(UserDefinedType[dict[str, str]]):  # pylint: disable=abstract-method
    """A custom type for PostgreSQL's tsvector type."""

    cache_ok = True

    def get_col_spec(self) -> str:
        return "TSVECTOR"

    @property
    def python_type(self) -> type[Any]:
        return dict

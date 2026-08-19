#!/usr/bin/env python3

# Copyright (c) 2025-2026, Camptocamp SA
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

import argparse
import json
from typing import Any, cast


def _format_type(type_definition: dict[str, Any]) -> str:
    """Get the type definition as a ReStructuredText (name or ref)."""
    if type_definition["type"] == "intrinsic":
        return cast("str", type_definition["name"])

    if type_definition["type"] == "array":
        return f"{_format_type(type_definition['elementType'])}\\[]"

    if type_definition["type"] == "union":
        return f"{' | '.join([_format_type(t) for t in type_definition['types']])}"

    if type_definition["type"] == "reference":
        postfix = ""
        if "typeArguments" in type_definition:
            postfix = f"\\<{', '.join([_format_type(t) for t in type_definition['typeArguments']])}>"

        return f":ref:`integrator_guide_ngeo_properties_{type_definition['name']}`{postfix}"

    if type_definition["type"] == "reflection" and "indexSignature" in type_definition["declaration"]:
        assert len(type_definition["declaration"]["indexSignature"]["parameters"]) == 1
        return (
            f"{{{_format_type(type_definition['declaration']['indexSignature']['parameters'][0]['type'])}: "
            f"{_format_type(type_definition['declaration']['indexSignature']['type'])}}}"
        )

    raise AssertionError(f"Unknown type '{type_definition['type']}':\n{type_definition}")


def _get_type(type_definition: dict[str, Any]) -> list[str]:
    """Get the type definition as a ReStructuredText (name or ref) this is for dictionary based types."""
    result = []
    if type_definition["name"] == "__type":
        result.append("\nProperties:")
        for child in type_definition.get("children", []):
            result += _get_type(child)
        return result

    options = []
    if "type" in type_definition:
        options.append(_format_type(type_definition["type"]))
    if type_definition["flags"].get("isOptional"):
        options.append("optional")
    options_string = f" ({', '.join(options)})" if options else ""

    result.append(f" * ``{type_definition['name']}``{options_string}")
    return result


def _browse(elem: dict[str, Any], types: dict[str, str]) -> None:
    """Browse the tree of type definitions."""
    if (
        len(elem.get("sources", [])) == 1
        and elem["sources"][0]["fileName"] == "config.ts"
        and elem.get("kindString") == "Type alias"
    ):
        result = []
        result.append(f".. _integrator_guide_ngeo_properties_{elem['name']}:")
        result.append("")
        result.append("".join(["~" for _ in elem["name"]]))
        result.append(elem["name"])
        result.append("".join(["~" for _ in elem["name"]]))
        if "comment" in elem:
            if "shortText" in elem["comment"]:
                result.append(elem["comment"]["shortText"])
            if "text" in elem["comment"]:
                result.append(elem["comment"]["text"])
        if "defaultValue" in elem:
            result.append(f"Default value: {elem['defaultValue']}")

        if "declaration" in elem["type"]:
            result += _get_type(elem["type"]["declaration"])

        types[elem["name"]] = "\n".join(result)
    else:
        for child in elem.get("children", []):
            _browse(child, types)


def main() -> None:
    """Convert the ngeo config to ReStructuredText."""
    parser = argparse.ArgumentParser("Convert the config from the JSON from typedoc to ReStructuredText")
    parser.add_argument(
        "--type",
        help="create a separate file for a type",
        nargs=2,
        action="append",
        default=[],
    )
    parser.add_argument("input", help="the JSON file from typedoc")
    parser.add_argument("other", help="filename for other types")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    types: dict[str, str] = {}
    _browse(data, types)

    exported_types = []
    for type_name, file_name in args.type:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(types[type_name])
        exported_types.append(type_name)

    with open(args.other, "w", encoding="utf-8") as f:
        f.write("Ngeo internal object configuration options\n")
        f.write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        for type_name, type_content in sorted(types.items(), key=lambda e: e[0]):
            if type_name not in exported_types:
                f.write(type_content)
                f.write("\n\n")


if __name__ == "__main__":
    main()

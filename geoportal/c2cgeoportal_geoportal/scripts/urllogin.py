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

import argparse
import binascii
import json
import sys
import time
from typing import cast

from Crypto.Cipher import AES  # nosec
from Crypto.Cipher.ChaCha20_Poly1305 import ChaCha20Poly1305Cipher  # nosec

from c2cgeoportal_geoportal.scripts import fill_arguments, get_appsettings


def create_token(aeskey: str, user: str, password: str, valid: bool) -> str:
    """Create the authenticated URL token."""
    auth = {"u": user, "p": password, "t": int(time.time()) + valid * 3600 * 24}

    if aeskey is None:
        print("urllogin is not configured")
        sys.exit(1)
    cipher = cast(ChaCha20Poly1305Cipher, AES.new(aeskey.encode("ascii"), AES.MODE_EAX))
    data = json.dumps(auth)
    mod_len = len(data) % 16
    if mod_len != 0:
        data += "".join([" " for i in range(16 - mod_len)])
    ciphertext, tag = cipher.encrypt_and_digest(data.encode("utf-8"))
    return binascii.hexlify(cipher.nonce + tag + ciphertext).decode("ascii")


def get_argparser() -> argparse.ArgumentParser:
    """Get the argument parser for this script."""

    parser = argparse.ArgumentParser(description="Generate an auth token")
    fill_arguments(parser, use_attribute=True)
    parser.add_argument("user", help="The username")
    parser.add_argument("password", help="The password")
    parser.add_argument("valid", type=int, default=1, nargs="?", help="Is valid for, in days")
    return parser


def main() -> None:
    """Run the command."""

    args = get_argparser().parse_args()
    settings = get_appsettings(args)
    urllogin = settings.get("urllogin", {})
    aeskey = urllogin.get("aes_key")
    auth_enc = create_token(aeskey, args.user, args.password, args.valid)

    print(f"Use: auth={auth_enc}")


if __name__ == "__main__":
    main()

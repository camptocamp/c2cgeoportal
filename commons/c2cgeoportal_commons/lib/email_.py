# Copyright (c) 2013-2025, Camptocamp SA
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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from socket import gaierror
from typing import Any, cast

try:
    from pyramid.httpexceptions import HTTPInternalServerError
except ModuleNotFoundError:

    class HTTPInternalServerError(BaseException):  # type: ignore[no-redef]
        """Fallback class."""


_LOG = logging.getLogger(__name__)


def send_email_config(settings: dict[str, Any], email_config_name: str, email: str, **kwargs: Any) -> None:
    """Send an email from the config information."""
    smtp_config = settings["smtp"]
    email_config = cast("dict[str, str]", settings[email_config_name])

    try:
        send_email(
            email_config["email_from"],
            [email],
            email_config["email_body"].format(**kwargs),
            email_config["email_subject"],
            smtp_config,
        )
    except gaierror:
        _LOG.exception("Unable to send the email.")
        raise HTTPInternalServerError("See server logs for details")  # pylint: disable=raise-missing-from


def send_email(
    from_addr: str,
    to_address: list[str],
    body: str,
    subject: str,
    smtp_config: dict[str, str],
) -> None:
    """Send an email."""
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_address)
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    SMTPClass = smtplib.SMTP_SSL if smtp_config.get("ssl", False) else smtplib.SMTP
    with SMTPClass(smtp_config["host"]) as smtp:
        if smtp_config.get("starttls", False):
            smtp.starttls()
        if smtp_config.get("user", False):
            smtp.login(smtp_config["user"], smtp_config["password"])

        smtp.sendmail(from_addr, to_address, msg.as_string())

# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
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
from typing import Dict, Any, List, cast
from socket import gaierror
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from pyramid.httpexceptions import HTTPInternalServerError


LOG = logging.getLogger(__name__)


def send_email_config(
    settings: Dict[str, Any],
    email_config_name: str,
    email: str, **kwargs: Dict[str, Any]
) -> None:  # pragma: no cover
    smtp_config = settings['smtp']
    email_config = cast(Dict[str, str], settings[email_config_name])

    try:
        send_email(
            email_config['email_from'], [email],
            email_config['email_body'].format(**kwargs),
            email_config['email_subject'],
            smtp_config,
        )
    except gaierror:
        LOG.error('Unable to send the email.', exc_info=True)
        raise HTTPInternalServerError('See server logs for details')


def send_email(
    from_addr: str, to_addrs: List[str], body: str, subject: str,
    smtp_config: Dict[str, str]
) -> None:  # pragma: no cover
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Connect to server
    if smtp_config.get('ssl', False):
        smtp = smtplib.SMTP_SSL(smtp_config['host'])  # type: smtplib.SMTP
    else:
        smtp = smtplib.SMTP(smtp_config['host'])
    if smtp_config.get('user', False):
        smtp.login(smtp_config['user'], smtp_config['password'])
    if smtp_config.get('starttls', False):
        smtp.starttls()

    smtp.sendmail(from_addr, to_addrs, msg.as_string())
    smtp.close()

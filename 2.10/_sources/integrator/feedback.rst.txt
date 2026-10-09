.. _integrator_feedback:

Configure feedback
==================

The configuration in ``vars.yaml`` looks like this:

.. code:: yaml

   # SMTP configuration could be already there if needed by other feature
   smtp:
       host: smtp.example.com:465
       ssl: true
       user: <username>
       password: <password>
       starttls: false

   feedback:
        # Used to send a feedback notification email
        email_from: info@camptocamp.com
        email_subject: Feedback - Map viewer
        email_body: |
            This is an automated email. A new feedback has been inserted in the database.

            Instance: {instance}

            Feedback ID: {id_feedback}

            User agent: {user_agent}

            Application: {application}

            Permalink: {permalink}

            User email: {user_email}

            User text: {text}

The feedback form data is stored in the ``feedback`` database table with the
following fields: ``user_agent``, ``application``, ``permalink``, ``text``,
and ``email``.

The service exposes a ``POST /feedback`` endpoint. The frontend can access it
through the ``feedbackUrl`` route entrypoint, configured in
``interfaces_config.default.routes.feedbackUrl`` in the ``vars.yaml`` file.

When a user provides an email address in the ``email_optional`` field, a
notification email is sent to that address using the configured SMTP server.

If the SMTP host ends with a colon (`:`) followed by a number, and
there is no port specified, that suffix will be stripped off and the
number interpreted as the port number to use.

Replace the ``smtp.example.com`` value by a working SMTP server name.
If your SMTP server does not require user login, then remove the configuration
for user and password.

Altcha anti-spam protection
----------------------------

The feedback form can be protected against spam using `ALTCHA <https://altcha.org>`_,
an open-source proof-of-work challenge. When enabled, the frontend must solve a
cryptographic puzzle before submitting the form.

The default configuration is already in ``CONST_vars.yaml``:

.. code:: yaml

   altcha:
     hmac_secret: '{ALTCHA_HMAC_SECRET}'
     algorithm: 'PBKDF2/SHA-256'
     cost: 5000
     expires_in: 300

To enable ALTCHA, set ``feedback.altcha: true`` in your ``vars.yaml`` and
configure the ``ALTCHA_HMAC_SECRET`` environment variable with a strong secret
value (at least 32 characters, alphanumeric).

When ``feedback.altcha`` is ``true``, the ``POST /feedback`` endpoint requires
a valid ALTCHA payload in the ``altcha`` form field. The frontend can fetch a
new challenge from the ``GET /altcha/challenge`` endpoint.

By default ``hmac_secret`` is empty, which disables the ALTCHA challenge
generation and verification.

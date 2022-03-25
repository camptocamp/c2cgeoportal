.. _integrator_shortener:

Configure short URL
===================

The configuration in ``vars.yaml`` looks like this:

.. code:: yaml

   # SMTP configuration could be already there if needed by other feature
   smtp:
       host: smtp.example.com:465
       ssl: true
       user: <username>
       password: <password>
       starttls: false

   shortener:
        # The base of created URL
        base_url:  https://{host}/{apache_entry_point}s/
        # Used to send a confirmation email
        email_from: info@camptocamp.com
        email_subject: You have created the following short URL
        email_body: |
            Hello,

            Somebody sent you the following link:
            {short_url}

            With the message:
            {message}

            Sincerely yours
            The GeoMapFish team
        # length (default) of ref of new short url
        # Can be change when you want
        # max 20 (size of the column)
        length: 4

The shortened URL is sent by email to the current registered user email address
unless another address has been provided through the email field in the
viewer interface.

If the SMTP host ends with a colon (`:`) followed by a number, and
there is no port specified, that suffix will be stripped off and the
number interpreted as the port number to use.

Replace the ``smtp.example.com`` value by a working SMTP server name.
If your SMTP server does not require user login, then remove the configuration
for user and password.

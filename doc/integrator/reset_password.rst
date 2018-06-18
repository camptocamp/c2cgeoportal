Reset password
--------------

When a user has forgotten his/her password, a new one may be sent by email if some additional
GeoMapFish configuration is provided.

And to generate the required e-mail, in the ``vars.yaml`` file, add the following configuration:

.. code:: yaml

    # SMTP configuration could be already there if needed by other feature
    smtp:
        host: smtp.example.com:465
        ssl: true
        user: <username>
        password: <password>
        starttls: false

    reset_password:
        # Used to send a confirmation email
        email_from: info@camptocamp.com
        email_subject: New password generated for GeoMapFish
        email_body: |
            Hello {user},

            You have asked for an new password,
            the newly generated password is: {password}

            Sincerely yours
            The GeoMapfish team

If the SMTP host ends with a colon (`:`) followed by a number, and
there is no port specified, that suffix will be stripped off and the
number interpreted as the port number to use.

Replace the ``smtp.example.com`` value by a working SMTP server name.

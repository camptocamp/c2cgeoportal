.. _integrator_reset_password:

Reset password
==============

When a user has forgotten his/her password, a new one may be sent by email if some additional
GeoMapFish configuration is provided.

In the ``<package>/template/*.js`` files, in the ``cgxp_login`` plugin you should add the
service URL with the following configuration:

.. code:: javascript

   loginResetPasswordURL: "${request.route_url('loginresetpassword') | n}",

And to generate the required e-mail, in the ``vars_<package>.yaml`` file, add the following configuration:

.. code:: yaml

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
        smtp:
            host: smtp.example.com:465
            ssl: true
            user: <username>
            password: <password>
            starttls: false

If the SMTP host ends with a colon (`:`) followed by a number, and
there is no port specified, that suffix will be stripped off and the
number interpreted as the port number to use.

Replace the ``smtp.example.com`` value by a working SMTP server name.

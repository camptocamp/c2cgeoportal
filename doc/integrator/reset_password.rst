.. _integrator_reset_password:

Reset password
==============

When a user has forgotten his/her password, a new one may be sent by email if some additional
GeoMapFish configuration is provided.

In the ``<package>/template/*.js`` files, in the ``cgxp_login`` plugin you should add the
service URL with the following configuration:

.. code:: javascript

   loginResetPasswordURL: "${request.route_url('loginresetpassword') | n}",

And to generate the required e-mail, in the ``vars_<package>.yaml`` file, the following configuration:

.. code:: yaml

    reset_password:
        # Used to send a confirmation email
        email_from: info@camptocamp.com
        email_subject: New password generated for GeoMapFish
        email_body: |
            Hello,

            You ask for an new password,
            the new generated password is: {password}

            Sincerely yours
            The GeoMapfish team
        smtp_server: smtp.example.com

from unittest import TestCase
from pyramid import testing


class Test_includeme(TestCase):

    def setUp(self):
        self.config = testing.setUp(
            # the c2cgeoportal includeme function requires a number
            # of settings
            settings={
                'sqlalchemy.url': 'postgresql://u:p@h/d',
                'srid': 3857,
                'schema': 'main',
                'parentschema': '',
                'default_max_age': 86400,
                'tilecache.cfg': 'c2cgeoportal/tests/tilecache.cfg',
                'app.cfg': 'c2cgeoportal/tests/config.yaml'
            })

    def test_set_user_validator_directive(self):
        import c2cgeoportal
        self.config.include(c2cgeoportal.includeme)
        self.failUnless(
            self.config.set_user_validator.im_func.__docobj__ is
            c2cgeoportal.set_user_validator
        )

    def test_default_user_validator(self):
        import c2cgeoportal
        self.config.include(c2cgeoportal.includeme)
        self.assertEqual(self.config.registry.validate_user,
                         c2cgeoportal.default_user_validator)

    def test_user_validator_overwrite(self):
        import c2cgeoportal
        self.config.include(c2cgeoportal.includeme)

        def custom_validator(username, password):
            return False  # pragma: nocover
        self.config.set_user_validator(custom_validator)
        self.assertEqual(self.config.registry.validate_user,
                         custom_validator)

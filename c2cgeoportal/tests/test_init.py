from unittest import TestCase
from pyramid import testing


class Test_includeme(TestCase):

    def setUp(self):
        self.config = testing.setUp(
            # the c2cgeoportal includeme function requires a number
            # of settings
            settings={
                'sqlalchemy.url': 'postgresql://u:p@h/d',
                'srid': 900913,
                'schema': 'main',
                'parentschema': '',
                'formalchemy_default_zoom': 0,
                'formalchemy_default_lon': 0,
                'formalchemy_default_lat': 0,
                'formalchemy_available_functionalities': '',
                'tilecache.cfg': 'c2cgeoportal/tests/tilecache.cfg'
                }
            )

    def test_set_user_validator_directive(self):
        import c2cgeoportal
        self.config.include(c2cgeoportal.includeme)
        self.failUnless(
                self.config.set_user_validator.im_func.__docobj__ is
                        c2cgeoportal.set_user_validator)

    def test_default_user_validator(self):
        import c2cgeoportal
        self.config.include(c2cgeoportal.includeme)
        self.assertEqual(self.config.registry.validate_user,
                         c2cgeoportal.default_user_validator)

    def test_user_validator_overwrite(self):
        import c2cgeoportal
        self.config.include(c2cgeoportal.includeme)

        def custom_validator(username, password):
            return False
        self.config.set_user_validator(custom_validator)
        self.assertEqual(self.config.registry.validate_user,
                         custom_validator)

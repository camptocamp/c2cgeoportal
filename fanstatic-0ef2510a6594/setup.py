from setuptools import setup

long_description = (
    open('README.txt').read()
    + '\n' +
    open('CHANGES.txt').read())

setup(
    name='fanstatic',
    version='0.12dev',
    description="Flexible static resources for web applications.",
    classifiers=[],
    keywords='',
    author='Fanstatic Developers',
    author_email='fanstatic@googlegroups.com',
    long_description=long_description,
    license='BSD',
    url='http://fanstatic.org',
    packages=['fanstatic'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Paste', 'WebOb'],
    extras_require = dict(
        test=['pytest >= 2.0'],
        ),
    entry_points = {
        'paste.filter_app_factory': [
            'fanstatic = fanstatic:make_fanstatic',
            'publisher = fanstatic:make_publisher',
            'injector = fanstatic:make_injector',
            ],
        'paste.app_factory': [
            'serf = fanstatic:make_serf',
            ],
    })

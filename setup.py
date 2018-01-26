import os

from setuptools import setup, find_packages

requires = [
    'multidict',
    'plaster_pastedeploy',
    'pyramid',
    'pyramid_beaker',
    'pyramid_debugtoolbar',
    'pyramid_mako',
    'waitress',
    'WTForms'
]

entry_points = {
    'paste.app_factory': [
        'main = mafia:main',
    ]
}

setup(
    name='mafia',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    entry_points=entry_points,
)

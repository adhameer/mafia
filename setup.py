from setuptools import setup, find_packages

requires = [
    'flask',
    'flask_wtf',
    'multidict',
]

setup(
    name='mafia',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
)

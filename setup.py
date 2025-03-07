"""Installer for the collective.volto.formsupport package."""

from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="collective.volto.formsupport",
    version="3.2.3",
    description="Add support for customizable forms in Volto",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: 6.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone CMS",
    author="RedTurtle Technology",
    author_email="sviluppo@redturtle.it",
    url="https://github.com/collective/collective.volto.formsupport",
    project_urls={
        "PyPI": "https://pypi.python.org/pypi/collective.volto.formsupport",
        "Source": "https://github.com/collective/collective.volto.formsupport",
        "Tracker": "https://github.com/collective/collective.volto.formsupport/issues",
    },
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["collective", "collective.volto"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=[
        "setuptools",
        "z3c.jbot",
        "Zope",
        "plone.api>=1.8.4",
        "plone.dexterity",
        "plone.i18n",
        "plone.memoize",
        "plone.protect",
        "plone.registry",
        "plone.restapi>=8.36.0",
        "plone.schema",
        "Products.GenericSetup",
        "Products.PortalTransforms",
        "souper.plone",
        "click",
        "beautifulsoup4",
        "collective.volto.otp",
    ],
    extras_require={
        "hcaptcha": [
            "plone.formwidget.hcaptcha>=1.0.1",
        ],
        "recaptcha": [
            "plone.formwidget.recaptcha",
        ],
        "norobots": [
            "collective.z3cform.norobots",
        ],
        "honeypot": [
            "collective.honeypot>=2.1",
        ],
        "blocksfield": [
            "collective.volto.blocksfield",
        ],
        "test": [
            "plone.app.testing",
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            "plone.testing>=5.0.0",
            "plone.app.contenttypes[test]",
            "plone.restapi[test]",
            "plone.app.iterate",
            "Products.MailHost",
            "plone.browserlayer",
            "collective.MockMailHost",
            "collective.honeypot",
            "plone.formwidget.hcaptcha",
            "plone.formwidget.recaptcha",
            "collective.z3cform.norobots",
            "collective.honeypot",
            "collective.volto.otp",
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = collective.volto.formsupport.locales.update:update_locale
    formsupport_data_cleansing = collective.volto.formsupport.scripts.cleansing:main
    """,
)

.. image:: https://img.shields.io/pypi/v/collective.volto.formsupport.svg
    :target: https://pypi.python.org/pypi/collective.volto.formsupport/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/status/collective.volto.formsupport.svg
    :target: https://pypi.python.org/pypi/collective.volto.formsupport
    :alt: Egg Status

.. image:: https://img.shields.io/pypi/pyversions/collective.volto.formsupport.svg?style=plastic   :alt: Supported - Python Versions

.. image:: https://img.shields.io/pypi/l/collective.volto.formsupport.svg
    :target: https://pypi.python.org/pypi/collective.volto.formsupport/
    :alt: License

.. image:: https://coveralls.io/repos/github/collective/collective.volto.formsupport/badge.svg
    :target: https://coveralls.io/github/collective/collective.volto.formsupport
    :alt: Coverage


============================
collective.volto.formsupport
============================

Add some helper routes and functionalities for Volto sites with ``form`` blocks provided by `volto-form-block <https://github.com/collective/volto-form-block>`_ Volto plugin.

plone.restapi endpoints
=======================

@submit-form
------------

Endpoint that the frontend should call as a submit action.

You can call it with a POST on the context where the block form is stored like this::

> curl -i -X POST http://localhost:8080/Plone/my-form/@submit-form -H 'Accept: application/json' -H 'Content-Type: application/json' --data-raw '{"block_id": "123456789", "data": [{"field_id": "foo", "value":"foo", "label": "Foo"},{"field_id": "from", "value": "support@foo.com"}, {"field_id":"name", "value": "John Doe", "label": "Name"}]}'

where:

- ``my-form`` is the context where we have a form block
- ``block_id`` is the id of the block
- ``data`` contains the submitted form data

Calling this endpoint, it will do some actions (based on block settings) and returns a ``204`` response.


@form-data
----------

This is an expansion component.

There is a rule that returns a ``form-data`` item into "components" slot if the user can edit the
context (**Modify portal content** permission) and there is a block that can store data.

Calling with "expand=true", this endpoint returns the stored data::

> curl -i -X GET http://localhost:8080/Plone/my-form/@form-data -H 'Accept: application/json' -H 'Content-Type: application/json' --user admin:admin


And replies with something similar::

    {
        "@id": "http://localhost:8080/Plone/my-form/@form-data",
        "items": [
            {
            "block_id": "123456789",
            "date": "2021-03-10T12:25:24",
            "from": "support@foo.com",
            "id": 912078826,
            "name": "John Doe"
            },
            ...
        ],
        "items_total": 42
    }

@form-data-export
-----------------

Returns a csv file with all data (only for users that have **Modify portal content** permission)::

> curl -i -X GET http://localhost:8080/Plone/my-form/@form-data-export -H 'Accept: application/json' -H 'Content-Type: application/json' --user admin:admin

If form fields changed between some submissions, you will see also columns related to old fields.

@form-data-clear
----------------

Reset the store (only for users that have **Modify portal content** permission)::

> curl -i -X GET http://localhost:8080/Plone/my-form/@form-data-clear -H 'Accept: application/json' -H 'Content-Type: application/json' --user admin:admin


Form actions
============

Using `volto-form-block <https://github.com/collective/volto-form-block>`_ you can set if the form submit should send data to an email address
or store it into an internal catalog (or both).

Send
----

If block is set to send data, an email with form data will be sent to the recipient set in block settings or (if not set) to the site address.

If ther is an ``attachments`` field in the POST data, these files will be attached to the emal sent.

Store
-----

If block is set to store data, we store it into the content that has that block (with a `souper.plone <https://pypi.org/project/souper.plone>`_ catalog).

The store is an adapter registered for *IFormDataStore* interface, so you can override it easily.

Only fields that are also in block settings are stored. Missing ones will be skipped.

Each Record stores also two *service* attributes:

- **fields_labels**: a mapping of field ids to field labels. This is useful when we export csv files, so we can labels for the columns.
- **fields_order**: sorted list of field ids. This can be used in csv export to keep the order of fields.

We store these attributes because the form can change over time and we want to have a snapshot of the fields in the Record.

Block serializer
================

There is a custom block serializer for type ``form``.

This serializer removes all fields that start with "\**default_**\" if the user can't edit the current context.

This is useful because we don't want to expose some internals configurations (for example the recipient email address)
to external users that should only fill the form.

If the block has a field ``captcha``, an additional property ``captcha_props`` is serialized by the ``serialize``
method provided by the ICaptchaSupport named adapter, the result contains useful metadata for the client, as the
captcha public_key, ie::

    {
        "subblocks": [
            ...
        ],
        "captcha": "recaptcha",
        "captcha_props": {
            "provider": "recaptcha",
            "public_key": "aaaaaaaaaaaaa"
        }
    }

Captcha support
===============

Captcha support requires a specific name adapter that implements ``ICaptchaSupport``.
This product contains implementations for:

- HCaptcha (plone.formwidget.hcaptcha)
- Google ReCaptcha (plone.formwidget.recaptcha)
- Custom questions and answers (collective.z3cform.norobots)
- Honeypot (collective.honeypot)


Each implementation must be included, installed and configured separately.

To include one implementation, you need to install the egg with the needed extras_require:

- collective.volto.formsupport[recaptcha]
- collective.volto.formsupport[hcaptcha]
- collective.volto.formsupport[norobots]
- collective.volto.formsupport[honeypot]

During the form post, the token captcha will be verified with the defined captcha method.

For captcha support `volto-form-block` version >= 2.4.0 is required.

Honeypot configuration
----------------------

If honeypot dependency is available in the buildout, the honeypot validation is enabled and selectable in forms.

Default field name is `protected_1` and you can change it with an environment variable. See `collective.honeypot <https://github.com/collective/collective.honeypot#id7>`_ for details.

Attachments upload limits
=========================

Forms can have one or more attachment field to allow users to upload some files.

These files will be sent via mail, so it could be a good idea setting a limit to them.
For example if you use Gmail as mail server, you can't send messages with attachments > 25MB.

There is an environment variable that you can use to set that limit (in MB)::

    [instance]
    environment-vars =
        FORM_ATTACHMENTS_LIMIT 25

By default this is not set.

The upload limit is also passed to the frontend in the form data with the `attachments_limit` key.

Examples
========

This add-on can be seen in action at the following sites:

- https://www.comune.modena.it/form/contatti


Translations
============

This product has been translated into

- Italian


Installation
============

Install collective.volto.formsupport by adding it to your buildout::

    [buildout]

    ...

    eggs =
        collective.volto.formsupport


and then running ``bin/buildout``


Contribute
==========

- Issue Tracker: https://github.com/collective/collective.volto.formsupport/issues
- Source Code: https://github.com/collective/collective.volto.formsupport


License
=======

The project is licensed under the GPLv2.

Authors
=======

This product was developed by **RedTurtle Technology** team.

.. image:: https://avatars1.githubusercontent.com/u/1087171?s=100&v=4
   :alt: RedTurtle Technology Site
   :target: https://www.redturtle.it/

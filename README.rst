.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

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


============================
collective.volto.formsupport
============================

Add some helper routes and functionalities for Volto sites with `form` blocks provided by `INSERT_VOLTO_PLUGIN_NAME_HERE` Volto plugin.

plone.restapi endpoints
=======================

@submit-form
------------

Endpoint that the frontend should call as a submit action.

You can call it with a POST on the context where the block form is stored like this::

> curl -i -X POST http://localhost:8080/Plone/my-form/@submit-form -H 'Accept: application/json' -H 'Content-Type: application/json' --data-raw '{"block_id": "123456789", "data": [{"field_id": "foo", "value":"foo", "label": "Foo"},{"field_id": "from", "value": "support@foo.com"}, {"field_id":"name", "value": "John Doe", "label": "Name"}]}'

where:

- `my-form`is the context where we have a form block
- `block_id` is the id of the block
- `data` contains the submitted form data

Calling this endpoint, it will do some actions (based on block settings) and returns a `204` response.


@form-data
----------

Returns the stored data (only for users that have "Modify portal content" permission)::

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

Returns a csv file with all data (only for users that have "Modify portal content" permission)::

> curl -i -X GET http://localhost:8080/Plone/my-form/@form-data-export -H 'Accept: application/json' -H 'Content-Type: application/json' --user admin:admin

If form fields changed between some submissions, you will see also columns related to old fields.

@form-data-clear
----------------

Reset the store (only for users that have "Modify portal content" permission)::

> curl -i -X GET http://localhost:8080/Plone/my-form/@form-data-clear -H 'Accept: application/json' -H 'Content-Type: application/json' --user admin:admin


Form actions
============

Using `INSERT_VOLTO_PLUGIN_NAME_HERE` you can set if the form submit should send data to an email address
or store it into an internal catalog (or both).

Send
----

If block is set to send data, an email with form data will be sent to the recipient set in block settings or (if not set) to the site address.

Store
-----

If block is set to store data, we store it into the content that has that block (with a `souper.plone https://pypi.org/project/souper.plone`_ catalog).

The store is an adapter registered for `IFormDataStore` interface, so you can override it easily.

Only fields that are also in block settings are stored. Missing ones will be skipped.

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
   :target: http://www.redturtle.it/

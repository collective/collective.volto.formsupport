Changelog
=========

2.0.3 (2021-10-25)
------------------

- Fix permission checks in serializer.
  [nzambello]


2.0.2 (2021-10-25)
------------------

- Fix permission checks.
  [cekk]


2.0.1 (2021-10-18)
------------------

- [fix] do not send attachments multiple times.
  [cekk]


2.0.0 (2021-08-19)
------------------

- Convert field types: checkbox => multiple_choice and radio => single_choice
  to follow new schema in volto-form-block (https://github.com/collective/volto-form-block/pull/7).
  [cekk]


1.0.5 (2021-05-12)
------------------

- Added Brazilian Portuguese (pt_BR) translations.
  [ericof]


1.0.4 (2021-04-15)
------------------

- Changed the classifiers inside setup.py. This should fix some installation
  issues.
  [arsenico13]


1.0.3 (2021-04-08)
------------------

- NEW: The @submit-form entry-point now takes into account if a field is "marked"
  with "use_as_reply_to" and use that field for "from" and "reply to".
  [arsenico13]


1.0.2 (2021-03-24)
------------------

- Fix form_data for anon.
  [cekk]

1.0.1 (2021-03-24)
------------------

- Fix README for pypi.
  [cekk]


1.0.0 (2021-03-24)
------------------

- Initial release.
  [cekk]

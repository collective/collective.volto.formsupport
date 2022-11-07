Changelog
=========

2.6.2 (2022-11-07)
------------------

- Fix collective.honeypot version.
  [cekk]

2.6.1 (2022-11-07)
------------------

- Fix dependencies.
  [cekk]

2.6.0 (2022-11-07)
------------------

- Add collective.honeypot support.
  [cekk]


2.5.0 (2022-10-04)
------------------

- Add limit attachments validation. Can be configured with environment variable.
  [cekk]
- Export also compiling date in csv.
  [cekk]

2.4.0 (2022-09-08)
------------------

- Add collective.z3cform.norobots support
  [erral]

2.3.0 (2022-05-26)
------------------

- Breaking change: changed the way to store data keys. Now we use field_id as key for Records.
  [cekk]
- Fix quoting in csv export.
  [cekk]
- Generate csv columns with proper field labels, and keep the form order.
  [cekk]
- Captcha support #13.
  [mamico]


2.2.0 (2022-04-07)
------------------

- Notify an event on sumbit.
  [mamico]


2.1.0 (2022-03-25)
------------------

- Support for user_as_bcc field in volto-form-block: send a separate mail for each email field with that flag.
  [cekk]


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

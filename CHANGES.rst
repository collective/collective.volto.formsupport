Changelog
=========

3.2.3 (2025-03-07)
------------------

- Now in the CSV export the obsolete records fields are ordered
  alphabetically after the current form fields.
  [folix-01]

- Add current form columns to CSV export event if field are empty.
  [folix-01]


3.2.2 (2025-03-05)
------------------

- Format list values in format_fields as comma separated strings to improve readability on email messages.
  [cekk]


3.2.1 (2025-01-09)
------------------

- Adapt email subject templating functionality to different value types.
  [folix-01]


3.2.0 (2024-11-15)
------------------

- Added an adapter (`IDataAdapter`) to allow information to be added as a return value
  to the form-data expander. This allows addons that integrate information to be added
  rather than overwriting the expander each time.
  [mamico]

- Add FormSubmittedEvent to handle the new compiled forms.
  [folix-01]

- Add PostAdapter to predispose the customization of data handling by other add-ons.
  [folix-01]


3.1.5 (2024-10-24)
------------------

- Fix otp verification logic: do not break if otp is not in POST call
  [cekk]


3.1.4 (2024-09-27)
------------------

- Add missing collective.volto.otp include for pip environment setup
  [folix-01]

- Switchable email bcc fields OTP verification.
  [folix-01]

- Added ISO formatted strings being allowed as date inputs
  [JeffersonBledsoe]


3.1.3 (2024-09-11)
------------------

- Send messages to emails signed as 'use_as_bcc' independently from 'send' flag.
  [folix-01]

- Update Italian translations.
  [cekk]


3.1.2 (2024-08-08)
------------------

- Fix upgradestep from version.
  [folix-01]


3.1.1 (2024-08-08)
------------------

- Fix mail header and footer links.
  [folix-01]
- Plone5 compatibility in the upgradesteps
  [folix-01]
- Install otp package by upgradestep
  [folix-01]
- Maintain the fields order in email message.
  [folix-01]
- Remove otp logics (moved to collective.volto.otp)
  [folix-01]

3.1.0 (2024-07-04)
------------------

- Configurable header and footer for email message.
  [folix-01]
- Subject templating
- Handle the edge cases where the `blocks` attribute is not set.
  [mamico]
- Configuring with plone/meta
  [mamico]


3.0.2 (2024-05-05)
------------------

- Cleanup all possible HTML in user formitted data and convert it to plain text.
  [cekk]


3.0.1 (2024-04-18)
------------------

- Fix README.
  [cekk]


3.0.0 (2024-04-18)
------------------

- Add functionality to check the user inserted email by an OTP.
  [folix-01]
- Breaking change: clear data method changed from GET to DELETE
  [mamico]
- Fix: with multiple blocks on the same page, all data is deleted.
  Now, if you pass a parameter block_id, only the records related to the
  block are deleted.
  [mamico]
- Feat: clear data restapi accept a parameter for remove the expired records
  [mamico]
- data cleaning script
  [mamico]
- Allow attaching an XML version of the form data to the sent email #22
  [JeffersonBledsoe]
- Allow the IDs of fields to be customised for CSV download and XML attaachments #22
  [JeffersonBledsoe]
- Add Spanish translation.
  [macagua]
- Add German translation.
  [mbarde]
- Allow forwarding request headers in the sent emails #27
  [JeffersonBledsoe]
- Added support for sending emails as a table #31
  [JeffersonBledsoe]
- Add validation for email fields.
  [cekk]
- Better compose email message with plain and html text.
  [cekk]
- Prevent XSS applying safe_html transform to all string values passed on form.
  [cekk]
- Discard fields submitted that are not defined in form schema.
  [cekk]
- On form submit, reply with a 200 with submitted data (eventually cleaned) for confirm message.
  [cekk]
- Fix label in send_mail_template.
  [cekk]
- Prevent XSS also in send_message field.
  [cekk]

2.7.0 (2023-04-03)
------------------

- Override content-transfer-encoding using `MAIL_CONTENT_TRANSFER_ENCODING` env
  [mamico]
- The form block can now be stored in a Volto block container (columns,
  accordion, tabs, etc)
  [tiberiuichim]


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

- Notify an event on submit.
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

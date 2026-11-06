# collective.volto.formsupport

Add helper routes and functionality for Volto sites using the `form` block
provided by [volto-form-block](https://github.com/collective/volto-form-block).
The supported `volto-form-block` version is 3.13.0 or later.

## Installation

Clone this repository and install the development environment:

```shell
git clone git@github.com:collective/collective.volto.formsupport.git
cd collective.volto.formsupport
make install
```

## REST API

### `@submit-form`

Submit form data to the context containing the form block:

```shell
curl -i -X POST http://localhost:8080/Plone/my-form/@submit-form \
    -H 'Accept: application/json' -H 'Content-Type: application/json' \
    --data '{"block_id":"123456789","data":[{"field_id":"name","value":"Jane Doe"}]}'
```

`block_id` identifies the form block and `data` contains the submitted fields.
The endpoint validates and cleans submitted values, then performs the actions
configured on the block: sending an email, storing the submission, or both.
Form attachments can be emailed and optionally stored as blobs.

### `@form-data`

Users with `Modify portal content` permission can retrieve stored submissions.
The response includes `items`, `items_total`, and `expired_total`. Use
`block_id` to select a form on a page. Optional `start_date` and `end_date`
parameters filter submissions by date; date-only end dates include the full
day.

Pagination is enabled when both `b_size` and `b_start` are supplied. The
response then includes `batching` links and `items_total` reflects the filtered
result count.

### `@form-data-export` and `@form-data-clear`

`@form-data-export` downloads stored submissions as CSV. Current form fields
are listed first, followed by legacy fields and fixed columns. Access requires
`Modify portal content`.

`@form-data-clear` deletes stored submissions. Its payload can include
`block_id` to restrict the operation to one form, and `expired: true` to
remove only submissions older than the retention period configured on that
block.

## Form actions

Forms can send submissions to configured recipients or the site address.
Acknowledgement emails can be sent to a submitted address. Optional XML
attachments follow the format used by `collective.easyform`.

For stored data, only fields defined in the block are saved. The
`IFormDataStore` adapter can be overridden by integrations. Stored attachments
are available through the `saved_data/@@download` view to users who can edit
the context. The CSV export supports custom field labels and preserves the
field order captured with each submission.

## Captcha and honeypot support

Captcha implementations are provided for:

- [hCaptcha](https://github.com/plone/plone.formwidget.hcaptcha)
- [Google reCAPTCHA](https://github.com/plone/plone.formwidget.recaptcha)
- [Custom questions](https://github.com/collective/collective.z3cform.norobots)
- [Honeypot](https://github.com/collective/collective.honeypot)

Install the corresponding package extra: `hcaptcha`, `recaptcha`, `norobots`,
or `honeypot`. For attachment size limits, set `FORM_ATTACHMENTS_LIMIT` to a
size in megabytes.

## Development

Run the test suite with `make test`. This repository follows the
[Cookieplone development workflow](https://6.docs.plone.org/install/create-project-cookieplone.html).
Issues and source are available on the
[project GitHub page](https://github.com/collective/collective.volto.formsupport).

## License

GPLv2.

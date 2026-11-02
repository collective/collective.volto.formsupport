"""Single-use form tokens with a minimum age, for every form.

The tokens come from plone.restapi (``plone.restapi.form_token``): its
``@form-token`` endpoint issues them, and ``@submit-form`` checks them here,
next to the captcha of the form, if it has one.

They are only enabled when plone.restapi has form tokens and they are
configured, see "Form tokens" in the README.  Otherwise forms work as before,
without tokens.
"""

try:
    from plone.restapi import form_token as restapi_form_token
except ImportError:
    # plone.restapi without form tokens.
    restapi_form_token = None


def is_enabled():
    return restapi_form_token is not None and restapi_form_token.is_enabled()


def get_min_age():
    return restapi_form_token.get_min_age()


def verify_token(context, request, block_id, token):
    """Raise BadRequest unless the token of the submission is valid."""
    form = "{} block={}".format("/".join(context.getPhysicalPath()), block_id)
    restapi_form_token.verify_token(request, token, form)

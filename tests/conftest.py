from collective.volto.formsupport.testing import (
    VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING,
)
from collective.volto.formsupport.testing import VOLTO_FORMSUPPORT_FUNCTIONAL_TESTING
from collective.volto.formsupport.testing import VOLTO_FORMSUPPORT_INTEGRATION_TESTING
from pytest_plone import fixtures_factory


pytest_plugins = ["pytest_plone"]


globals().update(
    fixtures_factory((
        (VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING, "functional"),
        (VOLTO_FORMSUPPORT_FUNCTIONAL_TESTING, "functional_basic"),
        (VOLTO_FORMSUPPORT_INTEGRATION_TESTING, "integration"),
    ))
)

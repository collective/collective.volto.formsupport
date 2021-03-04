# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import (
    applyProfile,
    FunctionalTesting,
    IntegrationTesting,
    PloneSandboxLayer,
)
from plone.testing import z2

import collective.volto.formsupport


class CollectiveVoltoFormsupportLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.restapi
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.volto.formsupport)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.volto.formsupport:default')


COLLECTIVE_VOLTO_FORMSUPPORT_FIXTURE = CollectiveVoltoFormsupportLayer()


COLLECTIVE_VOLTO_FORMSUPPORT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_VOLTO_FORMSUPPORT_FIXTURE,),
    name='CollectiveVoltoFormsupportLayer:IntegrationTesting',
)


COLLECTIVE_VOLTO_FORMSUPPORT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_VOLTO_FORMSUPPORT_FIXTURE,),
    name='CollectiveVoltoFormsupportLayer:FunctionalTesting',
)


COLLECTIVE_VOLTO_FORMSUPPORT_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        COLLECTIVE_VOLTO_FORMSUPPORT_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='CollectiveVoltoFormsupportLayer:AcceptanceTesting',
)

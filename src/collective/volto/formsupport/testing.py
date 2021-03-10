# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import (
    applyProfile,
    FunctionalTesting,
    IntegrationTesting,
    PloneSandboxLayer,
    quickInstallProduct,
)
from plone.restapi.testing import PloneRestApiDXLayer
from plone.testing import z2

import collective.MockMailHost
import collective.volto.formsupport
import plone.restapi


class VoltoFormsupportLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.volto.formsupport)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.restapi:blocks")
        applyProfile(portal, "collective.volto.formsupport:default")


VOLTO_FORMSUPPORT_FIXTURE = VoltoFormsupportLayer()


VOLTO_FORMSUPPORT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(VOLTO_FORMSUPPORT_FIXTURE,),
    name="VoltoFormsupportLayer:IntegrationTesting",
)


VOLTO_FORMSUPPORT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(VOLTO_FORMSUPPORT_FIXTURE,),
    name="VoltoFormsupportLayer:FunctionalTesting",
)


class VoltoFormsupportRestApiLayer(PloneRestApiDXLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        super(VoltoFormsupportRestApiLayer, self).setUpZope(
            app, configurationContext
        )
        self.loadZCML(package=collective.MockMailHost)
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.volto.formsupport)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "collective.volto.formsupport:default")
        applyProfile(portal, "plone.restapi:blocks")
        quickInstallProduct(portal, "collective.MockMailHost")
        applyProfile(portal, "collective.MockMailHost:default")


VOLTO_FORMSUPPORT_API_FIXTURE = VoltoFormsupportRestApiLayer()
VOLTO_FORMSUPPORT_API_INTEGRATION_TESTING = IntegrationTesting(
    bases=(VOLTO_FORMSUPPORT_API_FIXTURE,),
    name="VoltoFormsupportRestApiLayer:Integration",
)

VOLTO_FORMSUPPORT_API_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(VOLTO_FORMSUPPORT_API_FIXTURE, z2.ZSERVER_FIXTURE),
    name="VoltoFormsupportRestApiLayer:Functional",
)

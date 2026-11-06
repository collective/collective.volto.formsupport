"""Init and utils."""

from zope.i18nmessageid import MessageFactory

import logging


__version__ = "4.0.0.dev0"

PACKAGE_NAME = "collective.volto.formsupport"

_ = MessageFactory(PACKAGE_NAME)

logger = logging.getLogger(PACKAGE_NAME)

from zope.interface import Attribute
from zope.interface import Interface
from zope.interface.interfaces import IObjectEvent
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class ICollectiveVoltoFormsupportLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IFormDataStore(Interface):
    def add(data):
        """
        Add data to the store

        @return: record id
        """

    def length():
        """
        @return: number of items stored into store
        """

    def search(query):
        """
        @return: items that match query
        """


class IPostEvent(Interface):
    """
    Event fired when a form is submitted (before actions)
    """


class ICaptchaSupport(Interface):
    def __init__(context, request):
        """Initialize adapter"""

    def is_enabled():
        """Captcha method enabled
        @return: True if the method is enabled/configured
        """

    def verify(data):
        """Verify the captcha
        @return: True if verified, Raise exception otherwise
        """


class IFormSubmittedEvent(IObjectEvent):
    """An event that's fired upon a workflow transition."""

    obj = Attribute("The context object")

    form = Attribute("Form")
    form_data = Attribute("Form Data")


class IPostAdapter(Interface):
    def data():
        pass


# BBB
IFormData = IPostAdapter


class IDataAdapter(Interface):
    def __call__(result, block_id=None):
        pass

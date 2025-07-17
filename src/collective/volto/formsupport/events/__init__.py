from collective.volto.formsupport.interfaces import IFormSubmittedEvent
from zope.interface import implementer
from zope.interface.interfaces import ObjectEvent


@implementer(IFormSubmittedEvent)
class FormSubmittedEvent(ObjectEvent):
    def __init__(self, obj, form, form_data):
        super().__init__(obj)
        self.form = form
        self.form_data = form_data

from zope import interface

from Solgema.fullcalendar import interfaces
from Solgema.fullcalendar import options

SolgemaFullcalendarPropertiesStorage = options.PersistentOptions.wire( "SolgemaFullcalendarPropertiesStorage", "Solgema.fullcalendar.storage", interfaces.ISolgemaFullcalendarProperties )

class SolgemaFullcalendarAdapter(SolgemaFullcalendarPropertiesStorage):
    interface.implements(interfaces.ISolgemaFullcalendarProperties)

    def __init__( self, context ):
        self.context = context


SFBaseEventStorage = options.PersistentOptions.wire( "SFBaseEventStorage", "Solgema.fullcalendar.baseEvent_storage", interfaces.ISFBaseEventFields )

class SFBaseEventAdapter(SFBaseEventStorage):
    interface.implements(interfaces.ISFBaseEventFields)

    def __init__( self, context ):
        self.context = context

    @property
    def isSolgemaFullcalendar(self):
        return getattr(self.context, 'layout', None) == 'solgemafullcalendar_view'

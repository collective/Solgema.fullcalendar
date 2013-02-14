from zope import interface
try:
    import plone.app.event
    from plone.event.interfaces import IEventAccessor, IEvent
    HAS_PAE = True
except ImportError:
    HAS_PAE = False

from Solgema.fullcalendar import interfaces
from Solgema.fullcalendar import options


SolgemaFullcalendarPropertiesStorage = options.PersistentOptions.wire(
    "SolgemaFullcalendarPropertiesStorage",
    "Solgema.fullcalendar.storage",
    interfaces.ISolgemaFullcalendarProperties)

class SolgemaFullcalendarAdapter(SolgemaFullcalendarPropertiesStorage):
    interface.implements(interfaces.ISolgemaFullcalendarProperties)

    def __init__( self, context ):
        self.context = context


SFBaseEventStorage = options.PersistentOptions.wire(
    "SFBaseEventStorage",
    "Solgema.fullcalendar.baseEvent_storage",
    interfaces.ISFBaseEventFields)

class SFBaseEventAdapter(SFBaseEventStorage):
    interface.implements(interfaces.ISFBaseEventFields)

    def __init__( self, context ):
        self.context = context
        self._all_day = None

    def _allDay(self):
        if HAS_PAE:
            if IEvent.providedBy(self.context):
                acc = IEventAccessor(self.context)
                return acc.whole_day or False
        if self._all_day is not None:
            return bool(self._all_day)
        return False

    def set_allDay(self, v):
        v = bool(v)
        if HAS_PAE:
            if IEvent.providedBy(self.context):
                acc = IEventAccessor(self.context)
                acc.whole_day = v
                return
        self._all_day = v

    allDay = property(_allDay, set_allDay)

    @property
    def isSolgemaFullcalendar(self):
        return getattr(self.context, 'layout', None) == 'solgemafullcalendar_view'

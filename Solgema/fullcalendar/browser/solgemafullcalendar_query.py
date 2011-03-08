from Acquisition import aq_base, aq_inner, aq_parent
from plone.app.layout.viewlets.common import ViewletBase
from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarProperties
from Solgema.fullcalendar.browser.solgemafullcalendar_views import listQueryTopicCriteria

class SolgemaFullcalendarQuery(ViewletBase):

    def __init__(self, *args, **kwargs):
        super(SolgemaFullcalendarQuery, self).__init__(*args, **kwargs)
        self.calendar = ISolgemaFullcalendarProperties(aq_inner(self.context), None)

    def listQueryTopicCriteria(self):
        return listQueryTopicCriteria(self.context)

    def displayUndefined(self):
        return getattr(self.calendar, 'displayUndefined', False)

    def getCookieItems(self, field):
        item = self.request.cookies.get(field,None)
        if item:
            items = item.find('+') == -1 and item or item.split('+')
            #it seems that sometimes it's utf-8 encoded and sometimes iso-8859-1.....
            if isinstance(items, (list, tuple)):
                try:
                    items = [a.decode('iso-8859-1') for a in items]
                except:
                    pass
                try:
                    items = [a.decode('utf-8') for a in items]
                except:
                    pass
                items = [a.encode('utf-8') for a in items]
            else:
                try:
                    items = items.decode('iso-8859-1')
                except:
                    pass
                try:
                    items = items.decode('utf-8')
                except:
                    pass
                items = items.encode('utf-8')
            return items
        return None

from Acquisition import aq_inner

from plone.app.layout.viewlets.common import ViewletBase
from Products.CMFCore.utils import getToolByName

from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarProperties
from Solgema.fullcalendar.browser.views import listQueryTopicCriteria, getCookieItems


class SolgemaFullcalendarQuery(ViewletBase):

    def __init__(self, *args, **kwargs):
        super(SolgemaFullcalendarQuery, self).__init__(*args, **kwargs)
        self.calendar = ISolgemaFullcalendarProperties(aq_inner(self.context), None)

    def listQueryTopicCriteria(self):
        return listQueryTopicCriteria(self.context)

    def displayUndefined(self):
        return getattr(self.calendar, 'displayUndefined', False)

    def getCookieItems(self, field):
        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'
        return getCookieItems(self.request, field, charset)

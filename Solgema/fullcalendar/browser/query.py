from Acquisition import aq_inner
from zope import component
from plone.app.layout.viewlets.common import ViewletBase
from Products.CMFCore.utils import getToolByName

from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarProperties
from Solgema.fullcalendar.browser.views import listQueryTopicCriteria, getCookieItems
from zope.schema.interfaces import IVocabularyFactory

class SolgemaFullcalendarTopicQuery(ViewletBase):

    def __init__(self, *args, **kwargs):
        super(SolgemaFullcalendarTopicQuery, self).__init__(*args, **kwargs)
        self.calendar = ISolgemaFullcalendarProperties(aq_inner(self.context), None)

    def listQueryTopicCriteria(self):
        return listQueryTopicCriteria(self.context)

    def displayUndefined(self):
        return getattr(self.calendar, 'displayUndefined', False)

    def getCookieItems(self, field):
        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'
        return getCookieItems(self.request, field, charset)

class SolgemaFullcalendarFolderQuery(ViewletBase):

    def __init__(self, *args, **kwargs):
        super(SolgemaFullcalendarFolderQuery, self).__init__(*args, **kwargs)
        self.calendar = ISolgemaFullcalendarProperties(aq_inner(self.context), None)

    def availableSubFolders(self):
        voc = component.getUtility(IVocabularyFactory, name=u'solgemafullcalendar.availableSubFolders', context=self.context)(self.context)
        return [(a, voc.getTerm(a).title) for a in getattr(self.calendar, 'availableSubFolders', [])]

    def getCookieItems(self, field):
        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'
        return getCookieItems(self.request, field, charset)

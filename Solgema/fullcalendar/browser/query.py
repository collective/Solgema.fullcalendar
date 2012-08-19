from Acquisition import aq_inner
from zope import component
from plone.app.layout.viewlets.common import ViewletBase
from Products.CMFCore.utils import getToolByName

from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarProperties, IListCriterias
from Solgema.fullcalendar.browser.views import getCookieItems
from zope.schema.interfaces import IVocabularyFactory

class SolgemaFullcalendarTopicQuery(ViewletBase):

    def __init__(self, *args, **kwargs):
        super(SolgemaFullcalendarTopicQuery, self).__init__(*args, **kwargs)
        self.calendar = ISolgemaFullcalendarProperties(aq_inner(self.context), None)

    def listQueryTopicCriteria(self):
        li = []
        for criteria in self.context.listCriteria():
            if criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion'] \
                    and criteria.getCriteriaItems() \
                    and len(criteria.getCriteriaItems()[0]) > 1 \
                    and len(criteria.getCriteriaItems()[0][1]['query']) > 0:
                li.append(criteria)

        if hasattr(self.calendar, 'availableCriterias') and getattr(self.calendar, 'availableCriterias', None) != None:
            li = [a for a in li if a.Field() in self.calendar.availableCriterias]

        return li

    def displayUndefined(self):
        return getattr(self.calendar, 'displayUndefined', False)

    def getCookieItems(self, field):
        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'
        return getCookieItems(self.request, field, charset)

class SolgemaFullcalendarCollectionQuery(SolgemaFullcalendarTopicQuery):

    def listQueryTopicCriteria(self):
        li = []
        for a in self.context.getField('query').getRaw(self.context):
            if a['o'] in ['plone.app.querystring.operation.selection.is', 'plone.app.querystring.operation.list.contains'] \
                    and a['i'] != 'portal_type' and len(a['v'])>0:
                li.append(a)

        if hasattr(self.calendar, 'availableCriterias') and getattr(self.calendar, 'availableCriterias', None) != None:
            li = [a for a in li if a['i'] in self.calendar.availableCriterias]

        return li

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

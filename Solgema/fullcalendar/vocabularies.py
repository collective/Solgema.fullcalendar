from zope.schema import vocabulary
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneLocalesMessageFactory as PLMF

from Solgema.fullcalendar.config import _


class TitledVocabulary(vocabulary.SimpleVocabulary):
    def fromTitles(cls, items, *interfaces):
        terms = [cls.createTerm(value,value,title) for (value,title) in items]
        return cls(terms, *interfaces)
    fromTitles = classmethod(fromTitles)

    def getTerm(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        try:
            return self.by_value[value]
        except KeyError:
            return vocabulary.SimpleVocabulary.createTerm('','','')

    def getTermByToken(self, token):
        """See zope.schema.interfaces.IVocabularyTokenized"""
        try:
            return self.by_token[token]
        except KeyError:
            return vocabulary.SimpleVocabulary.createTerm('','','')

def availableViews( context ):
    voc = [('month', _('Month', default='Month')),
           ('basicWeek', _('basicWeek', default='basicWeek')),
           ('basicDay', _('basicDay', default='basicDay')),
           ('agendaWeek', _('agendaWeek', default='agendaWeek')),
           ('agendaDay', _('agendaDay', default='agendaDay')),
           ('agendaDaySplit', _('agendaDaySplit', default='Day Split'))
          ]
    return TitledVocabulary.fromTitles( voc )

def daysOfWeek( context ):
    ts = getToolByName(context, 'translation_service')
    return TitledVocabulary.fromTitles([(d, PLMF(ts.day_msgid(d), default=ts.weekday_english(d))) for d in range(7)])

def dayHours( context ):
    return TitledVocabulary.fromTitles([(a, a<10 and '0'+str(a)+':00' or str(a)+':00') for a in range(25)])

def availableCriterias( topic ):
    li = []
    portal_atct = getToolByName(topic, 'portal_atct')
    for criteria in topic.listCriteria():
        field = criteria.Field()
        if criteria.meta_type=='ATPortalTypeCriterion' and len(criteria.getCriteriaItems()[0][1])>0:
            index = portal_atct.getIndex(field).friendlyName or portal_atct.getIndex(field).index
            li.append({'id':field, 'title':topic.translate(index)})
        elif criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion'] and criteria.getCriteriaItems() and len(criteria.getCriteriaItems()[0])>1 and len(criteria.getCriteriaItems()[0][1]['query'])>0:
            index = portal_atct.getIndex(field).friendlyName or portal_atct.getIndex(field).index
            li.append({'id':field, 'title':topic.translate(index)})

    return TitledVocabulary.fromTitles([(crit['id'], crit['title']) for crit in li])

def availableSubFolders( context ):
    folderContents = context.getFolderContents(contentFilter={'portal_type':'Folder'})
    return TitledVocabulary.fromTitles([(a.getId, a.Title) for a in folderContents])
    
def shortNameFormats(context):
    return TitledVocabulary.fromTitles([('a', _(u'abbreviated', default='abbreviated')),
                                        ('s', _(u'short', default='short'))])

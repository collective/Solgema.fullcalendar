import logging
import datetime
from urllib import unquote
try:
    import json
except:
    import simplejson as json

from OFS import CopySupport
from Acquisition import aq_inner, aq_parent
from zope.interface import implements
from zope import component
from zope.component import getMultiAdapter, getAdapters
from zope.i18nmessageid import MessageFactory
from zope.schema.interfaces import IVocabularyFactory
from plone.i18n.normalizer.interfaces import IURLNormalizer

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneLocalesMessageFactory as PLMF
from Products.CMFPlone import utils as CMFPloneUtils
from Products.CMFPlone.utils import safe_unicode 
from Products.ATContentTypes.interface import IATTopic, IATFolder

from Solgema.fullcalendar.config import _
from Solgema.fullcalendar import interfaces
from Solgema.fullcalendar import log

LOG = logging.getLogger('Solgema.fullcalendar')

DTMF = MessageFactory('collective.z3cform.datetimewidget')
pMF = MessageFactory('plone')

def getCopyObjectsUID(REQUEST):
    if REQUEST is not None and REQUEST.has_key('__cp'):
        cp = REQUEST['__cp']
    else:
        return []

    op, mdatas = CopySupport._cb_decode(cp)
    return {'op': op, 'url': ['/'.join(a) for a in mdatas][0]}


def listBaseQueryTopicCriteria(topic):
    li = []
    for criteria in topic.listCriteria():
        if criteria.meta_type == 'ATPortalTypeCriterion' \
                and len(criteria.getCriteriaItems()[0][1]) > 0:
            li.append(criteria)
        if criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion'] \
                and criteria.getCriteriaItems() \
                and len(criteria.getCriteriaItems()[0]) > 1 \
                and len(criteria.getCriteriaItems()[0][1]['query']) > 0:
            li.append(criteria)

    return li


def listQueryTopicCriteria(topic):
    calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(topic), None)
    li = listBaseQueryTopicCriteria(topic)
    for criteria in li:
        if criteria.meta_type=='ATPortalTypeCriterion' and len(criteria.getCriteriaItems()[0][1])==1:
            li.remove(criteria)

    if hasattr(calendar, 'availableCriterias') and getattr(calendar, 'availableCriterias', None) != None:
        li = [a for a in li if a.Field() in calendar.availableCriterias]

    return li


def getTopic(context, request):
    if not interfaces.ISolgemaFullcalendarMarker.providedBy(context):
        utils = getToolByName(context, 'plone_utils')
        page = utils.getDefaultPage(context, request)
        pageItem = page and getattr(context, page) or None
        if interfaces.ISolgemaFullcalendarMarker.providedBy(pageItem):
            return pageItem

        portal = getToolByName(context, 'portal_url').getPortalObject()
        referer = unquote(request.get('last_referer', request.get('HTTP_REFERER')))
        if referer.find('?')!=-1:
            referer = referer[:referer.index('?')]

        if referer[-5:] == '/view':
            referer = referer[:-5]

        if referer[-1:] == '/':
            referer = referer[:-1]

        portal_url = portal.absolute_url()
        topic_url = referer.replace(portal_url, '')
        topic_path = '/'.join(portal.getPhysicalPath()) + topic_url
        topic = portal.restrictedTraverse(topic_path)
        if utils.getDefaultPage(topic, request):
            page = utils.getDefaultPage(topic, request)
            topic_url = topic_url+'/'+page
            topic = getattr(topic, page)
            if interfaces.ISolgemaFullcalendarMarker.providedBy(topic):
                return topic
        url = '/'+portal.id+topic_url
        while not interfaces.ISolgemaFullcalendarMarker.providedBy(topic):
            url = url[0:url.rindex('/')]
            try:
                topic = portal.restrictedTraverse(url)
            except:
                break
                raise str(url)

        return topic
    else:
        return context


def getCriteriaItems(context, request):
    topic = getTopic(context, request)
    listCriteria = topic.listCriteria()
    topicCriteria = listQueryTopicCriteria(topic)
    if topicCriteria:
        selectedCriteria = request.cookies.get('sfqueryDisplay', topic.REQUEST.cookies.get('sfqueryDisplay', topicCriteria[0].Field()))
        criteria = [a for a in listCriteria if a.Field() == selectedCriteria]
    else:
        criteria = listCriteria

    criteria = [a for a in criteria if a.meta_type in
                   ['ATPortalTypeCriterion', 'ATSelectionCriterion', 'ATListCriterion']]
    if not criteria:
        return False

    criteria = criteria[0]
    if criteria.meta_type == 'ATPortalTypeCriterion':
        return {'name': criteria.Field(),
                'values': list(criteria.getCriteriaItems()[0][1])}

    if criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion']:
        return {'name': criteria.Field(),
                'values': list(criteria.getCriteriaItems()[0][1]['query']) + ['']
                }

    return False


def getCookieItems(request, field, charset):
    items = request.form.get(field)
    if items:
        return items
    items = request.cookies.get(field)
    if not items:
        return None
    if isinstance(items, (str, unicode)):
        items = items.find('+') == -1 and items or items.split('+')
    final = []
    if isinstance(items, (list, tuple)):
        for item in items:
            try:
                item = item.decode('latin1')
            except:
                pass
            final.append( safe_unicode(item).encode(charset) )
    else:
        try:
            items = items.decode('latin1')
        except:
            pass
        final = [safe_unicode(items).encode(charset)]

    return final

def getColorIndex(context, request, eventPath=None, brain=None):
    undefined =  'colorIndex-undefined'
    if not brain:
        if not eventPath:
            raise ValueError(u'You must provide eventPath or brain')

        catalog = getToolByName(context, 'portal_catalog')
        brains = catalog.searchResults(path=eventPath)
        if len(brains) == 0:
            log.error("Error computing color index : no result for path %s", eventPath)
            return undefined

        brain = brains[0]

    adapter = getMultiAdapter((context, request, brain),
                              interfaces.IColorIndexGetter)
    colorIndex = adapter.getColorIndex()
    return ' ' + (colorIndex or undefined)

class SolgemaFullcalendarView(BrowserView):
    """Solgema Fullcalendar Browser view for Fullcalendar rendering"""

    implements(interfaces.ISolgemaFullcalendarView)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context),
                                                                  None)

    def getCriteriaClass(self):
        return ''

    def displayNoscriptList(self):
        return getattr(self.calendar, 'displayNoscriptList', True)

class SolgemaFullcalendarTopicView(SolgemaFullcalendarView):
    """Solgema Fullcalendar Browser view for Fullcalendar rendering"""

    def getCriteriaClass(self):
        anon = self.context.portal_membership.isAnonymousUser()
        listCriteria = self.context.listCriteria()
        if not listCriteria:
            return ''
        if listCriteria[0].Field() == 'review_state' and anon:
            return ''

        return self.request.cookies.get('sfqueryDisplay', listCriteria[0].Field())

class SolgemaFullcalendarEventJS(BrowserView):
    """Solgema Fullcalendar Javascript variables"""

    implements(interfaces.ISolgemaFullcalendarJS)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        portal_state = getMultiAdapter((context, request), name=u'plone_portal_state')
        self.portal = portal_state.portal() 
        self._ts = getToolByName(context, 'translation_service')
        self.portal_language = portal_state.language()
        self.calendar = None

    def getFirstDay(self):
        return 1

    def getYear(self):
        now = datetime.datetime.now()
        return int(now.year)

    def getMonthNumber(self):
        now = datetime.datetime.now()
        return int(now.month)

    def getDate(self):
        now = datetime.datetime.now()
        return int(now.day)

    def getMonthsNames(self):
        return [PLMF(self._ts.month_msgid(m), default=self._ts.month_english(m)) for m in [a+1 for a in range(12)]]

    def getMonthsNamesAbbr(self):
        return [PLMF(self._ts.month_msgid(m, format='a'), default=self._ts.month_english(m, format='a')) for m in [a+1 for a in range(12)]]

    def getWeekdaysNames(self):
        return [PLMF(self._ts.day_msgid(d), default=self._ts.weekday_english(d)) for d in range(7)]

    def getWeekdaysNamesAbbr(self):
        if self.portal_language in ['de']:
            return [PLMF(self._ts.day_msgid(d)+'_short', default=self._ts.weekday_english(d)+'_short') for d in range(7)]
        else:
            return [PLMF(self._ts.day_msgid(d, format='a'), default=self._ts.weekday_english(d, format='a')) for d in range(7)]

    def getTodayTranslation(self):
        return DTMF('Today', 'Today')

    def getMonthTranslation(self):
        return _('Month', 'Month')

    def getWeekTranslation(self):
        return _('Week', 'Week')

    def getDayTranslation(self):
        return _('Day', 'Day')

    def getDaySplitTranslation(self):
        return _('DaySplit', 'DaySplit')

    def getAllDayText(self):
        return _('Allday', 'all-day')

    def getAddEventText(self):
        return _('addNewEvent', 'Add New Event')

    def getEditEventText(self):
        return _('editEvent', 'Edit Event')
    
    def getDeleteConfirmationText(self):
        return pMF('alert_really_delete', 'Do you really want to delete this item?')

    def getCustomTitleFormat(self):
        if self.portal_language in ['fr']:
            return '{month: "MMMM yyyy", week: "d[ MMMM][ yyyy]{ \'-\' d MMMM yyyy}", day: \'dddd d MMMM yyyy\'}'
        elif self.portal_language in ['de']:
            return '{month: \'MMMM yyyy\', week: "d[ yyyy].[ MMMM]{ \'- \'d. MMMM yyyy}", day: \'dddd, d. MMMM yyyy\'}'
        else:
            return '{month: \'MMMM yyyy\', week: "MMM d[ yyyy]{ \'-\'[ MMM] d yyyy}", day: \'dddd, MMM d, yyyy\'}'

    def getHourFormat(self):
        if self.portal_language in ['fr', 'de', 'it']:
            return 'HH:mm'
        else:
            return 'h(:mm)tt'

    def columnFormat(self):
        if self.portal_language in ['de']:
            return "{month: 'ddd', week: 'ddd d. MMM', day: 'dddd d. MMM'}"
        elif self.portal_language in ['fr']:
            return "{month: 'dddd', week: 'ddd d/MM', day: 'dddd d/MM'}"
        else:
            return "{month: 'ddd', week: 'ddd M/d', day: 'dddd M/d'}"

    def getTargetFolder(self):
        target_folder = getattr(self.calendar, 'target_folder', None)
        if target_folder:
            addContext = self.portal.unrestrictedTraverse('/'+self.portal.id+target_folder)
        elif IATFolder.providedBy(self.context):
            addContext = self.context
        else:
            addContext = aq_parent(aq_inner(self.context))
        return addContext.absolute_url()

    def getHeaderRight(self):
        return 'month, agendaWeek, agendaDay'

    def getHeaderLeft(self):
        return 'prev,next today calendar'

    def getPloneVersion(self):
        portal_migration = getToolByName(self.context, 'portal_migration')
        try:
            return portal_migration.getSoftwareVersion()
        except:
            return portal_migration.getInstanceVersion()
    
    def slotMinutes(self):
        return '30'

    def defaultCalendarView(self):
        return 'agendaWeek'

    def calendarWeekends(self):
        return 'true'

    def firstHour(self):
        return '-1'

    def minTime(self):
        return '0'

    def maxTime(self):
        return '24'

    def allDaySlot(self):
        return 'false'

    def calendarHeight(self):
        return None

    def getTopicRelativeUrl(self):
        return '/'+self.context.absolute_url(relative=1)

    def getTopicAbsoluteUrl(self):
        return self.context.absolute_url()

    def disableAJAX(self):
        return 'false'

    def caleditable(self):
        return 'true'

    def disableDragging(self):
        return 'false'

    def disableResizing(self):
        return 'false'

    def __call__(self):
        self.request.RESPONSE.setHeader('Content-Type','application/x-javascript; charset=utf-8')
        return super(SolgemaFullcalendarEventJS, self).__call__()
        
class SolgemaFullcalendarTopicJS(SolgemaFullcalendarEventJS):
    """Solgema Fullcalendar Javascript variables"""

    implements(interfaces.ISolgemaFullcalendarJS)
    
    def __init__(self, context, request):
        super(SolgemaFullcalendarTopicJS, self).__init__(context, request)
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context), None)

    def getFirstDay(self):
        if getattr(self.calendar, 'relativeFirstDay', '') in [None, '']:
            return self.calendar.firstDay
        else:
            now = datetime.datetime.now()
            delta = datetime.timedelta(hours=int(getattr(self.calendar, 'relativeFirstDay')))
            newdate = now+delta
            return newdate.isoweekday() - 1

    def getYear(self):
        if getattr(self.calendar, 'relativeFirstDay', '') in [None, '']:
            return datetime.datetime.now().year
        else:
            now = datetime.datetime.now()
            delta = datetime.timedelta(hours=int(getattr(self.calendar, 'relativeFirstDay')))
            newdate = now+delta
            return int(newdate.year)

    def getMonthNumber(self):
        if getattr(self.calendar, 'relativeFirstDay', '') in [None, '']:
            return datetime.datetime.now().month
        else:
            now = datetime.datetime.now()
            delta = datetime.timedelta(hours=int(getattr(self.calendar, 'relativeFirstDay')))
            newdate = now+delta
            return int(newdate.month)

    def getDate(self):
        if getattr(self.calendar, 'relativeFirstDay', '') in [None, '']:
            return datetime.datetime.now().day
        else:
            now = datetime.datetime.now()
            delta = datetime.timedelta(hours=int(getattr(self.calendar, 'relativeFirstDay')))
            newdate = now+delta
            return int(newdate.day)

    def getHeaderLeft(self):
        headerLeft = getattr(self.calendar, 'headerLeft', 'prev,next today calendar')
        if isinstance(headerLeft, list):
            return ','.join(headerLeft)
        return headerLeft

    def getHeaderRight(self):
        headerRight = getattr(self.calendar, 'headerRight', 'month,agendaWeek,agendaDay')
        if isinstance(headerRight, list):
            return ','.join(headerRight)
        return headerRight

    def getTopicRelativeUrl(self):
        if CMFPloneUtils.isDefaultPage(self.context, self.request):
            return '/'+aq_parent(aq_inner(self.context)).absolute_url(relative=1)
        else:
            return '/'+self.context.absolute_url(relative=1)

    def getTopicAbsoluteUrl(self):
        return self.context.absolute_url()
    
    def slotMinutes(self):
        return getattr(self.calendar, 'slotMinutes', '30')

    def defaultCalendarView(self):
        return getattr(self.calendar, 'defaultCalendarView', 'agendaWeek')

    def calendarWeekends(self):
        return getattr(self.calendar, 'weekends', True) and 'true' or 'false'

    def firstHour(self):
        return getattr(self.calendar, 'firstHour', '-1')

    def minTime(self):
        return getattr(self.calendar, 'minTime', '0')

    def maxTime(self):
        return getattr(self.calendar, 'maxTime', '24')

    def allDaySlot(self):
        return getattr(self.calendar, 'allDaySlot', False) and 'true' or 'false'

    def calendarHeight(self):
        return getattr(self.calendar, 'calendarHeight', '600')

    def disableAJAX(self):
        return getattr(self.calendar, 'disableAJAX', False) \
                    and 'true' or 'false'

    def caleditable(self):
        return getattr(self.calendar, 'editable', True) and 'true' or 'false'

    def disableDragging(self):
        return getattr(self.calendar, 'disableDragging', False) \
                    and 'true' or 'false'

    def disableResizing(self):
        return getattr(self.calendar, 'disableResizing', False) \
                    and 'true' or 'false'

class SFTopicSources(SolgemaFullcalendarView):

    implements(interfaces.ISolgemaFullcalendarEventsSources)

    def getColor(self, fieldid, value):
        colorsDict = self.calendar.queryColors
        
        if not colorsDict or not colorsDict.get(fieldid):
            return None
        value = str(component.queryUtility(IURLNormalizer).normalize(safe_unicode(value)))
        newColorsDict = {}
        for k,v in colorsDict.get(fieldid, {}).items():
            k = safe_unicode(k)
            if k == value or str(component.queryUtility(IURLNormalizer).normalize(k)) == value:
                return v
        return None
                
    def __call__(self, *args, **kw):
        """Render JS eventSources. Separate cookie request in different sources."""
        self.request.response.setHeader('Content-Type', 'application/x-javascript')
        criteria = self.getCriteriaClass()
        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'
        values = getCookieItems(self.request, criteria, charset)
        fromCookie = True
        if values == None:
            fromCookie = False
            CriteriaItems = getCriteriaItems(self.context, self.request)
            values = CriteriaItems and [a for a in CriteriaItems['values'] if a] or []
            criteria = CriteriaItems['name']
        eventSources = []
        if values:
            for value in values:
                d = {}
                if fromCookie:
                    value = value.decode('utf-8')
                d['url'] = self.context.absolute_url()+'/@@solgemafullcalendarevents?'+criteria+'='+value
                d['type'] = 'POST'
                d['color'] = self.getColor(criteria, value)
                d['title'] = value
                #d['data'] = {criteria:value} Unfortunately this is not possible to remove an eventSource with data from fullcalendar
                #it recognises only eventSource by url....
                if criteria == 'Subject':
                    d['extraData'] = {'subject:list':value}
                elif criteria in ['Creator', 'Contributor']:#How to get the right field name?
                    d['extraData'] = {criteria.lower()+'s:lines':value}
                else:
                    d['extraData'] = {criteria:value}
                eventSources.append(d.copy())
        else:
            eventSources.append({'url':self.context.absolute_url()+'/@@solgemafullcalendarevents'})
        
        gcalSourcesAttr = getattr(self.calendar, 'gcalSources', '')
        if gcalSourcesAttr != None:
            gcalSources = gcalSourcesAttr.split('\n')
            for i in range(len(gcalSources)):
                url = gcalSources[i]
                if url:
                    gcalColors = self.calendar.queryColors.get('gcalSources', {})
                    eventSources.append({'url':       url,
                                        'dataType':  'gcal',
                                        'className': 'gcal-event gcal-source'+str(i+1),
                                        'color':     gcalColors.get('source'+str(i), ''),
                                        'title':     'GCAL '+str(i+1)})

        return json.dumps(eventSources, sort_keys=True)

class SFFolderSources(SolgemaFullcalendarView):

    implements(interfaces.ISolgemaFullcalendarEventsSources)
                
    def getColor(self, fieldid, value):
        colorsDict = self.calendar.queryColors
        
        if not colorsDict or not colorsDict.get(fieldid):
            return None
        value = str(component.queryUtility(IURLNormalizer).normalize(safe_unicode(value)))
        newColorsDict = {}
        for k,v in colorsDict.get(fieldid, {}).items():
            k = safe_unicode(k)
            if k == value or str(component.queryUtility(IURLNormalizer).normalize(k)) == value:
                return v
        return None
                
    def __call__(self, *args, **kw):
        """Render JS eventSources. Separate cookie request in different sources."""
        self.request.response.setHeader('Content-Type', 'application/x-javascript')
        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'
        values = getCookieItems(self.request, 'subFolders', charset)
        availableSubFolders = getattr(self.calendar, 'availableSubFolders', [])
        fromCookie = True
        if values == None:
            fromCookie = False
            values = getattr(self.calendar, 'availableSubFolders', [])
        voc = component.getUtility(IVocabularyFactory, name=u'solgemafullcalendar.availableSubFolders', context=self.context)(self.context)
        eventSources = []
        if values:
            for value in values:
                if not value in availableSubFolders:
                    continue
                d = {}
                if fromCookie:
                    value = value.decode('utf-8')
                d['url'] = self.context.absolute_url()+'/'+value+'/@@solgemafullcalendarevents'
                d['type'] = 'POST'
                d['color'] = self.getColor('subFolders', value)
                d['title'] = voc.getTerm(value).title
                d['target_folder'] = self.context.absolute_url()+'/'+value
                eventSources.append(d.copy())
        else:
            eventSources.append({'url':self.context.absolute_url()+'/@@solgemafullcalendarevents'})
        
        gcalSourcesAttr = getattr(self.calendar, 'gcalSources', '')
        if gcalSourcesAttr != None:
            gcalSources = gcalSourcesAttr.split('\n')
            for i in range(len(gcalSources)):
                url = gcalSources[i]
                if url:
                    gcalColors = self.calendar.queryColors.get('gcalSources', {})
                    eventSources.append({'url':       url,
                                        'dataType':  'gcal',
                                        'className': 'gcal-event gcal-source'+str(i+1),
                                        'color':     gcalColors.get('source'+str(i), ''),
                                        'title':     'GCAL '+str(i+1)})

        return json.dumps(eventSources, sort_keys=True)

class SFEventSources(BrowserView):

    implements(interfaces.ISolgemaFullcalendarEventsSources)
                
    def __call__(self, *args, **kw):
        return json.dumps([self.context.absolute_url()+'/@@solgemafullcalendarevents',])

class SolgemaFullcalendarEvents(BrowserView):
    """Solgema Fullcalendar Update browser view"""

    implements(interfaces.ISolgemaFullcalendarEvents)

    def __call__(self, *args, **kw):
        """Render JS Initialization code"""
        self.request.response.setHeader('Content-Type', 'application/x-javascript')
        sources = getAdapters((self.context, self.request),
                                 interfaces.IEventSource)
        events = []
        for name, source in sources:
            events.extend(source.getEvents())

        return json.dumps(events, sort_keys=True)


class SolgemaFullcalendarColorsCssFolder(BrowserView):
    """Solgema Fullcalendar Javascript variables"""

    implements(interfaces.ISolgemaFullcalendarColorsCss)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context), None)

    def __call__(self):
        colorsDict = self.calendar.queryColors
        availableSubFolders = getattr(self.calendar, 'availableSubFolders', [])
        css = ''
        if not colorsDict or not availableSubFolders:
            return css
        folderIds = [a.getId for a in self.context.getFolderContents(contentFilter={'portal_type':'Folder'})]
        if not folderIds:
            return css
        fieldid = 'subFolders'

        for i in range(len(availableSubFolders)):
            folderId = availableSubFolders[i]
            color = None
            for k,v in colorsDict.get(fieldid, {}).items():
                k = safe_unicode(k)
                if k == folderId:
                    color = v
                    break
            if color:
                css += 'label.%scolorIndex-%s {\n' % (fieldid, str(i))
                css += '    color: %s;\n' % (str(color))
                css += '}\n\n'

        return css

class SolgemaFullcalendarColorsCssTopic(BrowserView):
    """Solgema Fullcalendar Javascript variables"""

    implements(interfaces.ISolgemaFullcalendarColorsCss)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context), None)

    def __call__(self):
        colorsDict = self.calendar.queryColors
        criterias = listBaseQueryTopicCriteria(self.context)
        css = ''
        if not colorsDict:
            return css

        for criteria in criterias:
            field = criteria.Field()

            fieldid = str(field)
            if not colorsDict.has_key(fieldid):
                continue

            selectedItems = []
            if criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion']:
                selectedItems = criteria.getCriteriaItems()[0][1]['query']
            elif criteria.meta_type == 'ATPortalTypeCriterion':
                selectedItems = criteria.getCriteriaItems()[0][1]

            for i in range(len(selectedItems)):
                cValName = str(component.queryUtility(IURLNormalizer).normalize(safe_unicode(selectedItems[i])))

                color = None
                for k,v in colorsDict.get(fieldid, {}).items():
                    k = safe_unicode(k)
                    if k == cValName or str(component.queryUtility(IURLNormalizer).normalize(k)) == cValName:
                        color = v
                        break
                if color:
                    css += 'label.%scolorIndex-%s {\n' % (fieldid, str(i))
                    css += '    color: %s;\n' % (str(color))
                    css += '}\n\n'

        return css

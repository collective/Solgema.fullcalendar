import datetime
from urllib import unquote
try:
    import json
except:
    import simplejson as json

from OFS import CopySupport
from Acquisition import aq_inner, aq_parent
from zope.interface import implements
from zope.component import getMultiAdapter, getAdapters
from zope.i18nmessageid import MessageFactory

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneLocalesMessageFactory as PLMF
from Products.CMFPlone import utils as CMFPloneUtils
from Products.CMFPlone.utils import safe_unicode 

from Solgema.fullcalendar.config import _
from Solgema.fullcalendar import interfaces
from Solgema.fullcalendar import log



DTMF = MessageFactory('collective.z3cform.datetimewidget')

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
        topic = portal.restrictedTraverse('/'+portal.id+topic_url)
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
    item = request.cookies.get(field, False)
    if not item:
        return False

    items = item.find('+') == -1 and item or item.split('+')

    if isinstance(items, (list, tuple)):
        items = [safe_unicode(a).encode(charset) for a in items]
    else:
        items = safe_unicode(items).encode(charset)
        items = [items]

    return items

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
        anon = self.context.portal_membership.isAnonymousUser()
        listCriteria = self.context.listCriteria()
        if not listCriteria:
            return ''
        if listCriteria[0].Field() == 'review_state' and anon:
            return ''

        return self.request.cookies.get('sfqueryDisplay', listCriteria[0].Field())

    def displayNoscriptList(self):
        return getattr(self.calendar, 'displayNoscriptList', True)

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
        return [PLMF(self._ts.day_msgid(d, format='a'), default=self._ts.weekday_english(d, format='a')) for d in range(7)]

    def getTodayTranslation(self):
        return DTMF('Today', 'Today')

    def getMonthTranslation(self):
        return _('Month', 'Month')

    def getWeekTranslation(self):
        return _('Week', 'Week')

    def getDayTranslation(self):
        return _('Day', 'Day')

    def getAllDayText(self):
        return _('Allday', 'all-day')

    def getAddEventText(self):
        return _('addNewEvent', 'Add New Event')

    def getEditEventText(self):
        return _('editEvent', 'Edit Event')

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
        return aq_parent(aq_inner(self.context)).absolute_url()

    def getHeaderRight(self):
        return 'month, agendaWeek, agendaDay'

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

    def getTargetFolder(self):
        target_folder = getattr(self.calendar, 'target_folder', None)
        addContext = target_folder and self.portal.unrestrictedTraverse('/'+self.portal.id+target_folder) or aq_parent(aq_inner(self.context))
        return addContext.absolute_url()

    def getHeaderRight(self):
        headerRight = getattr(self.calendar, 'headerRight', ['month', 'agendaWeek', 'agendaDay'])
        return ','.join(headerRight)

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


class SolgemaFullcalendarEvents(BrowserView):
    """Solgema Fullcalendar Update browser view"""

    implements(interfaces.ISolgemaFullcalendarEvents)

    def __init__(self, context, request):
        super(SolgemaFullcalendarEvents, self).__init__(context, request)
        #self.copyDict = getCopyObjectsUID(request)

    def __call__(self, *args, **kw):
        """Render JS Initialization code"""
        self.request.response.setHeader('Content-Type', 'application/x-javascript')
        sources = getAdapters((self.context, self.request),
                                 interfaces.IEventSource)
        events = []
        for name, source in sources:
            events.extend(source.getEvents())

        return json.dumps(events, sort_keys=True)


class SolgemaFullcalendarColorsCss(BrowserView):
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
                cValName = selectedItems[i]
                if not colorsDict[fieldid].has_key(cValName):
                    continue

                color = colorsDict[fieldid][cValName]
                if color:
                    css += '#calendar .%scolorIndex-%s {\n' % (fieldid, str(i))
                    css += '    border:1px solid %s;\n' % (str(color))
                    css += '}\n\n'
                    css += '#calendar .%scolorIndex-%s .fc-event-skin,\n' % (fieldid, str(i))
                    css += '#calendar .%scolorIndex-%s .fc-event-time {\n' % (fieldid, str(i))
                    css += '    background-color: %s;\n' % (str(color))
                    css += '    border-color: %s;\n' % (str(color))
                    css += '}\n\n'
                    css += 'label.%scolorIndex-%s {\n' % (fieldid, str(i))
                    css += '    color: %s;\n' % (str(color))
                    css += '}\n\n'

        return css

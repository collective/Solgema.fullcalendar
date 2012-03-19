from DateTime import DateTime
from Acquisition import aq_inner
from AccessControl import getSecurityManager
from zope.interface import implements, Interface
from zope.component import queryAdapter, adapts, getMultiAdapter, getAdapters
from Products.ZCatalog.interfaces import ICatalogBrain

from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interfaces.topic import IATTopic

from Solgema.fullcalendar.browser.views import getCopyObjectsUID, getColorIndex
from Solgema.fullcalendar import interfaces
from Solgema.fullcalendar.browser.views import listQueryTopicCriteria,\
    getCriteriaItems, getCookieItems

try:
    from plone.app.event.ical import EventsICal
    HAS_CALEXPORT_SUPPORT = True
except ImportError:
    HAS_CALEXPORT_SUPPORT = False

try:
    from plone.app.event.interfaces import IEvent
    hasPloneAppEvent = True
except ImportError:
    from Products.ATContentTypes.interfaces.event import IATEvent as IEvent
    hasPloneAppEvent = False

try:
    from plone.app.event.interfaces import IRecurrence
    HAS_RECURRENCE_SUPPORT = True
except ImportError:
    HAS_RECURRENCE_SUPPORT = False


class SolgemaFullcalendarCatalogSearch(object):
    implements(interfaces.ISolgemaFullcalendarCatalogSearch)

    def __init__(self, context):
        self.context = context

    def searchResults(self, args):
        catalog = getToolByName(self.context, 'portal_catalog')
        return catalog.searchResults(**args)


class SolgemaFullcalendarEditableFilter(object):
    implements(interfaces.ISolgemaFullcalendarEditableFilter)

    def __init__(self, context):
        self.context = context

    def _listSFAllowedRolesAndUsersModify(self):
        sm = getSecurityManager()
        user = sm.getUser()
        effective_roles = user.getRoles()
        if sm.calledByExecutable():
            eo = sm._context.stack[-1]
            proxy_roles = getattr(eo, '_proxy_roles', None)
            if proxy_roles is not None:
                effective_roles = proxy_roles
        result = list( effective_roles )
        result.append( 'Anonymous' )
        result.append( 'user:%s' % user.getId() )
        return result

    def filterEvents(self, args):
        editargs = args.copy()
        catalog = getToolByName(self.context, 'portal_catalog')
        editargs['SFAllowedRolesAndUsersModify'] = self._listSFAllowedRolesAndUsersModify()
        return [a.UID for a in catalog.searchResults(**editargs)]
        
class SolgemaFullcalendarTopicEventDict(object):
    implements(interfaces.ISolgemaFullcalendarTopicEventDict)

    def __init__(self, topic, request):
        self.context = topic
        self.request = request
        self.copyDict = getCopyObjectsUID(request)

    def getBrainExtraClass(self, item):
        return ''

    def getObjectExtraClass(self, item):
        extraclasses = getAdapters((item, self.request),
                                 interfaces.ISolgemaFullcalendarExtraClass)
        classes = []
        for name, source in extraclasses:
            classes.append(source.extraClass())
        if not classes:
            return ''
        return ' '.join(classes)

    def dictFromBrain(self, brain, editableEvents=[]):

        if brain.UID in editableEvents:
            editable = True
        else:
            editable = False

        if brain.end - brain.start > 1.0:
            allday = True
        else:
            allday = False

        if getattr(brain, 'SFAllDay', None) in [False,True]:
            allday = brain.SFAllDay

        copycut = ''
        if self.copyDict and brain.getPath() == self.copyDict['url']:
            copycut = self.copyDict['op'] == 1 and ' event_cutted' or ' event_copied'
        typeClass = ' type-'+brain.portal_type
        colorIndex = getColorIndex(self.context, self.request, brain=brain)
        extraClass = self.getBrainExtraClass(brain)
        if HAS_RECURRENCE_SUPPORT:
            event = brain.getObject()
            start = DateTime(self.request.get('start'))
            end = DateTime(self.request.get('end'))
            occurences = IRecurrence(event).occurrences(limit_start=start, limit_end=end)
        else:
            occurences = [(brain.start.rfc822(), brain.end.rfc822())]
        events = []
        for occurence_start, occurence_end in occurences:
            events.append({
                "id": "UID_%s" % (brain.UID),
                "title": brain.Title,
                "description": brain.Description,
                "start": HAS_RECURRENCE_SUPPORT and occurence_start.isoformat() or occurence_start,
                "end": HAS_RECURRENCE_SUPPORT and occurence_end.isoformat() or occurence_end,
                "url": brain.getURL(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled state-" + str(brain.review_state) + (editable and " editable" or "")+copycut+typeClass+colorIndex+extraClass})
        return events

    def dictFromObject(self, item, args={}):
        eventPhysicalPath = '/'.join(item.getPhysicalPath())
        wft = getToolByName(self.context, 'portal_workflow')
        state = wft.getInfoFor(self.context, 'review_state')
        member = self.context.portal_membership.getAuthenticatedMember()
        if member.has_permission('Modify portal content', item):
            editable = True

        if item.end() - item.start() > 1.0:
            allday = True
        else:
            allday = False

        adapted = interfaces.ISFBaseEventFields(item, None)
        if adapted:
            allday = adapted.allDay

        copycut = ''
        if self.copyDict and eventPhysicalPath == self.copyDict['url']:
            copycut = self.copyDict['op'] == 1 and ' event_cutted' or ' event_copied'

        typeClass = ' type-' + item.portal_type
        colorIndex = getColorIndex(self.context, self.request, eventPhysicalPath)
        extraClass = self.getObjectExtraClass(item)
        if HAS_RECURRENCE_SUPPORT:
            start = DateTime(self.request.get('start'))
            end = DateTime(self.request.get('end'))
            occurences = IRecurrence(item).occurrences(limit_start=start, limit_end=end)
        else:
            occurences = [(item.start().rfc822(), item.end().rfc822())]
        events = []
        for occurence_start, occurence_end in occurences:
            events.append({
                "status": "ok",
                "id": "UID_%s" % (item.UID()),
                "title": item.Title(),
                "description": item.Description(),
                "start": HAS_RECURRENCE_SUPPORT and occurence_start.isoformat() or occurence_start,
                "end": HAS_RECURRENCE_SUPPORT and occurence_end.isoformat() or occurence_end,
                "url": item.absolute_url(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled state-" + str(state) + (editable and " editable" or "")+copycut+typeClass+colorIndex+extraClass})

        return events

    def createDict(self, itemsList=[], args={}):
        li = []

        eventsFilter = queryAdapter(self.context,
                                    interfaces.ISolgemaFullcalendarEditableFilter)
        editableEvents = eventsFilter.filterEvents(args)

        for item in itemsList:
            if hasattr(item, '_unrestrictedGetObject'):
                li.extend(self.dictFromBrain(item, editableEvents=editableEvents))
            else:
                li.extend(self.dictFromObject(item))

        return li


class SolgemaFullcalendarEventDict(object):
    implements(interfaces.ISolgemaFullcalendarEventDict)

    def __init__(self, event, request):
        self.context = event
        self.request = request
        self.copyDict = getCopyObjectsUID(request)

    def getExtraClass(self):
        extraclasses = getAdapters((self.context, self.request),
                                 interfaces.ISolgemaFullcalendarExtraClass)
        classes = []
        for name, source in extraclasses:
            classes.append(source.extraClass())
        if not classes:
            return ''
        return ' '.join(classes)

    def __call__(self):
        context = self.context

        eventPhysicalPath = '/'.join(context.getPhysicalPath())
        wft = getToolByName(context, 'portal_workflow')
        state = wft.getInfoFor(context, 'review_state')
        member = context.portal_membership.getAuthenticatedMember()
        editable = bool(member.has_permission('Modify portal content', context))
        allday = (context.end() - context.start()) > 1.0

        adapted = interfaces.ISFBaseEventFields(context, None)
        if adapted:
            allday = adapted.allDay

        copycut = ''
        if self.copyDict and eventPhysicalPath == self.copyDict['url']:
            copycut = self.copyDict['op'] == 1 and ' event_cutted' or ' event_copied'

        typeClass = ' type-' + context.portal_type
        colorIndex = getColorIndex(context, self.request, eventPhysicalPath)
        extraClass = self.getExtraClass()
        return {"status": "ok",
                "id": "UID_%s" % context.UID(),
                "title": context.Title(),
                "description": context.Description(),
                "start": context.start().rfc822(),
                "end": context.end().rfc822(),
                "url": context.absolute_url(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled state-" + str(state) + (editable and " editable" or "")+copycut+typeClass+colorIndex+extraClass}



class ColorIndexGetter(object):

    implements(interfaces.IColorIndexGetter)
    adapts(Interface, Interface, ICatalogBrain)

    def __init__(self, context, request, source):
        self.context = context
        self.request = request
        self.source = source

    def getColorIndex(self):
        context, request, brain = self.context, self.request, self.source
        criteriaItems = getCriteriaItems(context, request)
        colorIndex = ''
        if not criteriaItems:
            return colorIndex

        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'
        selectedItems = getCookieItems(request, criteriaItems['name'], charset)
        if not selectedItems:
            selectedItems = criteriaItems['values']

        if not isinstance(selectedItems, list):
            selectedItems = [selectedItems,]

        if criteriaItems:
            brainVal = getattr(brain, criteriaItems['name'])
            brainVal = isinstance(brainVal, (tuple, list)) and brainVal or [brainVal,]
            for val in brainVal:
                if criteriaItems['values'].count(val) != 0 and val in selectedItems:
                    colorIndex = 'colorIndex-'+str(criteriaItems['values'].index(val))
                    colorIndex += ' '+criteriaItems['name']+'colorIndex-'+str(criteriaItems['values'].index(val))
                    break

        return colorIndex


class TopicEventSource(object):
    """Event source that get events from the topic
    """
    implements(interfaces.IEventSource)
    adapts(IATTopic, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context), None)

    def convertAsList(self, items):
        if isinstance(items, str):
            return [items,]

        return items

    def _getBrains(self, args, filters):

        searchMethod = getMultiAdapter((self.context,),
                                       interfaces.ISolgemaFullcalendarCatalogSearch)
        brains = searchMethod.searchResults(args)

        for filt in filters:
            if isinstance(filt['values'], str):
                brains = [ a for a in brains if not getattr(a, filt['name']) ]
            else:
                brains = [ a for a in brains
                            if not getattr(a, filt['name'])
                            or len([b for b in self.convertAsList(getattr(a, filt['name']))
                                    if b in filt['values']])>0 ]

        return brains

    def _getCriteriaArgs(self):
        context, request = self.context, self.request
        response = request.response

        query = context.buildQuery()
        topicCriteria = listQueryTopicCriteria(context)
        args = {}
        if not query:
            return ({}, [])

        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'

        if 'Type' in query.keys():
            items = getCookieItems(request, 'Type', charset)
            if items:
                args['Type'] = items
            else:
                args['Type'] = query['Type']
        filters = []
        #reinit cookies if criterions are no more there
        for criteria in context.listCriteria():
            if criteria not in listQueryTopicCriteria(context):
                response.expireCookie(criteria.Field())

        if request.cookies.get('sfqueryDisplay', None) not in [a.Field() for a in topicCriteria]:
            response.expireCookie('sfqueryDisplay')

        for criteria in self.context.listCriteria():
            if criteria.meta_type not in ['ATSelectionCriterion', 'ATListCriterion', 'ATSortCriterion', 'ATPortalTypeCriterion'] and criteria.Field():
                args[criteria.Field()] = query[criteria.Field()]
            elif criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion'] and criteria.getCriteriaItems() and len(criteria.getCriteriaItems()[0])>1 and len(criteria.getCriteriaItems()[0][1]['query'])>0:
                items = getCookieItems(request, criteria.Field(), charset)
                if items and criteria in topicCriteria:
                    if 'undefined' in items:
                        filters.append({'name':criteria.Field(), 'values':items})
                    else:
                        args[criteria.Field()] = items
                else:
                    args[criteria.Field()] = query[criteria.Field()]

        return args, filters

    def getEvents(self):
        context = self.context
        request = self.request
        args, filters = self._getCriteriaArgs()
        args['start'] = {'query': DateTime(request.get('end')), 'range':'max'}
        args['end'] = {'query': DateTime(request.get('start')), 'range':'min'}
        if getattr(self.calendar, 'overrideStateForAdmin', True) and args.has_key('review_state'):
            pm = getToolByName(context,'portal_membership')
            user = pm.getAuthenticatedMember()
            if user and user.has_permission('Modify portal content', context):
                del args['review_state']

        brains = self._getBrains(args, filters)
        topicEventsDict = getMultiAdapter((context, self.request),
                                          interfaces.ISolgemaFullcalendarTopicEventDict)
        result = topicEventsDict.createDict(brains, args)
        return result

    def getICalObjects(self):
        args, filters = self._getCriteriaArgs()
        brains = self._getBrains(args, filters)
        return [a.getObject() for a in brains]

    def getICal(self):
        args, filters = self._getCriteriaArgs()
        brains = self._getBrains(args, filters)
        if HAS_CALEXPORT_SUPPORT:
            return ''.join([EventsICal(b.getObject())()
                                    for b in brains])
        else:
            return ''.join([b.getObject().getICal() for b in brains])

class StandardEventSource(object):
    """Event source that display an event
    """
    implements(interfaces.IEventSource)
    adapts(IEvent, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def getObjectExtraClass(self):
        extraclasses = getAdapters((self.context, self.request),
                                 interfaces.ISolgemaFullcalendarExtraClass)
        classes = []
        for name, source in extraclasses:
            classes.append(source.extraClass())
        if not classes:
            return ''
        return ' '.join(classes)

    def getEvents(self):
        context = self.context
        eventPhysicalPath = '/'.join(context.getPhysicalPath())
        wft = getToolByName(context, 'portal_workflow')
        state = wft.getInfoFor(context, 'review_state')
        member = context.portal_membership.getAuthenticatedMember()
        editable = bool(member.has_permission('Modify portal content', context))
        allday = (context.end() - context.start()) > 1.0

        adapted = interfaces.ISFBaseEventFields(context, None)
        if adapted:
            allday = adapted.allDay
        if hasattr(context, 'whole_day'):
            allday = context.whole_day
        extraClass = self.getObjectExtraClass()
        typeClass = ' type-' + context.portal_type
        
        if HAS_RECURRENCE_SUPPORT:
            start  = DateTime(self.request.get('start'))
            end = DateTime(self.request.get('end'))
            occurences = IRecurrence(context).occurrences(limit_start=start, limit_end=end)
        else:
            occurences = [(context.start().rfc822(), context.end().rfc822())]
        events = []
        for occurence_start, occurence_end in occurences:
            events.append({
                "status": "ok",
                "id": "UID_%s" % (context.UID()),
                "title": context.Title(),
                "description": context.Description(),
                "start": HAS_RECURRENCE_SUPPORT and occurence_start.isoformat() or occurence_start,
                "end": HAS_RECURRENCE_SUPPORT and occurence_end.isoformat() or occurence_end,
                "url": context.absolute_url(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled state-" + str(state) + (editable and " editable" or "")+typeClass+extraClass
                })
        return events



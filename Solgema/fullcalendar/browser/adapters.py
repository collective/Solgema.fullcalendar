# -*- coding: utf-8 -*-
import itertools
from copy import deepcopy
from DateTime import DateTime
from datetime import datetime
from Acquisition import aq_inner, aq_parent
from AccessControl import getSecurityManager
from zope.interface import implements, Interface
from zope.component import queryAdapter, adapts, getMultiAdapter, getAdapters
from types import GeneratorType
try:
    from Products.ZCatalog.interfaces import ICatalogBrain
except:
    class ICatalogBrain(Interface): pass
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interface import IATTopic, IATFolder

from Solgema.fullcalendar.browser.views import (
    getCopyObjectsUID,
    getColorIndex,
    getCookieItems,
)
from Solgema.fullcalendar import interfaces

try:
    from plone.app.event.ical import calendar_from_event
    from icalendar.cal import Event as EVENT_COMPONENT_CLS
    HAS_CALEXPORT_SUPPORT = True
except ImportError:
    HAS_CALEXPORT_SUPPORT = False

from Products.ATContentTypes.interface import IATEvent
try:
    from plone.event.interfaces import IEvent, IEventAccessor, IOccurrence
    from plone.event.interfaces import IEvent as IEvent_GENERIC
    from plone.event.utils import pydt
    hasPloneAppEvent = True
except ImportError:
    from Products.ATContentTypes.interface import IATEvent as IEvent_GENERIC
    hasPloneAppEvent = False

try:
    from plone.event.interfaces import IRecurrenceSupport
    HAS_RECURRENCE_SUPPORT = True
except ImportError:
    HAS_RECURRENCE_SUPPORT = False

try:
    from plone.app.collection.interfaces import ICollection
except:
    class ICollection(Interface): pass

try:
    from plone.app.contenttypes.interfaces import ICollection as IDXCollection
    from plone.app.contenttypes.interfaces import IFolder
except:
    class IDXCollection(Interface): pass
    class IFolder(Interface): pass


def handle_recurrence(request):
    return bool(HAS_RECURRENCE_SUPPORT and request.get('start')
                and request.get('end'))

def dict_from_events(events,
                    editable=None,
                    state=None,
                    color=None,
                    css=None):

    def dict_from_item(item):
        if hasPloneAppEvent and (IEvent.providedBy(item) or
                                 IOccurrence.providedBy(item)):
            # plone.app.event DX or AT Event
            is_occurrence = IOccurrence.providedBy(item)
            acc = IEventAccessor(item)
            return {
                "status": "ok",
                "id": "UID_%s" % (acc.uid),
                "title": acc.title,
                "description": acc.description,
                "start": acc.start.isoformat(),
                "end": acc.end.isoformat(),
                "url": acc.url,
                "editable": editable,
                "allDay": acc.whole_day,
                "className": "contextualContentMenuEnabled %s %s %s %s" % (
                                state and "state-%s" % str(state) or "",
                                editable and "editable" or "",
                                css and css or "",
                                is_occurrence and "occurrence" or ""),
                "color": color}
        elif IATEvent.providedBy(item):
            # Products.ATContentTypes ATEvent
            allday = (item.end() - item.start()) > 1.0
            adapted = interfaces.ISFBaseEventFields(item, None)
            if adapted:
                allday = adapted.allDay

            return {
                "status": "ok",
                "id": "UID_%s" % (item.UID()),
                "title": item.Title(),
                "description": item.Description(),
                "start": item.start().ISO8601(),
                "end": item.end().ISO8601(),
                "url": item.absolute_url(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled %s %s %s" % (
                                state and "state-%s" % str(state) or "",
                                editable and "editable" or "",
                                css and css or ""),
                "color": color}
        elif ICatalogBrain.providedBy(item):
            # Event catalog brain
            if type(item.end) != DateTime:
                brainend = DateTime(item.end)
                brainstart = DateTime(item.start)
            else:
                brainend = item.end
                brainstart = item.start

            allday = (brainend - brainstart) > 1.0

            if getattr(item, 'SFAllDay', None) in [False, True]:
                allday = item.SFAllDay

            return {
                "status": "ok",
                "id": "UID_%s" % (item.UID),
                "title": item.Title,
                "description": item.Description,
                "start": brainstart.ISO8601(),
                "end": brainend.ISO8601(),
                "url": item.getURL(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled %s %s %s" % (
                                state and "state-%s" % str(state) or "",
                                editable and "editable" or "",
                                css and css or ""),
                "color": color}
        else:
            raise ValueError('item type not supported for: %s' % repr(item))

    if not isinstance(events, (list, tuple, GeneratorType)):
        events = [events]

    return [dict_from_item(item) for item in events]


def get_recurring_events(request, event):
    if isinstance(event.start, datetime):
        tz = event.start.tzinfo
        start = datetime.fromtimestamp(request.get('start')).replace(tzinfo=tz)
        end = datetime.fromtimestamp(request.get('end')).replace(tzinfo=tz)
    else:
        start = pydt(DateTime(request.get('start')))
        end = pydt(DateTime(request.get('end')))
    events = IRecurrenceSupport(event).occurrences(range_start=start,
                                                   range_end=end)
    return events


class SolgemaFullcalendarCatalogSearch(object):
    implements(interfaces.ISolgemaFullcalendarCatalogSearch)

    def __init__(self, context):
        self.context = context

    def searchResults(self, kwargs):
        catalog = getToolByName(self.context, 'portal_catalog')
        return catalog.searchResults(**kwargs)


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
        result = list(effective_roles)
        result.append('Anonymous')
        result.append('user:%s' % user.getId())
        return result

    def filterEvents(self, kwargs):
        editargs = kwargs.copy()
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

        copycut = ''
        if self.copyDict and brain.getPath() == self.copyDict['url']:
            copycut = self.copyDict['op'] == 1 and ' event_cutted' \
                                             or ' event_copied'
        typeClass = ' type-' + brain.portal_type
        colorDict = getColorIndex(self.context, self.request, brain=brain)
        colorIndex = colorDict.get('class', '')
        color = colorDict.get('color', '')
        extraClass = self.getBrainExtraClass(brain)

        events = []
        if handle_recurrence(self.request):
            event = brain.getObject()
            if IRecurrenceSupport(event, None):
                events = get_recurring_events(self.request, event)
            else:
                events = brain
        else:
            events = brain
        return (dict_from_events(
            events,
            editable=editable,
            state=brain.review_state,
            color=color,
            css=copycut + typeClass + colorIndex + extraClass
            ))

    def dictFromObject(self, item, kwargs={}):
        eventPhysicalPath = '/'.join(item.getPhysicalPath())
        wft = getToolByName(self.context, 'portal_workflow')
        state = wft.getInfoFor(self.context, 'review_state')
        member = self.context.portal_membership.getAuthenticatedMember()
        if member.has_permission('Modify portal content', item):
            editable = True

        copycut = ''
        if self.copyDict and eventPhysicalPath == self.copyDict['url']:
            copycut = self.copyDict['op'] == 1 and ' event_cutted' \
                                             or ' event_copied'

        typeClass = ' type-' + item.portal_type
        colorDict = getColorIndex(self.context, self.request, eventPhysicalPath)
        colorIndex = colorDict.get('class', '')
        color = colorDict.get('color', '')
        extraClass = self.getObjectExtraClass(item)

        events = []
        if handle_recurrence(self.request) and IRecurrenceSupport(item, None):
            events = get_recurring_events(self.request, item)
        else:
            events = item
        return (dict_from_events(
            events,
            editable=editable,
            state=state,
            color=color,
            css=copycut + typeClass + colorIndex + extraClass
            ))


    def createDict(self, itemsList=[], kwargs={}):
        li = []

        eventsFilter = queryAdapter(self.context,
                           interfaces.ISolgemaFullcalendarEditableFilter)
        editableEvents = eventsFilter.filterEvents(kwargs)

        for item in itemsList:
            if hasattr(item, '_unrestrictedGetObject'):
                li.extend(self.dictFromBrain(item,
                                             editableEvents=editableEvents))
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
        event = self.context
        context = self.context
        referer = self.request.get('HTTP_REFERER')
        if referer:
            portal = getToolByName(self.context, 'portal_url').getPortalObject()
            url = "/".join(portal.getPhysicalPath()) + referer.replace(portal.absolute_url(), '')
            context = portal.restrictedTraverse(url)
        eventPhysicalPath = '/'.join(event.getPhysicalPath())
        wft = getToolByName(context, 'portal_workflow')
        state = wft.getInfoFor(event, 'review_state')
        member = context.portal_membership.getAuthenticatedMember()
        editable = bool(member.has_permission('Modify portal content', event))

        copycut = ''
        if self.copyDict and eventPhysicalPath == self.copyDict['url']:
            copycut = self.copyDict['op'] == 1 and ' event_cutted' \
                                             or ' event_copied'

        typeClass = ' type-' + event.portal_type
        colorDict = getColorIndex(context, self.request, eventPhysicalPath)
        colorIndex = colorDict.get('class', '')
        color = colorDict.get('color', '')
        extraClass = self.getExtraClass()

        events = []
        if handle_recurrence(self.request) and IRecurrenceSupport(event, None):
            events = get_recurring_events(self.request, event)
        else:
            events = event
        return (dict_from_events(
            events,
            editable=editable,
            state=state,
            color=color,
            css=copycut + typeClass + colorIndex + extraClass
            ))


class FolderColorIndexGetter(object):

    implements(interfaces.IColorIndexGetter)
    adapts(IATFolder, Interface, ICatalogBrain)

    def __init__(self, context, request, source):
        self.context = context
        self.request = request
        self.source = source
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context),
                                                                  None)

    def getColorIndex(self):
        context, request, brain = self.context, self.request, self.source
        availableSubFolders = getattr(self.calendar, 'availableSubFolders', [])
        final = {'color':'',
                 'class':''}
        if not availableSubFolders:
            return final.copy()
        colorsDict = self.calendar.queryColors

        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'
        selectedItems = getCookieItems(request, 'subFolders', charset)
        if not selectedItems:
            selectedItems = availableSubFolders

        if not isinstance(selectedItems, list):
            selectedItems = [selectedItems, ]
        for val in availableSubFolders:
            if val not in selectedItems:
                continue
            for parentid in brain.getPath().split('/'):
                if val != parentid:
                    continue
                final['color'] = colorsDict.get('subFolders', {}).get(val, '')
                colorIndex = ' colorIndex-%s' % availableSubFolders.index(val)
                colorIndex += ' subFolderscolorIndex-%s' % availableSubFolders.index(val)
                final['class'] = colorIndex
        return final.copy()


class DXFolderColorIndexGetter(FolderColorIndexGetter):

    implements(interfaces.IColorIndexGetter)
    adapts(IFolder, Interface, ICatalogBrain)


class ColorIndexGetter(object):

    implements(interfaces.IColorIndexGetter)
    adapts(Interface, Interface, ICatalogBrain)

    def __init__(self, context, request, source):
        self.context = context
        self.request = request
        self.source = source
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context),
                                                                  None)

    def getColorIndex(self):
        context, request, brain = self.context, self.request, self.source
        criteriaItems = getMultiAdapter((context, request),
                                        interfaces.ICriteriaItems)()
        final = {'color':'',
                 'class':''}
        if not criteriaItems:
            return final.copy()
        colorsDict = self.calendar.queryColors

        props = getToolByName(self.context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'
        selectedItems = getCookieItems(request, criteriaItems['name'], charset)
        if not selectedItems:
            selectedItems = criteriaItems['values']

        if not isinstance(selectedItems, list):
            selectedItems = [selectedItems, ]
        final = {}
        if criteriaItems:
            brainVal = getattr(brain, criteriaItems['name'])
            brainVal = isinstance(brainVal, (tuple, list)) and brainVal or [brainVal, ]
            valColorsDict = colorsDict.get(criteriaItems['name'], {})
            for val in brainVal:
                if criteriaItems['values'].count(val) != 0 \
                   and val in selectedItems:
                    final['color'] = colorsDict.get(criteriaItems['name'], {}).get(val, '')
                    colorIndex = ' colorIndex-%s' % criteriaItems['values'].index(val)
                    colorIndex += ' ' + criteriaItems['name'] + colorIndex
                    final['class'] = colorIndex
        return final.copy()


class FolderEventSource(object):
    """Event source that get events from the topic
    """
    implements(interfaces.IEventSource)
    adapts(IATFolder, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal = context.portal_url.getPortalObject()
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context),
                                                                  None)

    def convertAsList(self, items):
        if isinstance(items, str):
            return [items, ]

        return items

    def _getBrains(self, _args, filters):

        searchMethod = getMultiAdapter((self.context,),
                           interfaces.ISolgemaFullcalendarCatalogSearch)
        brains = searchMethod.searchResults(_args)

        for filt in filters:
            if isinstance(filt['values'], str):
                brains = [a for a in brains if not getattr(a, filt['name'])]
            else:
                brains = [a for a in brains
                          if not getattr(a, filt['name'])
                             or len([b for b in self.convertAsList(getattr(a,
                                                                 filt['name']))
                                    if b in filt['values']]) > 0]

        return brains

    def getTargetFolder(self):
        target_folder = getattr(self.calendar, 'target_folder', None)
        if target_folder:
            addContext = self.portal.unrestrictedTraverse('/' + self.portal.id \
                                                          + target_folder)
        elif IATFolder.providedBy(self.context):
            addContext = self.context
        else:
            addContext = aq_parent(aq_inner(self.context))
        return addContext

    def _getCriteriaArgs(self):
        return ({'path':
                    {'query':'/'.join(self.getTargetFolder().getPhysicalPath()),
                     'depth':1}},
                [])

    def getEvents(self):
        context = self.context
        request = self.request
        _args, filters = self._getCriteriaArgs()
        try:
            end = int(request.get('end'))
        except:
            end = request.get('end')
        try:
            start = int(request.get('start'))
        except:
            start = request.get('start')
        _args['start'] = {'query': DateTime(end), 'range':'max'}
        _args['end'] = {'query': DateTime(start), 'range':'min'}

        brains = self._getBrains(_args, filters)
        topicEventsDict = getMultiAdapter((context, self.request),
                              interfaces.ISolgemaFullcalendarTopicEventDict)
        result = topicEventsDict.createDict(brains, _args)
        return result

    def getICalObjects(self):
        _args, filters = self._getCriteriaArgs()
        brains = self._getBrains(_args, filters)
        return [a.getObject() for a in brains]

    def getICal(self):
        _args, filters = self._getCriteriaArgs()
        brains = self._getBrains(_args, filters)
        if HAS_CALEXPORT_SUPPORT:
            _cal = lambda b: calendar_from_event(b.getObject())
            _isevent = lambda c: isinstance(c, EVENT_COMPONENT_CLS)
            _vevents = lambda cal: filter(_isevent, cal.subcomponents)
            events = list(itertools.chain(*[_vevents(_cal(b)) for b in brains]))
            # ical export of components has trailing CRLF between each VEVENT
            return ''.join([e.to_ical() for e in events])
        else:
            return ''.join([b.getObject().getICal() for b in brains])


class DXFolderEventSource(FolderEventSource):
    """Event source that get events from the folder
    """
    implements(interfaces.IEventSource)
    adapts(IFolder, Interface)

    def getTargetFolder(self):
        target_folder = getattr(self.calendar, 'target_folder', None)
        if target_folder:
            addContext = self.portal.unrestrictedTraverse('/' + self.portal.id \
                                                          + target_folder)
        elif IFolder.providedBy(self.context):
            addContext = self.context
        else:
            addContext = aq_parent(aq_inner(self.context))
        return addContext


class listBaseQueryTopicCriteria(object):
    """Get criterias dicts for topic and collections
    """
    implements(interfaces.IListBaseQueryCriteria)
    adapts(IATTopic)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        li = []
        for criteria in self.context.listCriteria():
            if criteria.meta_type == 'ATPortalTypeCriterion' \
                    and len(criteria.getCriteriaItems()[0][1]) > 0:
                li.append({'i':criteria.Field(),
                           'v':criteria.getCriteriaItems()[0][1],
                           'o':criteria.meta_type})
            if criteria.meta_type in ['ATSelectionCriterion',
                                      'ATListCriterion'] \
                    and criteria.getCriteriaItems() \
                    and len(criteria.getCriteriaItems()[0]) > 1 \
                    and len(criteria.getCriteriaItems()[0][1]['query']) > 0:
                li.append({'i':criteria.Field(),
                           'v':criteria.getCriteriaItems()[0][1]['query'],
                           'o':criteria.meta_type})

        return li


class listBaseQueryCollectionCriteria(object):
    """Get criterias dicts for topic and collections
    """
    implements(interfaces.IListBaseQueryCriteria)
    adapts(ICollection)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        return self.context.getField('query').getRaw(self.context)


class listBaseQueryDXCollectionCriteria(object):
    """Get criterias dicts for DX-collections
    """
    implements(interfaces.IListBaseQueryCriteria)
    adapts(IDXCollection)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        return self.context.query


class listCriteriasTopicAdapter(object):
    """Get criterias dicts for topic
    """
    implements(interfaces.IListCriterias)
    adapts(IATTopic)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(self.context),
                                                             None)
        li = interfaces.IListBaseQueryCriteria(self.context)()
        for criteria in li:
            if criteria['o'] == 'ATPortalTypeCriterion' \
               and len(criteria['v']) == 1:
                li.remove(criteria)

        if hasattr(calendar, 'availableCriterias') \
           and getattr(calendar, 'availableCriterias', None) != None:
            li = [a for a in li if a['i'] in calendar.availableCriterias]

        return dict([(a['i'], a['v']) for a in li])


class listCriteriasCollectionAdapter(object):
    """Get criterias dicts for collections
    """
    implements(interfaces.IListCriterias)
    adapts(ICollection)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(self.context),
                                                             None)
        li = interfaces.IListBaseQueryCriteria(self.context)()
        for criteria in li:
            if criteria['i'] == 'portal_type' and len(criteria['v']) == 1:
                li.remove(criteria)

        if hasattr(calendar, 'availableCriterias') \
           and getattr(calendar, 'availableCriterias', None) != None:
            li = [a for a in li if a['i'] in calendar.availableCriterias]

        return dict([(a['i'], a['v']) for a in li])


class listCriteriasDXCollectionAdapter(object):
    """Get criterias dicts for collections
    """
    implements(interfaces.IListCriterias)
    adapts(IDXCollection)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(self.context),
                                                             None)
        li = deepcopy(interfaces.IListBaseQueryCriteria(self.context)())
        for criteria in li:
            if criteria['i'] == 'portal_type' and len(criteria['v']) == 1:
                li.remove(criteria)

        if hasattr(calendar, 'availableCriterias') \
           and getattr(calendar, 'availableCriterias', None) != None:
            li = [a for a in li if a['i'] in calendar.availableCriterias]

        return dict([(a['i'], a['v']) for a in li])


def getTopic(context, request):
    if not interfaces.ISolgemaFullcalendarMarker.providedBy(context):
        utils = getToolByName(context, 'plone_utils')
        page = utils.getDefaultPage(context, request)
        pageItem = page and getattr(context, page) or None
        if interfaces.ISolgemaFullcalendarMarker.providedBy(pageItem):
            return pageItem

        portal = getToolByName(context, 'portal_url').getPortalObject()
        referer = unquote(request.get('last_referer',
                                      request.get('HTTP_REFERER')))
        if referer.find('?') != -1:
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
            topic_url = topic_url + '/' + page
            topic = getattr(topic, page)
            if interfaces.ISolgemaFullcalendarMarker.providedBy(topic):
                return topic
        url = '/' + portal.id + topic_url
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


class CriteriaItemsTopic(object):

    implements(interfaces.ICriteriaItems)
    adapts(IATTopic, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        topic = getTopic(self.context, self.request)
        listCriteria = topic.listCriteria()
        topicCriteria = interfaces.IListCriterias(topic)()
        if topicCriteria:
            selectedCriteria = self.request.cookies.get('sfqueryDisplay',
                                   topic.REQUEST.cookies.get('sfqueryDisplay',
                                                       topicCriteria.keys()[0]))
            criteria = [a for a in listCriteria if a.Field() == selectedCriteria]
        else:
            criteria = listCriteria

        criteria = [a for a in criteria if a.meta_type in
                    ['ATPortalTypeCriterion',
                     'ATSelectionCriterion',
                     'ATListCriterion']
                   ]
        if not criteria:
            return False
        criteria = criteria[0]
        if criteria.meta_type == 'ATPortalTypeCriterion':
            return {
                'name': criteria.Field(),
                'values': list(criteria.getCriteriaItems()[0][1])
            }
        if criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion']:
            return {
                'name': criteria.Field(),
                'values': list(criteria.getCriteriaItems()[0][1]['query']) + ['']
            }
        return False


class CriteriaItemsCollection(object):

    implements(interfaces.ICriteriaItems)
    adapts(ICollection, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        topic = getTopic(self.context, self.request)
        listCriteria = self.context.getField('query').getRaw(self.context)
        topicCriteria = interfaces.IListCriterias(topic)()
        if topicCriteria:
            selectedCriteria = self.request.cookies.get('sfqueryDisplay',
                                   topic.REQUEST.cookies.get('sfqueryDisplay',
                                                       topicCriteria.keys()[0]))
            criteria = [a for a in listCriteria if a['i'] == selectedCriteria]
        else:
            criteria = listCriteria

        criteria = [a for a in criteria if a['o'] in
                    ['plone.app.querystring.operation.selection.is',
                     'plone.app.querystring.operation.list.contains'] or
                    a['i'] == 'portal_type']
        if not criteria:
            return False

        criteria = criteria[0]

        return {'name': criteria['i'],
                'values': criteria['v']}


class CriteriaItemsDXCollection(object):

    implements(interfaces.ICriteriaItems)
    adapts(IDXCollection, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        topic = getTopic(self.context, self.request)
        listCriteria = self.context.query
        topicCriteria = interfaces.IListCriterias(topic)()
        if topicCriteria:
            selectedCriteria = self.request.cookies.get('sfqueryDisplay',
                                   topic.REQUEST.cookies.get('sfqueryDisplay',
                                                       topicCriteria.keys()[0]))
            criteria = [a for a in listCriteria if a['i'] == selectedCriteria]
        else:
            criteria = listCriteria

        criteria = [a for a in criteria if a['o'] in
                    ['plone.app.querystring.operation.selection.is',
                     'plone.app.querystring.operation.list.contains'] or
                    a['i'] == 'portal_type']
        if not criteria:
            return False

        criteria = criteria[0]

        return {'name': criteria['i'],
                'values': criteria['v']}


class TopicEventSource(FolderEventSource):
    """Event source that get events from the topic
    """
    implements(interfaces.IEventSource)
    adapts(IATTopic, Interface)

    def _getCriteriaArgs(self):
        context, request = self.context, self.request
        response = request.response

        query = context.buildQuery()
        topicCriteria = interfaces.IListCriterias(context)()
        listCriteria = context.listCriteria()
        _args = {}
        if not query:
            return ({}, [])

        props = getToolByName(context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'

        if 'Type' in query.keys():
            items = getCookieItems(request, 'Type', charset)
            if items:
                _args['Type'] = items
            else:
                _args['Type'] = query['Type']
        elif 'portal_type' in query.keys():
            items = getCookieItems(request, 'portal_type', charset)
            if items:
                _args['portal_type'] = items
            else:
                _args['portal_type'] = query['portal_type']
        filters = []
        #reinit cookies if criterions are no more there
        for cId in [c.Field() for c in listCriteria]:
            if cId not in topicCriteria.keys():
                response.expireCookie(cId)

        if request.cookies.get('sfqueryDisplay', None) not in topicCriteria.keys():
            response.expireCookie('sfqueryDisplay')

        for criteria in listCriteria:
            criteriaId = criteria.Field()
            if criteriaId and criteria.meta_type not in ['ATSelectionCriterion',
                                                         'ATListCriterion',
                                                         'ATSortCriterion',
                                                         'ATPortalTypeCriterion']:
                _args[criteriaId] = query[criteriaId]
            elif criteria.meta_type in ['ATSelectionCriterion',
                                        'ATListCriterion'] \
               and criteria.getCriteriaItems() \
               and len(criteria.getCriteriaItems()[0]) > 1 \
               and len(criteria.getCriteriaItems()[0][1]['query']) > 0:
                items = getCookieItems(request, criteriaId, charset)
                if items and criteriaId in topicCriteria.keys():
                    if 'undefined' in items:
                        filters.append({'name':criteriaId, 'values':items})
                    else:
                        _args[criteriaId] = items
                else:
                    _args[criteriaId] = query[criteriaId]

        return _args, filters

    def getEvents(self):
        context = self.context
        request = self.request
        _args, filters = self._getCriteriaArgs()
        try:
            end = int(request.get('end'))
        except:
            end = request.get('end')
        try:
            start = int(request.get('start'))
        except:
            start = request.get('start')
        _args['start'] = {'query': DateTime(end), 'range':'max'}
        _args['end'] = {'query': DateTime(start), 'range':'min'}
        if getattr(self.calendar, 'overrideStateForAdmin', True) \
           and _args.has_key('review_state'):
            pm = getToolByName(context, 'portal_membership')
            user = pm.getAuthenticatedMember()
            if user and user.has_permission('Modify portal content', context):
                del _args['review_state']

        brains = self._getBrains(_args, filters)
        topicEventsDict = getMultiAdapter((context, self.request),
                                  interfaces.ISolgemaFullcalendarTopicEventDict)
        result = topicEventsDict.createDict(brains, _args)
        return result


class CollectionEventSource(TopicEventSource):
    """Event source that get events from the plone.app.collection
    """
    implements(interfaces.IEventSource)
    adapts(ICollection, Interface)

    def _getCriteriaArgs(self):
        context, request = self.context, self.request
        response = request.response

        queryField = context.getField('query')
        listCriteria = queryField.getRaw(context)

        # Handle operator-only query strings accordingly.
        query = dict(['v' in a and (a['i'], a['v']) or (a['i'], a['o'])
                      for a in listCriteria])

        topicCriteria = interfaces.IListCriterias(context)()
        _args = {}
        if not query:
            return ({}, [])

        props = getToolByName(context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'

        if 'Type' in query.keys():
            items = getCookieItems(request, 'Type', charset)
            if items:
                _args['Type'] = items
            else:
                _args['Type'] = query['Type']
        filters = []
        #reinit cookies if criterions are no more there
        for cId in [c['i'] for c in listCriteria]:
            if cId not in topicCriteria.keys():
                response.expireCookie(cId)

        if request.cookies.get('sfqueryDisplay', None) not in topicCriteria.keys():
            response.expireCookie('sfqueryDisplay')

        for criteria in listCriteria:
            criteriaId = criteria['i']
            if criteria['o'] not in \
               ['plone.app.querystring.operation.selection.is',
                'plone.app.querystring.operation.list.contains'] \
               and criteriaId != 'portal_type':
                _args[criteriaId] = query[criteriaId]
            else:
                items = getCookieItems(request, criteriaId, charset)
                if items and criteriaId in topicCriteria.keys():
                    if 'undefined' in items:
                        filters.append({'name':criteriaId, 'values':items})
                    else:
                        _args[criteriaId] = items
                else:
                    _args[criteriaId] = query[criteriaId]

        return _args, filters

    def getEvents(self):
        context = self.context
        brains = context.queryCatalog(batch=False)
        topicEventsDict = getMultiAdapter(
            (context, self.request),
            interfaces.ISolgemaFullcalendarTopicEventDict)
        result = topicEventsDict.createDict(brains, {})
        return result


def convert(value):
    query = value['query']
    if isinstance(query, unicode):
        query = query.encode("utf-8")
    elif isinstance(query, list):
        query = [
            item.encode("utf-8") if isinstance(item, unicode) else item
            for item in query
        ]
    else:
        pass
    value['query'] = query
    return value


class DXCollectionEventSource(TopicEventSource):
    """Event source that get events from the collection
    """
    implements(interfaces.IEventSource)
    adapts(IDXCollection, Interface)

    def _getCriteriaArgs(self):
        context, request = self.context, self.request
        response = request.response

        listCriteria = context.query

        query = dict([
            (key, convert(value))
            for key, value in queryparser.parseFormquery(context, listCriteria).items()
        ])

        topicCriteria = interfaces.IListCriterias(context)()
        _args = {}
        if not query:
            return ({}, [])

        props = getToolByName(context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'

        if 'Type' in query.keys():
            items = getCookieItems(request, 'Type', charset)
            if items:
                _args['Type'] = items
            else:
                _args['Type'] = query['Type']
        filters = []
        #reinit cookies if criterions are no more there
        for cId in [c['i'] for c in listCriteria]:
            if cId not in topicCriteria.keys():
                response.expireCookie(cId)

        if request.cookies.get('sfqueryDisplay', None) not in topicCriteria.keys():
            response.expireCookie('sfqueryDisplay')

        for criteria in listCriteria:
            criteriaId = criteria['i']
            if criteria['o'] not in \
               ['plone.app.querystring.operation.selection.is',
                'plone.app.querystring.operation.list.contains'] \
               and criteriaId != 'portal_type':
                _args[criteriaId] = query[criteriaId]
            else:
                items = getCookieItems(request, criteriaId, charset)
                if items and criteriaId in topicCriteria.keys():
                    if 'undefined' in items:
                        filters.append({'name':criteriaId, 'values':items})
                    else:
                        _args[criteriaId] = items
                else:
                    _args[criteriaId] = query[criteriaId]

        return _args, filters


class StandardEventSource(object):
    """Event source that display an event
    """
    implements(interfaces.IEventSource)
    adapts(IEvent_GENERIC, Interface)

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
        wft = getToolByName(context, 'portal_workflow')
        state = wft.getInfoFor(context, 'review_state')
        member = context.portal_membership.getAuthenticatedMember()
        editable = bool(member.has_permission('Modify portal content', context))
        extraClass = self.getObjectExtraClass()
        typeClass = ' type-' + context.portal_type

        events = []
        if handle_recurrence(self.request) and IRecurrenceSupport(context, None):
            events = get_recurring_events(self.request, context)
        else:
            events = context
        return (dict_from_events(
            events,
            editable=editable,
            state=state,
            css=typeClass + extraClass
            ))

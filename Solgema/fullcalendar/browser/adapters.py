from DateTime import DateTime
from Acquisition import aq_inner
from AccessControl import getSecurityManager
from zope.interface import implements, Interface
from zope.component import queryAdapter, adapts, getMultiAdapter, getAdapters
try:
    from Products.ZCatalog.interfaces import ICatalogBrain
except:
    ICatalogBrain = Interface
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interface import IATTopic, IATFolder

from Solgema.fullcalendar.browser.views import getCopyObjectsUID, getColorIndex
from Solgema.fullcalendar import interfaces
from Solgema.fullcalendar.browser.views import getCookieItems

try:
    from plone.app.event.ical import EventsICal
    HAS_CALEXPORT_SUPPORT = True
except ImportError:
    HAS_CALEXPORT_SUPPORT = False

try:
    from plone.app.event.interfaces import IEvent
    hasPloneAppEvent = True
except ImportError:
    from Products.ATContentTypes.interface import IATEvent as IEvent
    hasPloneAppEvent = False

try:
    from plone.app.event.interfaces import IRecurrence
    HAS_RECURRENCE_SUPPORT = True
except ImportError:
    HAS_RECURRENCE_SUPPORT = False

try:
    from plone.app.collection.interfaces import ICollection
except:
    ICollection = Interface

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
        if type(brain.end) != DateTime:
            brainend = DateTime(brain.end)
            brainstart = DateTime(brain.start)
        else:
            brainend = brain.end
            brainstart = brain.start

        if brain.UID in editableEvents:
            editable = True
        else:
            editable = False

        if brainend - brainstart > 1.0:
            allday = True
        else:
            allday = False

        if getattr(brain, 'SFAllDay', None) in [False,True]:
            allday = brain.SFAllDay

        copycut = ''
        if self.copyDict and brain.getPath() == self.copyDict['url']:
            copycut = self.copyDict['op'] == 1 and ' event_cutted' or ' event_copied'
        typeClass = ' type-'+brain.portal_type
        colorDict = getColorIndex(self.context, self.request, brain=brain)
        colorIndex = colorDict.get('class', '')
        color = colorDict.get('color', '')
        extraClass = self.getBrainExtraClass(brain)
        HANDLE_RECURRENCE = HAS_RECURRENCE_SUPPORT and self.request.get('start') and self.request.get('end')
        if HANDLE_RECURRENCE:
            event = brain.getObject()
            start = DateTime(self.request.get('start'))
            end = DateTime(self.request.get('end'))
            occurences = IRecurrence(event).occurrences(limit_start=start, limit_end=end)
            occurenceClass = ' occurence'
        else:
            occurences = [(brainstart.rfc822(), brainend.rfc822())]
            occurenceClass = ''
        events = []
        for occurence_start, occurence_end in occurences:
            events.append({
                "id": "UID_%s" % (brain.UID),
                "title": brain.Title,
                "description": brain.Description,
                "start": HANDLE_RECURRENCE and occurence_start.isoformat() or occurence_start,
                "end": HANDLE_RECURRENCE and occurence_end.isoformat() or occurence_end,
                "url": brain.getURL(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled state-" + str(brain.review_state) + (editable and " editable" or "")+copycut+typeClass+colorIndex+extraClass+occurenceClass,
                "color": color})
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
        colorDict = getColorIndex(self.context, self.request, eventPhysicalPath)
        colorIndex = colorDict.get('class', '')
        color = colorDict.get('color', '')
        extraClass = self.getObjectExtraClass(item)
        HANDLE_RECURRENCE = HAS_RECURRENCE_SUPPORT and self.request.get('start') and self.request.get('end')
        if HANDLE_RECURRENCE:
            start = DateTime(self.request.get('start'))
            end = DateTime(self.request.get('end'))
            occurences = IRecurrence(item).occurrences(limit_start=start, limit_end=end)
            occurenceClass = ' occurence'
        else:
            occurences = [(item.start().rfc822(), item.end().rfc822())]
            occurenceClass = ''
        events = []
        for occurence_start, occurence_end in occurences:
            events.append({
                "status": "ok",
                "id": "UID_%s" % (item.UID()),
                "title": item.Title(),
                "description": item.Description(),
                "start": HANDLE_RECURRENCE and occurence_start.isoformat() or occurence_start,
                "end": HANDLE_RECURRENCE and occurence_end.isoformat() or occurence_end,
                "url": item.absolute_url(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled state-" + str(state) + (editable and " editable" or "")+copycut+typeClass+colorIndex+extraClass+occurenceClass,
                "color": color})

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
        event = self.context
        context = self.context
        referer = self.request.get('HTTP_REFERER')
        if referer:
            portal = getToolByName(self.context, 'portal_url').getPortalObject()
            url = '/'+portal.id+referer.replace(portal.absolute_url(), '')
            context = portal.restrictedTraverse(url)
        eventPhysicalPath = '/'.join(event.getPhysicalPath())
        wft = getToolByName(context, 'portal_workflow')
        state = wft.getInfoFor(event, 'review_state')
        member = context.portal_membership.getAuthenticatedMember()
        editable = bool(member.has_permission('Modify portal content', event))
        allday = (event.end() - event.start()) > 1.0

        adapted = interfaces.ISFBaseEventFields(event, None)
        if adapted:
            allday = adapted.allDay

        copycut = ''
        if self.copyDict and eventPhysicalPath == self.copyDict['url']:
            copycut = self.copyDict['op'] == 1 and ' event_cutted' or ' event_copied'

        typeClass = ' type-' + event.portal_type
        colorDict = getColorIndex(context, self.request, eventPhysicalPath)
        colorIndex = colorDict.get('class', '')
        color = colorDict.get('color', '')
        extraClass = self.getExtraClass()

        HANDLE_RECURRENCE = HAS_RECURRENCE_SUPPORT and self.request.get('start') and self.request.get('end')
        if HANDLE_RECURRENCE:
            start = DateTime(self.request.get('start'))
            end = DateTime(self.request.get('end'))
            occurences = IRecurrence(event).occurrences(limit_start=start, limit_end=end)
            occurenceClass = ' occurence'
        else:
            occurences = [(event.start().rfc822(), event.end().rfc822())]
            occurenceClass = ''
        events = []
        for occurence_start, occurence_end in occurences:
            events.append({
                "status": "ok",
                "id": "UID_%s" % (event.UID()),
                "title": event.Title(),
                "description": event.Description(),
                "start": HANDLE_RECURRENCE and occurence_start.isoformat() or occurence_start,
                "end": HANDLE_RECURRENCE and occurence_end.isoformat() or occurence_end,
                "url": event.absolute_url(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled state-" + str(state) + (editable and " editable" or "")+copycut+typeClass+colorIndex+extraClass+occurenceClass,
                "color": color})

        return events

class FolderColorIndexGetter(object):

    implements(interfaces.IColorIndexGetter)
    adapts(IATFolder, Interface, ICatalogBrain)

    def __init__(self, context, request, source):
        self.context = context
        self.request = request
        self.source = source
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context), None)

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
            selectedItems = [selectedItems,]
        for val in availableSubFolders:
            if val in selectedItems:
                for parentid in brain.getPath().split('/'):
                    if val == parentid:
                        final['color'] = colorsDict.get('subFolders', {}).get(val, '')
                        colorIndex = ' colorIndex-'+str(availableSubFolders.index(val))
                        colorIndex += ' subFolderscolorIndex-'+str(availableSubFolders.index(val))
                        final['class'] = colorIndex

        return final.copy()

class ColorIndexGetter(object):

    implements(interfaces.IColorIndexGetter)
    adapts(Interface, Interface, ICatalogBrain)

    def __init__(self, context, request, source):
        self.context = context
        self.request = request
        self.source = source
        self.calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(context), None)

    def getColorIndex(self):
        context, request, brain = self.context, self.request, self.source
        criteriaItems = getMultiAdapter((context, request),  interfaces.ICriteriaItems)()
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
            selectedItems = [selectedItems,]
        final = {}
        if criteriaItems:
            brainVal = getattr(brain, criteriaItems['name'])
            brainVal = isinstance(brainVal, (tuple, list)) and brainVal or [brainVal,]
            valColorsDict = colorsDict.get(criteriaItems['name'], {})
            for val in brainVal:
                if criteriaItems['values'].count(val) != 0 and val in selectedItems:
                    final['color'] = colorsDict.get(criteriaItems['name'], {}).get(val, '')
                    colorIndex = ' colorIndex-'+str(criteriaItems['values'].index(val))
                    colorIndex += ' '+criteriaItems['name']+'colorIndex-'+str(criteriaItems['values'].index(val))
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

    def getTargetFolder(self):
        target_folder = getattr(self.calendar, 'target_folder', None)
        if target_folder:
            addContext = self.portal.unrestrictedTraverse('/'+self.portal.id+target_folder)
        elif IATFolder.providedBy(self.context):
            addContext = self.context
        else:
            addContext = aq_parent(aq_inner(self.context))
        return addContext

    def _getCriteriaArgs(self):
        return ({'path':{'query':'/'.join(self.getTargetFolder().getPhysicalPath()), 'depth':1}}, [])

    def getEvents(self):
        context = self.context
        request = self.request
        args, filters = self._getCriteriaArgs()
        try:
            end = int(request.get('end'))
        except:
            end = request.get('end')
        try:
            start = int(request.get('start'))
        except:
            start = request.get('start')
        args['start'] = {'query': DateTime(end), 'range':'max'}
        args['end'] = {'query': DateTime(start), 'range':'min'}

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

class listBaseQueryTopicCriteria(object):
    """Get criterias dicts for topic and collections
    """
    implements(interfaces.IListBaseQueryTopicCriteria)
    adapts(IATTopic)

    def __init__(self, context):
        self.context = context
    
    def __call__(self):
        li = []
        for criteria in self.context.listCriteria():
            if criteria.meta_type == 'ATPortalTypeCriterion' \
                    and len(criteria.getCriteriaItems()[0][1]) > 0:
                li.append({'i':criteria.Field(), 'v':criteria.getCriteriaItems()[0][1], 'o':criteria.meta_type})
            if criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion'] \
                    and criteria.getCriteriaItems() \
                    and len(criteria.getCriteriaItems()[0]) > 1 \
                    and len(criteria.getCriteriaItems()[0][1]['query']) > 0:
                li.append({'i':criteria.Field(), 'v':criteria.getCriteriaItems()[0][1]['query'], 'o':criteria.meta_type})

        return li

class listBaseQueryCollectionCriteria(object):
    """Get criterias dicts for topic and collections
    """
    implements(interfaces.IListBaseQueryTopicCriteria)
    adapts(ICollection)

    def __init__(self, context):
        self.context = context
    
    def __call__(self):
        return self.context.getField('query').getRaw(self.context)

class listCriteriasTopicAdapter(object):
    """Get criterias dicts for topic and collections
    """
    implements(interfaces.IListCriterias)
    adapts(IATTopic)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(self.context), None)
        li = interfaces.IListBaseQueryTopicCriteria(self.context)()
        for criteria in li:
            if criteria['o']=='ATPortalTypeCriterion' and len(criteria['v'])==1:
                li.remove(criteria)

        if hasattr(calendar, 'availableCriterias') and getattr(calendar, 'availableCriterias', None) != None:
            li = [a for a in li if a['i'] in calendar.availableCriterias]

        return dict([(a['i'], a['v']) for a in li])

class listCriteriasCollectionAdapter(object):
    """Get criterias dicts for topic and collections
    """
    implements(interfaces.IListCriterias)
    adapts(ICollection)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        calendar = interfaces.ISolgemaFullcalendarProperties(aq_inner(self.context), None)
        li = interfaces.IListBaseQueryTopicCriteria(self.context)()
        for criteria in li:
            if criteria['i']=='portal_type' and len(criteria['v'])==1:
                li.remove(criteria)

        if hasattr(calendar, 'availableCriterias') and getattr(calendar, 'availableCriterias', None) != None:
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
            selectedCriteria = self.request.cookies.get('sfqueryDisplay', topic.REQUEST.cookies.get('sfqueryDisplay', topicCriteria.keys()[0]))
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
            selectedCriteria = self.request.cookies.get('sfqueryDisplay', topic.REQUEST.cookies.get('sfqueryDisplay', topicCriteria.keys()[0]))
            criteria = [a for a in listCriteria if a['i'] == selectedCriteria]
        else:
            criteria = listCriteria

        criteria = [a for a in criteria if a['o'] in
                   ['plone.app.querystring.operation.selection.is', 'plone.app.querystring.operation.list.contains'] or 
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
        args = {}
        if not query:
            return ({}, [])

        props = getToolByName(context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'

        if 'Type' in query.keys():
            items = getCookieItems(request, 'Type', charset)
            if items:
                args['Type'] = items
            else:
                args['Type'] = query['Type']
        filters = []
        #reinit cookies if criterions are no more there
        for cId in [c.Field() for c in listCriteria]:
            if cId not in topicCriteria.keys():
                response.expireCookie(cId)

        if request.cookies.get('sfqueryDisplay', None) not in topicCriteria.keys():
            response.expireCookie('sfqueryDisplay')

        for criteria in listCriteria:
            criteriaId = criteria.Field()
            if criteria.meta_type not in ['ATSelectionCriterion', 'ATListCriterion', 'ATSortCriterion', 'ATPortalTypeCriterion'] and criteriaId:
                args[criteriaId] = query[criteriaId]
            elif criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion'] and criteria.getCriteriaItems() and len(criteria.getCriteriaItems()[0])>1 and len(criteria.getCriteriaItems()[0][1]['query'])>0:
                items = getCookieItems(request, criteriaId, charset)
                if items and criteriaId in topicCriteria.keys():
                    if 'undefined' in items:
                        filters.append({'name':criteriaId, 'values':items})
                    else:
                        args[criteriaId] = items
                else:
                    args[criteriaId] = query[criteriaId]

        return args, filters

    def getEvents(self):
        context = self.context
        request = self.request
        args, filters = self._getCriteriaArgs()
        try:
            end = int(request.get('end'))
        except:
            end = request.get('end')
        try:
            start = int(request.get('start'))
        except:
            start = request.get('start')
        args['start'] = {'query': DateTime(end), 'range':'max'}
        args['end'] = {'query': DateTime(start), 'range':'min'}
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

        query = dict([(a['i'], a['v']) for a in listCriteria])
        topicCriteria = interfaces.IListCriterias(context)()
        args = {}
        if not query:
            return ({}, [])

        props = getToolByName(context, 'portal_properties')
        charset = props and props.site_properties.default_charset or 'utf-8'

        if 'Type' in query.keys():
            items = getCookieItems(request, 'Type', charset)
            if items:
                args['Type'] = items
            else:
                args['Type'] = query['Type']
        filters = []
        #reinit cookies if criterions are no more there
        for cId in [c['i'] for c in listCriteria]:
            if cId not in topicCriteria.keys():
                response.expireCookie(cId)

        if request.cookies.get('sfqueryDisplay', None) not in topicCriteria.keys():
            response.expireCookie('sfqueryDisplay')

        for criteria in listCriteria:
            criteriaId = criteria['i']
            if criteria['o'] not in ['plone.app.querystring.operation.selection.is', 'plone.app.querystring.operation.list.contains'] and criteriaId != 'portal_type':
                args[criteriaId] = query[criteriaId]
            else:
                items = getCookieItems(request, criteriaId, charset)
                if items and criteriaId in topicCriteria.keys():
                    if 'undefined' in items:
                        filters.append({'name':criteriaId, 'values':items})
                    else:
                        args[criteriaId] = items
                else:
                    args[criteriaId] = query[criteriaId]

        return args, filters

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
        HANDLE_RECURRENCE = HAS_RECURRENCE_SUPPORT and self.request.get('start') and self.request.get('end')
        if HANDLE_RECURRENCE:
            start  = DateTime(self.request.get('start'))
            end = DateTime(self.request.get('end'))
            occurences = IRecurrence(context).occurrences(limit_start=start, limit_end=end)
            occurenceClass = ' occurence'
        else:
            occurences = [(context.start().rfc822(), context.end().rfc822())]
            occurenceClass = ''
        events = []
        for occurence_start, occurence_end in occurences:
            events.append({
                "status": "ok",
                "id": "UID_%s" % (context.UID()),
                "title": context.Title(),
                "description": context.Description(),
                "start": HANDLE_RECURRENCE and occurence_start.isoformat() or occurence_start,
                "end": HANDLE_RECURRENCE and occurence_end.isoformat() or occurence_end,
                "url": context.absolute_url(),
                "editable": editable,
                "allDay": allday,
                "className": "contextualContentMenuEnabled state-" + str(state) + (editable and " editable" or "")+typeClass+extraClass+occurenceClass
                })
        return events



from urllib import quote_plus
try:
    import json
except:
    import simplejson as json

from DateTime import DateTime
from OFS import CopySupport
from OFS.CopySupport import CopyError
from zExceptions import Unauthorized
from ZODB.POSException import ConflictError
from Acquisition import aq_inner, aq_parent
from AccessControl import getSecurityManager
from zope.component import getMultiAdapter, queryMultiAdapter, queryUtility
from zope.i18n import translate
from zope.i18nmessageid import MessageFactory

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as PLMF
from Products.CMFPlone.utils import transaction_note
from Products.CMFPlone.utils import safe_unicode
from plone.i18n.normalizer.interfaces import IIDNormalizer

from Solgema.fullcalendar import interfaces


DTMF = MessageFactory('collective.z3cform.datetimewidget')

# Check for Plone versions
try:
   from plone.app.upgrade import v40
   HAS_PLONE30 = True
   HAS_PLONE40 = True
except ImportError:
   HAS_PLONE40 = False
   try:
       from Products.CMFPlone.migrations import v3_0
   except ImportError:
       HAS_PLONE30 = False
   else:
       HAS_PLONE30 = True


def getCopyObjectsUID(REQUEST):
    if REQUEST is not None and REQUEST.has_key('__cp'):
        cp = REQUEST['__cp']
    else:
        return []

    op, mdatas = CopySupport._cb_decode(cp)
    return {'op':op, 'url': ['/'.join(a) for a in mdatas][0]}


class BaseActionView(BrowserView):

    def __init__(self, context, request):
        super(BaseActionView, self).__init__(context, request)
        request.response.setHeader('Cache-Control', 'no-cache')
        request.response.setHeader('Pragma', 'no-cache')


class SFJsonEvent(BaseActionView):

    def __call__(self, *args, **kw):
        eventDict = getMultiAdapter((self.context, self.request),
                                    interfaces.ISolgemaFullcalendarEventDict)()
        return json.dumps(eventDict, sort_keys=True)


class SFDisplayAddMenu(BaseActionView):

    def __call__(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        context = aq_inner(self.context)
        target_folder = getattr(interfaces.ISolgemaFullcalendarProperties(context, None), 'target_folder', None)
        target_folder = target_folder \
                    and portal.unrestrictedTraverse('/'+ portal.id + target_folder) \
                    or aq_parent(context)

        if not getSecurityManager().checkPermission('Add portal content', target_folder):
            raise Unauthorized, "You can't add an event on %s" % str(target_folder)

        query = self.context.buildQuery()
        copyDict = getCopyObjectsUID(self.request)

        # The 'Item Type' criteria uses the 'Type' index while the 'Item Type
        # (internal)' criteria uses the 'portal_type' index.
        #
        # We need to check for both, portal_type first, because it's more
        # specific than 'Type', which just indexes the content type's Title
        # property (which can be non-unique).
        index = query and query.get('portal_type') or query.get('Type') 
        if index:
            if isinstance(index, (list, tuple)) and len(index) > 1:
                return json.dumps({'display': True})

            portal_type = isinstance(index, (tuple, list)) and index[0] or index
            if copyDict and portal.restrictedTraverse(copyDict['url']).portal_type == portal_type:
                return json.dumps({'display': True})
            else:
                portal_type = isinstance(query['Type'], (tuple, list)) and query['Type'][0] or query['Type']
                if copyDict and portal.restrictedTraverse(copyDict['url']).portal_type == portal_type:
                    return json.dumps({'display': True})
        else:
            portal_type = 'Event'

        pTypes = [a for a in getToolByName(context, 'portal_types').listTypeInfo() if a.id == portal_type]
        pTypeTitle = pTypes and pTypes[0].Title() or portal_type
        typeTitle = translate(pTypeTitle, context=self.request)
        if HAS_PLONE40:
            title = PLMF(u'heading_add_item', default='Add ${itemtype}', mapping={'itemtype' : typeTitle})
        else:
            title = PLMF(u'label_add_type', default='Add ${type}', mapping={'type' : typeTitle})

        return json.dumps({'display': False, 'type': portal_type,
                           'title': translate(title, context=self.request)})


class SFAddMenu(BaseActionView):

    def __init__(self, context, request):
        super(SFAddMenu, self).__init__(context, request)
        self.portal = getToolByName(self.context, 'portal_url').getPortalObject()
        self.portal_url = self.portal.absolute_url()
        self.adapted = interfaces.ISolgemaFullcalendarProperties(aq_inner(context),
                                                                 None)
        target_folder = getattr(self.adapted, 'target_folder', None)
        self.addContext = target_folder and self.portal.unrestrictedTraverse('/'+self.portal.id+target_folder) or aq_parent(aq_inner(self.context))
        self.EventAllDay = self.request.get('EventAllDay', False)
        self.ReqAllDay = self.EventAllDay and '&EventAllDay='+self.EventAllDay or ''
        self.startDate = self.request.get('startDate', '')
        self.endDate = self.request.get('endDate', '')
        self.query = self.context.buildQuery()
        self.addableTypes = self.getMenuAddableTypes(self.query)

    def getMenuAddableTypes(self, query=None):
        if not query:
            return ['Event',]
        types = query.get('portal_type') or self.query.get('Type') or ['Event',]
        if not isinstance(types, (tuple, list)):
            return [types]
        return types

    def getMenuFactory(self):
        idnormalizer = queryUtility(IIDNormalizer)
        baseUrl = self.addContext.absolute_url()
        portal_types = getToolByName(self.context, 'portal_types').listTypeInfo()
        aTypes = [a for a in portal_types if a.id in self.addableTypes]
        addingview = queryMultiAdapter((self.addContext, self.request), name='+')
        results = []
        for t in aTypes:
            typeId = t.id
            cssId = idnormalizer.normalize(typeId)
            cssClass = 'contenttype-%s' % cssId
            factory = t.factory
            if addingview is not None and \
               queryMultiAdapter((addingview, self.request), name=factory) is not None:
                url = '%s/+/%s' % (baseUrl, factory,)
            else:
                url = '%s/createSFEvent?type_name=%s&startDate=%s&endDate=%s' % (baseUrl, 
                       quote_plus(typeId), quote_plus(str(self.startDate)), quote_plus(str(self.endDate)))

            icon = t.getIcon()
            if icon:
                icon = '%s/%s' % (self.portal_url, icon)

            title = translate(t.Title(), context=self.request)
            results.append({ 'id'           : typeId,
                             'title'        : PLMF(u'label_add_type', default='Add ${type}', mapping={'type' : title}),
                             'description'  : t.Description(),
                             'action'       : url,
                             'selected'     : False,
                             'icon'         : icon,
                             'extra'        : {'id' : cssId, 'separator' : None, 'class' : cssClass},
                             'submenu'      : None,
                            })

        # Sort the addable content types based on their translated title
        results = [(translate(ctype['title'], context=self.request), ctype) for ctype in results]
        results.sort()
        results = [ctype[-1] for ctype in results]
        return results

    def getMenuPaste(self):
        """Return menu item entries in a TAL-friendly form."""
        copyDict = getCopyObjectsUID(self.request)
        query = self.context.buildQuery()
        portal_type = query and query.get('portal_type') or query.get('Type', None)
        portal_types = []
        if not copyDict:
            return []

        if portal_type and isinstance(portal_type, (tuple, list)):
            portal_types = portal_type
        elif portal_type:
            portal_types = [portal_type,]

        item = None
        try:
            item = self.portal.restrictedTraverse(copyDict['url'])
        except:
            pass

        if item and not item.portal_type in portal_types:
            return []

        results = []

        actions_tool = getToolByName(self.portal, 'portal_actions')
        pasteAction = [a for a in actions_tool.listActionInfos(object=aq_inner(self.addContext), categories=('object_buttons',)) if a['id'] == 'paste']

        plone_utils = getToolByName(self.portal, 'plone_utils')
        
        context_url = self.addContext.absolute_url()
        for action in pasteAction:
            if action['allowed']:
                cssClass = 'actionicon-object_buttons-%s' % action['id']
                icon = plone_utils.getIconFor('object_buttons', action['id'], None)
                if icon:
                    icon = '%s/%s' % (self.addContext.absolute_url(), icon)
                
                start_date = quote_plus(str(self.startDate))
                results.append({ 'title'       : action['title'],
                                 'description' : '',
                                 'action'      : '%s/SFJsonEventPaste?startDate=%s%s' % (context_url, start_date, self.ReqAllDay),
                                 'selected'    : False,
                                 'icon'        : icon,
                                 'extra'       : {'id': action['id'], 'separator': None, 'class': cssClass},
                                 'submenu'     : None,
                                 })
        return results

    def getMenuItems(self):
        return self.getMenuFactory()+self.getMenuPaste()


class SFJsonEventDelete(BaseActionView):

    def __call__(self):
        eventid = 'UID_'+self.context.UID()
        parent = self.context.aq_inner.aq_parent
        title = safe_unicode(self.context.title_or_id())

        try:
            lock_info = self.context.restrictedTraverse('@@plone_lock_info')
        except AttributeError:
            lock_info = None

        if lock_info is not None and lock_info.is_locked():
            status = 'locked'
            message = PLMF(u'${title} is locked and cannot be deleted.',
                mapping={u'title' : title})
        else:
            parent.manage_delObjects(self.context.getId())
            status = 'ok'
            message = PLMF(u'${title} has been deleted.',
                        mapping={u'title' : title})
            transaction_note('Deleted %s' % self.context.absolute_url())

        return json.dumps({'status':status, 'message':parent.translate(message), 'id':eventid})


class SFJsonEventCopy(BaseActionView):

    def __call__(self):
        title = safe_unicode(self.context.title_or_id())
        mtool = getToolByName(self.context, 'portal_membership')
        if not mtool.checkPermission('Copy or Move', self.context):
            message = PLMF(u'Permission denied to copy ${title}.',
                    mapping={u'title' : title})
            status = 'error'
            raise json.dumps({'status':status, 'message':self.context.translate(message)})

        parent = aq_parent(aq_inner(self.context))
        try:
            cp = parent.manage_copyObjects(self.context.getId())
            status = 'copied'
        except CopyError:
            status = 'error'
            message = PLMF(u'${title} is not copyable.',
                        mapping={u'title' : title})
            return json.dumps({'status':status, 'message':parent.translate(message)})

        message = PLMF(u'${title} copied.',
                    mapping={u'title' : title})
        transaction_note('Copied object %s' % self.context.absolute_url())
        contextId = 'UID_'+self.context.UID()
        return json.dumps({'status':status, 'message':self.context.translate(message), 'cp':cp, 'id':contextId})


class SFJsonEventCut(BaseActionView):

    def __call__(self):
        title = safe_unicode(self.context.title_or_id())

        mtool = getToolByName(self.context, 'portal_membership')
        if not mtool.checkPermission('Copy or Move', self.context):
            message = PLMF(u'Permission denied to copy ${title}.',
                    mapping={u'title' : title})
            status = 'error'
            raise json.dumps({'status':status, 'message':self.context.translate(message)})

        try:
            lock_info = self.context.restrictedTraverse('@@plone_lock_info')
        except AttributeError:
            lock_info = None

        parent = aq_parent(aq_inner(self.context))
        if lock_info is not None and lock_info.is_locked():
            status = 'error'
            message = PLMF(u'${title} is locked and cannot be cut.',
                        mapping={u'title' : title})
            return json.dumps({'status': status,
                               'message': parent.translate(message)})

        try:
            cp = parent.manage_cutObjects(self.context.getId())
            status = 'copied'
        except CopyError:
            status = 'error'
            message = PLMF(u'${title} is not copyable.',
                        mapping={u'title' : title})
            return json.dumps({'status':status, 'message':parent.translate(message)})

        message = PLMF(u'${title} copied.',
                    mapping={u'title' : title})
        transaction_note('Copied object %s' % self.context.absolute_url())
        contextId = 'UID_'+self.context.UID()
        return json.dumps({'status':status, 'message':self.context.translate(message), 'cp':cp, 'id':contextId})


class SFJsonEventPaste(BaseActionView):

    def __init__(self, context, request):
        super(SFJsonEventPaste, self).__init__(context, request)
        self.EventAllDay = self.request.get('EventAllDay', False) not in [False, 'false']
        self.startDate = self.request.get('startDate', '')
        self.portal = getToolByName(self.context, 'portal_url').getPortalObject()
        self.copyDict = getCopyObjectsUID(self.request)

    def createJsonEvent(self, event):
        return getMultiAdapter((event, self.request),
                               interfaces.ISolgemaFullcalendarEventDict)()

    def __call__(self):
        msg=PLMF(u'Copy or cut one or more items to paste.')
        if self.context.cb_dataValid():
            try:
                baseObject = self.portal.restrictedTraverse(self.copyDict['url'])
                baseId = 'UID_' + baseObject.UID()
                intervalle = baseObject.endDate - baseObject.startDate
                cb_copy_data = self.request['__cp']
                pasteList = self.context.manage_pasteObjects(cb_copy_data=cb_copy_data)
                newObject = getattr(self.context, pasteList[0]['new_id'])
                startDate = self.startDate
                if self.EventAllDay:
                    startDate = DateTime(self.startDate).strftime('%Y-%m-%d ')+baseObject.startDate.strftime('%H:%M')

                newObject.setStartDate(DateTime(startDate))
                newObject.setEndDate(newObject.start() + intervalle)
                newObject.reindexObject()
                transaction_note('Pasted content to %s' % (self.context.absolute_url()))
                return json.dumps({'status':'pasted',
                                   'event':self.createJsonEvent(newObject),
                                   'url':newObject.absolute_url(),
                                   'op':self.copyDict['op'],
                                   'id':baseId})
            except ConflictError:
                raise
            except ValueError:
                msg=PLMF(u'Disallowed to paste item(s).')
            except (Unauthorized, 'Unauthorized'):
                msg=PLMF(u'Unauthorized to paste item(s).')
            except CopyError: # fallback
                msg=PLMF(u'Paste could not find clipboard content.')

        return json.dumps({'status':'failure',
                           'message':self.context.translate(msg)})


class SolgemaFullcalendarWorkflowTransition(BaseActionView):

    def __call__(self):
        request = self.request
        event_path = request.get('event_path', None)
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        url_list = event_path.split('/content_status_modify?workflow_action=')
        item_path = url_list[0]
        workflow_action = url_list[1]
        portal_url = portal.absolute_url()
        event_url = item_path.replace(portal_url, '')
        event = portal.restrictedTraverse(portal.id + event_url)
        contentEditSuccess = 0
        portal_workflow = event.portal_workflow
        transitions = portal_workflow.getTransitionsFor(event)
        transition_ids = [t['id'] for t in transitions]
        comment = self.request.get('comment', None)
        effective_date = self.request.get('effective_date', None)
        expiration_date = self.request.get('expiration_date', None)

        if workflow_action in transition_ids \
                and not effective_date and event.EffectiveDate() == 'None':
            effective_date=DateTime()

        def editContent(obj, effective, expiry):
            kwargs = {}
            if effective and (isinstance(effective, DateTime) or len(effective) > 5): # may contain the year
                kwargs['effective_date'] = effective

            if expiry and (isinstance(expiry, DateTime) or len(expiry) > 5): # may contain the year
                kwargs['expiration_date'] = expiry

            event.plone_utils.contentEdit(obj, **kwargs)

        #You can transition content but not have the permission to ModifyPortalContent
        try:
            editContent(event, effective_date, expiration_date)
            contentEditSuccess = 1
        except (Unauthorized,'Unauthorized'):
            pass

        wfcontext = event

        # Create the note while we still have access to wfcontext
        note = 'Changed status of %s at %s' % (wfcontext.id, wfcontext.absolute_url())

        if workflow_action in transition_ids:
            wfcontext = event.portal_workflow.doActionFor(
                event, workflow_action, comment=comment)

        if not wfcontext:
            wfcontext = event

        #The object post-transition could now have ModifyPortalContent permission.
        if not contentEditSuccess:
            try:
                editContent(wfcontext, effective_date, expiration_date)
            except (Unauthorized,'Unauthorized'):
                pass

        transaction_note(note)
        eventDict = getMultiAdapter((event, request),
                                    interfaces.ISolgemaFullcalendarEventDict)()
        return json.dumps(eventDict, sort_keys=True)


class SolgemaFullcalendarDropView(BaseActionView):

    def __call__(self):
        request = self.context.REQUEST
        event_uid = request.get('event')

        if event_uid:
            event_uid = event_uid.split('UID_')[1]

        brains = self.context.portal_catalog(UID=event_uid)

        obj = brains[0].getObject()
        startDate, endDate = obj.start(), obj.end()
        dayDelta, minuteDelta = float(request.get('dayDelta')), float(request.get('minuteDelta'))

        startDate = startDate + dayDelta + minuteDelta / 1440.0
        endDate = endDate + dayDelta + minuteDelta / 1440.0

        obj.setStartDate(startDate)
        obj.setEndDate(endDate)

        adapted = interfaces.ISFBaseEventFields(obj, None)
        if adapted:
            if request.get('allDay', None) == 'true':
                setattr(adapted, 'allDay', True)
            if request.get('allDay', None) == 'false':
                setattr(adapted, 'allDay', False)

        obj.reindexObject()
        return True


class SolgemaFullcalendarResizeView(BaseActionView):

    def __call__(self):
        request = self.context.REQUEST
        event_uid = request.get('event')
        if event_uid:
            event_uid = event_uid.split('UID_')[1]

        brains = self.context.portal_catalog(UID=event_uid)
        obj = brains[0].getObject()
        endDate = obj.end()
        dayDelta, minuteDelta = float(request.get('dayDelta')), float(request.get('minuteDelta'))
        endDate = endDate + dayDelta + minuteDelta / 1440.0
        obj.setEndDate(endDate)
        obj.reindexObject()
        return True


class SolgemaFullcalendarActionGuards(BrowserView):

    def is_calendar_layout(self):
        selected_layout = getattr(self.context, 'layout', '')
        return selected_layout == 'solgemafullcalendar_view'

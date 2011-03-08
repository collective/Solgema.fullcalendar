from urllib import quote_plus
from OFS import CopySupport
from OFS.CopySupport import CopyError, eInvalid, eNotFound
from zExceptions import Unauthorized, BadRequest
from ZODB.POSException import ConflictError
from Acquisition import aq_base, aq_inner, aq_parent
from zope.interface import implements, Interface
from Products.Five import BrowserView
from zope.component import getMultiAdapter, queryMultiAdapter, getAdapters, queryUtility
from Products.CMFCore.utils import getToolByName
from plone.i18n.normalizer.interfaces import IIDNormalizer
from zope.i18nmessageid import MessageFactory
from zope.i18n import translate
from DateTime import DateTime
from Products.CMFPlone.utils import transaction_note
from Products.CMFPlone.utils import safe_unicode
from Products.Five.utilities import marker
try:
    import json
except:
    import simplejson as json
from AccessControl import getSecurityManager
from Solgema.fullcalendar.config import _
plMF = MessageFactory('plone')
PLMF = MessageFactory('plonelocales')
ATMF = MessageFactory('atcontenttypes')
DTMF = MessageFactory('collective.z3cform.datetimewidget')
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from Solgema.fullcalendar.interfaces import *
from Solgema.fullcalendar.browser.solgemafullcalendar_views import getTopic, getCriteriaItems, getColorIndex

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

class SFJsonEvent(BrowserView):

    def __call__(self, *args, **kw):
        eventDict = getMultiAdapter((self.context, self.request), ISolgemaFullcalendarEventDict)()
        return json.dumps(eventDict, sort_keys=True)

class SFDisplayAddMenu(BrowserView):

    def __call__(self):
        query = self.context.buildQuery()
        copyDict = getCopyObjectsUID(self.request)
        if query.has_key('Type'):
            if isinstance(query['Type'], (list, tuple)) and len(query['Type'])>1:
                return json.dumps({'display':True})
            else:
                portal_type = isinstance(query['Type'], (tuple, list)) and query['Type'][0] or query['Type']
                portal = getToolByName(self.context, 'portal_url').getPortalObject()
                if copyDict and portal.restrictedTraverse(copyDict['url']).portal_type == portal_type:
                    return json.dumps({'display':True})
        else:
            portal_type = 'Event'
        pTypes = [a for a in getToolByName(self.context, 'portal_types').listTypeInfo() if a.id == portal_type]
        pTypeTitle = pTypes and pTypes[0].Title() or portal_type
        typeTitle = translate(pTypeTitle, context=self.request)
        if HAS_PLONE40:
            title = plMF(u'heading_add_item', default='Add ${itemtype}', mapping={'itemtype' : typeTitle})
        else:
            title = plMF(u'label_add_type', default='Add ${type}', mapping={'type' : typeTitle})
        return json.dumps({'display':False, 'type':portal_type, 'title':translate(title, context=self.request)})

class SFAddMenu(BrowserView):

    def __init__(self, context, request):
        super(SFAddMenu, self).__init__(context, request)
        self.portal = getToolByName(self.context, 'portal_url').getPortalObject()
        self.portal_url = self.portal.absolute_url()
        self.adapted = ISolgemaFullcalendarProperties(aq_inner(context), None)
        target_folder = getattr(self.adapted, 'target_folder', None)
        self.addContext = target_folder and self.portal.unrestrictedTraverse('/'+self.portal.id+target_folder) or aq_parent(aq_inner(self.context))
        self.EventAllDay = self.request.get('EventAllDay', False)
        self.ReqAllDay = self.EventAllDay and '&EventAllDay='+self.EventAllDay or ''
        self.startDate = self.request.get('startDate', '')
        self.endDate = self.request.get('endDate', '')
        self.query = self.context.buildQuery()
        self.addableTypes = isinstance(self.query.get('Type', ['Event',]), (tuple, list)) and self.query.get('Type', ['Event',]) or [self.query.get('Type'),'Event']

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
                url = '%s/createSFEvent?type_name=%s&startDate=%s&endDate=%s' % (baseUrl, quote_plus(typeId), self.startDate, self.endDate)
            icon = t.getIcon()
            if icon:
                icon = '%s/%s' % (self.portal_url, icon)
            title = translate(t.Title(), context=self.request)
            results.append({ 'id'           : typeId,
                             'title'        : plMF(u'label_add_type', default='Add ${type}', mapping={'type' : title}),
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
        portal_type = query.get('Type', None)
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

        portal_state = getMultiAdapter((self.addContext, self.request), name='plone_portal_state')

        actions_tool = getToolByName(self.portal, 'portal_actions')
        pasteAction = [a for a in actions_tool.listActionInfos(object=aq_inner(self.addContext), categories=('object_buttons',)) if a['id'] == 'paste']

        plone_utils = getToolByName(self.portal, 'plone_utils')

        for action in pasteAction:
            if action['allowed']:
                cssClass = 'actionicon-object_buttons-%s' % action['id']
                icon = plone_utils.getIconFor('object_buttons', action['id'], None)
                if icon:
                    icon = '%s/%s' % (self.addContext.absolute_url(), icon)

                results.append({ 'title'       : action['title'],
                                 'description' : '',
                                 'action'      : self.addContext.absolute_url()+'/SFJsonEventPaste?startDate='+self.startDate+self.ReqAllDay,
                                 'selected'    : False,
                                 'icon'        : icon,
                                 'extra'       : {'id': action['id'], 'separator': None, 'class': cssClass},
                                 'submenu'     : None,
                                 })
        return results

    def getMenuItems(self):
        return self.getMenuFactory()+self.getMenuPaste()

class SFJsonEventDelete(BrowserView):

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
            message = plMF(u'${title} is locked and cannot be deleted.',
                mapping={u'title' : title})
        else:
            parent.manage_delObjects(self.context.getId())
            status = 'ok'
            message = plMF(u'${title} has been deleted.',
                        mapping={u'title' : title})
            transaction_note('Deleted %s' % self.context.absolute_url())

        return json.dumps({'status':status, 'message':parent.translate(message), 'id':eventid})

class SFJsonEventCopy(BrowserView):

    def __call__(self):
        title = safe_unicode(self.context.title_or_id())
        mtool = getToolByName(self.context, 'portal_membership')
        if not mtool.checkPermission('Copy or Move', self.context):
            message = plMF(u'Permission denied to copy ${title}.',
                    mapping={u'title' : title})
            status = 'error'
            raise json.dumps({'status':status, 'message':self.context.translate(message)})

        parent = aq_parent(aq_inner(self.context))
        try:
            cp = parent.manage_copyObjects(self.context.getId())
            status = 'copied'
        except CopyError:
            status = 'error'
            message = plMF(u'${title} is not copyable.',
                        mapping={u'title' : title})
            return json.dumps({'status':status, 'message':parent.translate(message)})

        message = plMF(u'${title} copied.',
                    mapping={u'title' : title})
        transaction_note('Copied object %s' % self.context.absolute_url())
        contextId = 'UID_'+self.context.UID()
        return json.dumps({'status':status, 'message':self.context.translate(message), 'cp':cp, 'id':contextId})

class SFJsonEventCut(BrowserView):

    def __call__(self):
        title = safe_unicode(self.context.title_or_id())

        mtool = getToolByName(self.context, 'portal_membership')
        if not mtool.checkPermission('Copy or Move', self.context):
            message = plMF(u'Permission denied to copy ${title}.',
                    mapping={u'title' : title})
            status = 'error'
            raise json.dumps({'status':status, 'message':self.context.translate(message)})

        try:
            lock_info = self.context.restrictedTraverse('@@plone_lock_info')
        except AttributeError:
            lock_info = None

        if lock_info is not None and lock_info.is_locked():
            status = 'error'
            message = plMF(u'${title} is locked and cannot be cut.',
                        mapping={u'title' : title})
            return json.dumps({'status':status, 'message':parent.translate(message)})

        parent = aq_parent(aq_inner(self.context))
        try:
            cp = parent.manage_cutObjects(self.context.getId())
            status = 'copied'
        except CopyError:
            status = 'error'
            message = plMF(u'${title} is not copyable.',
                        mapping={u'title' : title})
            return json.dumps({'status':status, 'message':parent.translate(message)})

        message = plMF(u'${title} copied.',
                    mapping={u'title' : title})
        transaction_note('Copied object %s' % self.context.absolute_url())
        contextId = 'UID_'+self.context.UID()
        return json.dumps({'status':status, 'message':self.context.translate(message), 'cp':cp, 'id':contextId})

class SFJsonEventPaste(BrowserView):

    def __init__(self, context, request):
        super(SFJsonEventPaste, self).__init__(context, request)
        self.EventAllDay = self.request.get('EventAllDay', False) not in [False, 'false']
        self.startDate = self.request.get('startDate', '')
        self.portal = getToolByName(self.context, 'portal_url').getPortalObject()
        self.copyDict = getCopyObjectsUID(self.request)

    def createJsonEvent(self, event):
        return getMultiAdapter((event, self.request), ISolgemaFullcalendarEventDict)()

    def __call__(self):
        
        msg=plMF(u'Copy or cut one or more items to paste.')
        status='failure'
        if self.context.cb_dataValid:
            try:
                baseObject = self.portal.restrictedTraverse(self.copyDict['url'])
                baseId = 'UID_'+baseObject.UID()
                intervalle = baseObject.endDate-baseObject.startDate
                cb_copy_data = self.request['__cp']
                pasteList = self.context.manage_pasteObjects(cb_copy_data=cb_copy_data)
                newObject = getattr(self.context, pasteList[0]['new_id']) 
                startDate = self.startDate
                if self.EventAllDay:
                    startDate = DateTime(self.startDate).strftime('%Y-%m-%d ')+baseObject.startDate.strftime('%H:%M')
                newObject.setStartDate( DateTime(startDate) )
                newObject.setEndDate(newObject.startDate + intervalle)
                newObject.reindexObject()
                transaction_note('Pasted content to %s' % (self.context.absolute_url()))
                return json.dumps({'status':'pasted', 'event':self.createJsonEvent(newObject), 'url':newObject.absolute_url(), 'op':self.copyDict['op'], 'id':baseId})
            except ConflictError:
                raise
            except ValueError:
                msg=plMF(u'Disallowed to paste item(s).')
            except (Unauthorized, 'Unauthorized'):
                msg=plMF(u'Unauthorized to paste item(s).')
            except: # fallback
                msg=plMF(u'Paste could not find clipboard content.')

        return json.dumps({'status':'failure', 'message':self.context.translate(msg)})

class SolgemaFullcalendarWorkflowTransition(BrowserView):

    def __call__(self):
        request = self.context.REQUEST
        event_path = self.request.get('event_path', None)
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        url_list = event_path.split('/content_status_modify?workflow_action=')
        item_path = url_list[0]
        workflow_action = url_list[1]
        copyDict = getCopyObjectsUID(self.request)
        portal_url = portal.absolute_url()
        event_url = item_path.replace(portal_url, '')
        event = portal.restrictedTraverse(portal.id+event_url)
        eventPhysicalPath = '/'.join(event.getPhysicalPath())
        plone_utils = getToolByName(event, 'plone_utils')
        contentEditSuccess = 0
        plone_log = event.plone_log
        portal_workflow = event.portal_workflow
        transitions = portal_workflow.getTransitionsFor(event)
        transition_ids = [t['id'] for t in transitions]
        comment = self.request.get('comment', None)
        effective_date = self.request.get('effective_date', None)
        expiration_date = self.request.get('expiration_date', None)

        if workflow_action in transition_ids and not effective_date and event.EffectiveDate()=='None':
            effective_date=DateTime()

        def editContent(obj, effective, expiry):
            kwargs = {}
            if effective and (isinstance(effective, DateTime) or len(effective) > 5): # may contain the year
                kwargs['effective_date'] = effective
            if expiry and (isinstance(expiry, DateTime) or len(expiry) > 5): # may contain the year
                kwargs['expiration_date'] = expiry
            event.plone_utils.contentEdit( obj, **kwargs)

        #You can transition content but not have the permission to ModifyPortalContent
        try:
            editContent(event,effective_date,expiration_date)
            contentEditSuccess=1
        except (Unauthorized,'Unauthorized'):
            pass

        wfcontext = event

        # Create the note while we still have access to wfcontext
        note = 'Changed status of %s at %s' % (wfcontext.id, wfcontext.absolute_url())

        if workflow_action in transition_ids:
            wfcontext=event.portal_workflow.doActionFor( event,
                                                         workflow_action,
                                                         comment=comment )
    
        if not wfcontext:
            wfcontext = event

        #The object post-transition could now have ModifyPortalContent permission.
        if not contentEditSuccess:
            try:
                editContent(wfcontext, effective_date, expiration_date)
            except (Unauthorized,'Unauthorized'):
                pass

        transaction_note(note)

        eventDict = getMultiAdapter((event, self.request), ISolgemaFullcalendarEventDict)()
        return json.dumps(eventDict, sort_keys=True)

class SolgemaFullcalendarDropView(BrowserView):

    def __call__(self):
        request = self.context.REQUEST
        event_uid = request.get('event')

        if event_uid:
            event_uid = event_uid.split('UID_')[1]
        brains = self.context.portal_catalog(UID = event_uid)

        obj = brains[0].getObject()
        startDate, endDate = obj.startDate, obj.endDate
        dayDelta, minuteDelta = float(request.get('dayDelta')), float(request.get('minuteDelta'))

        startDate = startDate + dayDelta + minuteDelta / 1440.0        
        endDate = endDate + dayDelta + minuteDelta / 1440.0

        obj.setStartDate(startDate)
        obj.setEndDate(endDate)

        adapted = ISFBaseEventFields(obj, None)
        if adapted:
            if request.get('allDay', None) == 'true':
                setattr(adapted, 'allDay', True)
            if request.get('allDay', None) == 'false':
                setattr(adapted, 'allDay', False)

        obj.reindexObject()
        return True


class SolgemaFullcalendarResizeView(BrowserView):

    def __call__(self):
        request = self.context.REQUEST
        event_uid = request.get('event')
        if event_uid:
            event_uid = event_uid.split('UID_')[1]
        brains = self.context.portal_catalog(UID = event_uid)
        obj = brains[0].getObject()
        endDate = obj.endDate 
        dayDelta, minuteDelta = float(request.get('dayDelta')), float(request.get('minuteDelta'))
        
        endDate = endDate + dayDelta + minuteDelta / 1440.0
        
        obj.setEndDate(endDate)
        obj.reindexObject()
        return True

class SolgemaFullcalendarActionGuards(BrowserView):

    def is_calendar_layout(self):
        selected_layout = getattr(self.context, 'layout', '')
        return selected_layout == 'solgemafullcalendar_view'

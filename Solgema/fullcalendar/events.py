from zope.component import adapter
from zope.annotation.interfaces import IAnnotatable

from Acquisition import aq_parent
from Products.CMFCore.permissions import setDefaultRoles
from Products.GenericSetup.interfaces import IBeforeProfileImportEvent
from Products.GenericSetup.interfaces import IProfileImportedEvent
from Products.CMFCore.utils import getToolByName

@adapter(IProfileImportedEvent)
def handleProfileImportedEvent(event):
    #Don't bother me and leave my view where it is!
    context = event.tool
    ttool = getToolByName(context, 'portal_types')
    topic_type = ttool.Topic
    topic_methods = topic_type.view_methods
    if 'solgemafullcalendar_view' not in topic_methods:
        topic_type.manage_changeProperties(view_methods=topic_methods+tuple(['solgemafullcalendar_view',]))

    if 'collective.js.jqueryui' in event.profile_id and event.full_import:
        portal_setup = getToolByName(context, 'portal_setup')
        try:
            portal_setup.runAllImportStepsFromProfile('profile-Solgema.fullcalendar:default')
        except:
            pass

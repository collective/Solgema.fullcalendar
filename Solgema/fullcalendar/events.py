from zope.component import adapter

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
    event_type = ttool.Event
    event_methods = event_type.view_methods
    if 'solgemafullcalendar_view' not in event_methods:
        event_type.manage_changeProperties(view_methods=event_methods+tuple(['solgemafullcalendar_view',]))

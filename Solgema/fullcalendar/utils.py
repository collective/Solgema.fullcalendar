from Products.CMFCore.utils import getToolByName

# Check for plone.(app.)uuid, conditional uid getter with fallback
try:
    from plone.uuid.interfaces import IUUID
    import plone.app.uuid
    get_uid = lambda o: IUUID(o, None)
except ImportError:
    get_uid = lambda o: o.UID()


def checkViews(context):
    ttool = getToolByName(context, 'portal_types')
    topic_type = getattr(ttool, 'Topic', None)
    if topic_type:
        topic_methods = topic_type.view_methods
        if 'solgemafullcalendar_view' not in topic_methods:
            topic_type.view_methods=topic_methods+tuple(['solgemafullcalendar_view',])

    event_type = getattr(ttool, 'Event', None)
    if event_type:
        event_methods = event_type.view_methods
        if 'solgemafullcalendar_view' not in event_methods:
            event_type.view_methods=event_methods+tuple(['solgemafullcalendar_view',])

    folder_type = getattr(ttool, 'Folder', None)
    if folder_type:
        folder_methods = folder_type.view_methods
        if 'solgemafullcalendar_view' not in folder_methods:
            folder_type.view_methods=folder_methods+tuple(['solgemafullcalendar_view',])

    collection_type = getattr(ttool, 'Collection', None)
    if collection_type:
        collection_methods = collection_type.view_methods
        if 'solgemafullcalendar_view' not in collection_methods:
            collection_type.view_methods=collection_methods+tuple(['solgemafullcalendar_view',])

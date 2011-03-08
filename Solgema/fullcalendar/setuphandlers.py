from Products.CMFCore.utils import getToolByName

def installSolgemaFullcalendar(context):
    if context.readDataFile('solgemafullcalendar_various.txt') is None:
        return
    site = context.getSite()

    ttool = getToolByName(site, 'portal_types')
    topic_type = ttool.Topic
    topic_methods = topic_type.view_methods
    if 'solgemafullcalendar_view' not in topic_methods:
        topic_type.manage_changeProperties(view_methods=topic_methods+tuple(['solgemafullcalendar_view',]))

    jstool = getToolByName(site, 'portal_javascripts')
    jstool.cookResources()
    csstool = getToolByName(site, 'portal_css')
    csstool.cookResources()

def uninstallSolgemaFullcalendar(context):
    if context.readDataFile('solgemafullcalendar_various.txt') is None:
        return
    site = context.getSite()
    ttool = getToolByName(site, 'portal_types')
    topic_type = ttool.Topic
    topic_methods = topic_type.view_methods
    li = []
    for method in topic_methods:
        if method != 'solgemafullcalendar_view':
            li.append(method)
    topic_type.manage_changeProperties(view_methods=tuple(li))
    catalog = getToolByName(site, 'portal_catalog')
    topics = catalog.searchResults(portal_type='Topic')
    for ctopic in topics:
        topic = ctopic.getObject()
        if getattr(topic, 'layout', None) == 'solgemafullcalendar_view':
            setattr(topic, 'layout', '')


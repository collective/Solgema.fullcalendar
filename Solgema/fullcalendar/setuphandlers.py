from Products.CMFCore.utils import getToolByName


def installSolgemaFullcalendar(context):
    if context.readDataFile('solgemafullcalendar_various.txt') is None:
        return
    site = context.getSite()
    jstool = getToolByName(site, 'portal_javascripts')
    jstool.cookResources()
    csstool = getToolByName(site, 'portal_css')
    csstool.cookResources()


def uninstallSolgemaFullcalendar(context):
    if context.readDataFile('solgemafullcalendar_uninstall_various.txt') is None:
        return
    site = context.getSite()
    catalog = getToolByName(site, 'portal_catalog')
    ttool = getToolByName(site, 'portal_types')
    ctypes = [
        'Event',
        'Folder',
        'Topic',
        'Collection',
    ]
    for ctype in ctypes:
        fti = getattr(ttool, ctype, None)
        if not fti:
            continue
        view_methods = fti.view_methods
        view_methods = tuple(i for i in view_methods if i != 'solgemafullcalendar_view')
        fti.manage_changeProperties(view_methods=view_methods)
        brains = catalog.searchResults(portal_type=ctype)
        for brain in brains:
            obj = brain.getObject()
            if getattr(obj, 'layout', None) == 'solgemafullcalendar_view':
                setattr(obj, 'layout', '')

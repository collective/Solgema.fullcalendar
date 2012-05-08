import transaction
from Acquisition import aq_inner
from zope import component
from Products.CMFPlone.utils import safe_unicode 
from Products.CMFCore.utils import getToolByName
from plone.i18n.normalizer.interfaces import IURLNormalizer
from Solgema.fullcalendar import interfaces
from Solgema.fullcalendar.Extensions.install import checkViews

PRODUCT_DEPENDENCIES = ['Solgema.ContextualContentMenu', 'plone.app.z3cform', 'collective.js.jqueryui']

def doNothing(context):
    pass


def updateRegistries(context):
    jstool = getToolByName(context, 'portal_javascripts')
    jstool.cookResources()
    csstool = getToolByName(context, 'portal_css')
    csstool.cookResources()


def checkPortalTypes(context):
    #be sure solgemafullcalendar_view is installed
    ttool = getToolByName(context, 'portal_types')
    topic_type = ttool.Topic
    topic_methods = topic_type.view_methods
    if 'solgemafullcalendar_view' not in topic_methods:
        topic_type.manage_changeProperties(view_methods=topic_methods+tuple(['solgemafullcalendar_view',]))


def upgrade03(context):
    portal_quickinstaller = getToolByName(context, 'portal_quickinstaller')
    for product in PRODUCT_DEPENDENCIES:
        if not portal_quickinstaller.isProductInstalled(product):
            try:
                portal_quickinstaller.installProduct(product)
            except:
                pass
            transaction.savepoint()


def upgrade11(context):
    portal_quickinstaller = getToolByName(context, 'portal_quickinstaller')

    for product in PRODUCT_DEPENDENCIES:
        if not portal_quickinstaller.isProductInstalled(product):
            portal_quickinstaller.installProduct(product)
            transaction.savepoint()

    updateRegistries(context)

def upgrade12(context):
    portal_setup = getToolByName(context, 'portal_setup')
    portal_setup.runAllImportStepsFromProfile('profile-Solgema.fullcalendar.upgrades:upgrade12', purge_old=False)
    updateRegistries(context)


def upgrade13(context):
    portal_setup = getToolByName(context, 'portal_setup')
    portal_setup.runAllImportStepsFromProfile('profile-Solgema.fullcalendar.upgrades:upgrade13', purge_old=False)
    updateRegistries(context)


def upgrade14(context):
    updateRegistries(context)


def upgrade16(context):
    #be sure solgemafullcalendar_view is installed
    ttool = getToolByName(context, 'portal_types')
    topic_type = ttool.Topic
    topic_methods = topic_type.view_methods
    if 'solgemafullcalendar_view' not in topic_methods:
        topic_type.manage_changeProperties(view_methods=topic_methods+tuple(['solgemafullcalendar_view',]))
    updateRegistries(context)


def upgrade17(context):
    portal_quickinstaller = getToolByName(context, 'portal_quickinstaller')
    portal_setup = getToolByName(context, 'portal_setup')

    for product in PRODUCT_DEPENDENCIES:
        if not portal_quickinstaller.isProductInstalled(product):
            portal_quickinstaller.installProduct(product)
            transaction.savepoint()

    portal_setup.runAllImportStepsFromProfile('profile-Solgema.fullcalendar.upgrades:upgrade17', purge_old=False)
    checkPortalTypes(context)
    updateRegistries(context)


def upgrade18(context):

    portal_quickinstaller = getToolByName(context, 'portal_quickinstaller')
    portal_setup = getToolByName(context, 'portal_setup')

    for product in PRODUCT_DEPENDENCIES:
        if not portal_quickinstaller.isProductInstalled(product):
            portal_quickinstaller.installProduct(product)
            transaction.savepoint()

    portal_setup.runAllImportStepsFromProfile(
             'profile-Solgema.fullcalendar.upgrades:upgrade18',
             purge_old=False)
    checkPortalTypes(context)
    updateRegistries(context)


def upgrade19(context):

    portal_quickinstaller = getToolByName(context, 'portal_quickinstaller')
    portal_setup = getToolByName(context, 'portal_setup')

    for product in PRODUCT_DEPENDENCIES:
        if not portal_quickinstaller.isProductInstalled(product):
            portal_quickinstaller.installProduct(product)
            transaction.savepoint()

    portal_setup.runAllImportStepsFromProfile(
              'profile-Solgema.fullcalendar.upgrades:upgrade19',
              purge_old=False)
    checkPortalTypes(context)
    updateRegistries(context)


def upgrade20(context):

    context.runAllImportStepsFromProfile(
              'profile-collective.js.colorpicker:default',
              purge_old=False)
    context.runAllImportStepsFromProfile(
              'profile-collective.js.fullcalendar:default',
              purge_old=False)
    context.runAllImportStepsFromProfile(
              'profile-Solgema.fullcalendar.upgrades:upgrade2',
              purge_old=False)


def upgrade210(context):
    checkViews(context)
    catalog = getToolByName(context, 'portal_catalog')
    for topic in [a.getObject() for a in catalog.searchResults(portal_type="Topic")]:
        calendar = interfaces.ISolgemaFullcalendarProperties(topic, None)
        newColors = {}
        if calendar:
            for k,v in calendar.queryColors.items():
                colDict = {}
                for l,w in v.items():
                    l = safe_unicode(l)
                    colDict[str(component.queryUtility(IURLNormalizer).normalize(l))] = w
                newColors[k] = colDict.copy()
            calendar.queryColors = newColors.copy()

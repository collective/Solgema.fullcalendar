import transaction
from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Solgema.fullcalendar.config import PRODUCT_DEPENDENCIES

def install(self, reinstall=False):

    portal_quickinstaller = getToolByName(self, 'portal_quickinstaller')
    portal_setup = getToolByName(self, 'portal_setup')

    for product in PRODUCT_DEPENDENCIES:
        if not portal_quickinstaller.isProductInstalled(product):
            portal_quickinstaller.installProduct(product)
            transaction.savepoint()

    portal_setup.runAllImportStepsFromProfile('profile-Solgema.fullcalendar:default', purge_old=False)
    portal_quickinstaller.notifyInstalled('Solgema.fullcalendar')
    transaction.savepoint()

def uninstall( self ):
    out = StringIO()
    portal_setup = getToolByName(self, 'portal_setup')
    print >> out, "Removing Solgema.fullcalendar"
    portal_setup.runAllImportStepsFromProfile('profile-Solgema.fullcalendar:uninstall', purge_old=False)
    return out.getvalue()


# -*- coding: utf-8 -*-

from zope.interface import directlyProvides
from zope.component import queryMultiAdapter
from plone.app.testing.helpers import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.browserlayer.utils import registered_layers

from Solgema.fullcalendar.testing import INTEGRATION_TESTING
from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarLayer

import unittest

PROJECTNAME = 'Solgema.fullcalendar'


class InstallTestCase(unittest.TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.skins = self.portal['portal_skins']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_installed(self):
        qi = self.portal['portal_quickinstaller']
        self.assertTrue(qi.isProductInstalled(PROJECTNAME))

    def test_addon_layer(self):
        layers = [l.getName() for l in registered_layers()]
        self.assertIn('ISolgemaFullcalendarLayer', layers)

    def test_skin_layers(self):
        self.assertIn('solgemafullcalendar', self.skins)

    def test_view_available(self):
        directlyProvides(self.request, ISolgemaFullcalendarLayer)
        login(self.portal, TEST_USER_NAME)
        self.portal.invokeFactory('Folder', 'folder')
        folder = getattr(self.portal, 'folder')
        view = queryMultiAdapter((folder, self.request),
                                 name='solgemafullcalendar_view')
        self.assertTrue(view is not None)


class UninstallTestCase(unittest.TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.skins = self.portal['portal_skins']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.qi = self.portal['portal_quickinstaller']
        self.qi.uninstallProducts(products=[PROJECTNAME])

    def test_uninstalled(self):
        self.assertFalse(self.qi.isProductInstalled(PROJECTNAME))

    def test_addon_layer_removed(self):
        layers = [l.getName() for l in registered_layers()]
        self.assertNotIn('ISolgemaFullcalendarLayer', layers)

    def test_skin_layers_removed(self):
        self.assertNotIn('solgemafullcalendar', self.skins)

    # FIXME: this test (and the corresponding in the InstallTestCase)
    #        is wrong; it should check if `solgemafullcalendar_view`
    #        has been removed from FTI `view_methods` attribute
    #        view is registered in ZCML and will be always available
    @unittest.expectedFailure
    def test_view_unavailable(self):
        login(self.portal, TEST_USER_NAME)
        self.portal.invokeFactory('Folder', 'folder')
        folder = getattr(self.portal, 'folder')
        view = queryMultiAdapter((folder, self.request),
                                 name='solgemafullcalendar_view')
        self.assertTrue(view is None)

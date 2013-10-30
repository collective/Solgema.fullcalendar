# -*- coding: utf-8 -*-

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.browserlayer.utils import registered_layers
from Solgema.fullcalendar.testing import INTEGRATION_TESTING

import unittest2 as unittest

PROJECTNAME = 'Solgema.fullcalendar'


class InstallTestCase(unittest.TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.skins = self.portal['portal_skins']

    def test_installed(self):
        qi = self.portal['portal_quickinstaller']
        self.assertTrue(qi.isProductInstalled(PROJECTNAME))

    def test_addon_layer(self):
        layers = [l.getName() for l in registered_layers()]
        self.assertIn('ISolgemaFullcalendarLayer', layers)

    def test_skin_layers(self):
        self.assertIn('solgemafullcalendar', self.skins)


class UninstallTestCase(unittest.TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
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

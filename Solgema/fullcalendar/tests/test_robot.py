# -*- coding: utf-8 -*-
from plone.testing import layered
from Solgema.fullcalendar.testing import ROBOT_TESTING
from Solgema.fullcalendar.testing import DEXTERITY_ONLY

import robotsuite
import unittest


tests = ['robot/atfolder.robot', 'robot/collection.robot']

# FIXME: skip Robot Framework for Dexterity-based content types
if DEXTERITY_ONLY:
    tests = []


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(
            robotsuite.RobotTestSuite(t, noncritical=['Expected Failure']),
            layer=ROBOT_TESTING)
        for t in tests
    ])
    return suite

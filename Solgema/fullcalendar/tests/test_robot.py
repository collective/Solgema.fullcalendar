from plone.testing import layered

import robotsuite

from Solgema.fullcalendar.testing import ROBOT_TESTING


def test_suite():
    return layered(robotsuite.RobotTestSuite('robot/atfolder.robot', 'robot/attopic.robot', 'robot/collection.robot'),
                   layer=ROBOT_TESTING)

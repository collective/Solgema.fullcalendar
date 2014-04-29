*** Settings ***
Resource  plone/app/robotframework/keywords.robot
Resource  plone/app/robotframework/selenium.robot
Resource  common.robot

Library  Remote  ${PLONE_URL}/RobotRemote
Library  plone.app.robotframework.keywords.Debugging

Suite Setup  Suite Setup
Suite Teardown  Close all browsers

Test Setup  Test Setup

*** Test cases ***
Use calendar view for topicOne
    Go to  ${PLONE_URL}/topic_one
    Activate calendar view
    Calendar view is rendered  agendaWeek
    Properties link is present

Change period of calendar
    Change period  agendaDay
    Calendar view is rendered  agendaDay
    Change period  month
    Calendar view is rendered  month

Test events display
    Event is not visible  month  event_one
    Event is not visible  month  event_two

*** Keywords ***
Test Setup
    # need to reactivate Topic content type
    ${topic_uid} =  Create content  type=Topic  id=topic_one  title=Topic One
    Create content  type=Event  id=event_one  title=Event One
    Create content  type=Event  id=event_two  title=Event Two

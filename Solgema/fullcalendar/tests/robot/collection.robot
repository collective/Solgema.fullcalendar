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
Use calendar view for collectionOne
    Go to  ${PLONE_URL}/collection_one
    Activate calendar view
    Calendar view is rendered  agendaWeek
    Properties link is present

Change period of calendar
    Change period  agendaDay
    Calendar view is rendered  agendaDay
    Change period  month
    Calendar view is rendered  month

Test events display
    Event is visible  month  event_one
    Event is visible  month  event_two

*** Keywords ***
Test Setup
    ${collection_uid} =  Create content  type=Collection  id=collection_one  title=Collection One
    Create content  type=Event  id=event_one  container=${collection_uid}  title=Event One
    Create content  type=Event  id=event_two  container=${collection_uid}  title=Event Two

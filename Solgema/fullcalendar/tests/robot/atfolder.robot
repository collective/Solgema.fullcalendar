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
Use calendar view for folderOne
    Go to  ${PLONE_URL}/folder_one
    Activate calendar view
    Calendar view is rendered  Week
    Properties link is present

*** Keywords ***
Test Setup
    ${folder_uid} =  Create content  type=Folder  id=folder_one  title=Folder One
    Create content  type=Event  id=event_one  container=${folder_uid}  title=Event One

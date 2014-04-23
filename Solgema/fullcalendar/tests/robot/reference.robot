*** Settings ***
Resource  plone/app/robotframework/keywords.robot
Resource  plone/app/robotframework/selenium.robot

Library  Remote  ${PLONE_URL}/RobotRemote
Library  plone.app.robotframework.keywords.Debugging

Suite Setup  Suite Setup
Suite Teardown  Close all browsers

Test Setup  Test Setup

*** Test cases ***
Use calendar view for folderOne
    Go to  ${PLONE_URL}/folder_one
    Open Display Menu
    Click element  plone-contentmenu-display-solgemafullcalendar_view
    Debug

*** Keywords ***
Suite Setup
    Open test browser
    Enable autologin as  Manager

Test Setup
    Create content  type=Folder  id=folder_one  title=Calendar
    Create content  type=Event  id=event_one  title=My first Event
    #Create content  type=RefBrowserDemo  id=atrb  title=ATRB Demo

Close overlay
    Wait until element is visible  css=.overlay-ajax .close
    Click element  css=.overlay-ajax .close

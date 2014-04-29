*** Settings ***
Resource  plone/app/robotframework/keywords.robot
Resource  plone/app/robotframework/selenium.robot
Resource  Solgema/fullcalendar/tests/robot/common.robot

Library  Remote  ${PLONE_URL}/RobotRemote
Library  plone.app.robotframework.keywords.Debugging

#Suite Setup  Suite Setup
Suite Teardown  Close all browsers

Test Setup  Test Setup

*** Test cases ***
Use calendar view for folderOne
    Calendar view is rendered  agendaWeek
    Properties link is present
    Element should not be visible  SFQuery

Change period of calendar
    Change period  agendaDay
    Calendar view is rendered  agendaDay
    Change period  month
    Calendar view is rendered  month

Test events display
    Event is visible  agendaWeek  event_one
    Event is visible  agendaWeek  event_two
    Event is not visible  agendaWeek  subevent_one

#Test setting target folder
#    Enter properties  0
#    Set target_folder  toto

Test setting sub folders
    Enter properties  1
    Select list by value in-out  availableSubFolders  subfolder_one  subfolder_two
    Click button  form-buttons-apply
    Activate calendar view  # we need to reactivate calendar view !
    Calendar view is rendered  agendaWeek
    Query element is visible and checked  solgema-subFolders-subfolder_one
    Query element is visible and checked  solgema-subFolders-subfolder_two
    Event is not visible  agendaWeek  event_one
    Event is visible  agendaWeek  subevent_one
    Event is visible  agendaWeek  subevent_two

*** Keywords ***
Test Setup
    Connect
    ${folder_uid} =  Create content  type=Folder  id=folder_one  title=Folder One
    Create content  type=Event  id=event_one  container=${folder_uid}  title=Event One
    Create content  type=Event  id=event_two  container=${folder_uid}  title=Event Two
    ${folder1_uid} =  Create content  type=Folder  id=subfolder_one  container=${folder_uid}  title=Subfolder One
    Create content  type=Event  id=subevent_one  container=${folder1_uid}  title=Sub event One
    ${folder2_uid} =  Create content  type=Folder  id=subfolder_two  container=${folder_uid}  title=Subfolder Two
    Create content  type=Event  id=subevent_two  container=${folder2_uid}  title=Sub event Two
    Go on calendar 'folder_one'

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

# issue #43
Test events display
    Event is not visible  month  event_one
    Event is not visible  month  event_two

Setting criteria and test events display
    Set the 'Type' Criterion to 'Event'
    Activate calendar view  # we need to reactivate calendar view !
    Calendar view is rendered  agendaWeek
    Event is visible  agendaWeek  event_one
    Event is visible  agendaWeek  event_two

# To be continued with query part display ...

*** Keywords ***
Test Setup
    ${collection_uid} =  Create content  type=Collection  id=collection_one  title=Collection One
    Create content  type=Event  id=event_one  title=Event One
    Create content  type=Event  id=event_two  title=Event Two

Set the '${criterion}' Criterion to '${value}'
    Click link  Edit
    Wait until page contains element  xpath=//select[@name="addindex"]
    Select from list  xpath=//select[@name="addindex"]  ${criterion}
    Wait until page contains element  xpath=//select[@class='queryoperator']
    Select from list  xpath=//select[@class='queryoperator']  Is
    Select checkbox  css=.queryvalue input[value=${value}]
    #Wait until page contains  1 items matching your search terms.
    Click button  Save

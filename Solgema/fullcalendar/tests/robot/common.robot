*** Keywords ***

## Actions

Activate calendar view
    Open Display Menu
    Click element  plone-contentmenu-display-solgemafullcalendar_view

Change period
    [Arguments]  ${period}
    Click element  css=.fc-button-${period}

Enter properties
    [Arguments]  ${fieldset_number}=0
    Click link  css=#contentview-solgemafullcalendar_view a
    Click link  fieldsetlegend-${fieldset_number}

Set target_folder
    [Arguments]  ${value}
    Debug

Select list by value in-out
    [Arguments]  ${attribute}  @{value}
    Select From List By Value  form-widgets-${attribute}-from  @{value}
    Click button  css=#formfield-form-widgets-${attribute} button[name=from2toButton]

## Tests

Calendar view is rendered
    [Arguments]  ${period}
    Page should contain element  css=.fc-header-left .fc-button-today
    Element should be visible  css=.fc-content .fc-view-${period}

Properties link is present
    Page should contain element  contentview-solgemafullcalendar_view

Event is visible
    [Arguments]  ${period}  ${event_id}
    Element should be visible  css=.fc-content .fc-view-${period} a.fc-event[href$="/${event_id}"]

Event is not visible
    [Arguments]  ${period}  ${event_id}
    Element should not be visible  css=.fc-content .fc-view-${period} a.fc-event[href$="/${event_id}"]

Query element is visible and checked
    [Arguments]  ${input_id}  
    Element should be visible  css=.SFQuery_input #${input_id}
    Checkbox should be selected  css=.SFQuery_input #${input_id}

## Other

Suite Setup
    Open test browser
    Enable autologin as  Manager

Connect
    Open test browser
    Enable autologin as  Manager

Go on calendar '${element}'
    Go to  ${PLONE_URL}/${element}
    Activate calendar view
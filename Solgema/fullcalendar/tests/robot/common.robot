*** Keywords ***

## Actions

Activate calendar view
    Open Display Menu
    Click element  plone-contentmenu-display-solgemafullcalendar_view

Change period
    [Arguments]  ${period}
    Click element  css=.fc-button-${period}

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

## Other

Suite Setup
    Open test browser
    Enable autologin as  Manager

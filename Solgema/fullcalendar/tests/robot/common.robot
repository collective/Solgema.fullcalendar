*** Keywords ***

## Actions

Activate calendar view
    Open Display Menu
    Click element  plone-contentmenu-display-solgemafullcalendar_view

## Tests

Calendar view is rendered
    [Arguments]  ${period}
    Page should contain element  css=.fc-header-left .fc-button-today
    Page should contain element  css=.fc-content .fc-view-agenda${period}

Properties link is present
    Page should contain element  contentview-solgemafullcalendar_view

## Other

Suite Setup
    Open test browser
    Enable autologin as  Manager

*** Keywords test ***
#Calendar view is rendered

*** Keywords ***
Activate calendar view
    Open Display Menu
    Click element  plone-contentmenu-display-solgemafullcalendar_view

Suite Setup
    Open test browser
    Enable autologin as  Manager

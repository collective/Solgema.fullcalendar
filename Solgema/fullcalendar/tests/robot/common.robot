*** Keywords test ***
Plone is installed
    Go to  ${PLONE_URL}
    Page should contain  Powered by Plone

*** Keywords ***
Activate calendar view
    Open Display Menu
    Click element  plone-contentmenu-display-solgemafullcalendar_view

Suite Setup
    Open test browser
    Enable autologin as  Manager

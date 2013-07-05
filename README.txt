Solgema.fullcalendar Package Readme
=========================

Overview
--------

Solgema.fullcalendar is a complete implementation of Adam Shaw Fullcalendar into Plone.
More info on Fullcalendar here: http://arshaw.com/fullcalendar/

This calendar allows you to display events type objects in a powerfull and fast ajax agenda.
You will be also able to add, edit and more generally manage your events throught the Calendar
with a strong AJAX framework.

The calendar is a view you can choose on a Topic. The view is named "solgemafullcalendar_view".
After that, a new object action permits you to set up the basics parameters for the calendar.

The calendar is strongly linked to the Topic as the events it displays are searched by the Topic and
it's criterias.

In addition to the calendar, there is a small query form you can display in the bottom of
the calendar to choose which event you want to display. The fields in this query form are
taken from the Topic's Criterions.


Changelog for Solgema.fullcalendar
--------
*Solgema.fullcalendar 1.8

 -Clicking on an event always asks for SFLight_event_view.pt. Allows the use of xdv theming
  (thanks to Sylvain Boureliou)
 -Comes with ui lightness 1.8.9 theme

*Solgema.fullcalendar 1.7

 -Removed own jqueryui and added collective.js.jqueryui (Thanks to Thomas Desvenain)
 -Fixed views and javascript files (fix issue #17 and #20, Thanks to Christian Lederman!)
 -Fixed dependencies declarations (Thanks to Olav Peeters)
 -Added a small workaround to solve a conflict between base jqueryui css and custom jqueryui lightness css.
 -Based on fullcalendar 1.4.10 (Thanks to Adam Arshaw)

*Solgema.fullcalendar 1.6

 -Fixed wrong call to getUrl method and completed with here/absolute_url
 -Fixed bad condition expression in actions (Thanks to Thomas Desvanain)
 -Added some steps to be sure (as sure as possible) that solgemafullcalendar_view remains in topic views

*Solgema.fullcalendar 1.5

 -Fixed adapting content that is not attribute annotable. ( changed indexer in catalog.py ) that fixes bug
  with plone.app.discussion.
 -Fixed cancel button and dialog close when editing. The edited event remained locked when closing dialog.
 -Fixed content type for solgemafullcalendar_vars.js

*Solgema.fullcalendar 1.4

 -Now based on Fullcalendar v 1.4.8
 -Fixed IE7 bug (thanks to Kyle Homstead)
 -Added the subtopics display in solgemafullcalendar_view (thanks to Christian Ledermann)
 -Added a <noscript> tag in solgemafullcalendar_view so that events are display even if javascript is not enabled.
  This can be disabled in Calendar View settings. (thanks to Christian Ledermann)

*Solgema.fullcalendar 1.3

 -Added the ability to choose your own color for events in the calendar. The color is linked to the topic's critrias.
 -Added colorpicker widget to choose the colors in Calendar View settings
 -Fixed Content Menu showing under calendar events

*Solgema.fullcalendar 1.2

 -Fixed calendar Height Setting
 -Using now jquery ui 1.8.5 (added javascripts for 1.8.5 and removed 1.8.4)

*Solgema.fullcalendar 1.1

 -Created an adapter to filter for editable events so that it can be easily overriden.
 -Solgema.ContextualContentMenu package included in configure.zcml
 -Installs Solgema.ContextualContentMenu properly
 -Fix jquery.js to 1.4.2 version (jquery.js added in skins directory)
 -Fix height dialog box
 -Added an override review_state in topic query for Admins so that the can see private events in calendar
  Event if they are not searched basically by the topic (e.g. for default events aggregator)

*Solgema.fullcalendar 1.0

 -Added relative start hour and relative start day
 -Fixed paste action in contextual content menu (when nothing in clipboard)
 -Fixed error when deleting topic's criterion after having set them in calendar view criterias.
 -Several bug fixed


*Solgema.fullcalendar 0.3

 -Added automatic dependencies installation in install.py ( installation of Solgema.ContextualContentMenu )
 -Changed the javascript in SFAjax_base_edit.cpt so that when editing through calendar, the dialog's iframe
  is resized to display the entire edit form ( fixes issue #1 )
 -Changed Dialog title when adding content ( msgid was "label_add_type" in Plone 3 and now 'heading_add_item'
  in Plone 4 ).


*Solgema.fullcalendar 0.2

 -Added a topicRelativeUrl variable into solgemafullcalendar_vars to fix the cookies path.
  (fix an issue with mutiple cookies when the topic is default view of a folder)

Installation Note
--------
You might encounter a conflict error with a wrong version of zope.i18n when buildout.
If so, edit your buildout.cfg and in the [version] part, ping the zope.i18n version to 3.6
zope.i18n = 3.6

Customizing the skin
--------
You can easyly customize de calendar skin:
Go to http://jquieryui.com and click on the Themes tab.
There you can create or choose an existing theme. After that, download it to your computer by selecting only: 
All UI Core, all UI Interactions and Dialog in UI Widgets. Unzip and copy the css file and all images in you
portal_skins/custom folder.

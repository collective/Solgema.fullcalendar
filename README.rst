Solgema.fullcalendar Package Readme
===================================

.. image:: https://secure.travis-ci.org/collective/Solgema.fullcalendar.png?branch=master
    :target: http://travis-ci.org/collective/Solgema.fullcalendar

.. image:: https://coveralls.io/repos/collective/Solgema.fullcalendar/badge.png?branch=master
    :target: https://coveralls.io/r/collective/Solgema.fullcalendar

Overview
--------

Solgema.fullcalendar is a complete implementation of
`Adam Shaw Fullcalendar <http://arshaw.com/fullcalendar/>`_ into Plone.

This calendar allows you to display events type objects in a powerful and fast
ajax agenda. You will be also able to add, edit and more generally manage your
events throught the Calendar with a strong AJAX framework.

The calendar is a view you can choose on a Collection, on a Folder or on an
Event. The view is named ``solgemafullcalendar_view``. After that, a new object
action permits you to set up the basics parameters for the calendar.

On a Collection, the calendar displays the events that are searched by the
Collection and it's criteria.

On a Folder, the calendar displays the events that are contained in the Folder
itself or in the sub-folders if they are selected in the calendar properties.

In addition to the calendar, there is a small query form you can display in the
bottom of the calendar to choose which event you want to display. The fields in
this query form are taken from the Collection criterions or from the subfolders
of the Folder.

As a developer, you can add event sources to the default one.
You just have to define named ``IEventSource`` adapters which provides each a
list of dictionaries needed by ``fullcalendar.js`` API.
You can also replace the default event source providing an unnamed
``IEventSource`` adapter for your specific context or layer.

Installation Note for Plone < 4.3
---------------------------------

Add this line in the versions section of your ``buildout.cfg``::

    [versions]
    ...
    collective.js.jqueryui = <1.9

Installation Note for Plone 3.x
-------------------------------

Add this line in the eggs section of your ``buildout.cfg``::

    eggs=
        ...
        collective.js.jqueryui<1.8

You will also have to pin the versions for ``plone.app.z3cform``::

    [versions]
    z3c.form = 1.9.0
    zope.i18n = 3.4.0
    zope.testing = 3.4.0
    zope.component = 3.4.0
    zope.securitypolicy = 3.4.0
    zope.app.zcmlfiles = 3.4.3
    plone.app.z3cform = 0.4.6
    collective.js.jqueryui = 1.7.2.7


Customizing the skin
--------------------

You can easily customize the calendar skin:

Go to http://jqueryui.com and click on the Themes tab. There you can create or
choose an existing theme. After that, download it to your computer by selecting
only: All UI Core, all UI Interactions and Dialog in UI Widgets. Unzip and copy
the css file and all images in your ``portal_skins/custom folder``.

You can also try collective.jqueryuithememanager_

.. _collective.jqueryuithememanager: http://plone.org/products/collective.jqueryuithememanager


Source Code
-----------

Source code is under GNU General Public Licence (GPL, see docs/LICENSE.txt).
It is located at the
`collective git repository at github <https://github.com/collective/Solgema.fullcalendar>`_
and contributions are welcome.


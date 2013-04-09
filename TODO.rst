TODO
====

* Simplify and structure codebase by:
  - Using GS-only setup and drop Extensions/* and setuphandlers.py,
  - Removing upgrades/profiles (upgrade registration alone is sufficient),
  - Creating a template directory and moving all templates in there (this
    breaks other peoples' code, if they override with z3c.jbot. But the better
    structure is worth the change),
  - Obsolete skins folder and use browser views/resources, if possible,
  - Don't modify html HEAD in skin templates to inject javascript, but use
    jsregistry for that,
  - Use namespace functions to encapsulate javascript,
  - Drop usage of propertybags and use approach like in
    P.CMFPlone.browser.syndication  or plone.app.event.ical.importer.

from datetime import datetime

from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.add import DefaultAddForm, DefaultAddView
from plone.event.interfaces import IEventAccessor
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Solgema.fullcalendar import interfaces


class InlineFrameEditForm(DefaultEditForm):
    """
    Subclass for edit form template override, because this cannot
    be done in ZCML for z3c.form.Form instances, as they use 'template',
    not 'index' attribute as callable for rendering template.

    Constructor injects 'ajax_load' into request to alter the behavior
    of the main template to avoid Plone page furniture when loading this
    stuff in an overlay/popup layer.  'ajax_include_head' is also set to
    ensure that JavaScript/CSS is correctly working for this minimal
    form view to operate in an iframe.
    """

    template = ViewPageTemplateFile('edit_dx_event.pt')

    def __init__(self, context, request):
        # tweak main template behavior
        request.form['ajax_load'] = 1
        request.form['ajax_include_head'] = 1
        super(InlineFrameEditForm, self).__init__(context, request)

    def __call__(self, *args, **kwargs):
        self.update(*args, **kwargs)  # induces redirect, canceled below
        method = self.request['REQUEST_METHOD']
        if method == 'POST' and 'form.buttons.save' in self.request.form:
            self.request.response.errmsg = 'OK'
            self.request.response.status = 200  # no redirect
            self.request.form['calendar_event_saved'] = 1
        return self.template(*args, **kwargs)

    def isodate(self):
        accessor = IEventAccessor(self.context)
        if accessor.start:
            return accessor.start.isoformat()
        return datetime.now().isoformat()


class EventIframeAddForm(DefaultAddForm):
    template = ViewPageTemplateFile('add_dx_event.pt')

    def isodate(self):
        if 'date_context' in self.request.form:
            return self.request.form.get('date_context').strip()
        return datetime.now().isoformat()


class InlineFrameAddView(DefaultAddView):
    form = EventIframeAddForm

    def __init__(self, context, request, name='plone.app.event.dx.event'):
        name = getattr(interfaces.ISolgemaFullcalendarProperties(context, None), 'eventType', 'Event')
        ti = getToolByName(context, 'portal_types').getTypeInfo(name)
        request.form['ajax_load'] = 1
        request.form['ajax_include_head'] = 1
        super(InlineFrameAddView, self).__init__(context, request, ti)

    def __call__(self, *args, **kwargs):
        self.update(*args, **kwargs)
        method = self.request['REQUEST_METHOD']
        if method == 'POST' and 'form.buttons.save' in self.request.form:
            self.index = ViewPageTemplateFile('add_dx_event.pt')
            self.request.response.errmsg = 'OK'
            self.request.response.status = 200  # no redirect
            self.request.form['calendar_event_saved'] = 1
            return self.index(self, *args, **kwargs)
        return self.render(*args, **kwargs)

    def isodate(self):
        if 'date_context' in self.request.form:
            return self.request.form.get('date_context').strip()
        return datetime.now().isoformat()

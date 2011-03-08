from Acquisition import aq_parent, aq_inner

from Products.CMFCore.utils import getToolByName

from plone.z3cform.layout import wrap_form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.i18nmessageid import MessageFactory
from z3c.form.interfaces import INPUT_MODE, DISPLAY_MODE
from z3c.form import form as z3cform, field as z3cfield
from z3c.form import button
from z3c.form import field, group as z3cgroup
from z3c.formwidget.query.widget import QuerySourceFieldRadioWidget
from z3c.form.browser.orderedselect import OrderedSelectWidget
from z3c.form.widget import SequenceWidget, FieldWidget
from z3c.form.browser import widget
from plone.z3cform.fieldsets import group, extensible
from zope.component import adapts, provideAdapter
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.http import IHTTPRequest

from Solgema.fullcalendar.vocabularies import TitledVocabulary
from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarProperties
from Solgema.fullcalendar.widgets.widgets import ColorDictInputFieldWidget
from Solgema.fullcalendar.content import SolgemaFullcalendarAdapter
from Solgema.fullcalendar.config import _
PLMF = MessageFactory('plone')

class CriteriasOrderedSelectWidget(OrderedSelectWidget):

    def update(self):
        """See z3c.form.interfaces.IWidget."""
        super(OrderedSelectWidget, self).update()
        widget.addFieldClass(self)
        self.value= [a for a in self.value if a != '']
        self.items = [
            self.getItem(term, count)
            for count, term in enumerate(self.terms)]
        self.selectedItems = [
            self.getItem(self.terms.getTermByToken(token), count)
            for count, token in enumerate(self.value)]
        self.notselectedItems = self.deselect()

def CriteriasOrderedSelectFieldWidget(field, request):
    """IFieldWidget factory for SelectWidget."""
    return FieldWidget(field, CriteriasOrderedSelectWidget(request))


class CalendarGroup(z3cgroup.Group):
    label = _(u'Calendar', default="Calendar")

    fields = z3cfield.Fields( ISolgemaFullcalendarProperties ).select(
        'slotMinutes',
        'allDaySlot',
        'defaultCalendarView',
        'headerRight',
        'weekends',
        'firstDay',
        'relativeFirstDay',
        'firstHour',
        'minTime',
        'maxTime',
        'target_folder',
        'calendarHeight',
        'displayNoscriptList')
    fields['target_folder'].widgetFactory[INPUT_MODE] = QuerySourceFieldRadioWidget

class QueryGroup(z3cgroup.Group):
    label = _(u'Query', default="Query")

    fields = z3cfield.Fields( ISolgemaFullcalendarProperties ).select(
        'availableCriterias',
        'displayUndefined',
        'overrideStateForAdmin')
    fields['availableCriterias'].widgetFactory[INPUT_MODE] = CriteriasOrderedSelectFieldWidget

class ColorsGroup(z3cgroup.Group):
    label = _(u'Colors', default="Colors")

    fields = z3cfield.Fields( ISolgemaFullcalendarProperties ).select(
        'queryColors')
    fields['queryColors'].widgetFactory[INPUT_MODE] = ColorDictInputFieldWidget


class SolgemaFullcalendarFormBase(extensible.ExtensibleForm, z3cform.EditForm ):

#    fields = z3cfield.Fields( ISolgemaFullcalendarProperties )
#    fields['target_folder'].widgetFactory[INPUT_MODE] = QuerySourceFieldRadioWidget
#    fields['availableCriterias'].widgetFactory[INPUT_MODE] = CriteriasOrderedSelectFieldWidget
#    fields['queryColors'].widgetFactory[INPUT_MODE] = ColorDictInputFieldWidget

    groups = (CalendarGroup, QueryGroup, ColorsGroup)
#    index = ViewPageTemplateFile('layout.pt', _prefix='')

    @button.buttonAndHandler(PLMF('label_save'), name='apply')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        changes = self.applyChanges(data)
        if changes:
            jstool = getToolByName(self.context, 'portal_javascripts')
            jstool.cookResources()
            self.status = self.successMessage
        else:
            self.status = self.noChangesMessage
        self.request.RESPONSE.redirect( self.context.absolute_url() )

    @button.buttonAndHandler(PLMF('label_cancel'), name='cancel')
    def handleCancel( self, action):
        self.request.RESPONSE.redirect( self.context.absolute_url() )

SolgemaFullcalendarForm = wrap_form(SolgemaFullcalendarFormBase)


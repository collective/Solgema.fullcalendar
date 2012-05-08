from z3c.form.interfaces import INPUT_MODE
from z3c.form import form as z3cform, field as z3cfield
from z3c.form import button
from z3c.form import group as z3cgroup
from z3c.formwidget.query.widget import QuerySourceFieldRadioWidget
from z3c.form.browser.orderedselect import OrderedSelectWidget
from z3c.form.widget import FieldWidget
from z3c.form.browser import widget

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as plMF
from plone.z3cform.layout import wrap_form
from plone.z3cform.fieldsets import extensible

from Solgema.fullcalendar.interfaces import ISolgemaFullcalendarProperties
from Solgema.fullcalendar.config import _


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
        'shortDayNameFormat',
        'headerLeft',
        'headerRight',
        'weekends',
        'firstDay',
        'relativeFirstDay',
        'firstHour',
        'minTime',
        'maxTime',
        'gcalSources',
        'target_folder',
        'calendarHeight',
        'displayNoscriptList',
        'disableAJAX',
        'caleditable',
        'disableDragging',
        'disableResizing')
    fields['target_folder'].widgetFactory[INPUT_MODE] = QuerySourceFieldRadioWidget

class TopicQueryGroup(z3cgroup.Group):
    label = _(u'Query', default="Query")

    fields = z3cfield.Fields( ISolgemaFullcalendarProperties ).select(
        'availableCriterias',
        'displayUndefined',
        'overrideStateForAdmin')
    fields['availableCriterias'].widgetFactory[INPUT_MODE] = CriteriasOrderedSelectFieldWidget

class FolderQueryGroup(z3cgroup.Group):
    label = _(u'Sub-Folders', default="Sub-Folders")

    fields = z3cfield.Fields( ISolgemaFullcalendarProperties ).select(
        'availableSubFolders',)
    fields['availableSubFolders'].widgetFactory[INPUT_MODE] = CriteriasOrderedSelectFieldWidget

class ColorsGroup(z3cgroup.Group):
    label = _(u'Colors', default="Colors")

    fields = z3cfield.Fields( ISolgemaFullcalendarProperties ).select(
        'queryColors')


class SolgemaFullcalendarFormBase(extensible.ExtensibleForm, z3cform.EditForm ):

    @button.buttonAndHandler(plMF('label_save', default=u'Save'), name='apply')
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

    @button.buttonAndHandler(plMF('label_cancel', default=u'Cancel'),
                             name='cancel')
    def handleCancel( self, action):
        self.request.RESPONSE.redirect( self.context.absolute_url() )

class SolgemaFullcalendarFormBaseTopic(SolgemaFullcalendarFormBase):
    groups = (CalendarGroup, TopicQueryGroup, ColorsGroup)
    
class SolgemaFullcalendarFormBaseFolder(SolgemaFullcalendarFormBase):
    groups = (CalendarGroup, FolderQueryGroup, ColorsGroup)

SolgemaFullcalendarFormTopic = wrap_form(SolgemaFullcalendarFormBaseTopic)
SolgemaFullcalendarFormFolder = wrap_form(SolgemaFullcalendarFormBaseFolder)

from zope.i18n import translate
from zope import component
from zope.formlib.form import Widgets
import zope.schema
from zope.interface import Interface
from zope.app.form.interfaces import IInputWidget, IDisplayWidget, ConversionError
from zope.schema import vocabulary
from zope.component import getUtility
from zope.schema._bootstrapinterfaces import RequiredMissing, WrongType
from zope.schema._bootstrapinterfaces import ConstraintNotSatisfied
from zope.interface import Interface, implements
from zope.schema.interfaces import ValidationError

from z3c.form.widget import Widget, FieldWidget
from z3c.form import interfaces

from z3c.form.converter import BaseDataConverter

from Solgema.fullcalendar.config import _
from Solgema.fullcalendar.browser.solgemafullcalendar_views import listQueryTopicCriteria, listBaseQueryTopicCriteria
from Solgema.fullcalendar.interfaces import ICustomUpdatingDict

class IColorDictInputWidget( interfaces.IWidget ):
    """For Dicts"""

class ColorDictInputWidget(Widget):
    implements(IColorDictInputWidget)
    keywidget = None
    prefix = 'form'
    keysVocabulary = []
    description = ''
    _missing = u'(no value)'

    def getTopicCriteriasKeys(self):
        criterias = listBaseQueryTopicCriteria(self.context)
        li = []
        for criteria in criterias:
            field = criteria.Field()
            fieldid = str(field)
            li.append(self.name+'.'+fieldid)
        return li

    def render(self):
        currentValues = self.value or {}
        criterias = listBaseQueryTopicCriteria(self.context)
        html = ''
        for criteria in criterias:
            field = criteria.Field()
            index = self.context.portal_atct.getIndex(field)
            fieldid = str(field)
            fieldname = index.friendlyName or index.index
            selectedItems = []
            if criteria.meta_type in ['ATSelectionCriterion', 'ATListCriterion']:
                selectedItems = criteria.getCriteriaItems()[0][1]['query']
            elif criteria.meta_type == 'ATPortalTypeCriterion':
                selectedItems = criteria.getCriteriaItems()[0][1]
            if selectedItems:
                html += '<br/><b>%s</b><br/><table>' % (fieldname)
                for item in selectedItems:
                    value = ''
                    if currentValues.has_key(fieldid) and currentValues[fieldid].has_key(item.decode('utf-8')):
                        value = currentValues[fieldid][item.decode('utf-8')]
                    html += '<tr><td>' + item.decode('utf-8') + '&nbsp;</td><td><input type="text" size="10" name="%s:record" value="%s" class="colorinput" style="background-color:%s;"></td></tr>' % ( self.name+'.'+fieldid+'.'+item.decode('utf-8'), value, value) + '</td></tr>'
                html+='</table>'
        return html

    def extract(self, default=interfaces.NOVALUE):
        """See z3c.form.interfaces.IWidget."""
        Dict = {}
        for key in self.getTopicCriteriasKeys():
            if self.request.get(key, ''):
                Dict[key.split('.')[-1]] = self.request.get(key)
        if len([a for a in Dict.values() if a]) != 0:
            return Dict
        return default

@zope.component.adapter(ICustomUpdatingDict, interfaces.IFormLayer)
@zope.interface.implementer(interfaces.IFieldWidget)
def ColorDictInputFieldWidget(field, request):
    """IFieldWidget factory for TextWidget."""
    return FieldWidget(field, ColorDictInputWidget(request))

class ColorDictDataConverter( BaseDataConverter ):

    type = dict
    errorMessage = _('The entered value is not a valid dict.')

    component.adapts(ICustomUpdatingDict, IColorDictInputWidget)

    def toWidgetValue(self, value):
        """See interfaces.IDataConverter"""
        if value is self.field.missing_value:
            return {}
        return value

    def toFieldValue(self, value):
        """See interfaces.IDataConverter"""
        if not value or len([a for a in value.values() if a]) == 0:
            return self.field.missing_value
        return value


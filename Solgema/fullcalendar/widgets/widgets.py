import zope.schema
from zope import component
from zope.interface import implements

from z3c.form.widget import Widget, FieldWidget
from z3c.form import interfaces

from z3c.form.converter import BaseDataConverter

from Solgema.fullcalendar.config import _
from Solgema.fullcalendar.browser.views import listBaseQueryTopicCriteria
from Solgema.fullcalendar.interfaces import ICustomUpdatingDict


class IColorDictInputWidget(interfaces.IWidget):
    """For Dicts"""


class ColorDictInputWidget(Widget):
    implements(IColorDictInputWidget)
    keywidget = None
    prefix = 'form'
    keysVocabulary = []
    description = ''
    _missing = u'(no value)'

    def getCriteriaKeys(self):
        criteria = listBaseQueryTopicCriteria(self.context)
        li = []
        for criterion in criteria:
            field = criterion.Field()
            fieldid = str(field)
            li.append(self.name+'.'+fieldid)

        return li

    def getCriteria(self):
        return listBaseQueryTopicCriteria(self.context)

    def render(self):
        currentValues = self.value or {}
        criteria = self.getCriteria()
        html = ''
        for criterion in criteria:
            field = criterion.Field()
            index = self.context.portal_atct.getIndex(field)
            fieldid = str(field)
            fieldname = index.friendlyName or index.index
            selectedItems = []
            if criterion.meta_type in ['ATSelectionCriterion', 'ATListCriterion']:
                selectedItems = criterion.getCriteriaItems()[0][1]['query']
            elif criterion.meta_type == 'ATPortalTypeCriterion':
                selectedItems = criterion.getCriteriaItems()[0][1]
            if selectedItems:
                html += '<br/><b>%s</b><br/><table>' % (fieldname)
                for item in selectedItems:
                    value = ''
                    if fieldid in currentValues \
                      and item.decode('utf-8') in currentValues[fieldid]:
                        value = currentValues[fieldid][item.decode('utf-8')]

                    html += """<tr><td>%s&nbsp;</td><td>
                    <input type="text" size="10" name="%s:record" value="%s"
                           class="colorinput" style="background-color:%s;" />
                    </td></tr>""" % (
                        item.decode('utf-8'),
                        self.name+'.'+fieldid+'.'+item.decode('utf-8'),
                        value, value)

                html+='</table>'

        return html

    def extract(self, default=interfaces.NOVALUE):
        """See z3c.form.interfaces.IWidget."""
        Dict = {}
        for key in self.getCriteriaKeys():
            if self.request.get(key, ''):
                Dict[key.split('.')[-1]] = self.request.get(key)
        if len([a for a in Dict.values() if a]) != 0:
            return Dict
        return default


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


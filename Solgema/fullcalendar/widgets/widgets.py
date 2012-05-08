import zope.schema
from zope import component
from zope.interface import implements
from plone.i18n.normalizer.interfaces import IURLNormalizer
from Products.CMFPlone.utils import safe_unicode

from z3c.form.widget import Widget, FieldWidget
from z3c.form import interfaces

from z3c.form.converter import BaseDataConverter
from Products.ATContentTypes.interface import IATTopic, IATFolder
from Solgema.fullcalendar.config import _
from Solgema.fullcalendar.browser.views import listBaseQueryTopicCriteria
from Solgema.fullcalendar.interfaces import ICustomUpdatingDict, ISolgemaFullcalendarProperties


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
        li = []
        if IATTopic.providedBy(self.context):
            criteria = listBaseQueryTopicCriteria(self.context)
            for criterion in criteria:
                field = criterion.Field()
                fieldid = str(field)
                li.append(self.name+'.'+fieldid)
        return li

    def getCriteria(self):
        if IATTopic.providedBy(self.context):
            return listBaseQueryTopicCriteria(self.context)
        return []

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
                    name = safe_unicode(item)
                    item = str(component.queryUtility(IURLNormalizer).normalize(name))
                    value = ''
                    if fieldid in currentValues \
                      and item in currentValues[fieldid]:
                        value = currentValues[fieldid][item]

                    html += """<tr><td>%s&nbsp;</td><td>
                    <input type="text" size="10" name="%s:record" value="%s"
                           class="colorinput" style="background-color:%s;" />
                    </td></tr>""" % (
                        name,
                        self.name+'.'+fieldid+'.'+item,
                        value, value)

                html+='</table>'
        calendar = ISolgemaFullcalendarProperties(self.context, None)
        gcalSourcesAttr = getattr(calendar, 'gcalSources', '')
        if gcalSourcesAttr != None:
            gcalSources = gcalSourcesAttr.split('\n')
            if gcalSources:
                html += '<br/><b>%s</b><br/><table>' % (_('Google Calendar Sources'))
                fieldid = 'gcalSources'
                for i in range(len(gcalSources)):
                    url = gcalSources[i]
                    item = 'source'+str(i)
                    value = ''
                    if fieldid in currentValues \
                        and item in currentValues[fieldid]:
                        value = currentValues[fieldid][item]
                            
                    html += """<tr><td><span title="%s">%s</span>&nbsp;</td></td><td>
                        <input type="text" size="10" name="%s:record" value="%s"
                               class="colorinput" style="background-color:%s;" />
                        </td></tr>""" % (
                            str(url),
                            'Source '+str(i+1),
                            self.name+'.'+fieldid+'.'+item,
                            value, value)
                html+='</table>'
        availableSubFolders = getattr(calendar, 'availableSubFolders', [])
        if IATFolder.providedBy(self.context) and availableSubFolders:
            html += '<br/><b>%s</b><br/><table>' % (_('Sub-Folders'))
            fieldid = 'subFolders'
            for folderId in availableSubFolders:
                value = ''
                if fieldid in currentValues \
                    and folderId in currentValues[fieldid]:
                    value = currentValues[fieldid][folderId]
                            
                html += """<tr><td><span title="%s">%s</span>&nbsp;</td></td><td>
                    <input type="text" size="10" name="%s:record" value="%s"
                           class="colorinput" style="background-color:%s;" />
                    </td></tr>""" % (
                        folderId,
                        folderId,
                        self.name+'.'+fieldid+'.'+folderId,
                        value, value)
            html+='</table>'

        return html

    def extract(self, default=interfaces.NOVALUE):
        """See z3c.form.interfaces.IWidget."""
        Dict = {}
        for key in self.getCriteriaKeys():
            if self.request.get(key, ''):
                Dict[key.split('.')[-1]] = self.request.get(key)

        key = self.name+'.gcalSources'
        if self.request.get(key, ''):
            Dict['gcalSources'] = self.request.get(key)

        key = self.name+'.subFolders'
        if self.request.get(key, ''):
            Dict['subFolders'] = self.request.get(key)

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

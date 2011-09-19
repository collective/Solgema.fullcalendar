from zope.i18n import translate
from zope.component import getAdapters

from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.lib import calendarsupport
from Products.ATContentTypes.browser.calendar import CalendarView
from plone.app.layout.viewlets.common import ViewletBase

from Solgema.fullcalendar.config import _
from Solgema.fullcalendar.interfaces import IEventSource

from Products.CMFPlone import PloneMessageFactory as PMF

class ICalExportButton(ViewletBase):


    def render(self):
        msg = translate(_('title_add_to_ical',
                          default=u"Download this calendar in iCal format"),
                        context=self.request)
        title = translate(_(u"iCal export"), context=self.request)
        url = self.context.absolute_url()
        portal_url = getToolByName(self.context, 'portal_url')()
        return """
                <a id="sfc-ical-export"
                   class="visualNoPrint"
                   title="%(msg)s"
                   href="%(url)s/ics_view">
                    <img width="16" height="16" title="%(title)s" alt="%(title)s"
                         src="%(portal_url)s/icon_export_ical.png">
                <span>%(title)s</span></a>
               """ % {'msg': msg, 'title': title,
                      'url': url, 'portal_url': portal_url}



class ICalExport(CalendarView):

    def update(self):
        context = self.context
        self.iscalendarlayout = context.unrestrictedTraverse('iscalendarlayout')()
        if self.iscalendarlayout:
            self.sources = [source for name, source
                                in getAdapters((self.context, self.request),
                                               IEventSource)]
        else:
            super(ICalExport, self).update()

    def feeddata(self):
        if self.iscalendarlayout:
            context = self.context
            data = calendarsupport.ICS_HEADER % dict(prodid=calendarsupport.PRODID)
            data += 'X-WR-CALNAME:%s\n' % context.Title()
            data += 'X-WR-CALDESC:%s\n' % context.Description()
            for source in self.sources:
                if hasattr(source, 'getICal'):
                    data += source.getICal()

            data += calendarsupport.ICS_FOOTER
            return data
        else:
            return super(ICalExport, self).feeddata()

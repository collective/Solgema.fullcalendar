from zope.component import adapter
from Products.GenericSetup.interfaces import IProfileImportedEvent
from Solgema.fullcalendar.Extensions.install import checkViews

@adapter(IProfileImportedEvent)
def handleProfileImportedEvent(event):
    #Don't bother me and leave my view where it is!
    context = event.tool
    checkViews(context)

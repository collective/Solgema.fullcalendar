import itertools

from zope import schema
from zope.interface import Interface, Attribute, implements, classProvides
from zope.schema.interfaces import ISource, IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.schema.interfaces import IDict
from zope.viewlet.interfaces import IViewletManager
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from Products.ZCTextIndex.ParseTree import ParseError

from Products.ATContentTypes.interface import IATFolder
from plone.app.vocabularies.catalog import SearchableTextSource, SearchableTextSourceBinder

from Solgema.fullcalendar.config import _


class IPersistentOptions( Interface ):
    """
    a base interface that our persistent option annotation settings,
    can adapt to. specific schemas that want to have context stored
    annotation values should subclass from this interface, so they
    use adapation to get access to persistent settings. for example,
    settings = IMySettings(context)
    """

class ISolgemaFullcalendarLayer(IDefaultBrowserLayer):
    """Solgema Fullcalendar layer"""

class ISolgemaFullcalendarView(Interface):
    """Solgema Fullcalendar View interface"""

class ISolgemaFullcalendarColorsCss(ISolgemaFullcalendarView):
    """Css generated for colors"""

class ISolgemaFullcalendarJS(ISolgemaFullcalendarView):
    """Solgema Fullcalendar View interface for JS Vars"""

    def getCalendar(self):
        """return the context and mark it with ISolgemaFullcalendarProperties so calendar data can be stored"""

    def getPortalLanguage(self):
        """get portal language"""

    def getMonthsNames(self):
        """get name of moths"""

    def getMonthsNamesAbbr(self):
        """get name of moths abbr"""

    def getWeekdaysNames(self):
        """get name of days"""

    def getWeekdaysNamesAbbr(self):
        """get name of days abbr"""

    def getTodayTranslation(self):
        """get translation for today"""

    def getMonthTranslation(self):
        """get translation for month"""

    def getWeekTranslation(self):
        """get translation for week"""

    def getDayTranslation(self):
        """get translation for day"""

    def getAllDayText(self):
        """get translation for all-day"""

    def getCustomTitleFormat(self):
        """get format to display dates in calendar header"""

    def userCanEdit(self):
        """return if user can edit calendar"""

class CustomSearchableTextSource(SearchableTextSource):
    implements(ISource)
    classProvides(IContextSourceBinder)

    def __init__(self, context, base_query={}, default_query=None):
        super(CustomSearchableTextSource, self).__init__(context, base_query=base_query, default_query=default_query)
        self.vocabulary = SimpleVocabulary([SimpleTerm(a, a, a) for a in self.baseTerms()])

    def baseTerms(self):
        query = self.base_query.copy()
        try:
            results = (x.getPath()[len(self.portal_path):] for x in self.catalog(**query))
        except ParseError:
            return []

        if query.has_key('path'):
            path = query['path']['query'][len(self.portal_path):]
            if path != '':
                return itertools.chain((path,), results)
        return results

    def search(self, query_string):
        results = super(CustomSearchableTextSource, self).search(query_string)
        return SimpleVocabulary([SimpleTerm(a, a, a) for a in results])

    def __contains__(self, value):
        return self.vocabulary.__contains__(value)

    def __iter__(self):
        return self.vocabulary.__iter__()

    def getTerm(self, value):
        return self.vocabulary.getTerm(value)


    def getTermByToken(self, token):
        return self.vocabulary.getTermByToken(token)


class CustomSearchableTextSourceBinder(SearchableTextSourceBinder):
    implements(IContextSourceBinder)
    def __call__(self, context):
        return CustomSearchableTextSource(context, base_query=self.query.copy(),
                                    default_query=self.default_query)

class ICustomUpdatingDict(IDict):
    """Interface for CustomUpdatingDict ( Colors Field )"""

class CustomUpdatingDict(schema.Dict):

    implements(ICustomUpdatingDict)

    def set(self, object, value):
        if self.readonly:
            raise TypeError("Can't set values on read-only fields "
                            "(name=%s, class=%s.%s)"
                            % (self.__name__,
                               object.__class__.__module__,
                               object.__class__.__name__))
        oldvalue = self.get(object)
        setattr(object, self.__name__, oldvalue.update(value))

class ISolgemaFullcalendarProperties(Interface):
    """An interface for specific calendar content stored in the object"""

    slotMinutes = schema.Int( title = _(u"label_slotMinutes"),
                                  required = True,
                                  description = _(u"help_slotMinutes"),
                                  default = 30 )

    allDaySlot = schema.Bool( title=_(u"label_allDaySlot"), default=True)

    defaultCalendarView = schema.Choice( title = _(u"label_defaultCalendarView"),
                                  required = True,
                                  description = _(u"help_defaultCalendarView"),
                                  source = "solgemafullcalendar.availableViews",
                                  default = 'agendaWeek' )

    shortDayNameFormat = schema.Choice( title = _(u"label_shortDayNameFormat"),
                                  required = True,
                                  description = _(u"help_shortDayNameFormat"),
                                  source = "solgemafullcalendar.shortNameFormats",
                                  default = 'a' )

    headerLeft = schema.TextLine( title = _(u"label_headerLeft"),
                                  required = False,
                                  description = _(u"help_headerLeft"),
                                  default = u'prev,next today calendar' )

    headerRight = schema.List( title = _(u"label_headerRight"),
                                  description = _(u"help_headerRight"),
                                  value_type = schema.Choice( title = _(u"label_headerRight"), source = "solgemafullcalendar.availableViews"),
                                  default = ['month', 'agendaWeek', 'agendaDay'] )

    weekends = schema.Bool( title=_(u"label_weekends"),
                                  description = _(u"help_weekends"),
                                  default=True)

    firstDay = schema.Choice( title = _(u"label_firstDay"),
                                  required = True,
                                  description = _(u"help_firstDay"),
                                  source = "solgemafullcalendar.daysOfWeek",
                                  default = 1 )

    relativeFirstDay = schema.TextLine( title = _(u"label_relativeFirstDay"),
                                  required = False,
                                  description = _(u"help_relativeFirstDay"),
                                  default = u'' )

    firstHour = schema.TextLine( title = _(u"label_firstHour"),
                                  required = True,
                                  description = _(u"help_firstHour"),
                                  default = u'-1' )

    minTime = schema.TextLine( title = _(u"label_minTime"),
                                  required = True,
                                  description = _(u"help_minTime"),
                                  default = u'0' )

    maxTime = schema.TextLine( title=_(u"label_maxTime"),
                                  description = _(u"help_minTime"),
                                  default = u'24')

    gcalSources = schema.Text( title=_(u"label_gcalSources", default="Google Calendar Sources"),
                                  required = False,
                                  description = _(u"help_gcalSources", default="Enter your Google Calendar feeds url here. the syntay should be : http://www.google.com/calendar/feeds/yourmail@gmail.com/... One url per line."),
                                  default = u'')
                                  
    target_folder = schema.Choice(title=_(u"label_target_folder"),
                                  description=_(u"help_target_folder"),
                                  required=False,
                                  source=CustomSearchableTextSourceBinder({'object_provides' : IATFolder.__identifier__},default_query='path:'))

    calendarHeight = schema.TextLine( title = _(u"label_calendarHeight"),
                                  required = False,
                                  description = _(u"help_calendarHeight"),
                                  default = u'600' )

    availableCriterias = schema.List( title = _(u"label_availableCriterias"),
                                  required = False,
                                  description = _(u"help_availableCriterias"),
                                  value_type = schema.Choice( title = _(u"label_availableCriterias"), source = "solgemafullcalendar.availableCriterias"),
                                  default = [] )

    availableSubFolders = schema.List( title = _(u"label_availableSubFolders"),
                                  required = False,
                                  description = _(u"help_availableSubFolders"),
                                  value_type = schema.Choice( title = _(u"label_availableSubFolders"), source = "solgemafullcalendar.availableSubFolders"),
                                  default = [] )

    queryColors = CustomUpdatingDict( title = _(u"label_queryColors"),
                                  required = False,
                                  description = _(u"help_queryColors"),
                                  default = {} )

    displayUndefined = schema.Bool( title=_(u"label_displayUndefined"),
                                  required = False,
                                  description = _(u"help_displayUndefined"),
                                  default=False)

    overrideStateForAdmin = schema.Bool( title=_(u"label_overrideStateForAdmin"),
                                  required = False,
                                  description = _(u"help_overrideStateForAdmin"),
                                  default=True)

    displayNoscriptList = schema.Bool( title=_(u"label_displayNoscriptList"),
                                  required = False,
                                  description = _(u"help_displayNoscriptList"),
                                  default=True)

    disableAJAX = schema.Bool(
                      title=_(u"label_disableAJAX", default="Disable AJAX"),
                      required=False,
                      description=_(u"help_disableAJAX", default="Disables contextual adding menu."),
                      default=False)

    caleditable = schema.Bool(
                      title=_(u"label_caleditable", default="Editable"),
                      required=False,
                      description=_(u"help_caleditable", default="Check this box if you want the events in the calendar to be editable."),
                      default=True)

    disableDragging = schema.Bool(
                      title=_(u"label_disableDragging", default="Disable Dragging"),
                      required=False,
                      description=_(u"help_disableDragging", default="Disables all event dragging, even when events are editable."),
                      default=False)

    disableResizing = schema.Bool(
                      title=_(u"label_disableResizing", default="Disable Resizing"),
                      required=False,
                      description=_(u"help_disableResizing", default="Disables all event resizing, even when events are editable."),
                      default=False)

    def isSolgemaFullcalendar(self):
        """get name of days"""

class ISolgemaFullcalendarEvents(Interface):
    """Solgema Fullcalendar update view interface"""

class ISolgemaFullcalendarEventsSources(Interface):
    """Solgema Fullcalendar get Events Sources"""

class ISolgemaFullcalendarEditableFilter(Interface):
    """Solgema Fullcalendar update view interface"""

    def filterEvents(self, args):
        """custom method that filters and returns list of paths of the events that can be edited"""

class ISolgemaFullcalendarCatalogSearch(Interface):
    """Solgema Fullcalendar Custom Events Search"""

    def searchResults(self, args):
        """Do the catalog search"""

class ISolgemaFullcalendarEventDict(Interface):
    """Return a friendly calendar dict for events"""

class ISolgemaFullcalendarTopicEventDict(Interface):
    """Return a friendly calendar dict for events in topic query"""

class ISolgemaFullcalendarExtraClass(Interface):
    """Adapter for extra class"""
    
    def extraClass(self):
        """return particular css class for item"""

class ISolgemaFullcalendarMarker(Interface):
    """A marker for items that can be displayed as solgemafullcalendar_view"""

class ISFBaseEventFields(Interface):
    """An interface that defines the specific Fullcalendar's events fields """

    allDay = schema.Bool( title=_(u"label_allDay", default=u"Display All day option"),
                                  description = _(u"help_allDay", default=u"Check this box to display All day option"),
                                  default=False)


class ISolgemaFullcalendarQuery(IViewletManager):
    """topic query for calendar"""


class IColorIndexGetter(Interface):
    """Adapter that provides a method to get color index from brain
    Adapts a context, a request and the source element
    """

    context = Attribute("""The calendar context""")
    request = Attribute("""The request""")
    source = Attribute("""The event which we get the color""")

    def getColorIndex(self):
        """Get color class
        """


class IEventSource(Interface):
    """Adapter that provides a list of events to display in calendar
    """

    def getEvents(self):
        """List of event objects to display in calendar
           (takes account of 'start' and 'end' values in request
        """

    def getIcal(self):
        """Ical export of events
        """

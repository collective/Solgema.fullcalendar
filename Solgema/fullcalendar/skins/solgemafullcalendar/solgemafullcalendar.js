if (!extraContentMenuActions) var extraContentMenuActions = [];

function readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
};

jq.fullCalendar.views.calendar = switchCalendarDay;

function switchCalendarDay(element, calendar) {
};

jq.fullCalendar.views.agendaDaySplit = AgendaDaySplitView;

function AgendaDaySplitView(element, calendar) {
	var t = this;

	// imports
	jq.fullCalendar.views.agendaDay.call(t, element, calendar);
	var opt = t.opt;
	var renderAgenda = t.renderAgenda;
	var formatDate = calendar.formatDate;
	var suggestedViewHeight;
	var options = t.calendar['options'];
        var baseRender = t.render;
	// exports
	t.render = render;
	t.name = 'agendaDaySplit';

    function vsides(element, includeMargins) {
	    return vpadding(element) +  vborders(element) + (includeMargins ? vmargins(element) : 0);
    }


    function vpadding(element) {
	    return (parseFloat(jq.curCSS(element[0], 'paddingTop', true)) || 0) +
	           (parseFloat(jq.curCSS(element[0], 'paddingBottom', true)) || 0);
    }


    function vmargins(element) {
	    return (parseFloat(jq.curCSS(element[0], 'marginTop', true)) || 0) +
	           (parseFloat(jq.curCSS(element[0], 'marginBottom', true)) || 0);
    }


    function vborders(element) {
	    return (parseFloat(jq.curCSS(element[0], 'borderTopWidth', true)) || 0) +
	           (parseFloat(jq.curCSS(element[0], 'borderBottomWidth', true)) || 0);
    }

	function calcSize() {
		var content = jq('.fc-content');
		if (options.contentHeight) {
			suggestedViewHeight = options.contentHeight;
		}
		else if (options.height) {
			var headerElement = jq('.fc-header');
			suggestedViewHeight = options.height - (headerElement ? headerElement.height() : 0) - vsides(content);
		}
		else {
			suggestedViewHeight = Math.round(content.width() / Math.max(options.aspectRatio, .5));
		}
	}

	function render(date, delta) {
		// base rendering
		baseRender(date, delta);

        // available only for solgemaSources as eventSources
        //is deleted from options during calendar initialisation.
        var solgemaSources = t.calendar.options['solgemaSources'];
        if (!solgemaSources) return;

		// splitted rendering
		var baseCalendar = element.parent().parent();
		element.css('display', 'table');
		calcSize();
		var axisWidth = jq('.fc-agenda-axis:first').width();
		var newOptions = jQuery.extend(true, {}, t.calendar.options);
		newOptions['header'] = {
				left: '',
				center: '',
				right: ''
			};
		newOptions['year'] = date.getFullYear();
		newOptions['month'] = date.getMonth();
		newOptions['date'] = date.getDate();
		newOptions['height'] = suggestedViewHeight;
		var sourcesNubmer = solgemaSources.length;
		var calWidth = (baseCalendar.width()-axisWidth)/sourcesNubmer;
		element.empty();
		for (var i=0; i<sourcesNubmer; i++) {
            var calOptions = jQuery.extend(true, {}, newOptions);
            solgemaSource = solgemaSources[i];
			element.append('<div id="cal'+i+'" style="display:table-cell;"></div>');
			calOptions['eventSources'] = [solgemaSource];
			calOptions['title'] = solgemaSource['title'];
			if (solgemaSource['target_folder']) calOptions['target_folder'] = solgemaSource['target_folder'];
			if (solgemaSource['extraData'])calOptions['extraData'] = solgemaSource['extraData'];
            if (sourcesNubmer == 1) {
				calOptions['defaultView'] = 'agendaDaySplitMonoColumn';
			} else if (i==0) {
				calOptions['defaultView'] = 'agendaDaySplitFirstColumn';
			} else if (i+1 == sourcesNubmer) {
				calOptions['defaultView'] = 'agendaDaySplitLastColumn';
			} else {
				calOptions['defaultView'] = 'agendaDaySplitColumn';
			}
			var curCal = jq('#cal'+i);
			if (i==0) {
				curCal.width(calWidth+axisWidth);
			} else if (i+1 != sourcesNubmer){
				curCal.width(calWidth);
			} else {
				curCal.width(calWidth-1);
			}
			curCal.fullCalendar(calOptions);
			if (sourcesNubmer != 1 && i+1 != sourcesNubmer) {
				curCal.find('.fc-agenda-slots').parent().parent().css('overflow-y', 'hidden');
			}
		}
        if (sourcesNubmer != 1) {
		    var lastContainer = jq('#cal'+(sourcesNubmer-1)).find('.fc-agenda-slots').parent().parent();
		    lastContainer.scroll( function () {
			    for (var i=0; i+1<sourcesNubmer; i++) {
		            var st = lastContainer.scrollTop();
			        jq('#cal'+i).find('.fc-agenda-slots').parent().parent().scrollTop(st);
			    }
		    });
		    var allDayHeight = 0;
		    jq('fc-agenda-allday').each( function(i, elem) {
		        if (jq(elem).height()>allDayHeight) allDayHeight = jq(elem).height();
		    });
		    jq('fc-agenda-allday').each( function(i, elem) {
		        jq(elem).height(allDayHeight);
		    });
        }
	}
};

function AgendaDaySplitColumnGeneral() {
    var t = this;
    var baseRenderEvents = t.renderEvents;
    t.renderEvents = renderEvents;

    function renderEvents(events, modifiedEventId) {
            baseRenderEvents(events, modifiedEventId);
	    var allDayHeight = 0;
	    jq('.fc-day-content').each( function(i, elem) {
	         if (jq(elem).height()>allDayHeight) allDayHeight = jq(elem).height();
	    });
	    jq('div.fc-day-content div').css('height', allDayHeight+'px');
	    var columnHeight = 0;
            jq('div.fc-content').each( function(i,elem) {
                col = jq(elem).find('div.fc-view table.fc-agenda-days td div:first');
                if (col.height()>columnHeight)columnHeight=col.height();
            });
            jq('div.fc-content').each( function(i,elem) {
                jq(elem).find('div.fc-view table.fc-agenda-days td div:first').height(columnHeight);
            });
        }
};

jq.fullCalendar.views.agendaDaySplitColumn = AgendaDaySplitColumn;

function AgendaDaySplitColumn(element, calendar) {
	var t = this;

	// imports
	jq.fullCalendar.views.agendaDay.call(t, element, calendar);
	var opt = t.opt;
	var renderAgenda = t.renderAgenda;
	var formatDate = calendar.formatDate;
    var baseRender = t.render;
        AgendaDaySplitColumnGeneral.call(t);
	// exports
	t.render = render;
	t.name = 'agendaDaySplitColumn';

	function render(date, delta) {
		baseRender(date, delta);
		corrAgenda();
	}

	function corrAgenda() {
		element.find('.fc-agenda-axis').remove();
		element.find('.fc-agenda-gutter').remove();
		element.find('.fc-col0').addClass('fc-last');
		element.find('thead .fc-col0:first').html(calendar['options']['title']);
	}
};

jq.fullCalendar.views.agendaDaySplitFirstColumn = AgendaDaySplitFirstColumn;

function AgendaDaySplitFirstColumn(element, calendar) {
	var t = this;

	// imports
	jq.fullCalendar.views.agendaDay.call(t, element, calendar);
	var opt = t.opt;
	var renderAgenda = t.renderAgenda;
	var formatDate = calendar.formatDate;
    var baseRender = t.render;
        AgendaDaySplitColumnGeneral.call(t);

	// exports
	t.render = render;
	t.name = 'agendaDaySplitFirstColumn';

	function render(date, delta) {
		baseRender(date, delta);
		corrAgenda();
	}

	function corrAgenda() {
		element.find('.fc-agenda-gutter').remove();
		element.find('.fc-col0').addClass('fc-last');
		jq('.fc-header-title:first').find('h2').html(t.title);
		element.find('thead .fc-col0:last').html(calendar['options']['title']);
	}
};

jq.fullCalendar.views.agendaDaySplitLastColumn = AgendaDaySplitLastColumn;

function AgendaDaySplitLastColumn(element, calendar) {
	var t = this;

	// imports
	jq.fullCalendar.views.agendaDay.call(t, element, calendar);
	var opt = t.opt;
	var renderAgenda = t.renderAgenda;
	var formatDate = calendar.formatDate;
    	var baseRender = t.render;
        AgendaDaySplitColumnGeneral.call(t);

	// exports
	t.render = render;
	t.name = 'agendaDaySplitLastColumn';

	function render(date, delta) {
		baseRender(date, delta);
		corrAgenda();
	}

	function corrAgenda() {
		element.find('.fc-agenda-axis').remove();
		element.find('.fc-col0').addClass('fc-last');
		element.find('thead .fc-col0:first').html(calendar['options']['title']);
	}
};

jq.fullCalendar.views.agendaDaySplitMonoColumn = AgendaDaySplitMonoColumn;

function AgendaDaySplitMonoColumn(element, calendar) {
	var t = this;

	// imports
	jq.fullCalendar.views.agendaDay.call(t, element, calendar);
	var opt = t.opt;
	var renderAgenda = t.renderAgenda;
	var formatDate = calendar.formatDate;
    var baseRender = t.render;

	// exports
	t.render = render;
	t.name = 'agendaDaySplitMonoColumn';

	function render(date, delta) {
		baseRender(date, delta);
		corrAgenda();
	}

	function corrAgenda() {
		element.find('thead .fc-col0:first').html(calendar['options']['title']);
	}
};

var SolgemaFullcalendar = {
    openAddMenu: function (start, end, allDay, event, view) {
      if(SolgemaFullcalendarVars.disableAJAX) { return; }
      jq.ajax({
        type :      'POST',
        url :       './@@SFDisplayAddMenu',
        dataType: "json",
        async:   true,
        data :      {},
        success :   function(msg) {
          if (msg['display']) {
            var data = new Object;
            var startMonth = start.getMonth()+1;
            var endMonth = end.getMonth()+1;
            data['startDate:date'] = start.getFullYear()+'-'+startMonth+'-'+start.getDate()+' '+start.getHours()+':'+start.getMinutes();
            if (!allDay) {
              data['endDate:date'] = end.getFullYear()+'-'+endMonth+'-'+end.getDate()+' '+end.getHours()+':'+end.getMinutes();
            } else {
              data['endDate:date'] = end.getFullYear()+'-'+endMonth+'-'+end.getDate()+' 23:55';
              data['wholeDay:boolean'] = '1';
            }
            data['EventAllDay'] = allDay;
            openContextualContentMenu(event, this, '@@SFAddMenu', SolgemaFullcalendar.initAddContextualContentMenu, '.', data);
          } else {
            SolgemaFullcalendar.openFastAddForm(start, end, allDay, msg['type'], msg['title'], view);
          }
        }
      });
    },
    initAddContextualContentMenu: function () {
      if(SolgemaFullcalendarVars.disableAJAX) { return; }
      jq('#kss-spinner').show();
      var $dialogContent = jq("#event_edit_container");
      $dialogContent.empty();
      $dialogContent.dialog( "destroy" );
      jq("#contextualContentMenu a[href*='createSFEvent']").click( function(event) {
        event.preventDefault();
        var href = jq(this).attr('href');
        $dialogContent.append('<iframe src="'+href+'" width="100%" scrolling="no" frameborder="0" name="SFEventEditIFRAME" style="overflow-x:hidden; overflow-y:hidden;"></iframe>');
        $dialogContent.dialog({
          width: 700,
          height: 500,
          autoOpen: true,
          modal: true,
          title: jq(this).html(),
          close: function () {
            jq('#calendar').fullCalendar('unselect');
            jq('#kss-spinner').hide();
          }
        });
        jq(closeContextualContentMenu);
      });
      jq("#contextualContentMenu a[href*='SFJsonEventPaste']").click( function(event) {
        event.preventDefault();
        var $calendar = jq('#calendar');
        jq('#kss-spinner').show();
        var href = jq(this).attr('href');
        jq.get(href,{},function(json) {
            if(json['status'] == 'pasted') {
              $calendar.fullCalendar( 'refetchEvents' );
            } else {
              window.alert(json['message']);
            }
            jq('#kss-spinner').hide();
          },"json"
        );
        jq(closeContextualContentMenu);
      });
    },
    openFastAddForm: function (start, end, allDay, type_name, title, view) {
      if(SolgemaFullcalendarVars.disableAJAX) { return; }
      jq('#kss-spinner').show();
      var $dialogContent = jq("#event_edit_container");
      $dialogContent.empty();
      $dialogContent.dialog( "destroy" );
      var $calendar = jq('#calendar');
      var data = new Object;
      var startMonth = start.getMonth()+1;
      var endMonth = end.getMonth()+1;
      data['startDate:date'] = start.getFullYear()+'-'+startMonth+'-'+start.getDate()+' '+start.getHours()+':'+start.getMinutes();
      if (!allDay) {
        data['endDate:date'] = end.getFullYear()+'-'+endMonth+'-'+end.getDate()+' '+end.getHours()+':'+end.getMinutes();
      } else {
        data['endDate:date'] = end.getFullYear()+'-'+endMonth+'-'+end.getDate()+' 23:55';
        data['wholeDay:boolean'] = '1';
      }
      data['type_name'] = type_name;
      if (allDay) data['form.widgets.allDay'] = 1;
      target_folder = view['calendar']['options']['target_folder'];
      extraData = view['calendar']['options']['extraData'];
      if (extraData) jQuery.extend(true, data, extraData);
      $dialogContent.append('<iframe src="'+target_folder+'/createSFEvent?'+jq.param(data)+'" width="100%" scrolling="no" frameborder="0" name="SFEventEditIFRAME" style="overflow-x:hidden; overflow-y:hidden;"></iframe>');
      $dialogContent.dialog({
        width: 700,
        height: 500,
        autoOpen: true,
        modal: true,
        title: title,
        close: function () {
          jq('#calendar').fullCalendar('unselect');
          jq('#kss-spinner').hide();
        }
      });
    },
    openEditForm: function (eventurl) {
      if(SolgemaFullcalendarVars.disableAJAX) { return; }
      jq('#kss-spinner').show();
      var $dialogContent = jq("#event_edit_container");
      jq("#event_edit_container").dialog( "destroy" );
      $dialogContent.empty();
      $dialogContent.dialog( "destroy" );
      var $calendar = jq('#calendar');
      $dialogContent.append('<iframe src="'+eventurl+'/SFAjax_base_edit" width="100%" scrolling="no" frameborder="0" name="SFEventEditIFRAME" style="overflow-x:hidden; overflow-y:hidden;"></iframe>');
      $dialogContent.dialog({
        width: 700,
        height: 500,
        autoOpen: true,
        modal: true,
        title: SolgemaFullcalendarVars.editEventText,
        close: function () {
          jq('#calendar').fullCalendar('unselect');
          jq('#kss-spinner').hide();
        }
      });
      jq(closeContextualContentMenu);
    },
    openSFContextualContentMenu: function (event) {
      if(SolgemaFullcalendarVars.disableAJAX) { return; }
      afterContextualContentMenuOpened = function (event) {
        var $calendar = jq('#calendar');
        var $dialogContent = jq("#event_edit_container");
        jq("#contextualContentMenu a[href*='?workflow_action=']").click( function(event) {
          event.preventDefault();
          jq('#kss-spinner').show();
          href = jq(this).attr('href');
          jq.ajax({
            type :      'POST',
            url :       './@@solgemafullcalendar_workflowtransition',
            dataType: "json",
            async:   false,
            data :      {event_path:href},
            success :   function(msg) {
              $calendar.fullCalendar('removeEvents', [msg['id'],]);
              $calendar.fullCalendar('renderEvent', msg, false);
              jq(closeContextualContentMenu);
              jq('#kss-spinner').hide();
            },
            error : function(revertFunc) {
              jq('#kss-spinner').hide();
              jq(revertFunc);
            }
          });
        });
        jq("#contextualContentMenu a[href*='delete_confirmation']").click( function(event) {
          event.preventDefault();
          jq(closeContextualContentMenu);
          if (window.confirm(SolgemaFullcalendarVars.deleteConfirmationText)) {
            var href = jq(this).attr('href');
            var eventurl = href.substring(0, href.length-19);
            jq.ajax({
              type :   'POST',
              url :    eventurl+'@@SFJsonEventDelete',
              dataType:"json",
              async:   false,
              data :   {},
              success :function(json) {
                if(json['status'] == 'ok') {
                  $calendar.fullCalendar('removeEvents', [json['id'],]);
                } else {
                  window.alert(json['message']);
                }
              }
            });
          }
        });
        jq("#contextualContentMenu a[href*='edit']").click( function(event) {
          event.preventDefault();
          jq('#kss-spinner').show();
          var href = jq(this).attr('href');
          var eventurl = href.substring(0, href.length-5);
          SolgemaFullcalendar.openEditForm(eventurl);
        });
        jq("#contextualContentMenu a[href*='object_cut']").click( function(event) {
          event.preventDefault();
          jq('#kss-spinner').show();
          var href = jq(this).attr('href');
          var eventurl = href.substring(0, href.length-10);
          jq.ajax({
            type :   'POST',
            url :    eventurl+'@@SFJsonEventCut',
            dataType:"json",
            async:   false,
            data :   {},
            success :function(json) {
              if(json['status'] == 'copied') {
                document.cookie = "__cp="+json['cp']+'; path=/';
                jq.ajax({
                  type :   'POST',
                  url :    eventurl+'@@SFJsonEvent',
                  dataType:"json",
                  async:   false,
                  data :   {},
                  success :function(json) {
                    $calendar.fullCalendar( 'refetchEvents' );
                    jq('#kss-spinner').hide();
                    jq(closeContextualContentMenu);
                  }
                });
              } else {
                window.alert(json['message']);
                jq('#kss-spinner').hide();
              }
            }
          });
          jq('#kss-spinner').hide();
        });
        jq("#contextualContentMenu a[href*='object_copy']").click( function(event) {
          event.preventDefault();
          jq('#kss-spinner').show();
          var href = jq(this).attr('href');
          var eventurl = href.substring(0, href.length-11);
          jq.ajax({
            type :   'POST',
            url :    eventurl+'@@SFJsonEventCopy',
            dataType:"json",
            async:   false,
            data :   {},
            success :function(json) {
              if(json['status'] == 'copied') {
                document.cookie = "__cp="+json['cp']+'; path=/';
                jq.ajax({
                  type :   'POST',
                  url :    eventurl+'@@SFJsonEvent',
                  dataType:"json",
                  async:   false,
                  data :   {},
                  success :function(json) {
                    $calendar.fullCalendar( 'refetchEvents' );
                    jq('#kss-spinner').hide();
                    jq(closeContextualContentMenu);
                  }
                });
              } else {
                window.alert(json['message']);
                jq('#kss-spinner').hide();
              }
            }
          });
          jq('#kss-spinner').hide();
        });
        for(var i=0;i < extraContentMenuActions.length;i++) {
          var menuname = extraContentMenuActions[i];
          jq("#contextualContentMenu a[href*='"+extraContentMenuActions[i]+"']").click( function(event) {
            event.preventDefault();
            var href = jq(this).attr('href');
            eval('SFContentMenuFunction_'+menuname)(href);
          });
        }
      };
      openContextualContentMenu(event, this, 'contextualContentMenu', afterContextualContentMenuOpened);
    },
    openDisplayForm: function (fcevent, event) {
      if(SolgemaFullcalendarVars.disableAJAX) { return; }
      event.preventDefault();
      var url = fcevent['url'];
      var eventClasses = fcevent['className'];
      for (var x = 0; x < eventClasses.length; x++) {
        if (eventClasses[x].search('type-') != -1) {
          var portalType = eventClasses[x].substring(5, eventClasses[x].length).toLowerCase();
        }
      }
      if(portalType != undefined){
    	  var extra = '/SFLight_' + portalType + '_view';
          jq('#kss-spinner').show();
          var $dialogContent = jq("#event_edit_container");
          $dialogContent.empty();
          $dialogContent.dialog( "destroy" );
          jq.get(url + extra, {}, function(msg){
              $dialogContent.append(msg);
              $dialogContent.dialog({
                width: 600,
                autoOpen: true,
                modal: true,
                title: fcevent['title']
              });
              jq('#kss-spinner').hide();
           });

      }
      else{
    	  window.open(url)
      }
    },
    getEventSources: function () {
        var sources = [];
        jq.ajax({
        url     :  SolgemaFullcalendarVars.topicAbsoluteUrl + "/@@SFEventSources",
        dataType: "json",
        async   : false,
        success :   function(msg) {
            sources = msg;
            }
        });
        return sources
    },
};

function calendarOptions() {
    var shour = SolgemaFullcalendarVars.firstHour;
    if (shour.substring(0,1) == '+' ) {
        var curDate = new Date();
        var curHour = curDate.getHours();
        var firstHour = curHour+shour.substring(1,shour.length);
    } else if (shour.substring(0,1) == '-' ) {
        var curDate = new Date();
        var curHour = curDate.getHours();
        var firstHour = curHour-shour.substring(1,shour.length);
    } else {
        var firstHour = shour;
    }
    var options = {};
      options['editable'] = SolgemaFullcalendarVars.editable;
      options['disableDragging'] = SolgemaFullcalendarVars.disableDragging;
      options['disableResizing'] = SolgemaFullcalendarVars.disableResizing;
      options['slotMinutes'] = SolgemaFullcalendarVars.slotMinutes;
      options['defaultView'] = (readCookie('SFView')) ? readCookie('SFView') : SolgemaFullcalendarVars.defaultView;
      options['firstDay'] = SolgemaFullcalendarVars.firstDay;
      options['weekends'] = SolgemaFullcalendarVars.weekends;
      options['year'] = SolgemaFullcalendarVars.year;
      options['month'] = SolgemaFullcalendarVars.monthNunber;
      options['date'] = SolgemaFullcalendarVars.date;
      options['firstHour'] = firstHour;
      options['minTime'] = SolgemaFullcalendarVars.minTime;
      options['maxTime'] = SolgemaFullcalendarVars.maxTime;
      options['height'] = SolgemaFullcalendarVars.calendarHeight;
      options['header'] = {
        left: SolgemaFullcalendarVars.headerLeft,
        center: 'title',
        right: SolgemaFullcalendarVars.headerRight
      };
      options['theme'] = true;
      options['monthNames'] = SolgemaFullcalendarVars.monthNames;
      options['monthNamesShort'] = SolgemaFullcalendarVars.monthNamesShort;
      options['dayNames'] = SolgemaFullcalendarVars.dayNames;
      options['dayNamesShort'] = SolgemaFullcalendarVars.dayNamesShort;
      options['columnFormat'] = SolgemaFullcalendarVars.columnFormat;
      options['buttonText'] = {
        today: SolgemaFullcalendarVars.today,
        month: SolgemaFullcalendarVars.month,
        week: SolgemaFullcalendarVars.week,
        day: SolgemaFullcalendarVars.day,
        calendar: '&nbsp;Cal&nbsp;',
        agendaDaySplit: SolgemaFullcalendarVars.daySplit,
      };
      options['titleFormat'] = SolgemaFullcalendarVars.titleFormat;
      options['startParam'] = "start:int";
      options['endParam'] = "end:int";
      options['ignoreTimezone'] = false;
      // we need both eventSources and solgemaSources to be able to switch between
      // normal view and daysplit view
      options['solgemaSources'] = SolgemaFullcalendar.getEventSources();
      options['eventSources'] = options['solgemaSources'];
      options['axisFormat'] = SolgemaFullcalendarVars.axisFormat;
      options['allDaySlot'] = SolgemaFullcalendarVars.allDaySlot;
      options['allDayText'] = SolgemaFullcalendarVars.allDayText;
      options['weekMode'] = "liquid";
      options['timeFormat'] = SolgemaFullcalendarVars.axisFormat;
      options['eventDrop'] = function(event, dayDelta, minuteDelta, allDay) {
        jq('#kss-spinner').show();
        data = {event: event.id, dayDelta: dayDelta, minuteDelta: minuteDelta, allDay: allDay};
        jq.ajax({
          type :   'POST',
          url :    './solgemafullcalendar_drop',
          data :   data,
          success :function(msg) {
            jq('#kss-spinner').hide();
          }
        });
      };
      options['eventResize'] = function(event,dayDelta,minuteDelta,revertFunc) {
        if(SolgemaFullcalendarVars.disableAJAX) { return; }
        jq('#kss-spinner').show();
        var data = {event: event.id, dayDelta: dayDelta, minuteDelta: minuteDelta};
        jq.ajax({
          type :      'POST',
          url :       './solgemafullcalendar_resize',
          data :      data,
          success :   function(msg) {
            jq('#kss-spinner').hide();
          },
          error : function(revertFunc) {
            jq('#kss-spinner').hide();
            jq(revertFunc);
          }
        });
      };
      options['loading'] = function(bool) {
        if (bool) {
          jq('#kss-spinner').show();
        } else {
          jq('#kss-spinner').hide();
        }
      };
      options['selectable'] = true;
      options['selectHelper'] = true;
      options['select'] = function(start, end, allDay, event, view) {
        SolgemaFullcalendar.openAddMenu(start, end, allDay, event, view);
      };
      options['eventAfterRender'] = function(fcevent, element, view) {
        jq(element).click(function(event) {
          if(event.which == 3) {
            return false;
          }
        });
        if(jq(element).hasClass('contextualContentMenuEnabled')){
        	jq(element).bind("contextmenu", SolgemaFullcalendar.openSFContextualContentMenu);
        }
      };
      options['eventClick'] = function(fcevent, event) {
        SolgemaFullcalendar.openDisplayForm(fcevent, event);
      };
      options['buttonIcons'] = {
        calendar: 'calendar'
      };
      options['loading'] = function(value, view) {
        if (value) {
          jq('#kss-spinner').show();
        } else {
          jq('#kss-spinner').hide();
        }
      };
      options['target_folder'] = SolgemaFullcalendarVars.target_folder;
      return options;
};

function initCalendar(date) {
  if (jq('.fc-button-calendar').length != 0) {
    jq('.fc-button-calendar').unbind('click');
    jq('.fc-button-calendar').append('<span style="position:relative" id="datePickerWrapper"><div id="datePicker"/></span>');
    jq('#datePickerWrapper').insertAfter('.fc-button-calendar');
    jq('#datePicker').datepicker({
      dateFormat: "dd/mm/yy",
      onSelect: function(date, inst) {
        jq('#calendar').fullCalendar('gotoDate', date.split('/')[2], date.split('/')[1]-1, date.split('/')[0]);
        jq('#datePicker').css('display', 'none');
      }
    });
    if (date) jq('#datePicker').datepicker('setDate',date);
    jq('.fc-button-calendar').removeClass('ui-state-hover');
    jq('#datePicker').css('display', 'none');
    jq('.fc-button-calendar').click( function() {
      if (jq('#datePicker').css('display') != 'block') {
        jq('#datePicker').css('display', 'block');
      }
    });
  }
};

jq(document).ready(function() {
    var calendar = jq('#calendar').fullCalendar(calendarOptions());
    initCalendar();
    jq('#SFQuery input, #SFQuery a').click( function(event){
      jq('#kss-spinner').show();
      if (jq(this).attr('href')) {
        var href = jq(this).attr('href');
        var oldValue = jq("#SFQuery input[name=sfqueryDisplay]").attr('value');
        jq('#calendar').removeClass('query-'+oldValue);
        var sfqueryDisplay = href.substring(16, href.length);
        jq('#calendar').addClass('query-'+sfqueryDisplay);
        jq("#SFQuery input[name=sfqueryDisplay]").attr('value', sfqueryDisplay);
      } else {
        var sfqueryDisplay = jq(this).attr('name');
      }
      var data = jq('#SFQuery form').serializeArray();
      var cook = new Array;
      var keys = new Array;
      for (var x = 0; x <= data.length-1; x++) {
        if (keys.toString().search(data[x].name) == -1) {
          keys.push(data[x].name);
        }
      }
      for (var x = 0; x < keys.length; x++) {
        var value = '';
        jq.each(data, function(i, elem){
          if (elem.name == keys[x]) {
            if (value == '') {
              value = elem.value;
            } else {
              value = value+'+'+elem.value;
            }
          }
        });
        cook.push({'name':keys[x], 'value':value});
      }
      var form = new Array;
      var formData = new Array;
      jq.each(jq('#SFQuery form').find('input, textarea, checkbox'), function(i, elem){ form.push(elem.name); });
      jq.each(data, function(i, elem){ formData.push(elem.name) });
      form = form.filter(function(itm,i,form){return i==form.indexOf(itm);});
      formData = formData.filter(function(itm,i,formData){return i==formData.indexOf(itm);});
      jq.each(cook, function(i,elem){
        var path = SolgemaFullcalendarVars.topicRelativeUrl;
        document.cookie = elem.name+"="+elem.value+'; path='+path;
        if (path.substring(path.length-1,path.length)!='/') path =path+'/';
        document.cookie = elem.name+"="+elem.value+'; path='+path;
      });

      jq.each(form, function(i,elem){
        if(jq.inArray(elem, formData) == -1){
            var path = SolgemaFullcalendarVars.topicRelativeUrl;
            document.cookie = elem+"="+"'azertyuiop'"+'; path='+path; // Must have a value, otherwise the portal_catalog can ignore this criterion
            if (path.substring(path.length-1,path.length)!='/') path =path+'/';
            document.cookie = elem+"="+"'azertyuiop'"+'; path='+path;
        }
      });

      if (event.which) {
        var curView = calendar.fullCalendar('getView');
        baseSources = calendar.data('fullCalendar').options['solgemaSources'];
        var eventSources = SolgemaFullcalendar.getEventSources();
        calendar.data('fullCalendar').options['solgemaSources'] = eventSources;
        if (curView.name == 'agendaDaySplit') {
            jq('#calendar').css('height', jq('#calendar').height());
            var date = jq('#calendar').fullCalendar('getDate');
            var options = calendar.data('fullCalendar').options;
            jq('#calendar').fullCalendar('destroy');
            options['year'] = date.getFullYear();
            options['month'] = date.getMonth();
            options['date'] = date.getDate();
            options['defaultView'] = 'agendaDaySplit';
            options['eventSources'] = options['solgemaSources'];
            jq('#calendar').fullCalendar(options);
            jq('#calendar').css('height', jq('#calendar').height());
            initCalendar(date);
            jq('#calendar').css('height', 'auto');
        } else {
          if (jq(this).attr('href')) {
            for (var i=0; i<baseSources.length; i++) {
              var url = baseSources[i]['url'];
              calendar.fullCalendar('removeEventSource', {'url':url});
            }
            for (var i=0; i<eventSources.length; i++) {
              calendar.fullCalendar( 'addEventSource', eventSources[i] );
            }
          } else {
            var inputs = new Array;
            var topicAbsoluteUrl = SolgemaFullcalendarVars.topicAbsoluteUrl;
            jq('#SFQuery input').each( function(i, elem) {
              inputs.push({'name':jq(elem).attr('name'),
                           'value':jq(elem).attr('value')});
            });
            var uncheckeds = new Array;
            for (var i=0; i<inputs.length; i++) {
              var found = false;
              for (var j=0; j<data.length; j++) {
                if (inputs[i]['name']==data[j]['name'] && inputs[i]['value']==data[j]['value']) found = true;
              }
              if (!found) uncheckeds.push(inputs[i]);
            }
            for (var i=0; i<uncheckeds.length; i++) {
              for (var i=0;i<baseSources.length;i++) {
                var url = baseSources[i]['url'];
                if ( url.search( jq(this).val() ) != -1 ) calendar.fullCalendar( 'removeEventSource', {'url':url} );
              }
            }
            if (jq(this).attr('name')) {
              if(jq(this).attr('checked')) {
                for (var i=0;i<eventSources.length;i++) {
                  var url = eventSources[i]['url'];
                  if ( url.search( jq(this).val() ) != -1 ) calendar.fullCalendar( 'addEventSource', eventSources[i] );
                }
              }
            }
          }
        }
      }
      jq('#kss-spinner').hide();
    });
    jq('.fc-header-right a').click( function() {
      var divClass = jq(this).parents('div').attr('class');
      var classList = divClass.split(' ');
      for (var i=0; i<classList.length; i++) {
        if (classList[i].search('fc-button-') != -1){
          var path = SolgemaFullcalendarVars.topicRelativeUrl;
          if (path.substring(path.length-1,path.length)!='/') path =path+'/';
          val = classList[i].substring(10, classList[i].length);
          document.cookie = "SFView="+val+'; path='+path;
        }
      }
    });
});

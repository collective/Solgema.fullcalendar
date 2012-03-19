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

  var SolgemaFullcalendar = {
    openAddMenu: function (start, end, allDay, event) {
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
            SolgemaFullcalendar.openFastAddForm(start, end, allDay, msg['type'], msg['title']);
          }
        }
      });
    },
    initAddContextualContentMenu: function () {
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
    openFastAddForm: function (start, end, allDay, type_name, title) {
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
      $dialogContent.append('<iframe src="'+SolgemaFullcalendarVars.target_folder+'/createSFEvent?'+jq.param(data)+'" width="100%" scrolling="no" frameborder="0" name="SFEventEditIFRAME" style="overflow-x:hidden; overflow-y:hidden;"></iframe>');
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
          if (window.confirm("Voulez-vous supprimer cet événement ?")) {   // TODO: French ui-text in js, is this a joke?
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
    }
  };

  jq(document).ready(function() {
    var thisYear = SolgemaFullcalendarVars.year;
    var thisMonth = SolgemaFullcalendarVars.monthNunber;
    var thisDate = SolgemaFullcalendarVars.date;
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
    var calendar = jq('#calendar').fullCalendar({
      slotMinutes : SolgemaFullcalendarVars.slotMinutes,
      defaultView: (readCookie('SFView')) ? readCookie('SFView') : SolgemaFullcalendarVars.defaultView,
      firstDay : SolgemaFullcalendarVars.firstDay,
      weekends : SolgemaFullcalendarVars.weekends,
      year : thisYear,
      month : thisMonth,
      date : thisDate,
      firstHour : firstHour,
      minTime : SolgemaFullcalendarVars.minTime,
      maxTime : SolgemaFullcalendarVars.maxTime,
      height : SolgemaFullcalendarVars.calendarHeight,
      header: {
        left: 'prev,next today',
        center: 'title',
        right: SolgemaFullcalendarVars.headerRight
      },
      theme: true,
      monthNames: SolgemaFullcalendarVars.monthNames,
      monthNamesShort: SolgemaFullcalendarVars.monthNamesShort,
      dayNames: SolgemaFullcalendarVars.dayNames,
      dayNamesShort: SolgemaFullcalendarVars.dayNamesShort,
      columnFormat: SolgemaFullcalendarVars.columnFormat,
      buttonText: {
        prev: '&nbsp;&#9668;&nbsp;',
        next: '&nbsp;&#9658;&nbsp;',
        prevYear: '&nbsp;&lt;&lt;&nbsp;',
        nextYear: '&nbsp;&gt;&gt;&nbsp;',
        today: SolgemaFullcalendarVars.today,
        month: SolgemaFullcalendarVars.month,
        week: SolgemaFullcalendarVars.week,
        day: SolgemaFullcalendarVars.day
      },
      titleFormat: SolgemaFullcalendarVars.titleFormat,
      editable: true,
      startParam: "start:int",
      endParam: "end:int",
      ignoreTimezone: false,
      events: SolgemaFullcalendarVars.topicAbsoluteUrl + "/solgemafullcalendarevents",
      axisFormat: SolgemaFullcalendarVars.axisFormat,
      allDaySlot: SolgemaFullcalendarVars.allDaySlot,
      allDayText: SolgemaFullcalendarVars.allDayText,
      weekMode: "liquid",
      timeFormat: SolgemaFullcalendarVars.axisFormat,
      eventDrop: function(event, dayDelta, minuteDelta, allDay) {
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
      },
      eventResize: function(event,dayDelta,minuteDelta,revertFunc) {
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
      },
      loading: function(bool) {
        if (bool) {
          jq('#kss-spinner').show();
        } else {
          jq('#kss-spinner').hide();
        }
      },
      selectable: true,
      selectHelper: true,
      select: function(start, end, allDay, event, view) {
        SolgemaFullcalendar.openAddMenu(start, end, allDay, event);
      },
      eventAfterRender: function(fcevent, element, view) {
        jq(element).click(function(event) {
          if(event.which == 3) {
            return false;
          }
        });
        if(jq(element).hasClass('contextualContentMenuEnabled')){
        	jq(element).bind("contextmenu", SolgemaFullcalendar.openSFContextualContentMenu);
        }
      },
      eventClick: function(fcevent, event) {
        SolgemaFullcalendar.openDisplayForm(fcevent, event);
      }
    });
    jq('#SFQuery input, #SFQuery a').click( function(event){
      if (jq(this).attr('href')) {
        var href = jq(this).attr('href');
        var oldValue = jq("#SFQuery input[name=sfqueryDisplay]").attr('value');
        jq('#calendar').removeClass('query-'+oldValue);
        var sfqueryDisplay = href.substring(16, href.length);
        jq('#calendar').addClass('query-'+sfqueryDisplay);
        jq("#SFQuery input[name=sfqueryDisplay]").attr('value', sfqueryDisplay);
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
            document.cookie = elem+"="+"'azertyuiop'"+'; path='+path;       // Must have a value, otherwise the portal_catalog can ignore this criterion
            if (path.substring(path.length-1,path.length)!='/') path =path+'/';
            document.cookie = elem+"="+"'azertyuiop'"+'; path='+path;
        }
      });

      if (event.which) calendar.fullCalendar( 'refetchEvents' );
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

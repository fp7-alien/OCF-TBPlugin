
from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe
from itertools import groupby
from calendar import HTMLCalendar, monthrange
import datetime
from alien_plugin.log.log import *

class ResourceCalendar(HTMLCalendar):


    def __init__(self, pContestEvents):
        super(ResourceCalendar, self).__init__()
        #self.contest_events = self.group_by_day(pContestEvents)

    def __init__(self):
        super(ResourceCalendar, self).__init__()
        #self.contest_events = []

    def formatday(self, day, weekday,reservedDays):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            if datetime.date.today() == datetime.date(self.year, self.month, day):
                cssclass += ' today'
            #if day in self.contest_events:
            if day in reservedDays:
                cssclass += ' filled'
                body = []
                '''
                for contest in self.contest_events[day]:
                    body.append('<a href="%s">' % contest.get_absolute_url())
                    body.append(esc(contest.contest.name))
                    body.append('</a><br/>')
                '''
                return self.day_cell(cssclass, '<div class="dayNumber">%d</div> %s' % (day, ''.join(body)))
            return self.day_cell(cssclass, '<div class="dayNumber">%d</div>' % day)
        return self.day_cell('noday', '&nbsp;')

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super(ResourceCalendar, self).formatmonth(year, month)

    def group_by_day(self, events):
        field = lambda event: event.date_of_event.day
        return dict(
            [(day, list(items)) for day, items in groupby(events, field)]
        )

    def day_cell(self, cssclass, body):
        return '<td class="%s">%s</td>' % (cssclass, body)

    def formatmonth2(self, year, month,reservedDays):
        self.year, self.month = year, month
        theyear=year
        themonth=month
        withyear=True
        """
        Return a formatted month as a table.
        """
        v = []
        a = v.append
        a('<table border="0" cellpadding="0" cellspacing="0" class="month">')
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week,reservedDays))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)

    def formatweek(self, theweek,reservedDays):
        """
        Return a complete week as a table row.
        """
        s = ''.join(self.formatday(d, wd,reservedDays) for (d, wd) in theweek)
        return '<tr>%s</tr>' % s

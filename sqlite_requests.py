import sqlite3
from datetime import datetime


class Database(object):

    def __init__(self):
        self.con = sqlite3.connect('database_timecontrol.db')
        self.cur = self.con.cursor()

    def create_new_action(self, action):
        if action == "":
            return

        self.cur.execute('SELECT action FROM actions WHERE action_search = "{}"'.format(action.upper()))

        if len(self.cur.fetchall()) != 0:
            return

        self.cur.execute('INSERT INTO actions VALUES("{}", "{}")'.format(action, action.upper()))
        self.con.commit()

    def actions(self, search=""):
        if search == "":
            self.cur.execute('SELECT action FROM actions LIMIT 5')
        else:
            self.cur.execute('SELECT action FROM actions WHERE action_search LIKE "%{}%" LIMIT 5'
                             .format(search.upper()))
        return list(self.cur.fetchall())

    def current_actions(self):
        self.cur.execute('SELECT * FROM current_actions')
        return list(self.cur.fetchall())

    def set_active(self, action, active):
        if active:
            self.cur.execute('UPDATE current_actions SET is_active = "{}" WHERE action != "{}"'.format(False, action))
            self.cur.execute('UPDATE current_actions SET is_active = "{}", date_start = "{}" '
                             'WHERE action = "{}"'.format(active, datetime.now(), action))
        else:
            self.cur.execute('UPDATE current_actions SET is_active = "{}" WHERE action = "{}"'.format(active, action))
        self.con.commit()

    def append_current_action(self, date, action, in_process=True):

        self.cur.execute('SELECT action FROM current_actions WHERE action = "{}"'.format(action))

        if len(self.cur.fetchall()) != 0:
            return

        self.cur.execute('INSERT INTO current_actions VALUES("{}", "{}", "{}")'
                         .format(date, action, in_process))
        self.con.commit()

    def remove_current_action(self, action):

        self.cur.execute('DELETE FROM current_actions WHERE action = "{}"'.format(action))
        self.con.commit()

    def remove_action(self, action):

        self.cur.execute('DELETE FROM actions WHERE action = "{}"'.format(action))
        self.con.commit()

    def remove_completed_action(self, action, period_start, period_finish):

        self.cur.execute('DELETE FROM completed_actions WHERE action = "{}" AND '
                         'date_start BETWEEN "{}" AND "{}"'.format(action, period_start, period_finish))

        self.con.commit()

    def save_completed_action(self, action):

        self.cur.execute('UPDATE current_actions SET is_active = "{}" WHERE action = "{}"'.format(False, action))

        self.cur.execute('SELECT date_start FROM current_actions WHERE action = "{}"'.format(action))

        try:
            date_start = self.cur.fetchall()[0][0]
        except IndexError:
            self.con.commit()
            return

        delta = (datetime.now() - datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S.%f')).total_seconds()
        if delta < 5:
            return

        self.cur.execute('INSERT INTO completed_actions VALUES("{}", "{}", "{}")'
                         .format(date_start, datetime.now(), action))

        self.con.commit()

    def results(self, date_start, date_finish, show_variant):

        if show_variant == 'in total':
            self.cur.execute('SELECT action, SUM(CAST((JulianDay(date_finish) - JulianDay(date_start))'
                             '* 24 * 60 * 60 As Integer)) FROM completed_actions '
                             'WHERE date_start BETWEEN "{}" AND "{}"'
                             'GROUP BY action'.format(date_start, date_finish))
        elif show_variant == 'in detail':
            self.cur.execute('SELECT action, CAST((JulianDay(date_finish) - JulianDay(date_start))'
                             '* 24 * 60 * 60 As Integer), date_start, date_finish FROM completed_actions '
                             'WHERE date_start BETWEEN "{}" AND "{}"'.format(date_start, date_finish))
        else:
            print("Ошибка 1 sqlite_requests.py")

        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.con.close()


db = Database()

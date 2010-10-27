#!/usr/bin/env python

#  Copyright 2010 Leonid Movshovich <event.riga@gmail.com>

# This file is part of Webridge.
# Webridge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# Webridge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with Webridge.  If not, see <http://www.gnu.org/licenses/>.

import logging
import Queue
import threading

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from django.utils  import simplejson as json

import bridge
import actions

class TableIdGen :
    lock = threading.Lock()
    i = 0;
    def next(self) :
        self.lock.acquire();
        res = self.i
        self.i += 1
        self.lock.release()
        return res

table_idgen = TableIdGen()


def create_test_hall_updates() :
    return [{'type': 'table.add', 'value':table_idgen.next()}, {'type': 'table.add', 'value':table_idgen.next()}
            , {'type': 'table.remove', 'value': 0}
            , {'type': 'player.sit', 'value': {'name': 'jimmy', 'table': 0, 'position': 'N'}}
            , {'type': 'player.sit', 'value': {'name': 'johny', 'table': 0, 'position': 'S'}}
            , {'type': 'player.leave', 'value': {'table': 0, 'position': 'S'}}
            ]

user_queue = Queue.Queue()

def empty_queue() :
    res = []
    try :
#        while True :
        res.append(user_queue.get_nowait())
    except Queue.Empty :
        pass
    return res

class Redirector(webapp.RequestHandler) :
    def get(self) :
        self.redirect('index.html')

class UpdateHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user is not None:
            data = empty_queue()
            res = json.dumps(data)
            # logging.info(res)
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(res)
        else:
            self.redirect(users.create_login_url(self.request.uri))

class ActionHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user is not None:
            arglist = self.request.query_string.split('/')
            action = arglist[0]
            try :
                f = actions.action_processors[action]
            except KeyError:
                self.response.set_status(404)
            else :
                map(user_queue.put_nowait, f(user, *arglist[1:]))
        else:
            self.redirect(users.create_login_url(self.request.uri))

class StaticHandler(webapp.RequestHandler) :
    def get(self):
        user = users.get_current_user()

        if user is not None:
            page = self.request.path[1:]
            self.response.out.write(open(page, 'rb').read())
            if page.startswith('table.html') :
                map(user_queue.put_nowait, actions.create_new_deck())
            elif page.startswith('hall.html') :
                map(user_queue.put_nowait, create_test_hall_updates())
        else:
            self.redirect(users.create_login_url(self.request.uri))

def main():
    application = webapp.WSGIApplication([('/', Redirector),
                                          ('/hall.html', StaticHandler),
                                          ('/table.html', StaticHandler),
                                          ('/update.json', UpdateHandler),
                                          ('/action.json', ActionHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

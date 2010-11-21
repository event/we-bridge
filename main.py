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
from google.appengine.ext.webapp import util, template
from django.utils  import simplejson as json

import bridge
import actions

def checklogin(f) :
    def decorated(self):
        if users.get_current_user() is not None :
            f(self)
        else :
            self.redirect(users.create_login_url(self.request.uri))
        
    return decorated 


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
    @checklogin
    def get(self):
        data = empty_queue()
        res = json.dumps(data)
        logging.info(res)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(res)

class ActionHandler(webapp.RequestHandler):
    @checklogin
    def post(self):
        arglist = self.request.query_string.split('/')
        action = arglist[0]
        try :
            f = actions.action_processors[action]
        except KeyError:
            self.response.set_status(404)
        else :
            map(user_queue.put_nowait, f(users.get_current_user(), *arglist[1:]))

class StaticHandler(webapp.RequestHandler) :
    @checklogin
    def get(self):
        page = self.request.path[1:]
        if page.startswith('table.html') :
            map(user_queue.put_nowait, actions.create_new_deck_messages(users.get_current_user()))
        elif page.startswith('hall.html') :
            map(user_queue.put_nowait, create_test_hall_updates())
        else :
            self.response.set_status(404)
            return
            
        self.response.out.write(open(page, 'rb').read())

class ProtocolHandler(webapp.RequestHandler) :
    @checklogin
    def get(self):
        page = self.request.path[1:]
        values = {'protocol_id': self.request.query_string, 'vuln_EW': True, 'vuln_NS': False, 'dealer': 'S'
                  , 'N' : {'spades': 'A K Q', 'hearts': 'J 10 9', 'diamonds': '8 7 6', 'clubs': '5 4 3 2'}
                  , 'E' : {'spades': 'J 10 9', 'hearts': '8 7 6', 'diamonds': '5 4 3 2', 'clubs':  'A K Q'}
                  , 'S' : {'spades': '5 4 3 2', 'hearts': 'A K Q', 'diamonds': 'J 10 9', 'clubs':  '8 7 6'}
                  , 'W' : {'spades': '8 7 6', 'hearts': '5 4 3 2', 'diamonds': 'A K Q', 'clubs': 'J 10 9'}
                  , 'records': [{'N': 'Piotr', 'E': 'Johny', 'S': 'Susy', 'W': 'Wallet'
                                 , 'contract': '5<img src="images/s.png" alt="S"/>', 'decl': 'S'
                                 , 'lead': '<img src="images/s.png" alt="S"/>5', 'tricks': '='
                                 , 'result': '+670'}]}
        self.response.out.write(template.render(page, values))

def main():
    application = webapp.WSGIApplication([('/', Redirector),
                                          ('/hall.html', StaticHandler),
                                          ('/table.html', StaticHandler),
                                          ('/protocol.html', ProtocolHandler),
                                          ('/update.json', UpdateHandler),
                                          ('/action.json', ActionHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

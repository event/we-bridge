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

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from django.utils  import simplejson as json

import bridge


class Redirector(webapp.RequestHandler) :
    def get(self) :
        self.redirect('index.html')

def to_dict(hand) :
    s, h, d, c = bridge.split_by_suits(hand)
    return {'type': 'hand', 'value':{'suits':[{'suit': 'spades', 'cards': s}
                                              , {'suit': 'hearts', 'cards': h}
                                              , {'suit': 'diamonds', 'cards': d}
                                              , {'suit': 'clubs', 'cards': c}]}}

def add_players(hand_list) :
    hand_list[0]['value']['player'] = 'own'
    hand_list[1]['value']['player'] = 'left'
    hand_list[2]['value']['player'] = 'right'
    hand_list[3]['value']['player'] = 'part'
    return hand_list

user_queue = Queue.Queue()

def do_lead(player, suit, rank) :
#    if valid_lead(player, suit, rank) :
    user_queue.put_nowait({'type': 'lead', 'value': {'player': player, 'suit': suit, 'rank': rank}})

action_processors = {'lead': do_lead}


def empty_queue() :
    res = []
    try :
#        while True :
        res.append(user_queue.get_nowait())
    except Queue.Empty :
        pass
    return res

class UpdateHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user is not None:
            self.response.headers['Content-Type'] = 'application/json'
            data = empty_queue()
            res = json.dumps(data)
            # logging.info(res)
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
                f = action_processors[action]
            except KeyError:
                self.response.set_status(404)
            else :
                f(*arglist[1:])
        else:
            self.redirect(users.create_login_url(self.request.uri))

class StaticHandler(webapp.RequestHandler) :
    def get(self):
        user = users.get_current_user()

        if user is not None:
            self.response.out.write(open(self.request.path[1:], 'rb').read())
            hands = add_players(map(to_dict, bridge.get_deck()))
            for h in hands :
                user_queue.put_nowait(h)
        else:
            self.redirect(users.create_login_url(self.request.uri))

def main():
    application = webapp.WSGIApplication([('/', Redirector),
                                          ('/index.html', StaticHandler),
                                          ('/update.json', UpdateHandler),
                                          ('/action.json', ActionHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

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

class TableIdGen :
    lock = threading.Lock()
    i = 0;
    def next(self) :
        self.lock.acquire();
        res = self.i
        self.i += 1
        self.lock.release()
        return res

player_names = ['own', 'left', 'right', 'part']

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
    for i in xrange(4) :
        hand_list[i]['value']['player'] = player_names[i]
    return hand_list

table_idgen = TableIdGen()
def create_test_hall_updates() :
    return [{'type': 'table.add', 'value':table_idgen.next()}, {'type': 'table.add', 'value':table_idgen.next()}
            , {'type': 'table.remove', 'value': 0}
            , {'type': 'player.sit', 'value': {'name': 'jimmy', 'table': 0, 'position': 'N'}}
            , {'type': 'player.sit', 'value': {'name': 'johny', 'table': 0, 'position': 'S'}}
            , {'type': 'player.leave', 'value': {'table': 0, 'position': 'S'}}
            ]

user_queue = Queue.Queue()
current_deck = None
lead_history = None

def is_deck_empty(deck) :
    result = True;
    i = len(deck)
    while i > 0 and result :
        i -= 1
        result = len(deck[i]) == 0
        
    return result

def do_lead_server(user, player, suit, rank) :
    hand = current_deck[player_names.index(player)]
    last_round = lead_history[-1]
    if len(last_round) == 4 :
        current_round = []
        lead_history.append(current_round)
    else :
        current_round = last_round
    card = bridge.suit_rank_to_num(suit, rank)
    result = bridge.check_lead(hand, card, current_round)
    if result :
        hand.remove(card)
        current_round.append(card)
    return result


def do_lead(user, player, suit, rank) :
    if do_lead_server(user, player, suit[0].upper(), rank) :
        user_queue.put_nowait({'type': 'lead', 
                           'value': {'player': player, 'suit': suit, 'rank': rank, 'allowed': [suit]}})
        if is_deck_empty(current_deck) :
            create_and_send_new_deck()

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
                f = action_processors[action]
            except KeyError:
                self.response.set_status(404)
            else :
                f(user, *arglist[1:])
        else:
            self.redirect(users.create_login_url(self.request.uri))

def create_and_send_new_deck() :
    global current_deck
    global lead_history
    deck = bridge.get_deck()
    current_deck = deck
    hands = add_players(map(to_dict, deck))
    lead_history = [[]]
    for h in hands :
        user_queue.put_nowait(h)

class StaticHandler(webapp.RequestHandler) :
    def get(self):
        user = users.get_current_user()

        if user is not None:
            page = self.request.path[1:]
            self.response.out.write(open(page, 'rb').read())
            if page.startswith('table.html') :
                create_and_send_new_deck()
            elif page.startswith('hall.html') :
                test_updates = create_test_hall_updates()
                for u in test_updates :
                    user_queue.put_nowait(u)
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

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

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from django.utils  import simplejson as json
import django
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

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user is not None:
            self.response.headers['Content-Type'] = 'application/json'
            deck = bridge.get_deck()
            before_json = add_players(map(to_dict, deck))
            res = json.dumps(before_json)
            logging.warning(before_json)
            logging.warning(res)
            self.response.out.write(res)
#             self.response.out.write('''[{"type":"hand", "value":{"player":"own", "suits":
# [{"suit":"spades", "cards":"K Q J 10 5 2"}, {"suit":"hearts", "cards":"K Q J 10 5 2"}, 
# {"suit":"diamonds", "cards":"K Q J 10 5 2"}, {"suit":"clubs", "cards":"K Q J 10 5 2"}]}},
# {"type":"hand", "value":{"player":"part", "suits":
# [{"suit":"spades", "cards":"K Q J 10 5 2"}, {"suit":"hearts", "cards":"K Q J 10 5 2"}, 
# {"suit":"diamonds", "cards":"K Q J 10 5 2"}, {"suit":"clubs", "cards":"K Q J 10 5 2"}]}},
# {"type":"hand", "value":{"player":"left", "suits":
# [{"suit":"spades", "cards":"K Q J 10 5 2"}, {"suit":"hearts", "cards":"K Q J 10 5 2"}, 
# {"suit":"diamonds", "cards":"K Q J 10 5 2"}, {"suit":"clubs", "cards":"K Q J 10 5 2"}]}},
# {"type":"hand", "value":{"player":"right", "suits":
# [{"suit":"spades", "cards":"K Q J 10 5 2"}, {"suit":"hearts", "cards":"K Q J 10 5 2"}, 
# {"suit":"diamonds", "cards":"K Q J 10 5 2"}, {"suit":"clubs", "cards":"K Q J 10 5 2"}]}}]''')
        else:
            self.redirect(users.create_login_url(self.request.uri))

class StaticHandler(webapp.RequestHandler) :
    def get(self):
        user = users.get_current_user()

        if user is not None:
            self.response.out.write(open('index.html', 'rb').read())
        else:
            self.redirect(users.create_login_url(self.request.uri))

def main():
    application = webapp.WSGIApplication([('/', Redirector),
                                          ('/index.html', StaticHandler),
                                          ('/update.json', MainHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

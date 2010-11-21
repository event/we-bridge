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
import repository as repo

IMAGE_TEMPLATE = '<img src="images/%s.png" alt="%s"/>'

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

def protocol2map(curuser, p) :
    lead = bridge.num_to_suit_rank(p.moves[0])
    lead_s = lead[0][0]
    lead =  IMAGE_TEMPLATE % (lead_s, lead_s.upper()) + lead[1]
    cntrct = p.contract[:-1].replace('d', 'X').replace('r','XX')
    cntrct_s = cntrct[1]
    cntrct = cntrct[0] + IMAGE_TEMPLATE % (cntrct_s.lower(), cntrct_s) + cntrct[2:]
    return {'N': p.N.nickname(), 'E': p.E.nickname(), 'S': p.S.nickname(), 'W': p.W.nickname(), 
            'contract': cntrct, 'decl': p.contract[-1]
            , 'lead': lead, 'tricks': '=' if p.tricks == 0 else p.tricks, 'result': p.result
            , 'highlight': curuser in [p.N, p.E, p.S, p.W] }

class ProtocolHandler(webapp.RequestHandler) :
    @checklogin
    def get(self):
        page = self.request.path[1:]
        dealid = int(self.request.query_string)
        deal = repo.Deal.get_by_id(dealid)
        hands = map(bridge.split_by_suits, [deal.n_hand, deal.e_hand, deal.s_hand, deal.w_hand])
        h_val = dict(zip(bridge.SIDES
                         , [dict(zip(['clubs',  'diamonds', 'hearts', 'spades'], h)) for h in hands]))

        protoiter = repo.Protocol.get_by_deal(deal)
        
        values = {'protocol_id': dealid, 'vuln_EW': deal.vulnerability & bridge.VULN_EW
                  , 'vuln_NS': deal.vulnerability & bridge.VULN_NS, 'dealer': bridge.SIDES[deal.dealer]
                  , 'records': map(lambda x: protocol2map(users.get_current_user(), x), protoiter)}
        values.update(h_val)
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

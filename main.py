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
import inspect
import random
import string

from google.appengine.api import users, channel
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
        
    def decorated_w_user(self):
        user = users.get_current_user()
        if user is not None :
            prof = repo.UserProfile.get_or_create(user)
            prof.loggedin = True
            prof.put()
            f(self, prof)
        else :
            self.redirect(users.create_login_url(self.request.uri))
        
    if len(inspect.getargspec(f).args) > 1 :
        return decorated_w_user
    else :
        return decorated 


def arguments(request) :
    return request.query_string.split('/')

class Redirector(webapp.RequestHandler) :
    @checklogin
    def get(self) :
        self.redirect('hall.html')

class ActionHandler(webapp.RequestHandler):
    @checklogin
    def post(self, prof):
        arglist = arguments(self.request)
        action = arglist[0]
        try :
            f = actions.action_processors[action]
        except KeyError:
            self.response.set_status(404)
        else :
            f(prof, *arglist[1:])

def uname_messages(umap, baseplace) :
    result = []
    for p, u in umap.iteritems() :
        result.append({'type': 'user', 'value': {'position': bridge.relation(p, baseplace)\
                                                     , 'name': u.nickname()}})
    return result
                      

class TableHandler(webapp.RequestHandler) :
    @checklogin
    def get(self, prof):
        args = arguments(self.request)
        user = prof.user  
        if args[0] == 'new' :
            t = repo.Table()
            t.N = user
            ident = t.put().id()
            mes = {'type': 'table.add', 'value': {'id': ident}}
            repo.UserProfile.broadcast(mes)
            self.redirect('table.html?%s/N' % ident)
        else :
            tid = int(args[0]) 
            table = repo.Table.get_by_id(tid)
            if len(args) > 1 :
                place = args[1]
                if table.sit(place, user) :
                    mes = {'type': 'player.sit', 'value': {'id': tid, 'position': place, 'name': user.nickname()}}
                    repo.UserProfile.broadcast(mes)
                    umap = table.usermap()
                    prof.enqueue(uname_messages(umap, place))
                    del umap[place]
                    for p, u in umap.iteritems() :
                        rel = bridge.relation(place, p)
                        m  = {'type': 'user', 'value': {'position': rel, 'name': user.nickname()}}
                        repo.UserProfile.uenqueue(u, m)

                    if table.full() :
                        actions.start_new_deal(table)
                    table.put()    
                    relations = dict([(bridge.relation(p, place), p) for p in bridge.SIDES])
                    self.response.out.write(template.render('table.html', relations))
                else :
                    self.redirect('hall.html')
            else :
                self.redirect('hall.html')
                # table.kibitzers.append(user)
                # show_table_state(user)
                    

def nick_or_empty(user, tid, side):
    if user is None :
        return "<a href=table.html?%s/%s>take a sit</a>" % (tid, side)
    else :
        return user.nickname()

def show_all_tables() :
    res = []
    # obvious cache candidate
    for t in repo.Table.all():
        tid = t.key().id()
        res.append({'id': tid, 'N': nick_or_empty(t.N, tid, 'N'), 'E': nick_or_empty(t.E, tid, 'E')
                    , 'S': nick_or_empty(t.S, tid, 'S'), 'W': nick_or_empty(t.W, tid, 'W')
                    , 'kibcount': len(t.kibitzers)})
    return res

class HallHandler(webapp.RequestHandler) :
    @checklogin
    def get(self, prof):
        self.response.out.write(template.render('hall.html', {'tables': show_all_tables()}))

class ChannelHandler(webapp.RequestHandler) :
    @checklogin
    def get(self, prof):
        if prof.chanid is None :
            chanid = prof.user.nickname() \
                + ''.join([random.choice(string.letters + string.digits) for i in xrange(10)])
            prof.chanid = chanid
        else : 
            chanid = prof.chanid
        token = channel.create_channel(chanid)
        prof.enqueue(prof.messages)
        prof.messages = []
        prof.put()
        self.response.out.write(json.dumps(token))

def protocol2map(curuser, p) :
    lead = bridge.num_to_suit_rank(p.moves[0])
    lead_s = lead[0][0]
    lead =  IMAGE_TEMPLATE % (lead_s, lead_s.upper()) + lead[1]
    cntrct = p.contract[:-1].replace('d', 'x').replace('r','xx').replace('Z', 'NT')
    cntrct_s = cntrct[1]
    cntrct = cntrct[0] + IMAGE_TEMPLATE % (cntrct_s.lower(), cntrct_s) + cntrct[2:]
    return {'N': p.N.nickname(), 'E': p.E.nickname(), 'S': p.S.nickname(), 'W': p.W.nickname(), 
            'contract': cntrct, 'decl': p.contract[-1]
            , 'lead': lead, 'tricks': '=' if p.tricks == 0 else p.tricks, 'result': p.result
            , 'highlight': curuser in [p.N, p.E, p.S, p.W] }

class ProtocolHandler(webapp.RequestHandler) :
    @checklogin
    def get(self, prof):
        page = self.request.path[1:]
        dealid = int(self.request.query_string)
        deal = repo.Deal.get_by_id(dealid)
        hands = map(bridge.split_by_suits, [deal.n_hand, deal.e_hand, deal.s_hand, deal.w_hand])
        h_val = dict(zip(bridge.SIDES
                         , [dict(zip(['clubs',  'diamonds', 'hearts', 'spades'], h)) for h in hands]))

        protoiter = repo.Protocol.get_by_deal(deal)
        
        values = {'protocol_id': dealid, 'vuln_EW': deal.vulnerability & bridge.VULN_EW
                  , 'vuln_NS': deal.vulnerability & bridge.VULN_NS, 'dealer': bridge.SIDES[deal.dealer]
                  , 'records': map(lambda x: protocol2map(prof.user, x), protoiter)}
        values.update(h_val)
        self.response.out.write(template.render(page, values))




def main():
    application = webapp.WSGIApplication([('/', Redirector),
                                          ('/hall.html', HallHandler),
                                          ('/table.html', TableHandler),
                                          ('/protocol.html', ProtocolHandler),
                                          ('/channel.json', ChannelHandler),
                                          ('/action.json', ActionHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

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
import inspect
import random
import string
import math

from google.appengine.api import users, channel
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, template
from django.utils  import simplejson as json

import bridge
import actions
from actions import m 
import repository as repo
import time

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
            prof.put() # updates last access time for inactive user tracking
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
    def get(self) :
        return self.post()

    @checklogin
    def post(self, prof):
        arglist = arguments(self.request)
        action = arglist[0]
        try :
            f = actions.action_processors[action]
        except KeyError:
            self.response.set_status(404)
        else :
            redir = f(prof, *arglist[1:])
            logging.info('redirect to %s' % redir)
            if redir is not None :
                self.redirect(redir)

def uname_messages(umap, baseplace) :
    result = []
    for p, u in umap.iteritems() :
        result.append(m('user.sit', position = bridge.relation(p, baseplace), name = u.nickname()))
    return result

def current_table_state(user, place, table, allow_moves=True) :
    tid = table.key().id()
    umap = table.usermap()
    
    messages = [m('user.sit', position = bridge.relation(p, place), name = u.nickname()) 
                for p, u in umap.iteritems()]
    p = table.protocol
    if p is None :
        return messages
    deal = p.deal
    moves = p.moves
    hand = actions.hand_left(deal.hand_by_side(place), moves)
    messages += [m('hand', cards = hand, player = 'own')
                , m('start.bidding', vuln = deal.vulnerability, dealer = deal.dealer)]
    side = deal.dealer
    for b in p.bidding :
        messages.append(m('bid', side = side, bid = b))
        side = (side + 1) % 4

    c = p.contract
    if c is None :
        return messages
    
    messages.append(m('start.play', contract = c.replace('d', 'x').replace('r','xx') 
                      , lead = (bridge.SIDES.index(c[-1]) + 1) % 4))
    
    decl_side = c[-1]
    trump = c[1]
    full_rounds_played = len(moves) / 4
    rounds_total = int(math.ceil(float(len(moves)) / 4))
    decl_tricks, taker = bridge.decl_tricks_and_next_move_offset(moves[:(rounds_total - 2) * 4], trump)
    cards_to_show = moves[(rounds_total - 2) * 4:]
    lasttrick, lasttaker = bridge.decl_tricks_and_next_move_offset(cards_to_show, trump)
    if taker % 2 == 1 :
        decl_tricks += lasttrick
    else :
        decl_tricks += 2 - (rounds_total - full_rounds_played) - lasttrick
    defen_tricks = full_rounds_played - decl_tricks
    place_idx = bridge.SIDES.index(place)
    decl_idx = bridge.SIDES.index(decl_side)
    if place_idx % 2 == decl_idx % 2 :
        our_t = decl_tricks
        their_t = defen_tricks
    else :
        our_t = defen_tricks
        their_t = decl_tricks
    messages.append(m('tricks', our = our_t, their = their_t))
    rel_idx = (decl_idx + 1) - place_idx
    if len(cards_to_show) > 3 :
        lastrnd = cards_to_show[:4]
        lt_base = taker + rel_idx
        messages += [m('move', card = lastrnd[i], player = bridge.REL_SIDES[(lt_base + i)%4]) for i in xrange(4)]
        move_offs = bridge.decl_tricks_and_next_move_offset(lastrnd, trump)[1] + taker
        currnd = cards_to_show[4:]
    else :
        currnd = cards_to_show
        move_offs = taker
    
    s = (rel_idx + move_offs) % 4 
    for card in currnd :
        messages.append(m('move', card = card, player = bridge.REL_SIDES[s]))
        s = (s + 1) % 4
    dummy_side = p.dummy() 
    if place == dummy_side :
        messages.append(m('hand', cards = actions.hand_left(deal.hand_by_side(decl_side), moves)
                          , player = 'part'))
        return messages

    s = (rel_idx + taker + lasttaker) % 4
    if s == 2 and place == decl_side :
        messages[-1]['value']['next'] = 'part'
        hand = actions.hand_left(deal.hand_by_side(dummy_side), moves)
        s = 0
    else :
        messages[-1]['value']['next'] = 'own'

    if allow_moves and s == 0: 
        if rounds_total != full_rounds_played and bridge.has_same_suit(hand, currnd[0]):
            messages[-1]['value']['allowed'] = currnd[0] / 13 
        else :
            messages[-1]['value']['allowed'] = 'any'
            
    messages.append(m('hand', cards = actions.hand_left(deal.hand_by_side(dummy_side), moves)
                             , player = bridge.relation(dummy_side, place)))
    return messages
                      
class TableHandler(webapp.RequestHandler) :
    @checklogin
    def get(self, prof):
        args = arguments(self.request)
        user = prof.user  
        if args[0] == 'new' :
            t = repo.Table()
            t.N = user
            ident = t.put().id()
            repo.UserProfile.broadcast([m('table.add', tid=ident)
                                        , m('player.sit', tid = ident, position = 'N', name = user.nickname())])
            self.redirect('table.html?%s/N' % ident)
        else :
            tid = int(args[0]) 
            table = repo.Table.get_by_id(tid)
            if len(args) > 1 :
                place = args[1]
                current = table.user_by_side(place)
                if current is None :
                    table.sit(place, user)
                    mes = m('player.sit', tid = tid, position = place, name = user.nickname())
                    repo.UserProfile.broadcast(mes)
                    umap = table.usermap()
                    prof.enqueue(uname_messages(umap, place))
                    del umap[place]
                    nick = user.nickname()
                    for p, u in umap.iteritems() :
                        rel = bridge.relation(place, p)
                        mes  = m('user.sit', position = rel, name = nick)
                        repo.UserProfile.uenqueue(u, mes)

                    table.kib_broadcast(m('user.sit', position =  bridge.relation(place, 'S'), name = nick))
                        
                    if table.full() :
                        actions.start_new_deal(table)
                    table.put()    
                    values = dict([(bridge.relation(p, place), p) for p in bridge.SIDES])
                    values['username'] = prof.user.nickname()
                    values['tid'] = tid
                    self.response.out.write(template.render('table.html', values))
                elif current == user :
                    prof.enqueue(current_table_state(user, place, table))
                    values = dict([(bridge.relation(p, place), p) for p in bridge.SIDES])
                    values['username'] = prof.user.nickname()
                    values['tid'] = tid
                    self.response.out.write(template.render('table.html', values))
                else : # user tried to pick someones place
                    self.redirect('hall.html')
            else :
                place = 'S'
                table.kibitzers.append(user)
                table.put()
                prof.enqueue(current_table_state(user, place, table))
                repo.UserProfile.broadcast(m('player.sit', tid = tid))
                values = dict([(bridge.relation(p, place), p) for p in bridge.SIDES])
                values['username'] = prof.user.nickname()
                values['tid'] = tid
                self.response.out.write(template.render('table.html', values))
                    

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
        res.append({'tid': tid, 'N': nick_or_empty(t.N, tid, 'N'), 'E': nick_or_empty(t.E, tid, 'E')
                    , 'S': nick_or_empty(t.S, tid, 'S'), 'W': nick_or_empty(t.W, tid, 'W')
                    , 'kibcount': len(t.kibitzers)})
    return res

class HallHandler(webapp.RequestHandler) :
    @checklogin
    def get(self, prof):
        self.response.out.write(template.render(
                'hall.html', {'tables': show_all_tables(), 'username': prof.user.nickname()}))

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
        prof.put()
        self.response.out.write(json.dumps(token))

def protocol2map(curuser, p) :
    if p.contract == 'pass' :
        return {'N': p.N.nickname(), 'E': p.E.nickname(), 'S': p.S.nickname(), 'W': p.W.nickname(), 
                'contract': p.contract, 'result': 0
                , 'highlight': curuser in [p.N, p.E, p.S, p.W] }
        
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


class CronHandler(webapp.RequestHandler) :
    TIME_LIMIT_SECS = 30 * 60
    def get(self) :
        def logoff(p): 
            p.loggedin = False

        if self.request.headers['X-AppEngine-Cron'] != 'true' :
            self.response.set_status(404)
            return
        args = arguments(self.request)
        cmd = args[0]
        if cmd == 'logoff' :
            old = time.strftime('%F %T', time.gmtime(time.time() - self.TIME_LIMIT_SECS))
            profiles = repo.UserProfile.all().filter('lastact < ', old).fetch(100)
            map(logoff, profiles)
            db.put(profiles)


def main():
    application = webapp.WSGIApplication([('/', Redirector)
                                          , ('/cron.html', CronHandler)
                                          , ('/hall.html', HallHandler)
                                          , ('/table.html', TableHandler)
                                          , ('/protocol.html', ProtocolHandler)
                                          , ('/channel.json', ChannelHandler)
                                          , ('/action.json', ActionHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

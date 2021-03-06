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
import random
import string
import math
import time

from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.api import users, channel
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util, template
from django.utils  import simplejson as json
from django.utils.safestring import SafeString

import bridge
import actions
from utils import *
import repository as repo

IMAGE_TEMPLATE = '<img src="images/%s.png" alt="%s"/>'

def arguments(request) :
    return request.query_string.split('/')

class BaseHandler(webapp.RequestHandler) :
    def get(self) :
        self.process()

    def post(self) :
        self.process()

    def process(self) :
        user = users.get_current_user()
        if user is None :
            self.redirect(users.create_login_url(self.request.uri))
            return

        prof = repo.UserProfile.get_or_create(user)
        prof.loggedin = True
        toput = [prof]
        self.do(prof, toput)
        logging.debug(toput)
        tc = {}
        for v in toput :
            if isinstance(v, list) :
                tc.update([(i.key(), i) for i in v])
            elif v is not None :
                if v.is_saved() :
                    tc[v.key()] = v 
                else :
                    tc[id(v)] = v
        items = list(tc.values())
        if len(items) > 0 :
            db.put(items)

    def do(self, prof, toput) :
        raise NotImplementedError('Implement!')

class Redirector(BaseHandler) :
    def do(self, *args) :
        self.redirect('hall.html')

class ActionHandler(BaseHandler):
    def do(self, prof, toput):
        arglist = arguments(self.request)
        action = arglist[0]
        try :
            f = actions.action_processors[action]
        except KeyError:
            logging.warn('unsupported action %s from %s', action, prof.user)
            self.response.set_status(404)
        else :
            cont = f(prof, toput, *arglist[1:])
            if cont is not None :
                cont(self)

def current_table_state(user, place, table, allow_moves=True) :
    tkey = table.key()
    umap = table.usermap()
    
    messages = [m('player.sit', position = p, name = u.nickname(), tid = str(tkey)) 
                for p, u in umap.iteritems()]
    p = table.protocol
    if p is None :
        if len(umap) == 4 :
            logging.warn('4 users @%s, but deal not dealed', tkey)
            actions.start_new_deal(table, [])
            table.put()
        return messages
    deal = p.deal
    moves = p.moves
    hand = actions.hand_left(deal.hand_by_side(place), moves)
    messages += [m('hand', cards = hand, side = place)
                , m('start.bidding', vuln = deal.vulnerability, dealer = deal.dealer)]
    if len(p.bidding) == 0 :
        return messages
    side = deal.dealer
    place_idx = bridge.SIDES.index(place)
    part_idx = (place_idx + 2) % 4
    def bidmes(bid, side, part_idx) :
        s = bid.split(':', 1)
        b = s[0]
        if len(s) > 1 and side != part_idx:
            alert = s[1]
            return m('bid', side = side, alert = process_chat_message(alert), bid = b)
        else:
            return m('bid', side = side, bid = b)
        
    for bid in p.bidding[:-1] :
        messages.append(bidmes(bid, side, part_idx))
        side = (side + 1) % 4
    last_bid = bidmes(p.bidding[-1], side, part_idx)
    last_bid['value']['dbl_mode'] = actions.get_dbl_mode(p.bidding)
    messages.append(last_bid)
    
    c = p.contract
    if c is None :
        return messages

    decl_side = c[-1]
    dummy_side = p.dummy() 
    messages.append(m('start.play', contract = c.replace('d', 'x').replace('r','xx') 
                      , lead = (bridge.SIDES.index(c[-1]) + 1) % 4))
    move_done = len(moves) > 0
    if place == dummy_side :
        messages.append(m('hand', cards = actions.hand_left(deal.hand_by_side(decl_side), moves)
                          , side = decl_side))
    elif move_done  or  decl_side == place:
        messages.append(m('hand', cards = actions.hand_left(deal.hand_by_side(dummy_side), moves)
                          , side = dummy_side))
    if move_done :
        trump = c[1]
        full_rounds_played = len(moves) / 4
        rounds_total = int(math.ceil(float(len(moves)) / 4))
        decl_tricks, taker = bridge.decl_tricks_and_next_move_offset(moves[:(rounds_total - 2) * 4], trump)
        cards_to_show = moves[(rounds_total - 2) * 4:]
        lasttrick, lasttaker = bridge.decl_tricks_and_next_move_offset(cards_to_show, trump)
        if len(cards_to_show) > 3 :
            if taker % 2 == 1 :
                decl_tricks += 2 - (rounds_total - full_rounds_played) - lasttrick
            else :
                decl_tricks += lasttrick
        defen_tricks = full_rounds_played - decl_tricks
        decl_idx = bridge.SIDES.index(decl_side)
        if decl_idx % 2 == 0 :
            ns_t = decl_tricks
            ew_t = defen_tricks
        else :
            ns_t = defen_tricks
            ew_t = decl_tricks
        messages.append(m('tricks', NS = ns_t, EW = ew_t))
        rel_idx = (decl_idx + 1)
        if len(cards_to_show) > 3 :
            lastrnd = cards_to_show[:4]
            lt_base = taker + rel_idx
            messages += [m('move', card = lastrnd[i], side = bridge.SIDES[(lt_base + i)%4]) for i in xrange(4)]
            move_offs = bridge.decl_tricks_and_next_move_offset(lastrnd, trump)[1] + taker
            currnd = cards_to_show[4:]
        else :
            currnd = cards_to_show
            move_offs = taker
        s = (rel_idx + move_offs) % 4 
        for card in currnd :
            messages.append(m('move', card = card, side = bridge.SIDES[s]))
            s = (s + 1) % 4

        s = bridge.SIDES[(rel_idx + taker + lasttaker) % 4]
        if s == dummy_side and place == decl_side :
            messages[-1]['value']['next'] = dummy_side
            hand = actions.hand_left(deal.hand_by_side(dummy_side), moves)
            s = decl_side
        else :
            messages[-1]['value']['next'] = s

        if allow_moves and s == place: 
            if rounds_total != full_rounds_played and bridge.has_same_suit(hand, currnd[0]):
                messages[-1]['value']['allowed'] = currnd[0] / 13 
            else :
                messages[-1]['value']['allowed'] = 'any'
    if table.claim is None :
        return messages

    tricks_s = table.claim[:2]
    tricks = int(table.claim[:2])
    claim_side = table.claim[2]
    if tricks > 0 :
        claim_res = bridge.tricks_to_result(c, deal.vulnerability, tricks)
        messages.append(m('claim', side=claim_side, tricks=tricks_s, result=claim_res))
    if bridge.relation_idx(claim_side, place) % 2 == 1 : #opponent claim
        part_side = bridge.SIDES[part_idx]
        messages.append(m('hand', cards=actions.hand_left(deal.hand_by_side(claim_side), moves), side=claim_side))
        messages.append(m('hand', cards=actions.hand_left(deal.hand_by_side(part_side), moves), side=part_side))
        messages.append(m('hand', cards=actions.hand_left(deal.hand_by_side(dummy_side), moves), side=dummy_side))
    return messages
                      
def htmltable(user, place, tkey) :
    values = dict([(bridge.relation(p, place), p) for p in bridge.SIDES])
    values['username'] = user.nickname()
    values['tid'] = str(tkey)
    if place in ['N', 'S'] :
        values['we'] = 'NS'
        values['they'] = 'EW'
    else :
        values['we'] = 'EW'
        values['they'] = 'NS'
        
    return template.render('table.html', values)


class TableHandler(BaseHandler) :

    def do(self, prof, toput):
        args = arguments(self.request)
        user = prof.user  
        if args[0] == 'new' :
            t = repo.Table()
            t.N = user
            key = t.put()
            repo.UserProfile.broadcast(m('table.add', tid=str(key)))
            self.redirect('table.html?%s/N' % key)
        elif args[0].startswith('newtest') :
            t = repo.Table(key_name = args[0][3:])
            t.N = user
            key = t.put()
            self.redirect('table.html?%s/N' % key)
        else :
            prof.connected = False
            toput.append(prof)
            key = args[0]
            table = repo.Table.get(key)
            if table is None :
                logging.info('get %s failed', key)
                self.redirect('hall.html')
                return
            if len(args) > 1 :
                place = args[1]
                current = table.user_by_side(place)
                if current is None :
                    nick = user.nickname()
                    mes = m('player.sit', tid = str(key), position = place, name = nick)
                    toput.append(repo.UserProfile.broadcast(mes, user))
                    prof.enqueue(current_table_state(user, place, table))
                    prof.enqueue(mes)
                    toput.append(table.sit(place, user))
                    if table.pcount() == 3 and table.protocol is None :
                        umap = table.usermap()
                        umap[place] = user
                        prof.put()
                        actions.start_new_deal(table, toput, umap, False)
                    toput.append(table)   
                    self.response.out.write(htmltable(user, place, key))
                elif current == user :
                    prof.enqueue(current_table_state(user, place, table))
                    toput.append(prof)
                    self.response.out.write(htmltable(user, place, key))
                else : # user tried to pick someones place
                    self.redirect('hall.html')
            else :
                place = 'S'
                toput.append(repo.TablePlace(table=table, user=user))
                prof.enqueue(current_table_state(user, place, table, False))
                repo.UserProfile.broadcast(m('player.sit', tid = str(key)))
                self.response.out.write(htmltable(user, place, key))

                    

def nick_or_empty(umap, key, side, cur_user):
    if umap.has_key(side) :
        user = umap[side]
        if user == cur_user:
            return SafeString("<a href=\"table.html?%s/%s\">%s</a>" % (key, side, user.nickname()))
        else :
            return user.nickname()
    else :
        return SafeString("<a href=\"table.html?%s/%s\">take a sit</a>" % (key, side))

def show_all_tables(cur_user) :
    res = []
    # obvious cache candidate
    for t in repo.Table.all():
        key = t.key()
        if key.name() is None : # named keys are for test tables only
            umap = t.usermap()
            res.append({'tid': key
                        , 'N': nick_or_empty(umap, key, 'N', cur_user)
                        , 'E': nick_or_empty(umap, key, 'E', cur_user)
                        , 'S': nick_or_empty(umap, key, 'S', cur_user)
                        , 'W': nick_or_empty(umap, key, 'W', cur_user)
                        , 'kibcount': repo.TablePlace.kibitzer_q(t).count()})
    return res

class HallHandler(BaseHandler) :

    def do(self, prof, toput):
        prof.connected = False
        toput.append(prof)
        self.response.out.write(template.render(
                'hall.html', {'tables': show_all_tables(prof.user), 'username': prof.user.nickname()}))

class ChannelHandler(BaseHandler) :
    
    def do(self, prof, toput):
        if prof.chanid is None :
            chanid = prof.user.nickname()
            prof.chanid = chanid
        else : 
            chanid = prof.chanid
        prof.connected = False
        toput.append(prof)
        token = channel.create_channel(chanid)
        self.response.out.write(json.dumps(token))

def protocol2map(curuser, p) :
    if p.contract == 'pass' :
        return {'N': p.N.nickname(), 'E': p.E.nickname(), 'S': p.S.nickname(), 'W': p.W.nickname(), 
                'contract': p.contract, 'result': 0
                , 'highlight': curuser in [p.N, p.E, p.S, p.W] }
    if p.moves is not None and len(p.moves) > 0 :
        lead = bridge.num_to_suit_rank(p.moves[0])
        lead_s = lead[0][0]
        lead =  SafeString(IMAGE_TEMPLATE % (lead_s, lead_s.upper()) + lead[1])
    else :
        lead = None
    if p.contract is not None and len(p.contract) > 0 :
        cntrct = p.contract[:-1].replace('d', 'x').replace('r','xx')
        cntrct_s = cntrct[1]
        if cntrct_s == 'Z' :
            cntrct = SafeString(cntrct[0] + 'NT' + cntrct[2:])
        else :
            cntrct = SafeString(cntrct[0] + IMAGE_TEMPLATE % (cntrct_s.lower(), cntrct_s) + cntrct[2:])
        decl = p.contract[-1]
    else :
        cntrct = None
        decl = None

    return {'N': p.N.nickname(), 'E': p.E.nickname(), 'S': p.S.nickname(), 'W': p.W.nickname(), 
            'contract': cntrct, 'decl': decl
            , 'lead': lead, 'tricks': '=' if p.tricks == 0 else p.tricks, 'result': p.result
            , 'highlight': curuser in [p.N, p.E, p.S, p.W] }

class ProtocolHandler(BaseHandler) :
    
    def do(self, prof, toput):
        page = 'protocol.html'
        key = self.request.query_string
        deal = repo.Deal.get(key)
        hands = map(bridge.split_by_suits, [deal.N, deal.E, deal.S, deal.W])
        h_val = dict(zip(bridge.SIDES
                         , [dict(zip(['clubs',  'diamonds', 'hearts', 'spades'], h)) for h in hands]))

        protoiter = repo.Protocol.get_by_deal(deal)
        
        values = {'protocol_id': key, 'vuln_EW': deal.vulnerability & bridge.VULN_EW
                  , 'vuln_NS': deal.vulnerability & bridge.VULN_NS, 'dealer': bridge.SIDES[deal.dealer]
                  , 'records': map(lambda x: protocol2map(prof.user, x), protoiter)}
        values.update(h_val)
        self.response.out.write(template.render(page, values))


class ProfileHandler(BaseHandler) :

    def do(self, prof, toput):
        args = arguments(self.request)
        page = 'userprofile.html'
        if self.request.method == 'GET' :
            p = repo.UserProfile.get(args[0])
            if p is None :
                self.redirect('hall.html')
            else :
                self.response.out.write(template.render(page, {'p': p
                                                               , 'ro': args[0] != prof.user.nickname()
                                                               , 'username': args[0]}))
        elif self.request.method == 'POST' :
            if prof.user.nickname() != args[0] :
                logging.warn('user %s tried to change other users data', prof.user.nickname())
                self.redirect('hall.html')
                return
            toput.append(prof)
            prof.nickname = self.request.get('name')
            prof.bridgeinfo = self.request.get('bridgepref')
            prof.autosingleton = self.request.get('1ton_autoplay') == 'on'
            prof.skypeid = self.request.get('skypeid')
            prof.facebookid = self.request.get('facebookid')
            prof.twitterid = self.request.get('twitterid')
            self.response.out.write(template.render(page, {'p': prof, 'ro': False, 'username': args[0]}))
            


class CronHandler(webapp.RequestHandler) :
    TIME_LIMIT_SECS = 300
    def get(self) :
        args = arguments(self.request)
        cmd = args[0]
        if cmd == 'logoff' :
            old = time.strftime('%F %T', time.gmtime(time.time() - self.TIME_LIMIT_SECS))
            logging.info("logging out users older then %s", old)
            profiles = repo.UserProfile.gql('WHERE lastact < DATETIME(:1) AND loggedin = True', old).fetch(100)
            mes_recepients = []
            [p.logoff(mes_recepients) for p in  profiles]
            logging.info("Logged off %s users", len(profiles))
            models = profiles + reduce(list.__add__, mes_recepients, [])
            if len(models) > 0 :
                db.put(models)


def main():
    application = webapp.WSGIApplication([('/', Redirector)
                                          , ('/cron.html', CronHandler)
                                          , ('/hall.html', HallHandler)
                                          , ('/table.html', TableHandler)
                                          , ('/protocol.html', ProtocolHandler)
                                          , ('/userprofile.html', ProfileHandler)
                                          , ('/channel.json', ChannelHandler)
                                          , ('/action.json', ActionHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

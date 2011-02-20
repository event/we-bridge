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
from urllib import unquote

from google.appengine.api import users
from google.appengine.ext import db
from django.utils  import simplejson as json

import bridge
import repository as repo
from utils import *

def hand_left(hand, moves) :
    s = set(hand)
    s.difference_update(moves)
    return list(s)

def trick_side(taker, other) :
    taker_i = bridge.SIDES.index(taker)
    other_i = bridge.SIDES.index(other)
    return '+' if taker_i % 2 == other_i % 2 else '-'

def next_player_and_allowed_suit(round_end, moves, contract, side, deal) :
    if round_end :
        last_round = moves[-4:]
        taker = bridge.get_next_move_offset(last_round, contract[1])
        next = bridge.SIDES[(bridge.SIDES.index(side) + 1 + taker) % 4]
        allowed = 'any' 
    else : 
        fst_card_in_round = moves[-(len(moves) % 4)]
        next = bridge.SIDES[(bridge.SIDES.index(side) + 1) % 4]
        next_hand = hand_left(deal.hand_by_side(next), moves)
        if bridge.has_same_suit(next_hand, fst_card_in_round)  :
            allowed = fst_card_in_round / 13
        else : 
            allowed = 'any' 
    return next, allowed

def move_allowed(protocol, own_side, player_side, card, hand) :
    contract = protocol.contract
    if contract  is None :
        return False
    decl = contract[-1]
    valid_card = bridge.valid_card(hand, card, protocol.moves)
    res = (player_side == own_side 
           or (decl == own_side and player_side == bridge.partner_side(own_side))) and valid_card 
    return res

def do_move(prof, toput, tid, side, scard) :
    user = prof.user
    table = repo.Table.get_by_id(int(tid))
    protocol = table.protocol
    deal = protocol.deal
    card = int(scard)
    hand = deal.hand_by_side(side)
    if side is None or not move_allowed(protocol, table.side(user), side, card, hand) \
            or side != table.whosmove :
        logging.warn('bad move: %s %s %s %s %s %s %s %s', protocol.key(), card
                     , protocol.contract, user, player, table.key(), table.whosmove, side)
        return
    result = []
    # some kind of locking have to be implemented here. While actions in bridge game 
    #    are strictly sequential it is generally an error 
    #    to have any action started until previous is finished
    protocol.moves.append(card)
    dummy = protocol.dummy()
    rndend = protocol.round_ended()
    next, allowed = next_player_and_allowed_suit(rndend, protocol.moves, protocol.contract, side, deal)
    if len(protocol.moves) == 1 :
        dummy_hand = protocol.deal.hand_by_side(dummy)
        umap = table.usermap()
        del umap[dummy]
        del umap[protocol.contract[-1]]
        mes = m('hand', cards = dummy_hand, side = dummy)
        for u in umap.itervalues() :
            toput.append(repo.UserProfile.uenqueue(u, mes))

    umap = table.usermap()
    table.whosmove = next
    real_move = next
    if next == dummy :
        next = protocol.contract[-1]
    next_user = umap.pop(next)
    if rndend :
        if next in ['N', 'S'] :
            t = 'NS' 
        else :
            t = 'EW' 
    else :
        t = None
    mes = m('move', card = card, next = real_move, side = side, trick = t) 
    mover_mes = m('move', card = card, next = real_move, side = side, trick = t, allowed = allowed)
    toput.append(table.broadcast(mes))
    toput.append(repo.UserProfile.uenqueue(repo.TablePlace.get1(table=table, side=next).user, mover_mes))
    if protocol.finished() :
        cntrct = protocol.contract[:-1]
        protocol.result, protocol.tricks = bridge.deal_result(cntrct \
                                                             , protocol.deal.vulnerability, protocol.moves)
        toput.append(table.broadcast(m('end.play', contract = cntrct.replace('d', 'x').replace('r','xx')\
                                           , declearer = protocol.contract[-1]\
                                           , points = protocol.result\
                                           , tricks = protocol.tricks\
                                           , protocol_url = 'protocol.html?%s' % deal.key().id())))
    
        start_new_deal(table)
    toput.append(table)
    toput.append(protocol)

def create_new_deck(table) :
    p = table.protocol
    if p is not None :
        d = p.deal
        cvuln = d.vulnerability
        cdealer = d.dealer
        vinc = 1
        if cdealer == 3 :
            vinc += 1
        dealer = (cdealer + 1) % 4 
        vuln = (cvuln + vinc) % 4
    else :
        dealer = 0
        vuln = 0
    deck = bridge.get_deck()
    deal = repo.Deal.create(deck, vuln, dealer) 
    table.protocol = repo.Protocol.create(deal, N=table.N, E=table.E, S=table.S, W=table.W)
    table.whosmove = bridge.SIDES[dealer]
    return [m('hand', cards = c, side = s) for s, c in deck], vuln, dealer

def start_new_deal(table) :
    messages, vuln, dealer = create_new_deck(table)
    pairs = zip([table.N, table.E, table.S, table.W], messages)
    bid_starter = m('start.bidding', vuln = vuln, dealer = dealer)
    for p in pairs :
        repo.UserProfile.uenqueue(p[0], [p[1], bid_starter])

def bid_allowed(bidding, bid, contract) :
    if contract is not None :
        return False

    bid_cnt = len(bidding)
    if bid == bridge.BID_PASS :
        res = True
    elif bid == bridge.BID_DOUBLE :
        res = bid_cnt > 0 and bridge.is_value_bid(bidding[-1]) \
            or bid_cnt > 2 and bridge.is_value_bid(bidding[-3]) \
            and bidding[-2] == bidding[-1] == bridge.BID_PASS
    elif bid == bridge.BID_REDOUBLE :
        res = bid_cnt > 0 and bidding[-1] == bridge.BID_DOUBLE \
            or bid_cnt > 2 and bidding[-3] == bridge.BID_DOUBLE \
            and bidding[-2] == bidding[-1] == bridge.BID_PASS
    else :
        i = 1;
        while i <= bid_cnt and not bridge.is_value_bid(bidding[-i]) :
            i += 1
        res = i > bid_cnt or bidding[-i] < bid
    return res

def get_dbl_mode(bidding) :
    def last_value_bid_is(check_fun, bidding) :
        return check_fun(bidding[-1]) \
            or (len(bidding) > 2 and check_fun(bidding[-3]) and bidding[-2] == bidding[-1] == bridge.BID_PASS)
    if last_value_bid_is(lambda x: x.startswith(bridge.BID_DOUBLE), bidding):
        dbl_mode = 'rdbl'
    elif last_value_bid_is(bridge.is_value_bid, bidding) : 
        dbl_mode = 'dbl'
    else : 
        dbl_mode = 'none'
    return dbl_mode


def do_bid(prof, toput, tid, player, bid, alert=None) :
    user = prof.user
    table = repo.Table.get_by_id(int(tid))
    protocol = table.protocol
    cur_side = table.side_idx(user)
    if cur_side is None or not bid_allowed(map(bridge.remove_alert, protocol.bidding), 
                                           bridge.remove_alert(bid), protocol.contract) \
                                           or bridge.SIDES[cur_side] != table.whosmove :
        logging.warn('bad bid: %s %s %s %s %s %s %s %s', protocol.key(), bid
                     , protocol.contract, user, player, table.key(), table.whosmove, cur_side)
        return 
    if alert is not None :
        fullbid = bid + ':' + alert
    else :
        fullbid = bid
    protocol.bidding.append(fullbid)
    bid_cnt = len(protocol.bidding)
    if bid_cnt > 3 and all([b.startswith(bridge.BID_PASS) for b in protocol.bidding[-3:]]) :
        contract, rel_declearer = bridge.get_contract_and_declearer(protocol.bidding)
        deal = protocol.deal
        if contract == bridge.BID_PASS :
            protocol.contract = contract
            protocol.result = 0
            protocol.tricks = 0
            protocol.put()
            toput.append(table.broadcast([m('bid', side = cur_side, bid = bid, dbl_mode = 'none')
                                          , m('end.play', contract = contract
                                              , declearer = 'N/A'
                                              , points = protocol.result
                                              , tricks = protocol.tricks
                                              , protocol_url = 'protocol.html?%s' % deal.key().id())]))
            start_new_deal(table)
            toput.append(table)
            return

        declearer = (rel_declearer + protocol.deal.dealer) % 4
        leadmaker = (declearer + 1) % 4
        contract = contract + bridge.SIDES[declearer]
        protocol.contract = contract
        table.whosmove = bridge.SIDES[leadmaker]
        db.put([protocol, table])
        logging.info('contract %s by %s', contract, bridge.SIDES[declearer])
        start = m('start.play', contract = contract.replace('d', 'x').replace('r','xx') 
                             , lead = leadmaker)

        if alert is None :
            toput.append(table.broadcast([m('bid', side = cur_side, bid = bid, dbl_mode = 'none'), start]))
        else :
            toput.append(table.broadcast([m('bid', side = cur_side, bid = bid, alert = process_chat_message(alert)
                               , dbl_mode = 'none'), start]))
            toput.append(repo.UserProfile.uenqueue(
                repo.TablePlace.get1(table=table, side=bridge.SIDES[(cur_side + 2) % 4]).user
                , [m('bid', side = cur_side, bid = bid, dbl_mode = 'none'), start]))
        dummy = (declearer + 2) % 4
        dummy_side = bridge.SIDES[dummy]
        decl_side = bridge.SIDES[declearer]
        dummy_hand = deal.hand_by_side(dummy_side)
        mes = m('hand', cards = dummy_hand, side = dummy_side)
        toput.append(repo.UserProfile.uenqueue(table.user_by_side(decl_side), mes))
        mes = m('hand', cards = deal.hand_by_side(decl_side), side = decl_side)
        toput.append(repo.UserProfile.uenqueue(table.user_by_side(dummy_side), mes))
        return
    table.nextmove()
    toput.append(protocol)
    toput.append(table)
    dbl_mode = get_dbl_mode(protocol.bidding)
    if alert is None :
        toput.append(table.broadcast(m('bid', side = cur_side, bid = bid, dbl_mode = dbl_mode)))
    else :
        toput.append(table.broadcast(m('bid', side = cur_side, bid = bid, alert = process_chat_message(alert)
                          , dbl_mode = dbl_mode)))
        toput.append(repo.UserProfile.uenqueue(
                repo.TablePlace.get1(table=table, side=bridge.SIDES[(cur_side + 2) % 4]).user
                , m('bid', side = cur_side, bid = bid, dbl_mode = dbl_mode)))

        

def leave_table(prof, toput, tid) :
    tp = repo.TablePlace.get1(user=user, table='KIND(\'Table\', ' + tid + ')')
    toput.append(repo.UserProfile.broadcast(m('player.leave', tid = tid, position = tp.side)))
    return lambda x: x.redirect('hall.html')

def logoff(prof, toput) :
    prof.logoff(toput)
    return lambda x: x.redirect(users.create_logout_url(users.create_login_url('hall.html')))

def chat_message(prof, toput, target, *args) :
    text = process_chat_message('/'.join(args))
    if target == 'global' :
        toput.append(repo.UserProfile.broadcast(
            m('chat.message', wid = 'global', sender = prof.user.nickname(), message = text)
            , prof.user))
        if prof.enqueue(m('chat.message', wid = 'global', sender = 'own', message = text)) :
            toput.append(prof)
    elif target == 'users' : 
        uname = unquote(text) # check for ascii
        if uname.find('@') < 0 :
            uname += '@gmail.com'
        u = repo.UserProfile.gql('WHERE user = USER(:1)', uname).get()
        if u is None :
            put = prof.enqueue(m('chat.message', wid = 'global', sender = 'sys'
                              , message = 'user %s doesn\'t exist' % uname)) 
        elif not u.loggedin :
            put = prof.enqueue(m('chat.message', wid = 'global', sender = 'sys'
                              , message = 'user %s offline' % uname)) 
        else :
            put = prof.enqueue(m('chat.add', wid = uname, title = uname[:uname.find('@')]))
        if put :
            toput.append(prof)
    elif target.startswith('table') and target.find('@') < 0 :
        tid = int(target[target.find('_') + 1:])
        # table isn't too much needed here...
        t = repo.Table.get_by_id(tid)
        ulist = t.userlist()
        if prof.enqueue(m('chat.message', wid = target, sender = 'own', message = text)) :
            toput.append(prof)
        ulist.remove(prof.user)
        mes = m('chat.message', wid = target, sender = prof.user.nickname(), message = text)
        toput.append([repo.UserProfile.uenqueue(u, mes) for u in ulist])
        toput.append(t.kib_broadcast(mes))
    else :
        u = repo.UserProfile.gql('WHERE user = USER(:1)', target).get()
        if u is None :
            put = prof.enqueue(m('chat.message', wid = 'global', sender = 'sys'
                           , message = 'user %s doesn\'t exist' % target))
        elif not u.loggedin :
            put = prof.enqueue(m('chat.message', wid = 'global', sender = 'sys'
                           , message = 'user %s offline' % target))
        else :
            sender = prof.user.nickname()
            if sender.find('@') < 0 :
                wid = sender + '@gmail.com'
            else :
                wid = sender
            put = prof.enqueue(m('chat.message', wid = target, message = text, sender = 'own'))
            if u.enqueue(m('chat.message', wid = wid, message = text)) :
                toput.append(u)
        if put :
            toput.append(prof)
        
    
            

def ping(prof, toput):
    if not prof.connected :
        prof.send_stored_messages()
        toput.append(prof)

def usernames(prof, toput, query):
    # MAYBE list of online users should be maintained in memcache
    profiles = repo.UserProfile.gql(
        'WHERE loggedin = True AND user >= USER(:1) AND user <= USER(:2)', query, query + 'z') \
        .fetch(10)
        
    return lambda x: x.response.out.write(json.dumps([p.user.nickname() for p in profiles]))

action_processors = {'move': do_move, 'bid': do_bid, 'leave': leave_table
                     , 'logoff': logoff, 'chat': chat_message, 'ping': ping, 'usernames': usernames}


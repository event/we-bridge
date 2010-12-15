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

import bridge
import repository as repo

def checkturn(f) :
    '''Checks whenever user is allowed to act for corresponding side.
    In most cases user is allowed to act for 'own' only. Also check whether it is user's turn'''
    return f

def trick_side(taker, other) :
    taker_i = bridge.SIDES.index(taker)
    other_i = bridge.SIDES.index(other)
    return '+' if taker_i % 2 == other_i % 2 else '-'

@checkturn
def do_lead(prof, tid, player, scard) :
    user = prof.user
    table = repo.Table.get_by_id(int(tid))
    protocol = table.protocol
    deal = protocol.deal
    side = table.side(user)
    hand = deal.hand_by_side(side)
    card = int(scard)
    correct_move = bridge.check_move(hand, card, protocol.moves)
    result = []
    if correct_move :
        # some kind of locking have to be implemented here. While actions in bridge game 
        #    are strictly sequential it is generally an error 
        #    to have any action started until previous is finished
        protocol.add_move(card)
        rndend = protocol.round_ended()
        if rndend :
            last_round = protocol.moves[-4:]
            taker = bridge.get_trick_taker_offset(last_round, protocol.contract[1])
            next = bridge.SIDES[(bridge.SIDES.index(side) + 1 + taker) % 4]
            allowed = 'any' 
        else : 
            fst_card_in_round = protocol.moves[-(len(protocol.moves) % 4)]
            next = bridge.SIDES[(bridge.SIDES.index(side) + 1) % 4]
            next_hand = set(deal.hand_by_side(next))
            next_hand.difference_update(protocol.moves)
            if bridge.has_same_suit(list(next_hand), fst_card_in_round)  :
                allowed = fst_card_in_round / 13
            else : 
                allowed = 'any' 
        umap = table.usermap()
        next_user = umap.pop(next)
        mes = {'card': card}
        for p, u in umap.iteritems() :
            mes['player'] = bridge.relation(side, p)
            mes['trick'] = trick_side(next, p) if rndend else None
            repo.UserProfile.uenqueue(u, {'type': 'move', 'value': mes})
        mes['player'] = bridge.relation(side, next)
        mes['allowed'] = allowed
        mes['trick'] = '+' if rndend else None
        repo.UserProfile.uenqueue(next_user, {'type': 'move', 'value': mes})

        if protocol.finished() :
            cntrct = protocol.contract[:-1]
            protocol.result, protocol.tricks = bridge.deal_result(cntrct \
                                                             , protocol.deal.vulnerability, protocol.moves)
            table.broadcast({'type': 'end.play', 'value': 
                             {'contract': cntrct.replace('d', 'x').replace('r','xx')\
                                  , 'declearer': protocol.contract[-1]\
                                  , 'points': protocol.result\
                                  , 'tricks': protocol.tricks\
                                  , 'protocol_url': 'protocol.html?%s' % deal.key().id()}})
    
            start_new_deal(table)

        protocol.put()

def to_dict(hand) :
    return {'type': 'hand', 'value': {'cards': hand}}

def create_new_deck(table) :
    deck, vuln, dealer = bridge.get_deck()
    deal = repo.Deal.create(deck, vuln, dealer) 
    table.protocol = repo.Protocol.create(deal, N=table.N, E=table.E, S=table.S, W=table.W)
    return add_own(map(to_dict, deck)), vuln, dealer

def start_new_deal(table) :
    messages, vuln, dealer = create_new_deck(table)
    pairs = zip([table.N, table.E, table.S, table.W], messages)
    bid_starter = {'type': 'start.bidding', 'value' : {'vuln': vuln, 'dealer': dealer}}
    for p in pairs :
        repo.UserProfile.uenqueue(p[0], [p[1], bid_starter])

def add_own(hand_list) :
    for h in hand_list :
        h['value']['player'] = 'own'
    return hand_list

@checkturn
def do_bid(prof, tid, player, bid) :
    user = prof.user
    table = repo.Table.get_by_id(int(tid))
    protocol = table.protocol
    if protocol.contract is not None :
        logging.warn("Bid after end: %s by %s as %s @#%s", bid, user, player, tid)
        return []

    old_cnt = len(protocol.bidding)
    if not protocol.add_bid(bid) :
        logging.warn("Bid is lower then allowed: %s by %s as %s @#%s", bid, user, player, tid)
        return []

    bid_cnt = len(protocol.bidding)
    cur_side = (old_cnt + protocol.deal.dealer) % 4
    if bid_cnt > 3 and all([b == bridge.BID_PASS for b in protocol.bidding[-3:]]) :
        contract, rel_declearer = bridge.get_contract_and_declearer(protocol.bidding)
        declearer = (rel_declearer + protocol.deal.dealer) % 4
        protocol.contract = contract + bridge.SIDES[declearer]
        protocol.put()
        logging.info('contract %s by %s', contract, bridge.SIDES[declearer])
        table.broadcast([{'type': 'bid', 'value': {'side': cur_side, 'bid': bid, 'dbl_mode':'none'}}\
                , {'type': 'start.play', 'value'
                   : {'contract': contract.replace('d', 'x').replace('r','xx') 
                      , 'lead': (declearer + 1) % 4}}])
        return
    protocol.put()

    if bid == bridge.BID_DOUBLE or bid_cnt > 2 and protocol.bidding[-3] == bridge.BID_DOUBLE \
            and protocol.bidding[-2] == bid == bridge.BID_PASS :
        dbl_mode = 'rdbl'
    elif bridge.is_value_bid(bid) or bid_cnt > 2 and bridge.is_value_bid(protocol.bidding[-3]) \
            and protocol.bidding[-2] == bid == bridge.BID_PASS: 
        dbl_mode = 'dbl'
    else : 
        dbl_mode = 'none'

    table.broadcast({'type': 'bid', 'value': {'side': cur_side, 'bid': bid, 'dbl_mode':dbl_mode}})


action_processors = {'move': do_lead, 'bid': do_bid}


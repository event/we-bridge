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

player_names = ['part', 'right', 'own', 'left']
sides2names = {'own' : 'S', 'left' : 'W', 'part' : 'N', 'right' : 'E'}

deal_id = None
dealplay_id = None

def do_lead(user, player, suit, rank) :
    protocol = repo.Protocol.get_by_id(dealplay_id)
    deal = protocol.deal
    side = sides2names[player]
    hand = deal.hand_by_side(side)
    card = bridge.suit_rank_to_num(suit, rank)
    correct_move = bridge.check_move(hand, card, protocol.moves)
    result = []
    if correct_move :
        protocol.add_move(card)
        protocol.put()
        mes = {'player': player, 'suit': suit, 'rank': rank}
        if protocol.round_ended() :
            last_round = protocol.moves[-4:]
            taker = bridge.get_trick_taker_offset(last_round, protocol.contract[1])
            next = player_names[(player_names.index(player) + 1 +  taker) % 4]
            mes['next'] = next
            mes['allowed'] = 'any' 
        else : 
            fst_card_in_round = protocol.moves[-(len(protocol.moves) % 4)]
            logger.info('first card ' + fst_card_in_round)
            next_hand = set(deal.hand_by_side(sides2names[player_names[(player_names.index(player) + 1) % 4]]))
            next_hand.difference_update(protocol.moves)
            if bridge.has_same_suit(list(next_hand), card)  :
                mes['allowed'] = suit
            else : 
                mes['allowed'] = 'any' 
        logging.info('sending %s', mes)
        result.append({'type': 'move', 'value': mes})
        if protocol.finished() :
            result += create_new_deck(user)
    return result

def to_dict(hand) :
    c, d, h, s = bridge.split_by_suits(hand)
    return {'type': 'hand', 'value':{'suits':[{'suit': 'clubs', 'cards': c}
                                              , {'suit': 'diamonds', 'cards': d}
                                              , {'suit': 'hearts', 'cards': h}
                                              , {'suit': 'spades', 'cards': s}]}}

def create_new_deck(user) :
    global deal_id
    global dealplay_id
    deck, vuln, dealer = bridge.get_deck()
    deal = repo.Deal.create(deck, vuln, dealer) 
    deal_id = deal.key().id()
    dealplay_id = repo.Protocol.create(deal, user, user, user, user)
    return add_players(map(to_dict, deck))

def add_players(hand_list) :
    for i in xrange(4) :
        hand_list[i]['value']['player'] = player_names[i]
    return hand_list

def do_bid(user, player, bid) :
    if not is_allowed_user_player(user, player) :
        return []
    
    protocol = repo.Protocol.get_by_id(dealplay_id)
    if not protocol.add_bid(bid) :
        return []

    bid_cnt = len(protocol.bidding)
    if bid_cnt > 3 and reduce(lambda x, y: x and y == bridge.BID_PASS \
                                  , protocol.bidding[-3:], True) :
        contract, lead_maker = bridge.get_contract_and_lead_maker(protocol.bidding)
        protocol.contract = contract
        protocol.put()
        logging.info('contract ' + contract)
        return [{'type': 'start.play', 'value'
                 : {'contract': contract 
                    , 'lead': lead_maker + bridge.DEALERS.index(protocol.deal.dealer)}}]
    protocol.put()
    cur_side = (bid_cnt + bridge.DEALERS.index(protocol.deal.dealer)) % 4

    if bid == bridge.BID_DOUBLE or bid_cnt > 2 and protocol.bidding[-3] == bridge.BID_DOUBLE \
            and protocol.bidding[-2] == bid == bridge.BID_PASS :
        dbl_mode = 'rdbl'
    elif bridge.is_value_bid(bid) or bid_cnt > 2 and bridge.is_value_bid(protocol.bidding[-3]) \
            and protocol.bidding[-2] == bid == bridge.BID_PASS: 
        dbl_mode = 'dbl'
    else : 
        dbl_mode = 'none'

    return [{'type': 'bid', 'value': {'side': cur_side, 'bid': bid, 'dbl_mode':dbl_mode}}]


def is_allowed_user_player(user, player) :
    '''Checks whenever user is allowed to bid for corresponding side.
    In most cases user is allowed to bid for 'own' only. Also check whether it is user's turn'''
    return True

action_processors = {'move': do_lead, 'bid': do_bid}


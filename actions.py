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

player_names = ['own', 'left', 'part', 'right']
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
        if protocol.round_ended() :
            next_allowed = 'any' 
        else : 
            next_hand = deal.hand_by_side(sides2names[player_names[(player_names.index(player) + 1) % 4]])
            if bridge.has_same_suit(next_hand, card)  :
                next_allowed = suit
            else : 
                next_allowed = 'any'
        result.append({'type': 'lead', 'value': 
                      {'player': player, 'suit': suit, 'rank': rank, 'allowed': next_allowed}})
        if protocol.finished() :
            result += create_new_deck(user)
    return result

def to_dict(hand) :
    s, h, d, c = bridge.split_by_suits(hand)
    return {'type': 'hand', 'value':{'suits':[{'suit': 'spades', 'cards': s}
                                              , {'suit': 'hearts', 'cards': h}
                                              , {'suit': 'diamonds', 'cards': d}
                                              , {'suit': 'clubs', 'cards': c}]}}

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

action_processors = {'lead': do_lead}


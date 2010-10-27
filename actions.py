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

player_names = ['own', 'left', 'part', 'right']


current_deck = None
lead_history = None

def do_lead(user, player, suit, rank) :
    current_hand = player_names.index(player)
    hand = current_deck[current_hand]
    last_round = lead_history[-1]
    if len(last_round) == 4 :
        current_round = []
        lead_history.append(current_round)
    else :
        current_round = last_round
    card = bridge.suit_rank_to_num(suit, rank)
    correct_lead = bridge.check_lead(hand, card, current_round)
    result = []
    if correct_lead :
        hand.remove(card)
        current_round.append(card)
        if len(current_round) == 4 :
            next_allowed = 'any' 
        else : 
            next_hand = current_deck[(current_hand + 1) % 4]
            if bridge.has_same_suit(next_hand, card)  :
                next_allowed = suit
            else : 
                next_allowed = 'any'
        result.append({'type': 'lead', 'value': 
                      {'player': player, 'suit': suit, 'rank': rank, 'allowed': next_allowed}})
        if bridge.is_deck_empty(current_deck) :
            result += create_new_deck()
    return result

def to_dict(hand) :
    s, h, d, c = bridge.split_by_suits(hand)
    return {'type': 'hand', 'value':{'suits':[{'suit': 'spades', 'cards': s}
                                              , {'suit': 'hearts', 'cards': h}
                                              , {'suit': 'diamonds', 'cards': d}
                                              , {'suit': 'clubs', 'cards': c}]}}

def create_new_deck() :
    global current_deck
    global lead_history
    deck = bridge.get_deck()
    current_deck = deck
    lead_history = [[]]
    return add_players(map(to_dict, deck))

def add_players(hand_list) :
    for i in xrange(4) :
        hand_list[i]['value']['player'] = player_names[i]
    return hand_list

action_processors = {'lead': do_lead}


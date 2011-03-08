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
import random as rand

VULN_NONE = 0
VULN_NS = 1
VULN_EW = 2
VULN_BOTH = 3
VULN_OPTIONS = [VULN_NONE, VULN_NS, VULN_EW, VULN_BOTH]

DEALER_N = 0
DEALER_E = 1
DEALER_S = 2
DEALER_W = 3

DEALERS = [DEALER_N, DEALER_E, DEALER_S, DEALER_W]
SIDES = ['N', 'E', 'S', 'W']

REL_SIDES = ['own', 'left', 'part', 'right']

# bids are strings like '1C', '1D', '1H', '1S', '1Z'..'7S', '7Z'. 
# 'Z' is chosen for NT to have bids comparable as strings
BID_PASS = 'pass'
BID_DOUBLE = 'dbl'
BID_REDOUBLE = 'rdbl'
SPECIAL_BIDS = [BID_PASS, BID_DOUBLE, BID_REDOUBLE]

# cards are represented with number from 0 (2 of clubs) to 51 (ace of spades)
STRAIN_CLUB = 0
STRAIN_DIAMOND = 1
STRAIN_HEART = 2
STRAIN_SPADE = 3
STRAIN_NT = 4
S2STRAIN = {'C': STRAIN_CLUB, 'D': STRAIN_DIAMOND, 'H': STRAIN_HEART, 'S': STRAIN_SPADE, 'Z': STRAIN_NT}

CARDS_IN_SUIT = 13
CARDS_IN_HAND = 13

SUITS = ['clubs', 'diamonds', 'hearts', 'spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def relation(place, base) :
    return REL_SIDES[relation_idx(place, base)]

def relation_idx(place, base) :
    return SIDES.index(place) - SIDES.index(base)

def partner_side(side) :
    return SIDES[(SIDES.index(side) + 2) % 4]

def get_next_move_offset(last_round, trump) :
    if len(last_round) < 4 :
        return len(last_round)
    suits = map(lambda x: x / CARDS_IN_SUIT, last_round)
    t = S2STRAIN[trump]
    lead_suit = suits[0]
    if t == STRAIN_NT or t not in suits :
        t = lead_suit

    in_suit = filter(lambda x: x / CARDS_IN_SUIT == t, last_round)
    return last_round.index(max(in_suit))

def remove_alert(bid) :
    p = bid.find(':')
    if p < 0 :
        return bid
    else :
        return bid[:p]

def get_contract_and_declearer(bidding) :
    bidding = map(remove_alert, bidding)
    bidding = bidding[:-3]
    lastbid = bidding[-1]
    i = len(bidding) - 1
    dbl = ''
    if lastbid == BID_PASS :
        return BID_PASS, None
    elif lastbid == BID_DOUBLE :
        dbl = 'd'
        i -= 1
    elif lastbid == BID_REDOUBLE :
        dbl = 'r'
        i -= 1
    # some try-catch could be here to handle erroneous bidding
    while bidding[i] in SPECIAL_BIDS :
        i -= 1
    contract = bidding[i]
    suit = contract[1]
    decl =  i % 2
    while bidding[decl][1] != suit :
        decl += 2
    
    return contract + dbl, decl


def is_value_bid(bid) :
    return remove_alert(bid) not in SPECIAL_BIDS

def suit_rank_to_num(suit, rank):
    return 13 * SUITS.index(suit) + RANKS.index(rank)

def num_to_suit_rank(num) :
    return (SUITS[num / 13], RANKS[num % 13])

def has_same_suit(hand, card) :
    lbound = (card / 13) * 13
    hbound = lbound + 13
    i = len(hand)
    result = False
    while i > 0 and not result :
        i -= 1
        result = hand[i] > lbound and hand[i] < hbound
    return result

def same_suit(card1, card2) :
    return card1 / 13 == card2 / 13

def valid_card(hand, card, all_moves):
    h = set(hand)
    h.difference_update(all_moves)
    hand = list(h)
    if not card in hand :
        logging.warn("played with card not in hand")
        return False
    
    if len(all_moves) % 4 == 0 :
        return True

    fst_move_idx = (len(all_moves) / 4) * 4
    fst_move = all_moves[fst_move_idx]  # first move in this round
    if same_suit(fst_move, card) :
        return True

    hand.remove(card)
    res = not has_same_suit(hand, fst_move)
    return res


def get_deck() :
    res = range(52)
    random = rand.Random()
    random.shuffle(res)
    return zip(SIDES, [res[i:i + CARDS_IN_HAND] for i in xrange(0, len(res), CARDS_IN_HAND)])

def split_by_suits(hand) :
    def as_str(suit) : 
        suit.sort()
        suit.reverse()
        return ' '.join(map(lambda x: RANKS[x], suit))

    res = [[], [], [], []]
    for crd in hand :
        res[crd / CARDS_IN_SUIT].append(crd % CARDS_IN_SUIT)

    return map(as_str, res)

def get_distr(hand) :
    s = 0
    h = 0
    d = 0
    c = 0
    for crd in hand :
        if crd < 13 :
            s += 1
        elif crd < 26 :
            h += 1
        elif crd < 39 :
            d += 1
        else :
            c += 1
    return (s, h, d, c)

def doubled_undertricks_to_result(undertricks, vuln) :
    vadd = 100 if vuln else 0
    v = 300
    res = 0
    while undertricks > 3 :
        res += v
        undertricks -= 1
    v -= 100 - vadd
    while undertricks > 1 :
        res += v
        undertricks -= 1
    return (res + v - 100)
    

def tricks_to_result(contract, vuln, decl_tricks) :
    d = decl_tricks - (int(contract[0]) + 6)
    doubled = len(contract) == 3 and contract[2] == 'd'
    redoubled = len(contract) == 3 and contract[2] == 'r'
    plain = not doubled and not redoubled
    if d < 0 :
        if plain :
            vfac = 2 if vuln else 1
            return d * 50 * vfac
        else :
            dbld_res = doubled_undertricks_to_result(-d, vuln)
            if redoubled :
                dbld_res *= 2
            return -dbld_res
    else :
        level = int(contract[0])
        suit = contract[1]
        if suit in ['H', 'S', 'Z'] :
            base = 30
        else : 
            base = 20
        pts = base * level
        if suit == 'Z' :
            pts += 10

        if doubled :
            pts *= 2
            insult = 50
        elif redoubled :
            pts *= 4
            insult = 100
        else :
            insult = 0
        game = pts >= 100
        pts += insult
        slam = level == 6
        gslam = level == 7
        if not game :
            pts += 50
        else :
            pts += 500 if vuln else 300
            if slam :
                pts += 750 if vuln else 500
            elif gslam :
                pts += 1500 if vuln else 1000

        if not plain : 
            over_price = 100
            if redoubled :
                over_price *= 2
            if vuln :
                over_price *= 2
        else :
            over_price = base
        return pts + (d * over_price)
        
def decl_tricks_and_next_move_offset(moves, trump) :
    rounds = [moves[i: i+4] for i in xrange(0,len(moves),4)]
    if len(rounds) == 0 :
        return 0, 0
    if len(rounds[-1]) < 4 :
        last_offset = len(rounds.pop())
    else :
        last_offset = 0
    decl_tricks = 0
    decl_move = False
    old_o = 0
    for r in rounds :
        o = get_next_move_offset(r, trump)
        o = (o + old_o) % 4
        if (o % 2) == 1 :
            decl_tricks += 1
        old_o = o
    return decl_tricks, (old_o + last_offset) % 4

def declearer_tricks(moves, trump) :
    return decl_tricks_and_next_move_offset(moves, trump)[0]

def deal_result(contract, vuln, moves) :
    tricks = declearer_tricks(moves, contract[1])
    return tricks_to_result(contract, vuln, tricks), tricks
    

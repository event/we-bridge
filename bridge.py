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

DEALER_N = 0
DEALER_E = 1
DEALER_S = 2
DEALER_W = 3

DEALERS = [DEALER_N, DEALER_E, DEALER_S, DEALER_W]

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

CARDS_IN_SUIT = 13
CARDS_IN_HAND = 13

SUITS = ['clubs', 'diamonds', 'hearts', 'spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def get_contract_and_lead_maker(bidding) :
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

    return bidding[i] + dbl, i % 4


def is_value_bid(bid) :
    return bid not in SPECIAL_BIDS

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

def check_move(hand, card, all_moves):
    logging.info('checking for %s in %s', card, hand)
    if not card in hand or card in all_moves :
        logging.info('not allowed')
        return False
    
    if len(all_moves) % 4 == 0 :
        logging.info('round start: allowed')
        return True

    fst_move_idx = (len(all_moves) / 4) * 4
    fst_move = all_moves[fst_move_idx]  # first move in this round
    if same_suit(fst_move, card) :
        logging.info('fst_move is %s, now - %s: allowed', fst_move, card)
        return True

    hand.remove(card)
    res = not has_same_suit(hand, fst_move)
    logging.info('finally %s', res)
    return res


def get_deck() :
    res = range(52)
    random = rand.Random()
    random.shuffle(res)
    return (res[0:13], res[13:26], res[26:39], res[39:52])\
        , random.choice([VULN_NONE, VULN_NS, VULN_EW, VULN_BOTH])\
        , random.choice([DEALER_N, DEALER_S, DEALER_E, DEALER_W])

def split_by_suits(hand) :
    def as_str(suit) : 
        suit.sort()
        suit.reverse()
        return ' '.join(map(lambda x: RANKS[x], suit))

    res = [[], [], [], []]
    for crd in hand :
        res[crd / CARDS_IN_SUIT].append(crd % CARDS_IN_SUIT)

    return map(as_str, res)

def get_by_suit(hand, suit) :
    len(filter(lambda x: x >= suit * 13 and x < (suit+1) * 13, hand))

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


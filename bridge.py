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

import random as rand

VULN_NONE = 0
VULN_NS = 1
VULN_EW = 2
VULN_BOTH = 3

DEALER_N = 0
DEALER_S = 1
DEALER_E = 2
DEALER_W = 3

# bids from 1 club to 7 no trump are coded w/ numbers from 0 to 34 resp
BID_PASS = 35
BID_DOUBLE = 36
BID_REDOUBLE = 37

# cards are represented with number from 0 (2 of clubs) to 51 (ace of spades)
STRAIN_CLUB = 0
STRAIN_DIAMOND = 1
STRAIN_HEART = 2
STRAIN_SPADE = 3
STRAIN_NT = 4

CARDS_IN_SUIT = 13
CARDS_IN_HAND = 13

SUITS = ['spades', 'hearts', 'diamonds', 'clubs']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

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
    if not card in hand or card in all_moves :
        return False
    
    if len(all_moves) % 4 == 0 :
        return True

    fst_move_idx = (len(all_moves) / 4) * 4
    fst_move = all_moves[fst_move_idx]  # first move in this round
    if same_suit(fst_move, card) :
        return True

    hand.remove(card)
    return not has_same_suit(hand, fst_move)


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


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

SUIT_SPADE = 0
SUIT_HEART = 1
SUIT_DIAMOND = 2
SUIT_CLUB = 3

SUITS = ['S', 'H', 'D', 'C']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

def suit_rank_to_num(suit, rank):
    return 13 * SUITS.index(suit) + RANKS.index(rank)

def num_to_suit_rank(num) :
    return (SUITS[num / 13], RANKS[num % 13])
    
def check_lead(hand, card, current_round):
    return True

def get_deck() :
    res = range(52)
    rand.Random().shuffle(res)
    return (res[0:13], res[13:26], res[26:39], res[39:52])

def split_by_suits(hand) :
    def as_str(suit) :
        return ' '.join(map(lambda x: RANKS[x], suit))
    s, h, d, c = [], [], [], []
    for crd in hand :
        if crd < SUIT_HEART * 13 :
            s.append(crd)
        elif crd < SUIT_DIAMOND * 13 :
            h.append(crd - 13)
        elif crd < SUIT_CLUB * 13 :
            d.append(crd - 26)
        else :
            c.append(crd - 39)
    s.sort()
    s.reverse()
    h.sort()
    h.reverse()
    d.sort()
    d.reverse()
    c.sort()
    c.reverse()
    return (as_str(s), as_str(h), as_str(d), as_str(c))
    

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


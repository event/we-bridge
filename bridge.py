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

def get_deck() :
    res = range(52)
    rand.Random().shuffle(res)
    return (res[0:13], res[13:26], res[26:39], res[39:52])

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


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

import bridge


def test_deck_generator(deck_gen_func) :
    """
    test_deck_generator does tests deck generator function and print out the distribution probability. 
      distribution could be compared to e.g. www.playbridge.com
    deck_gen_func - no-arg function should return 4-tuple of 13-lists containing numbers 0-51. 
                       Each number represents a card: 0-12 - clubs; 13-25 - diamonds; etc.
    """
    def update(m, key) :
        if not key in m :
            m[key] = 0
        m[key] += 1

    def sort(tpl) :
        res = [tpl[0], tpl[1], tpl[2], tpl[3]]
        res.sort()
        res.reverse()
        return (res[0], res[1], res[2], res[3])

    def show_res(res, cnt) :
        print cnt
        l = res.items()
        l.sort()
        for k, v in l :
            print "%s - %f" %(k, float(v)/cnt)

    result = {}
    for i in xrange(100000) :
        d = deck_gen_func()
        for hand in d :
            distr = get_distr(hand)
            update(result, sort(distr))
    show_res(result, (i + 1)*4)


if __name__ == '__main__':
    test_deck_generator(bridge.get_deck)

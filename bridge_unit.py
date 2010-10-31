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

import unittest

import bridge

class CheckMoveTestCase(unittest.TestCase) :
    def test_card_not_in_hand(self) :
        assert not bridge.check_move([2], 1, None), 'card not in hand'

    def test_card_played_already(self) :
        assert not bridge.check_move([1], 1, [1]), 'card is already played'

    def test_card_new_round(self) :
        assert bridge.check_move([1], 1, []), 'new round - everything allowed'

    def test_card_right_suit(self) :
        assert bridge.check_move([1], 1, [0]), 'same suit - allowed'

    def test_card_no_suit(self) :
        assert bridge.check_move([1], 1, [15]), 'no same suit - allowed'

    def test_card_wrong_suit(self) :
        assert not bridge.check_move([1, 14], 1, [15]), 'another suit - disallowed'



if __name__ == '__main__' :
    unittest.main()


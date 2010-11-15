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
        self.assertFalse(bridge.check_move([2], 1, []), 'card not in hand')

    def test_card_played_already(self) :
        self.assertFalse(bridge.check_move([1], 1, [1]), 'card is already played')

    def test_card_new_round(self) :
        self.assertTrue(bridge.check_move([1], 1, []), 'new round - everything allowed')

    def test_card_right_suit(self) :
        self.assertTrue(bridge.check_move([1], 1, [0]), 'same suit - allowed')

    def test_card_no_suit(self) :
        self.assertTrue(bridge.check_move([1], 1, [15]), 'no same suit - allowed')

    def test_card_wrong_suit(self) :
        self.assertFalse(bridge.check_move([1, 14], 1, [15]), 'another suit - disallowed')

        
class CheckResCalcTestCase(unittest.TestCase) :
    def test_undertricks(self) :
        self.assertEquals(-50, bridge.tricks_to_result('1C', False, 6))
        self.assertEquals(-100, bridge.tricks_to_result('1C', True, 6))

        self.assertEquals(-100, bridge.tricks_to_result('1Cd', False, 6))
        self.assertEquals(-200, bridge.tricks_to_result('1Cd', True, 6))

        self.assertEquals(-200, bridge.tricks_to_result('1Cr', False, 6))
        self.assertEquals(-400, bridge.tricks_to_result('1Cr', True, 6))

    def test_1_club_even(self) :
        self.assertEquals(70, bridge.tricks_to_result('1C', False, 7))
        self.assertEquals(70, bridge.tricks_to_result('1C', True, 7))

        self.assertEquals(140, bridge.tricks_to_result('1Cd', False, 7))
        self.assertEquals(140, bridge.tricks_to_result('1Cd', True, 7))

        self.assertEquals(230, bridge.tricks_to_result('1Cr', False, 7))
        self.assertEquals(230, bridge.tricks_to_result('1Cr', True, 7))

    def test_1_club_over(self) :
        self.assertEquals(90, bridge.tricks_to_result('1C', True, 8))

        self.assertEquals(240, bridge.tricks_to_result('1Cd', False, 8))
        self.assertEquals(340, bridge.tricks_to_result('1Cd', True, 8))

        self.assertEquals(430, bridge.tricks_to_result('1Cr', False, 8))
        self.assertEquals(630, bridge.tricks_to_result('1Cr', True, 8))

    def test_2_heart_plain(self) :
        self.assertEquals(110, bridge.tricks_to_result('2H', True, 8))

        self.assertEquals(470, bridge.tricks_to_result('2Hd', False, 8))
        self.assertEquals(670, bridge.tricks_to_result('2Hd', True, 8))

        self.assertEquals(640, bridge.tricks_to_result('2Hr', False, 8))
        self.assertEquals(840, bridge.tricks_to_result('2Hr', True, 8))

    def test_3nt(self) :
        self.assertEquals(400, bridge.tricks_to_result('3Z', False, 9))

class CheckTrickCalc(unittest.TestCase) :
    def test_1_trick(self):
        self.assertEquals(1, bridge.declearer_tricks([0,1,2,3], 'Z'))
        self.assertEquals(0, bridge.declearer_tricks([0,1,4,3], 'Z'))

    def test_2_tricks(self) :
        self.assertEquals(1, bridge.declearer_tricks([0,1,2,3,4,5,6,7], 'Z'))
        self.assertEquals(2, bridge.declearer_tricks([0,1,2,3,4,5,8,7], 'Z'))
        self.assertEquals(1, bridge.declearer_tricks([0,1,8,3,4,5,6,7], 'Z'))
        self.assertEquals(0, bridge.declearer_tricks([8,1,2,3,9,5,6,7], 'Z'))


if __name__ == '__main__' :
    unittest.main()


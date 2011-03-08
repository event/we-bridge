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
        self.assertFalse(bridge.valid_card([2], 1, []), 'card not in hand')

    def test_card_played_already(self) :
        self.assertFalse(bridge.valid_card([1], 1, [1]), 'card is already played')

    def test_card_new_round(self) :
        self.assertTrue(bridge.valid_card([1], 1, []), 'new round - everything allowed')

    def test_card_right_suit(self) :
        self.assertTrue(bridge.valid_card([1], 1, [0]), 'same suit - allowed')

    def test_card_no_suit(self) :
        self.assertTrue(bridge.valid_card([1], 1, [15]), 'no same suit - allowed')

    def test_card_wrong_suit(self) :
        self.assertFalse(bridge.valid_card([1, 14], 1, [15]), 'another suit - disallowed')

        
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

    def test_half_round(self) :
        self.assertEquals((1, 3), bridge.decl_tricks_and_next_move_offset([37, 38, 27, 28, 26, 29], 'C'))
        self.assertEquals((1, 3), bridge.decl_tricks_and_next_move_offset([19, 25, 17, 14, 6, 9], 'C'))
        self.assertEquals((0, 0), bridge.decl_tricks_and_next_move_offset([0, 1, 12, 3, 14, 23], 'Z'))
        self.assertEquals((2, 3), bridge.decl_tricks_and_next_move_offset(
                [26, 28, 36, 37, 0, 1, 12, 3, 14, 23], 'Z'))

class CheckContractCalc(unittest.TestCase) :
    def test_simple(self):
        self.assertEquals(('1C', 0), bridge.get_contract_and_declearer(['1C', 'pass', 'pass', 'pass']))
        self.assertEquals(('2S', 3), bridge.get_contract_and_declearer(['pass', 'pass', 'pass', '2S'\
                                                                            , 'pass', 'pass', 'pass']))
        self.assertEquals(('3Z', 0), bridge.get_contract_and_declearer(['1Z', 'pass', '3Z', 'pass'\
                                                                            , 'pass', 'pass']))

    def test_w_doubles(self):
        self.assertEquals(('1Cd', 0), bridge.get_contract_and_declearer(['1C', 'pass', 'pass', 'dbl' \
                                                                             , 'pass', 'pass', 'pass']))

        self.assertEquals(('2Sr', 1), bridge.get_contract_and_declearer(['1C', '1S', 'pass', '2S'\
                                                                             , 'dbl', 'rdbl', 'pass' \
                                                                             , 'pass', 'pass']))


if __name__ == '__main__' :
    unittest.main()


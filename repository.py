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

from google.appengine.ext import db
import bridge

class Deal(db.Model) :
    n_hand = db.ListProperty(int)
    s_hand = db.ListProperty(int)
    e_hand = db.ListProperty(int)
    w_hand = db.ListProperty(int)
    vulnerability = db.IntegerProperty(choices = [bridge.VULN_NONE, bridge.VULN_NS
                                                  , bridge.VULN_EW, bridge.VULN_BOTH])
    dealer = db.IntegerProperty(choices = bridge.DEALERS)
    createDate = db.DateTimeProperty(auto_now_add=True)
    hand2side = {'N' : 'n_hand', 'S' : 's_hand', 'E' : 'e_hand', 'W' : 'w_hand'}
    @staticmethod
    def create(deal, vuln, dealer) :
        d = Deal()
        d.n_hand = deal[0]
        d.e_hand = deal[1]
        d.s_hand = deal[2]
        d.w_hand = deal[3]
        d.vulnerability = vuln
        d.dealer = dealer
        d.put()
        return d

    def hand_by_side(self, side) :
        return self.__getattribute__(self.hand2side[side])
    

class Protocol(db.Model) :
    N = db.UserProperty()
    S = db.UserProperty()
    E = db.UserProperty()
    W = db.UserProperty()
    bidding = db.StringListProperty()
    moves = db.ListProperty(int)
    deal = db.ReferenceProperty(Deal)
    result = db.IntegerProperty() # 0 = just made, +1 = one overtrick, -1 = one down
    playStarted = db.DateTimeProperty(auto_now_add=True)
    
    @staticmethod
    def create(dealmodel, N, S, E, W) :
        return Protocol(deal = dealmodel, N = N, E = E, S = S, W = W).put().id()
    
    def round_ended(self) :
        return len(self.moves) % 4 == 0

    def add_move(self, move) :
        self.moves.append(move)

    def finished(self) :
        return self.moves == 52

    def add_bid(self, bid) :
        bidding = self.bidding
        bid_cnt = len(bidding)
        if bid == bridge.BID_PASS :
            res = True
        elif bid == bridge.BID_DOUBLE :
            res = bid_cnt > 0 and bridge.is_value_bid(bidding[-1]) \
                or bid_cnt > 2 and bridge.is_value_bid(bidding[-3]) \
                and bidding[-2] == bidding[-1] == bridge.BID_PASS
        elif bid == bridge.BID_REDOUBLE :
            res = bid_cnt > 0 and bidding[-1] == bridge.BID_DOUBLE \
                or bid_cnt > 2 and bidding[-3] == bridge.BID_DOUBLE \
                and bidding[-2] == bidding[-1] == bridge.BID_PASS
        else :
            i = 1;
            while i <= bid_cnt and not bridge.is_value_bid(bidding[-i]) :
                i += 1
            res = i > bid_cnt or bidding[-i] < bid

        if res :
            self.bidding.append(bid)
            self.put()
        return res

    # FIXME: these below are all wrong. Should do full checks and exec in transaction        
    def add_card(self, card) :
        self.cardplay.append(card)
        self.put()

    def add_last_card(self, card, result) :
        self.result = result
        self.add_card(card)

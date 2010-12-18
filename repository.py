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

from google.appengine.ext import db
from google.appengine.api import users, channel
from django.utils  import simplejson as json
import bridge

class Deal(db.Model) :
    n_hand = db.ListProperty(int)
    s_hand = db.ListProperty(int)
    e_hand = db.ListProperty(int)
    w_hand = db.ListProperty(int)
    vulnerability = db.IntegerProperty(choices = bridge.VULN_OPTIONS)
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
    contract = db.StringProperty() # <level><suit>[d|r]<decl> eg. 3SdN, 2DS 
    tricks = db.IntegerProperty() # 0 = just made, +1 = one overtrick, -1 = one down
    result = db.IntegerProperty() # +100, -800, etc.
    playStarted = db.DateTimeProperty(auto_now_add=True)
    
    @staticmethod
    def create(dealmodel, N, E, S, W) :
        return Protocol(deal = dealmodel, N = N, E = E, S = S, W = W).put()
    
    @staticmethod
    def get_by_deal(deal) :
        return Protocol.all().filter('deal =', deal).order('playStarted')

    def round_ended(self) :
        return len(self.moves) % 4 == 0

    def finished(self) :
        return len(self.moves) == 52

    def dummy(self) :
        return bridge.SIDES[(bridge.SIDES.index(self.contract[-1]) + 2) % 4]

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
        return res

class UserProfile(db.Model) :
    chanid = db.StringProperty()
    user = db.UserProperty()
    loggedin = db.BooleanProperty()
    messages = db.StringListProperty()

    @staticmethod
    def broadcast(m) :
        for p in UserProfile.all().filter('loggedin =', True) :
            try :
                p.enqueue(m)
            except channel.InvalidChannelClientIdError :
                logging.warn('broadcast to %s failed', p.user.nickname())
                p.loggedin = False
           

    @staticmethod
    def uenqueue(user, m) :
        UserProfile.get_or_create(user).enqueue(m)

    @staticmethod
    def get_or_create(user) :
        res = UserProfile.gql('WHERE user = :1', user).get()
        if res is None :
            res = UserProfile()
            res.user = user
            res.put()
        return res
            
    def enqueue(self, m) :
        logging.info('%s: %s' % (self.user.nickname(), m))
        channel.send_message(self.chanid, json.dumps(m))
        

class Table(db.Model) :
    N = db.UserProperty()
    E = db.UserProperty()
    S = db.UserProperty()
    W = db.UserProperty()
    kibitzers = db.ListProperty(users.User)
    protocol = db.ReferenceProperty(Protocol)

    def user_by_side(self, side) :
        return self.__getattribute__(side)

    def side(self, user, player='own') :
        return bridge.SIDES[([self.N, self.E, self.S, self.W].index(user) + bridge.REL_SIDES.index(player)) % 4]

    def sit(self, place, user):
        self.__setattr__(place, user)

    def full(self):
        return all(map(lambda x: x is not None, [self.N, self.E, self.S, self.W]))

    def broadcast(self, m) :
        for u in [self.N, self.E, self.S, self.W] :
            if u is not None :
                UserProfile.uenqueue(u, m)

    # MAYBE store it in memory in place of each time recalculation
    def usermap(self) :
        return dict(filter(lambda x: x[1] is not None, 
                           zip(['N', 'E', 'S', 'W'], [self.N, self.E, self.S, self.W])))

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
    N = db.ListProperty(int)
    S = db.ListProperty(int)
    E = db.ListProperty(int)
    W = db.ListProperty(int)
    vulnerability = db.IntegerProperty(choices = bridge.VULN_OPTIONS)
    dealer = db.IntegerProperty(choices = bridge.DEALERS)
    createDate = db.DateTimeProperty(auto_now_add=True)
    @staticmethod
    def create(deal, vuln, dealer) :
        d = Deal()
        for side, cards in deal :
            d.__setattr__(side, cards)
        d.vulnerability = vuln
        d.dealer = dealer
        d.put()
        return d

    def hand_by_side(self, side) :
        return self.__getattribute__(side)
    

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


class Table(db.Model) :
    N = db.UserProperty()
    E = db.UserProperty()
    S = db.UserProperty()
    W = db.UserProperty()
    kibitzers = db.ListProperty(users.User)
    protocol = db.ReferenceProperty(Protocol)
    whosmove = db.StringProperty()
    
    def nextmove(self) :
        self.whosmove = bridge.SIDES[(bridge.SIDES.index(self.whosmove) + 1) % 4]
    
    def user_by_side(self, side) :
        return self.__getattribute__(side)

    def side(self, user, player='own') :
        try :
            return bridge.SIDES[self.side_idx(user, player)]
        except TypeError :
            return None

    def side_idx(self, user, player='own') :
        try :
            return ([self.N, self.E, self.S, self.W].index(user)
                    + bridge.REL_SIDES.index(player)) % 4
        except ValueError : 
            return None

    def sit(self, place, user):
        self.__setattr__(place, user)

    def full(self):
        return all(map(lambda x: x is not None, [self.N, self.E, self.S, self.W]))

    def empty(self):
        return all(map(lambda x: x is None, [self.N, self.E, self.S, self.W]))

    def broadcast(self, m, **kwargs) :
        ulist = [self.N, self.E, self.S, self.W]
        for u, m1 in kwargs.iteritems() :
            user = self.user_by_side(u)
            ulist.remove(user)
            UserProfile.uenqueue(user, m1)
        for u in ulist :
            if u is not None :
                UserProfile.uenqueue(u, m)
        self.kib_broadcast(m)

    def kib_broadcast(self, m) :
        for u in self.kibitzers :
            UserProfile.uenqueue(u, m)
            
    def userlist(self) :
        return filter(lambda x: x is not None, [self.N, self.E, self.S, self.W])

    # MAYBE store it in memory in place of each time recalculation
    def usermap(self) :
        return dict(filter(lambda x: x[1] is not None, 
                           zip(['N', 'E', 'S', 'W'], [self.N, self.E, self.S, self.W])))

    def remove_user(self, prof) :
        user = prof.user
        if user in self.kibitzers :
            self.kibitzers.remove(user)
            place = None # MAYBE this doesn't need to be published
        else : 
            place = self.side(user)
            if place is None :
                logging.warn('%s tried to leave a table while not sitting at it', user)
                return 
            self.sit(place, None)
            prof.table = None
            prof.put()
            self.broadcast(m('user.leave', position = place))
        if self.empty() :
            self.delete()
            mes = m('table.remove', tid = tid)
        else :
            self.put()
            mes = m('player.leave', tid = tid, position = place)
        UserProfile.broadcast(mes)



class UserProfile(db.Model) :
    chanid = db.StringProperty()
    user = db.UserProperty()
    table = db.ReferenceProperty(Table)
    loggedin = db.BooleanProperty()
    lastact = db.DateTimeProperty(auto_now = True)

    # MAYBE time consuming, optimize using background task
    @staticmethod
    def broadcast(m, exclude = None) :          
        users = UserProfile.all().filter('loggedin =', True)
        if exclude is not None :
            users = users.filter('user !=', exclude)
        for p in users :
            p.enqueue(m)
           

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
        logging.info('%s: %s', self.user.nickname(), m)
        try :
            channel.send_message(self.chanid, json.dumps(m))
        except channel.InvalidChannelClientIdError :
            logging.warn('broadcast to %s failed', self.user.nickname())
            self.loggedin = False
            self.put()


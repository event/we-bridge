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
from utils import m

class Deal(db.Model) :
    N = db.ListProperty(int, required=True)
    S = db.ListProperty(int, required=True)
    E = db.ListProperty(int, required=True)
    W = db.ListProperty(int, required=True)
    vulnerability = db.IntegerProperty(choices = bridge.VULN_OPTIONS, required=True)
    dealer = db.IntegerProperty(choices = bridge.DEALERS, required=True)
    createDate = db.DateTimeProperty(auto_now_add=True)
    @staticmethod
    def create(deal, vuln, dealer) :
        d = Deal(vulnerability=vuln, dealer=dealer, **deal)
        d.put()
        return d

    def hand_by_side(self, side) :
        return self.__getattribute__(side)
    

class Protocol(db.Model) :
    N = db.UserProperty(required=True)
    S = db.UserProperty(required=True)
    E = db.UserProperty(required=True)
    W = db.UserProperty(required=True)
    bidding = db.StringListProperty()
    moves = db.ListProperty(int)
    deal = db.ReferenceProperty(Deal, required=True)
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
    protocol = db.ReferenceProperty(Protocol)
    whosmove = db.StringProperty(choices = bridge.SIDES)
    
    def nextmove(self) :
        self.whosmove = bridge.SIDES[(bridge.SIDES.index(self.whosmove) + 1) % 4]
    
    def user_by_side(self, side) :
        res = TablePlace.get1(table=self, side=side)
        if res is None :
            return None
        else :
            return res.user 

    def side(self, user, player='own') :
        try :
            return bridge.SIDES[self.side_idx(user, player)]
        except TypeError :
            return None

    def side_idx(self, user, player='own') :
        try :
            return (bridge.SIDES.index(TablePlace.get1(table=self, user=user).side)
                    + bridge.REL_SIDES.index(player)) % 4
        except ValueError : 
            return None

    def sit(self, place, user):
        tp = TablePlace.get1(table=self, side=place)
        if tp is None :
            tp = TablePlace(table=self, side=place, user=user)
        else :
            tp.user = user
        return tp

    def pcount(self):
        return TablePlace.player_q(self).count(4)

    def bcast(self, m, q) :
        res = []
        for tp in q :
            p = UserProfile.uenqueue(tp.user, m)
            if p is not None :
                res.append(p)
        return res
        
 
    def broadcast(self, m) :
        return self.bcast(m, TablePlace.all().filter('table', self))

    def kib_broadcast(self, m) :
        return self.bcast(m, TablePlace.kibitzer_q(self))
            
    def userlist(self) :
        return [tp.user for tp in TablePlace.player_q(self).fetch(4)]

    # MAYBE store it in memory in place of each time recalculation
    def usermap(self) :
        return dict([(str(tp.side), tp.user) for tp in TablePlace.player_q(self).fetch(4)])

class TablePlace(db.Model) :
    user = db.UserProperty(required=True)
    side = db.StringProperty(required=True, choices = bridge.SIDES) #None for kibitzers
    table = db.ReferenceProperty(Table, required=True)
    
    @staticmethod
    def get1(**kwargs) :
        q = TablePlace.all()
        for k, v in kwargs.items() :
            q = q.filter(k, v)
        return q.get()

    @staticmethod
    def player_q(table) :
        return TablePlace.all().filter('table', table).filter('side !=', None)

    @staticmethod
    def kibitzer_q(table) :
        return TablePlace.all().filter('table', table).filter('side', None)

class UserProfile(db.Model) :
    chanid = db.StringProperty()
    user = db.UserProperty(required=True)
    loggedin = db.BooleanProperty()
    connected = db.BooleanProperty()
    messages = db.StringListProperty()
    lastact = db.DateTimeProperty(auto_now = True)

    # MAYBE time consuming, optimize using background task
    @staticmethod
    def broadcast(m, exclude = None) :          
        users = UserProfile.all().filter('loggedin =', True)
        if exclude is not None :
            users = users.filter('user !=', exclude)
        return filter(lambda x: x.enqueue(m), users)

    @staticmethod
    def uenqueue(users, m) :
        if not isinstance(users, list) :
            users = [users]
        res = []
        for prof in UserProfile.all().filter('user in', users):
            if prof.enqueue(m) :
                res.append(prof)
        return res

    @staticmethod
    def get_or_create(user) :
        res = UserProfile.gql('WHERE user = :1', user).get()
        if res is None :
            res = UserProfile(user = user)
            res.put()
        return res
            
    def enqueue(self, m) :
        if not self.loggedin :
            return False
        logging.info('%s: %s', self.user.nickname(), m)
        if self.connected :
            try :
                channel.send_message(self.chanid, json.dumps(m))
            except channel.InvalidChannelClientIdError :
                logging.warn('broadcast to %s failed', self.user.nickname())
                self.connected = False
            else :
                return False
        if not isinstance(m, list) :
            m = [m]
       
        self.messages += [json.dumps(x) for x in m]
        return True

    def send_stored_messages(self) :
        channel.send_message(self.chanid, '[' + ','.join(self.messages) + ']')
        self.messages = []
        self.connected = True
            
    def logoff(self, toput):
        self.loggedin = False
        tps = TablePlace.all().filter('user', self.user).fetch(100)
        db.delete(tps)
        for tp in tps :
            table = tp.table
            toput.append(UserProfile.broadcast(m('player.leave', tid = table.key().id(), position = tp.side)))

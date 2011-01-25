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

import re

def m(t, **kwargs) :
    return {'type': t, 'value': kwargs}

suitre = re.compile('!([SHDC])')
def process_chat_message(text) :
    def suit_replacer(match) :
        s = match.group(1)
        return '<img src="images/%s.png" alt="%s"/>' % (s.lower(), s)
    return suitre.sub(suit_replacer, text.replace('<', '&lt;').replace('>', '&gt;'))


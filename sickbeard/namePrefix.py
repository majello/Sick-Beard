# Author: Stefan Marte <stefan.marte@gmail.com>
# URL: http://github.com/majello/Sick-Beard
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import db

def load(filename):
    myDB = db.DBConnection()
    f = open(filename,"r")
    for line in f:
        line = line.decode('utf-8')
        prefix, prefixCategory, usage = line.split(':')
        if not prefix:
            continue
        myDB.action("INSERT OR REPLACE INTO name_prefix (prefix, prefixCategory, usage) VALUES (?,?,?)", [prefix, prefixCategory, usage])
    f.close()

def get():
    myDB = db.DBConnection()
    p = myDB.action("select prefix, prefixCategory, usage from name_prefix")
    return p

def makeNames(name,usage):
    r = []
    prefixes = get().fetchall()
    for p in prefixes:
        u = list(set(p['usage'].split(",")) & set(usage))
        if name.startswith(p['prefix']) and u != []:
            nm = name[len(p["prefix"]):].encode("ascii","ignore")
            r.append(nm.strip())
    return r

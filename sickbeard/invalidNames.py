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

from sickbeard import db

def findFile(filename, show = None,snum = None, epnum = None):
    # check if file in table
    myDB= db.DBConnection()
    ne = myDB.action("SELECT * FROM file_exceptions WHERE filename = ?",[filename]).fetchall()
    showname = None
    season = None
    episode = None
    if ne == []:
        # if not, insert
        myDB.action("INSERT INTO file_exceptions (filename, showname,season,episode) VALUES (?,?,?,?)",[filename,show,snum,epnum])
    else:
        # if it is, see if complete
        showname = ne[0]["showname"]
        season = ne[0]["season"]
        episode = ne[0]["episode"]
    # return show,season,episode
    return {"showname": showname,"season": season,"episode":episode}

def get():
    myDB= db.DBConnection()
    ne = myDB.action("SELECT * FROM file_exceptions ORDER BY filename").fetchall()
    r = {}
    for idx,f in enumerate(ne):
        r[idx] = {"filename":f["filename"],"showname":f["showname"],"season":f["season"],"episode":f["episode"]}
    return r

def update(values):
    myDB= db.DBConnection()
    for v in values:
        try:
            myDB.action("INSERT OR REPLACE INTO file_exceptions (filename, showname,season,episode) VALUES (?,?,?,?)",[v["filename"],v["showname"],v["season"],v["episode"]])
        except:
            pass
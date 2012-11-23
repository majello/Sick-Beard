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

from sickbeard import db, logger, name_parser

import os, time

def findFile(filename, show = None, snum = None, epnum = None, source = "Unknown"):
    # check if file in table
    myDB = db.DBConnection()
    ne = myDB.action("SELECT * FROM file_exceptions WHERE filename = ?", [filename]).fetchall()
    showname = None
    season = None
    episode = None
    if source.lower() == "unknown":
        logger.log("unknown source for %s" % (filename))
    if ne == []:
        # if not, insert
        if show == None or show == "None":
            show = ""
        if snum == None or snum == "None":
            snum = ""
        if epnum == None or epnum == "None":
            epnum = []
        episodes = ",".join([str(x) for x in epnum])
        myDB.action("INSERT INTO file_exceptions (filename, showname,season,episode,source,stamp) VALUES (?,?,?,?,?,?)", [filename, show, snum, episodes, source, int(time.time())])
    else:
        # if it is, see if complete
        showname = ne[0]["showname"]
        try:
            season = int(ne[0]["season"])
        except:
            season = None
        episode = ne[0]["episode"]
        try:
            episode = [int(e) for e in episode.split(",")]
        except:
            episode = None
    # return show,season,episode
    return {"showname": showname, "season": season, "episode":episode}

def get():
    myDB = db.DBConnection()
    ne = myDB.action("SELECT * FROM file_exceptions ORDER BY source asc,stamp desc").fetchall()
    r = {}
    for idx, f in enumerate(ne):
        age = ""
        try:
            age_base = time.time() - f["stamp"]
            age_seconds = int(age_base % 60)
            age_minutes = int(age_base / 60)
            age_hours = int(age_minutes / 60)
            age_minutes = int(age_minutes % 60)
            age_days = int(age_hours / 24)
            age_hours = int(age_hours % 24)
            age = "{}d {}:{}:{}".format(age_days, age_hours, age_minutes, age_seconds)
        except:
            pass
        r[idx] = {"filename":f["filename"], "showname":f["showname"], "season":f["season"], "episode":f["episode"], "source":f["source"], "age":age}
    return r

def update(values):
    myDB = db.DBConnection()
    for v in values:
        try:
            if v["delete"] == False:
                myDB.upsert("file_exceptions", {"showname":v["showname"], "season":v["season"], "episode":v["episode"]}, {"filename":v["filename"]})
                # myDB.action("INSERT OR REPLACE INTO file_exceptions (filename, showname,season,episode) VALUES (?,?,?,?)",[v["filename"],v["showname"],v["season"],v["episode"]])
            else:
                myDB.action("DELETE FROM file_exceptions where filename = ?", [v["filename"]])
        except:
            pass

def remove(full_filename, reason = "unknown reason"):
    # first strip path
    s1 = os.path.split(full_filename)
    s2 = os.path.splitext(s1[1])
    try:
        myDB = db.DBConnection()
        myDB.action("DELETE FROM file_exceptions where filename = ?", [s2[0]])
    except:
        raise
    else:
        logger.log("Removed %s from name exceptions due to %s" % (s2[0], reason))
    return

def expunge():
    # TODO: schedule regular expunge
    myDB = db.DBConnection()
    # clean up mess
    myDB.action('UPDATE file_exceptions SET showname="" WHERE showname = "None"')
    myDB.action('UPDATE file_exceptions SET season="" WHERE season = "None"')
    myDB.action('UPDATE file_exceptions SET episode="" WHERE episode = "None"')
    # see if we have old RSS entries
    # TODO: make expiry time configurable, currently set to 5 minutes
    myDB.action('DELETE FROM file_exceptions WHERE (source = "RSS" AND stamp < ?) OR source = "Unknown"', [int(time.time() - 5 * 60)])

def parse():
    myDB = db.DBConnection()
    names = myDB.action("SELECT filename FROM file_exceptions").fetchall()
    for r in names:
        filename = r["filename"]
        np = name_parser.parser.NameParser(filename)
        try:
            pr = np.parse(filename, fullname = False)
            myDB.action("UPDATE file_exceptions SET showname = ?, season = ?, episode = ? WHERE filename = ?", [pr.series_name, pr.season_number, ",".join([str(x) for x in pr.episode_numbers]), filename])
            logger.log(u"Parsed filename: %s" % filename)
        except name_parser.parser.InvalidNameException, e:
            logger.log(u"Unable to get parse filename %s: %s" % (filename, e))

class InvalidNamesProcesser():

    def run(self):
        expunge()
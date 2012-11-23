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

import string
import sys, time, threading
import sickbeard
from sickbeard import logger
from sickbeard import scene_exceptions

litnums = {0: "zero",
           1: "one",
           2: "two",
           3: "three",
           4: "four",
           5: "five",
           6: "six"}

network_variants = {"history": "history channel"}

showpatternCache = {}
nameVariationsCache = {}
networkVariationsCache = {}
xyPatternCache = {}
docTestCache = {}
episodeNameCache = {}

def _nameVariations(name, network=True):
    if network and name in networkVariationsCache:
        return networkVariationsCache[name]
    if not network and name in nameVariationsCache:
        return nameVariationsCache[name]
    if network and name.lower() in network_variants:
        name = network_variants[name.lower()]
    sname = name.lower().split()
    result = [name.lower()]
    # check for Documentaries ending
    result = result + [" ".join([x for x in sname if x != "documentaries"])]
    if network:
        # for our purposes, skip channel numbers (e.g. BBC Four -> BBC)
        sname = [n for n in sname if n not in litnums.values()]
        # check for Channel -> Ch
        result = result + [" ".join(["ch" if x == "channel" else x for x in sname])]
        # version without channel
        result = result + [" ".join(["" if x == "channel" else x for x in sname])]
        # check for National Geographics -> NG
        if len(sname) > 1:
            result = result + ["".join([x[0] for x in list(sname)])]
    if network:
        networkVariationsCache[name] = result
    else:
        nameVariationsCache[name] = result
    return result

def _numEpisodesForSeason(episode):
#    el = [e.name for e in episode.show.episodes if e.season == episode.season]
    return len(episode.show.episodes[episode.season])

def _networkShowPattern(episode, shownames):
    if not episode.show.tvdbid in showpatternCache:
        networks = set()
        shows = {x for n in shownames for x in _nameVariations(n, False)}
        if "documentary" in episode.show.genre.lower():
            networks = {" ".join([y, n]) for n in shows for y in _nameVariations(episode.show.network, True) if n != y and episode.show.network.lower() != n and not n.endswith("documentaries")}
        r = list(shows | networks)
        showpatternCache[episode.show.tvdbid] = r
    return showpatternCache[episode.show.tvdbid]


def _xOfyPattern(episode, weak=False):
    if not episode in xyPatternCache:
        pattern = []
        pattern.append("%dof%d" % (episode.episode, _numEpisodesForSeason(episode)))
        pattern.append("%02dof%d" % (episode.episode, _numEpisodesForSeason(episode)))
        pattern.append("%d of %d" % (episode.episode, _numEpisodesForSeason(episode)))
        pattern.append("%02d of %d" % (episode.episode, _numEpisodesForSeason(episode)))
        if weak == True:
            pattern.append("%dof" % (episode.episode))
            pattern.append("%02dof" % (episode.episode))
            pattern.append("%d of" % (episode.episode))
            pattern.append("%02d of" % (episode.episode))
        xyPatternCache[episode] = pattern
    return xyPatternCache[episode]

def _isDocumentary(show):
    if not show in docTestCache:
        docTestCache[show] = "documentary" in show.genre.lower()
    return docTestCache[show]

def _sanitizedEpisodeName(episode,tvdbid = None):
    if tvdbid == None or not tvdbid in episodeNameCache:
        r = episode.lower()
        r = string.replace(r,".","")
        r = string.replace(r,":","")
        r = string.replace(r,"-","")
        r = string.replace(r,"_","")
        r = string.replace(r,",","")
        if tvdbid == None:
            return r
        episodeNameCache[tvdbid] = r
    return episodeNameCache[tvdbid]


ruleDescriptions = {1:  "Show Name + Episode Name",
                    3:  "Show Name + Season + Episode Name",
                    5:  "Show Name + XofY",
                    9:  "Show Name + XofY + Episode Name",
                    11: "Show Name + \"Season\" + season + XofY",
                    12: "Show Name + \"Series\" + season + XofY",
                    15: "Show Name + \"Season\" + literal season + XofY",
                    17: "Show Name + \"Part\" + episode number + episode name",
                   }

def _namePattern1(episode, shownames):
    return (1, 10, [x + " " + _sanitizedEpisodeName(episode.name,episode.tvdbid) for x in _networkShowPattern(episode, shownames)])

def _namePattern3(episode, shownames):
    if not _isDocumentary(episode.show):
        return (3, 3, [])
    return (3, 10, [x + " " + sp + str(episode.season) + " " + _sanitizedEpisodeName(episode.name,episode.tvdbid) for sp in ["","S"] for x in _networkShowPattern(episode, shownames)])

def _namePattern5(episode, shownames):
    if not _isDocumentary(episode.show):
        return (5, 3, [])
    return (5, 3, [x+" "+p for x in _networkShowPattern(episode, shownames) for p in _xOfyPattern(episode, True)])

def _namePattern9(episode, shownames):
    if not _isDocumentary(episode.show):
        return (9, 5, [])
    return (9, 5, [x+" "+p+" " + _sanitizedEpisodeName(episode.name,episode.tvdbid) for x in _networkShowPattern(episode, shownames) for p in _xOfyPattern(episode)])

def _namePattern11(episode, shownames):
    if not _isDocumentary(episode.show):
        return (11, 8, [])
    return (11, 8, [x+" season " + str(episode.season)+" "+p for x in _networkShowPattern(episode, shownames) for p in _xOfyPattern(episode)])

def _namePattern12(episode, shownames):
    if not _isDocumentary(episode.show):
        return (12, 8, [])
    return (12, 8, [x+" series "+str(episode.season)+" "+p for x in _networkShowPattern(episode, shownames) for p in _xOfyPattern(episode)])

def _namePattern15(episode, shownames):
    if episode.season <=6 and _isDocumentary(episode.show):
        return (15, 8, [y+" "+x+" season "+litnums[episode.season]+" "+p for n in shownames for x in _nameVariations(n) for y in _nameVariations(episode.show.network) for p in _xOfyPattern(episode)])
    else:
        return (15, 8, [])

def _namePattern17(episode, shownames):
    if not _isDocumentary(episode.show):
        return (17, 8, [])
    return (17, 3, [x + " part "+str(episode.episode) + " " + _sanitizedEpisodeName(episode.name,episode.tvdbid) for x in _networkShowPattern(episode, shownames)])


class EpisodeParser(object):

    ruleList = []
    nameList = None
    nameAge = None
    nameLock = threading.RLock()
    buildLock = threading.RLock()

    def __init__(self):
        self.nameList = {}
        self.nameAge = 0
        for pattern in dir(sys.modules[__name__]):
            if pattern.startswith("_namePattern"):
                self.ruleList.append(pattern)
        return

    def getRuleName(self, ruleID):
        return ruleDescriptions[ruleID]

    def getNames(self, episode):
        with self.nameLock:
            self._parseShows()
            r = [(v[0], v[1], v[2], k,ruleDescriptions[v[1]]) for k, v in self.nameList.iteritems() if v[0] == episode]
            return r

    def match(self, filename):
        with self.nameLock:
            self._parseShows()
            prep = _sanitizedEpisodeName(filename)
            # TODO: replace for loop test for filename fragments (should be faster with large DB
            # REMINDER: 0 is episode, 1 is ruleID,2 is confidence
            result = [(v[0], v[1], v[2], k) for k,v in self.nameList.iteritems() if prep.startswith(k)]
            if result == []:
                return None
            else:
                v = max(result.iteritems(), key=lambda x: x[2])
                # confidence level 3 get special treatment, we prefer season 1 for those
                if v[2] == 3:
                    for k1 in result.iteritems():
                        if k1[0].season == 1 and k1[2] == 3:
                            v = k1
                            break
                # return just the episode
                return v[0]

    def _makeNames(self, nlist, episode, allnames):
        if episode.name.strip() == "":
            return
        for pattern in self.ruleList:
            try:
                l = getattr(sys.modules[__name__], pattern)(episode, allnames)
                for r in set(l[2]):
                    nlist[r] = (episode,l[0],l[1])
            except Exception as e:
                logger.log("name pattern returned error: %s" % (e))

    def _printCache(self):
        for pattern, info in self.nameList.iteritems():
            print "[ %2i (%2i)]%s: %s" % (info[2], info[1], pattern, info[0].name)

    def _parseShows(self,r=False):
        # TODO: implement variable refresh frequency
        if self.nameList == {} or time.time()-(5*60) > self.nameAge:
            if self.buildLock.acquire(False):
                try:
                    logger.log("Start building episode name patterns. This may take a while.")
                    # take times
                    q2 = time.time()
                    q0 = 0
                    q1 = 0
                    # clear the caches, just in case something changes
                    showpatternCache = {}
                    nameVariationsCache = {}
                    networkVariationsCache = {}
                    xyPatternCache = {}
                    docTestCache = {}
                    episodeNameCache = {}
                    # temporary list
                    nlist = {}
                    # build the names
                    for show in sickbeard.showList:
                        # pick up various show name variants
                        allnames = [show.name]
                        allnames += [name for name in scene_exceptions.get_scene_exceptions(show.tvdbid)]
                        # process documentaries, if allowed
                        if sickbeard.DOC_USE_NAMES == True and "documentary" in show.genre.lower():
                            q0a = time.time()
                            eplist = show.getAllEpisodes()
                            q0 += time.time()-q0a
                            for episode in eplist:
                                self._makeNames(nlist,episode, allnames)
                        # process specials if allowed
                        if sickbeard.SPEC_USE_NAMES == True:
                            q1a = time.time()
                            eplist = show.getAllEpisodes(season=0)
                            q1 += time.time() - q1a
                            for episode in eplist:
                                if episode.season == 0:
                                    self._makeNames(nlist,episode, allnames)
                            pass
                except Exception as e:
                    self.buildLock.release()
                    raise
                else:
                    self.buildLock.release()

            with self.nameLock:
                self.nameList = nlist
                self.nameAge = time.time()
            logger.log("Built %i episode name patterns in %i seconds (%i in database)." % (len(self.nameList), int(time.time()-q2), int(q1+q0)))
        return

episode_parser = EpisodeParser()

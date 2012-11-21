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


import sys, time, threading
import sickbeard
from sickbeard import db, logger
from sickbeard import scene_exceptions

litnums = {0:"zero",1:"one",2:"two",3:"three",4:"four",5:"five",6:"six"}

def _nameVariations(name,network=True):
    sname = name.lower().split()
    result = [name.lower()]
    # check for Documentaries ending
    result = result + [ " ".join([ x for x in sname if x != "documentaries"]) ]
    # check for Channel -> Ch
    result = result + [ " ".join([ "ch" if x == "channel" else x for x in sname ]) ]    
    # check for National Geographics -> NG
    if len(sname) > 1 and network:
        result = result + [ "".join([ x[0] for x in list(sname) ]) ]
    return result

def _numEpisodesForSeason(episode):
#    el = [e.name for e in episode.show.episodes if e.season == episode.season]
    return len(episode.show.episodes[episode.season])

showpatternCache = {}

def _networkShowPattern(episode,shownames):
    if not episode.show.tvdbid in showpatternCache:
        networks = set()
        shows = {x for n in shownames for x in _nameVariations(n,False)}
        if "documentary" in episode.show.genre.lower():
            networks = { " ".join([y,n]) for n in shows for y in _nameVariations(episode.show.network,True) if n <> y and episode.show.network.lower() <> n and not n.endswith("documentaries")}
        r = list( shows | networks)
        showpatternCache[episode.show.tvdbid] = r
    return showpatternCache[episode.show.tvdbid]

def _xOfyPattern(episode,weak=False):
    pattern = []
    pattern.append("%dof%d" % (episode.episode,_numEpisodesForSeason(episode)))
    pattern.append("%02dof%d" % (episode.episode,_numEpisodesForSeason(episode)))
    if weak == True:
        pattern.append("%dof" % (episode.episode))
        pattern.append("%02dof" % (episode.episode))
    return pattern

# showname + episodename
def _namePattern1(episode,shownames):
    return (1,10,[ " ".join([x,episode.name]) for x in _networkShowPattern(episode,shownames) ])

# show + season + episodename  
def _namePattern3(episode,shownames):
    return (3,10,[ " ".join([x,str(episode.season),episode.name]) for x in _networkShowPattern(episode,shownames) ])

# show + xofy (can match season show count) 
def _namePattern5(episode,shownames):
    if not "documentary" in episode.show.genre.lower(): return (5,3,[])
    return (5,3,[ " ".join([x,p]) for x in _networkShowPattern(episode,shownames) for p in _xOfyPattern(episode, True)])

# show + xofy + episodename
def _namePattern9(episode,shownames):
    if not "documentary" in episode.show.genre.lower(): return (9,5,[])
    return (9,5,[ " ".join([x,p,episode.name]) for x in _networkShowPattern(episode,shownames) for p in _xOfyPattern(episode) ])

# show + season + xofy
def _namePattern11(episode,shownames):
    if not "documentary" in episode.show.genre.lower(): return (11,8,[])
    return (11,8,[ " ".join([x,"season",str(episode.season),p]) for x in _networkShowPattern(episode,shownames) for p in _xOfyPattern(episode) ])

# show + series + xofy
def _namePattern12(episode,shownames):
    if not "documentary" in episode.show.genre.lower(): return (12,8,[])
    return (12,8,[ " ".join([x,"series",str(episode.season),p]) for x in _networkShowPattern(episode,shownames) for p in _xOfyPattern(episode) ])

# network + show + literal season + xofy
def _namePattern15(episode,shownames):
    if episode.season <=6 and "documentary" in episode.show.genre.lower():
        return (15,8,[ " ".join([y,x,"season",litnums[episode.season],p]) for n in shownames for x in _nameVariations(n) for y in _nameVariations(episode.show.network) for p in _xOfyPattern(episode) ])
    else:
        return (15,8,[])

class EpisodeParser(object):
    
    nameList = None
    nameAge = None
    nameLock = threading.RLock()
    
    def __init__(self):
        self.nameList = {}
        self.nameAge = 0
        return

    def _makeNames(self,episode,allnames):
        if episode.name.strip() == "":
            return
        for pattern in dir(sys.modules[__name__]):
            if pattern.startswith("_namePattern"):
                try:
                    l = getattr(sys.modules[__name__],pattern)(episode,allnames)
                    # test for silly results
#                    silly = [x for x in l[2] if len(x) <= 4]
#                    if silly != []:
#                        logger.log("Silly rule #%d result: %s" % (l[0],silly))
                    for r in set(l[2]):
                        el = {episode:(l[0],l[1])}
                        # reminder: rulenumber = l[0]
                        el.update(self.nameList.get(r,{}))
                        self.nameList[r] = el
                    # r = { x.lower(): (episode,l[1],l[0]) for x in l[2] if x.strip() != "" }
                    #self.nameList.update(r)
                except Exception as e:
                    logger.log("name pattern returned error: %s" % (e))
    
    def _printCache(self):
        for pattern,info in self.nameList.iteritems():
            print "[ %2i (%2i)]%s: %s" % (info[2],info[1],pattern,info[0].name)
    
    def _parseShows(self):
        with self.nameLock:
            # TODO: implement variable refresh frequency
            if self.nameList == {} or time.time()-(5*60) > self.nameAge:
                self.nameAge = time.time()
                for show in sickbeard.showList:
                    # pick up various show name variants
                    allnames = [show.name]
                    allnames += [name for name in scene_exceptions.get_scene_exceptions(show.tvdbid)]
                    # process documentaries, if allowed
                    if sickbeard.DOC_USE_NAMES == True and "documentary" in show.genre.lower():
                        eplist = show.getAllEpisodes()
                        for episode in eplist:
                            self._makeNames(episode,allnames)
                    # process specials if allowed 
                    if sickbeard.SPEC_USE_NAMES == True:
                        eplist = show.getAllEpisodes(season=0)
                        for episode in eplist:
                            if episode.season == 0:
                                self._makeNames(episode,allnames)
                        pass
                logger.log("Built %i episode name patterns in %i seconds." % (len(self.nameList),int(time.time()-self.nameAge)))            
#                    self._printCache()
        return
    
    def match(self,filename):
        with self.nameLock:
            self._parseShows()
            result = {}
            prep = filename.lower().replace("."," ")
            for possible,data in self.nameList.iteritems():
                if prep.startswith(possible):
                    result.update(data)
            if result == {}:
                return None
            else:
                k,v = max(result.iteritems(),key=lambda x:x[1][1] )
                # confidence level 3 get special treatment, we prefer season 1 for those
                if v[1] == 3:
                    for k1,v1 in result.iteritems():
                        if k1.season == 1 and v1[1] == 3:
                            k = k1
                return k
                    

episode_parser = EpisodeParser()
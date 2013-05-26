Sick Beard Majello Fork
=====

I have a few plans for this fork of the sickbeard piratebay edition:
* [POSTPONED] switchable db backends (such as mysql) for large libraries
* [POSTPONED] performance, as I have this running on a NAS, with a rather large library
* [IN PROGRESS] better support for documentaries, which i consider broken in the original releases
* [IN PROGRESS] enhanced name handling
* [PLANNED] recommendations, trending etc. (from trakt for the time being)
* [PLANNED] full library sync with trakt
* [PLANNED] twitter provider (eztv_it)
That should be enough for the time being.

Current Status
=====
* Implemented basic episode name searching for documentaries and specials (configurable):
  This version calculates a set of possible filenames for all relevant (documentaries, specials) episodes. This requires CPU and memeory, so beware.
* Episode page:
  This is mostly useful to see which names are generated for a given episode
* Invalid names handling:
  filenames that are not matched are saved in the database. if the file is scanned again later, show, season and episode numbers are retrieved from that table
* Manage invalid names page:
  interface to set episode information for unmatched file, delete them etc.
* Main Page
  implemented lazy loading of images, easier on mobile clients, esp. with a slow server 

Original
=====

*Sick Beard is currently an alpha release. There may be severe bugs in it and at any given time it may not work at all.*

Sick Beard is a PVR for newsgroup users (with limited torrent support). It watches for new episodes of your favorite shows and when they are posted it downloads them, sorts and renames them, and optionally generates metadata for them. It currently supports NZBs.org, NZBMatrix, Bin-Req, NZBs'R'Us, EZTV.it, and any Newznab installation and retrieves show information from theTVDB.com and TVRage.com.

Features include:

* automatically retrieves new episode torrent or nzb files
* can scan your existing library and then download any old seasons or episodes you're missing
* can watch for better versions and upgrade your existing episodes (to from TV DVD/BluRay for example)
* XBMC library updates, poster/fanart downloads, and NFO/TBN generation
* configurable episode renaming
* sends NZBs directly to SABnzbd, prioritizes and categorizes them properly
* available for any platform, uses simple HTTP interface
* can notify XBMC, Growl, or Twitter when new episodes are downloaded
* specials and double episode support


Sick Beard makes use of the following projects:

* [cherrypy][cherrypy]
* [Cheetah][cheetah]
* [simplejson][simplejson]
* [tvdb_api][tvdb_api]
* [ConfigObj][configobj]
* [SABnzbd+][sabnzbd]
* [jQuery][jquery]
* [Python GNTP][pythongntp]
* [SocksiPy][socks]
* [python-dateutil][dateutil]
* [jsonrpclib][jsonrpclib]
* [Subliminal][subliminal]

## Dependencies

To run Sick Beard from source you will need Python 2.6+ and Cheetah 2.1.0+. The [binary releases][googledownloads] are standalone.

## Bugs

If you find a bug please report it or it'll never get fixed. Verify that it hasn't [already been submitted][googleissues] and then [log a new bug][googlenewissue]. Be sure to provide as much information as possible.

[cherrypy]: http://www.cherrypy.org
[cheetah]: http://www.cheetahtemplate.org/
[simplejson]: http://code.google.com/p/simplejson/ 
[tvdb_api]: http://github.com/dbr/tvdb_api
[configobj]: http://www.voidspace.org.uk/python/configobj.html
[sabnzbd]: http://www.sabnzbd.org/
[jquery]: http://jquery.com
[pythongntp]: http://github.com/kfdm/gntp
[socks]: http://code.google.com/p/socksipy-branch/
[dateutil]: http://labix.org/python-dateutil
[googledownloads]: http://code.google.com/p/sickbeard/downloads/list
[googleissues]: http://code.google.com/p/sickbeard/issues/list
[googlenewissue]: http://code.google.com/p/sickbeard/issues/entry
[jsonrpclib]: https://github.com/joshmarshall/jsonrpclib
[subliminal]: https://github.com/Diaoul/subliminal

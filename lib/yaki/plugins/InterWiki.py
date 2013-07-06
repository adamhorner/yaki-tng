#!/usr/bin/env python
# encoding: utf-8
"""
InterWiki.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store
import urlparse, re, time
from BeautifulSoup import *

metaPage = 'meta/InterWikiMap'

class InterWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'a','interwiki')
    self.ac = webapp.getContext()
    self.load()
    
  def load(self):
    # load InterWikiMap
    try:
      page = self.ac.store.getRevision(metaPage)
    except:
      print "WARNING: no %s definitions" % metaPage
      return
    self.ac.interwikischemas = {}
    # prepare to parse only <pre> tags in it (so that we can have multiple maps organized by sections)
    plaintext = SoupStrainer('pre')
    map = ''.join([text.string for text in BeautifulSoup(page.render(), parseOnlyThese=plaintext)])
    # now that we have the full map, let's build the schema hash
    lines = map.split('\n')
    for line in lines:
      try:
        (schema, url) = line.strip().split(' ',1)
        self.ac.interwikischemas[schema.lower()] = url.replace("&amp;","&")
      except ValueError: # skip lines with more than two fields
        #print "WARNING: skipping line '%s'" % line
        pass
    #print "INFO: map is ", self.schemas
    self.mtime = time.time()
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    try:
      if (self.mtime < self.ac.store.mtime(metaPage)):
        self.load()
    except:
      return True
    try:
      url = tag['href']
    except KeyError:
      return True
    try:      
      (schema, link) = url.split(':',1)
    except ValueError:
      return False
    tag['rel'] = url
    # Remove base prefix in case it was added by BaseURI plugin earlier
    schema = schema.replace(self.ac.base,'').lower()
    if schema in self.ac.interwikischemas.keys():
      if '%s' in self.ac.interwikischemas[schema]:
        try:
          uri = self.ac.interwikischemas[schema] % link
        except:
          print "Error in processing Interwiki link (%s,%s,%s)" % (schema, link, self.schemas[schema])
          uri = self.ac.interwikischemas[schema] + link
      else:
        uri = self.ac.interwikischemas[schema] + link
      tag['href'] = uri
      (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(uri)
      tag['title'] = "link to %s on %s" % (link, netloc)
      tag['class'] = "interwiki"
      # this tag does not need to be re-processed
      return False

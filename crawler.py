
# Copyright (C) 2011 by Peter Goodman
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sqlite3 as lite
import sys
import urllib2
import urlparse
from pagerank import page_rank
from BeautifulSoup import *
from collections import defaultdict
import re

def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""

WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')

class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        self._url_queue = [ ]
        self._doc_id_cache = { }
        self._word_id_cache = { }

        # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

        # never go in and parse these tags
        self._ignored_tags = set([
            'meta', 'script', 'link', 'meta', 'embed', 'iframe', 'frame', 
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset', 
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._curr_url = ""
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = None

        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This function is implemented to fill in our "lexicon" table. It first
# checks to see if the word is in the word cache. If this is the case, it will 
# not check the database. If not in cache, it takes the word and adds it into our 
# table in the database. If it is already in the database, it will simply return the 
# word id. If it is not, it will be inserted and will be assigned a new word id.
#
#
    def word_id(self, word):
        # checks cache for a word match
        if word in self._word_id_cache:
            return self._word_id_cache[word]

        with con:
            cur = con.cursor() 

            # adds word into database, if already in db, ignore it
            cur.execute("INSERT OR IGNORE INTO lexicon (word) VALUES (?)", [word])

            # finds the corresponding word id
            cur.execute("SELECT id FROM lexicon WHERE word=:word", 
                    {"word": word})  
            con.commit()
            word_id = cur.fetchone()
    
        # convert tuple into int
        for w in word_id:
            pass
        
        # adds word and id into cache
        self._word_id_cache[word] = w

        return w
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This function is implemented to fill in our "document" table. It first
# checks to see if the url is in the word cache. If this is the case, it will 
# not check the database. If not in cache, it takes the url and adds it into our 
# table in the database. If it is already in the database, it will simply return the 
# doc id. If it is not, it will be inserted and will be assigned a new doc id.
#
#
    def document_id(self, url):
        # checks cache for a url match
        if url in self._doc_id_cache:
            return self._doc_id_cache[url]
        
        with con:
            cur = con.cursor() 

            # adds url into database, if already in db, ignore it
            cur.execute("INSERT OR IGNORE INTO document (url) VALUES(?)",[url])

            # finds the corresponding doc id
            cur.execute("SELECT id FROM document WHERE url=:url", 
                    {"url": url})  
            con.commit()
            doc_id = cur.fetchone()
    
        # convert tuple into int
        for d in doc_id:
            pass
        
        # adds url and id into cache
        self._doc_id_cache[url] = d

        return d
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""
            
        # compute the new url based on import 
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This function is implemented to fill in our "link" table. It will add all the links
# the current document is pointing out to i.e. outgoing links.
# 
#
    def add_link(self, from_doc_id, to_doc_id):

        with con:
            cur = con.cursor()   

            # add the link into database
            cur.execute("INSERT INTO link VALUES (?,?)",(from_doc_id,to_doc_id))
            con.commit()

        return
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This function is implemented to update info in the title column of our "document" table. 
# It will add the title of the current document into the database.
# 
#
    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        print "document title="+ repr(title_text)

        with con:
            cur = con.cursor()  

            # update the current documents title
            cur.execute("UPDATE document SET title = ? WHERE id= ?", (title_text, self._curr_doc_id) )
            # update the url_list
            cur.execute("INSERT INTO url_list VALUES (?,?,?,?)",(self._curr_doc_id,self._curr_url,title_text,0))

            con.commit()

        return
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_url, attr(elem,"href"))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))
        
        # add a link entry into the database from the current document to the
        # other document
        self.add_link(self._curr_doc_id, self.document_id(dest_url))


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This function is the core of finding relative searches. It will use both the word
# occurances in the document as well as their FONT FACTOR and will give it a word
# rank. The higher the word rank, the more relavent the keyword. After calculating
# this, it will store it into a separate table in our database called doc_id_#, 
# where # is the document id.
# 
#
    def _add_words_to_document(self):

        # Find number of occurances of each word and multiply
        # with the font factor to calculate the word_rank
        word_rank = {}
        for word_id,font_size in self._curr_words:
            if word_id not in word_rank:
                word_rank[word_id]=1*(font_size+1)
            else:
                word_rank[word_id]+=1*(font_size+1)

        # convert the dictionary into a tuple
        word_rank_tuple=word_rank.items()

        with con:
            cur = con.cursor()    

            # create a new table for individual doc_id_#
            cur.execute("DROP TABLE IF EXISTS doc_id_"+str(self._curr_doc_id))
            cur.execute("CREATE TABLE doc_id_" +str(self._curr_doc_id)+" (word_id INT,word_rank INT)")

            # fill the table with words found in the document as
            # well as the calculated word rank
            cur.executemany("INSERT INTO doc_id_"+str(self._curr_doc_id)+" VALUES(?,?)", word_rank_tuple)
            con.commit()

        print "    num words="+ str(len(self._curr_words))
        return
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _increase_font_factor(self, factor):
        """Increade/decrease the current font size."""
        def increase_it(elem):
            self._font_size += factor
        return increase_it
    
    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        words = WORD_SEPARATORS.split(elem.string.lower())
        for word in words:
            word = word.strip()
            if word in self._ignored_words:
                continue
            self._curr_words.append((self.word_id(word), self._font_size))
        
    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = [ ]
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))
            
            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come accross some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""
        class DummyTag(object):
            next = False
            name = ''
        
        class NextTag(object):
            def __init__(self, obj):
                self.next = obj
        
        tag = soup.html
        stack = [DummyTag(), soup.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)
                    
                    continue
                
                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)

    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""
        seen = set()

        while len(self._url_queue):

            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            doc_id = self.document_id(url)

            # we've already seen this document
            if doc_id in seen:
                continue

            seen.add(doc_id) # mark this document as haven't been visited
            
            socket = None
            try:
                socket = urllib2.urlopen(url, timeout=timeout)
                soup = BeautifulSoup(socket.read())

                self._curr_depth = depth_ + 1
                self._curr_url = url
                self._curr_doc_id = doc_id
                self._font_size = 0
                self._curr_words = [ ]
                self._index_document(soup)
                self._add_words_to_document()
                print "    url="+repr(self._curr_url)

            except Exception as e:
                print e
                pass
            finally:
                if socket:
                    socket.close()

if __name__ == "__main__":
    
    # create SQLite connection
    con = lite.connect('database.db')

    # create tables prior to startup
    with con:

        cur = con.cursor()    
        
        cur.execute("DROP TABLE IF EXISTS lexicon")
        cur.execute("CREATE TABLE lexicon(id INTEGER PRIMARY KEY ASC AUTOINCREMENT, word VARCHAR(100) UNIQUE NOT NULL)")

        cur.execute("DROP TABLE IF EXISTS document")
        cur.execute("CREATE TABLE document (id INTEGER PRIMARY KEY ASC AUTOINCREMENT,url VARCHAR(255) UNIQUE NOT NULL, title TEXT, page_rank REAL)")

        cur.execute("DROP TABLE IF EXISTS link")
        cur.execute("CREATE TABLE link (from_doc_id INT,to_doc_id INT)")

        cur.execute("DROP TABLE IF EXISTS url_list")
        cur.execute("CREATE TABLE url_list (doc_id INT, url TEXT, title TEXT, page_rank REAL)")

        con.commit()

    # call crawler with depth 1
    # this will populate our database with all relavent information
    bot = crawler(con, "urls.txt")
    bot.crawl(depth=1)

    
    # extract all links from database
    with con:    
    
        cur = con.cursor()    
        cur.execute("SELECT * FROM link")
        con.commit()
        links = cur.fetchall()

    # calculate the page rank links
    page_rank = page_rank(links)

    # convert page_rank dict into a list of tuples
    page_rank_tuple=page_rank.items()

    # update the document table in the database with page ranks
    with con:
        cur = con.cursor() 

        for x,y in page_rank_tuple:
            cur.execute("UPDATE document SET page_rank = ? WHERE id= ?", (float(y),int(x)))
            cur.execute("UPDATE url_list SET page_rank = ? WHERE doc_id= ?", (1000*float(y),int(x)))
        con.commit()

    # find max links    
    """
    with con:
        cur = con.cursor() 
        cur.execute("SELECT max(from_doc_id) FROM link")
        con.commit()
        max_link = cur.fetchone()
        print max_link
    """


import sqlite3 as lite
from spellCheck import *

# ModifyWord is to check the spelling error that might occur,the query will first search the word_id, if user encounters 
# typying error, the query will automatically modify the wrong word and search the database again. Then return the fixed word
# using newword.

Modifyword=0
newword='nothing'

def query_x(word):
    # create SQLite connection
    con = lite.connect('database.db')
    with con:
        global Modifyword
        Modifyword=0
        cur = con.cursor() 
        cur.execute("SELECT id FROM lexicon WHERE word=:word", 
                        {"word": word})  
        con.commit()
        word_id_copy = cur.fetchone()
        if(word_id_copy):
            for wr_id in word_id_copy:
                pass
        else:
            global Modifyword
            Modifyword=1
            word=correct(word)
            global newword
            newword=word
            cur = con.cursor() 
            cur.execute("SELECT id FROM lexicon WHERE word=:word", 
                            {"word": word})  
            con.commit()
            word_id_copy = cur.fetchone()
            if(word_id_copy):
                for wr_id in word_id_copy:
                    pass
            else:
                return []
        cur = con.cursor()    
        cur.execute("SELECT * FROM url_list")
        con.commit()
        links = cur.fetchall()    
        t=[]
        ##assuming its a list of tuples doc_id,link
        for doc_id,url,title,pagerank in links:
            cur = con.cursor()
            cur.execute("SELECT word_rank FROM doc_id_"+str(doc_id)+" WHERE word_id= :word_id",{"word_id": wr_id})  
            con.commit()
            font_rank = cur.fetchone()#rank based on count and font
            if(font_rank):
                for f_r in font_rank:
                    pass
                t.append( (title,url,f_r*pagerank) )
        return sorted(t, key=lambda x:-x[2])


def query(word):
    t = query_x(word)
    return t[0:30]


def check():
    return Modifyword
def get():
    return newword


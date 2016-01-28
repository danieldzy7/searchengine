from bottle import route, run, template, post, request, redirect, static_file
from query import* 
results='nothing'

@route("/")
@route("/search")
#Show the homepage
def search():
    f = open("homepage.html")
    html = "".join(f.readlines())
    return html

@post("/postsearch")
def postsearch():
    search = request.forms.get("search")
    results = query(search)
    Nextstep=check()
#Activate Spellchecking functionality:
#Nextstep will return a value whether it is 0 or 1. 
#If it's 0, that means the input spelling is correct and also the word_id is in database
#If it's 1, that means we have already modify the input word and search the modify_id in the database, and return the new result 
    if Nextstep==0:
        results.append(search)
        output = template('format_data', rows=results)
        return output
    if Nextstep==1:
        nword=get()
#If for both words the user input and the modify word that we fixed don't have word_id in database
#A "special" web page will be given to indicate the result is empty.  
        if not results:
            f = open("no.html")
   	    html = "".join(f.readlines())
            return html
#otherwise, we will return the result based on the fixed word.
        results.append(nword)
        output = template('format_data_after_spellCheck', rows=results)
        return output

@route("/false")
def false():
    return "False"

@route("/static/<filename>")
def static(filename):
    return static_file(filename, root="folder")

run(host="localhost", port=8080, debug=True)

%#template to generate a HTML table from a list of tuples (or list of lists, or tuple of tuples or ...)

<p><FONT SIZE=+4 COLOR="#F535AA">Snow Search Engine<link rel="stylesheet" href="static/result.css" type="text/css" /></FONT></p>
<table border="1">
<BODY background="static/12.jpg">
<script type="text/javascript" src="static/snowstorm.js"></script> 
%y=rows[-1]
<title> Snow Searched: {{y}} </title>
<p><i><FONT COLOR="#D00000">Did you mean :{{y}}</FONT></i></p>
%for x in rows[0:-1]:
  
  <a href = "{{x[1]}}"><FONT SIZE=+1 COLOR="#7A5DC7">{{x[0]}}</FONT></a>  <br> 
  <p> <a href ="{{x[1]}}"><FONT SIZE=+1 COLOR="#382D2C">{{x[1]}}</FONT></a><p> <br>  
  
%end
</table>



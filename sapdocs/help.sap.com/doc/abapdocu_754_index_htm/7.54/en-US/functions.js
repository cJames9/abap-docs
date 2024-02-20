function call_link(linked_file)
{
   if(parent.frames.length>0){
     parent.window.frames["basefrm"].window.location = linked_file;
     parent.window.frames["treeframe"].window.location = "abap_docu_tree.htm?file=" + linked_file;}
   else {
     window.location = linked_file;}
}
function call_search(linked_file)
{
   var textinput = window.query.value;
   while (textinput.indexOf("&")>-1){    textinput = textinput.replace("&","%26") }
   while (textinput.indexOf("+")>-1){    textinput = textinput.replace("+","%2B") }
   while (textinput.indexOf("=")>-1){    textinput = textinput.replace("=","%3D") }
   while (textinput.indexOf("?")>-1){    textinput = textinput.replace("?","%3F") }
   while (textinput.indexOf(" ")>-1){    textinput = textinput.replace(" ","%20") }
   while (textinput.indexOf('"')>-1){    textinput = textinput.replace('"',"%22") }
   while (textinput.indexOf("<")>-1){    textinput = textinput.replace("<","%3C") }
   while (textinput.indexOf(">")>-1){    textinput = textinput.replace(">","%3E") }
   if ( textinput.search( "\"" ) != -1 )
      { textinput = "\""; }
   linked_file = linked_file + "?query=" + textinput;
   if(parent.frames.length>0){
     parent.window.frames["basefrm"].window.location = linked_file;
     parent.window.frames["treeframe"].window.location = "abap_docu_tree.htm?file=" + linked_file;}
   else {
     window.location = linked_file;}
}
function getInput()
{
  var textinput = window.query.value;
  if ( event.keyCode == 13 ){
   call_search("search.htm"); }
}

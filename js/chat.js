var max_cookie = 4096;

function init_chat() {
    $(window).bind("resize", function () { 
	    adjust_panel($(".roompanel"));
	});

    $(".roomname").bind("click", onroomclick);
			     
    $(document).bind("click", function() { 
	    $(".roompanel").hide(); 
	    $(".roomname").removeClass("active"); 
	});
    $(".roompanel ul").bind("click", stop_propagation);
    $(".roompanel textarea").bind("click", stop_propagation);
			  
    $(".roompanel textarea").autoResize({extraSpace: 0, animateDuration: 100, limit: 100})
	.bind("keypress", onenter);
    $("#global").data("wid", "global");
    $("#users").data("wid", "users");

    $("#users div textarea").jsonSuggest(function(text, wildCard, caseSensitive, notCharacter, cb){
	    username_typeahead(text, cb);
	}, {"ajaxResults": true, minCharacters: 3, "onSelect": typeahead_select}).unbind("keypress");

    var rooms = JSON.parse($.cookie("we-chat-rooms"));
    if (rooms == null || rooms.length == 0) {
	rooms = $(".room").map(function() {return {"wid": $(this).data("wid")
						   , "title": $(this).find("div h3").text()}}).toArray();
	$.cookie("we-chat-rooms", JSON.stringify(rooms))
    }
    var messages = JSON.parse($.cookie("we-chat"), rooms);
    if (messages == null) {
	return;
    }
    messages.reverse();
    var newrooms = $(".room").map(function() {return {"wid": $(this).data("wid")
						      , "title": $(this).find("div h3").text()}}).toArray();
    var newmessages = [];
    var roomidxmap = {};
    for (var i = 0; i < newrooms.length; i += 1) {
	roomidxmap[i] = i;
    }
    for (var i = 0; i < messages.length; i += 1) {
	var m = messages[i];
	var idx = m.substr(0, m.indexOf("."));
	var rest = m.substr(m.indexOf(".") + 1);
	var sender = rest.substr(0, rest.indexOf(":"));
	var msg = rest.substr(rest.indexOf(":") + 1);
	var r = rooms[idx];
	if (r != null) {
	    var chatw = $(".room").filter(function(idx){return $(this).data("wid") == r.wid});
	    if (chatw.length == 0) {
		chatw = add_chat(r.wid, r.title, false);
		roomidxmap[idx] = newrooms.length;
		newrooms.push(r);
	    }
	    show_message({"wid": r.wid, "sender": sender, "message": msg}, chatw);
	    newmessages.push("" + roomidxmap[idx] + "." + sender + ":" + msg);
	}
    }
    newmessages.reverse();
    $.cookie("we-chat-rooms", JSON.stringify(newrooms));
    $.cookie("we-chat", JSON.stringify(newmessages));
}

function username_typeahead(text, callback) {
    $.getJSON("action.json?usernames/" + text, 
	      function(data){
		  callback(
			   $.map(data, 
				 function(e, i){return {"text": e};}));
		      });
}

function typeahead_select(selected) {
    $("#users div textarea").val("");
    var url = "action.json?chat/users/" + selected.text;
    $.post(url);
}

function adjust_panel(panel){ 
    var height = $(window).height();
    var max = height - 100;
    panel.css("max-height", max);
    panel.find("ul").css("max-height", max - 22);
}

function onenter(e){
    if (e.keyCode != "13"){
	return;
    }
    e.preventDefault();
    var text = $(this).val();
    if (!text.match(/\S+/g)) {
	return;
    }
    $(this).val("");
    var target = $(this).parent().parent().data("wid");
    var url = "action.json?chat/" + target + "/" + text;
    $.post(url);
}

function add_chat(wid, title, open){
    var room = $(".room").filter(function(idx){return $(this).data("wid") == wid});
    if (room.length > 0) {
	if (!room.find("div").is(":visible") && open) {
	    room.find("a").click();
	}
	return;
    }
    var ta = $("<textarea></textarea>").attr("rows", "1").bind("keypress", onenter)
	.bind("click", stop_propagation);
    var d = $("<div></div>").addClass("roompanel")
	.append($("<h3></h3>").html(title)
		.append($("<img src='images/close.png' alt='X'></img>")
			.bind("click", function(){remove_chat(wid)})))
	.append($("<ul></ul>").bind("click", stop_propagation))
	.append(ta);
    var link = $("<a></a>").addClass("roomname").bind("click", onroomclick).text(title);
    var res = $("<span></span>").data("wid", wid).addClass("room")
	.append(link)
	.append(d);
    $("#footpanel").append(res);
    adjust_panel(d);
    ta.autoResize({extraSpace: 0, animateDuration: 100, limit: 100});
    var rooms =  JSON.parse($.cookie("we-chat-rooms"));
    if (rooms == null) {
	rooms = [];
    }
    rooms.push({"wid": wid, "title": title});
    $.cookie("we-chat-rooms", JSON.stringify(rooms));
    if (open) {
	setTimeout(function(){link.click()}, 100);
    }
    return res;
}

function remove_chat(wid) {
    var rooms = JSON.parse($.cookie("we-chat-rooms"));
    var messages = JSON.parse($.cookie("we-chat"));
    var roomidx = 0;
    while (roomidx < rooms.length && rooms[roomidx].wid != wid) {
	roomidx += 1;
    }
    if (roomidx == rooms.length) {
	return;
    }
    var newmessages = [];
    var prefix = "" + roomidx + ".";
    messages.reverse();
    for (var i = 0; i < messages.length; i += 1) {
	if (messages[i].indexOf(prefix) != 0) {
	    newmessages.push(messages[i])
	}
    }
    $.cookie("we-chat", JSON.stringify(newmessages));
    $(".room").filter(function(idx){return $(this).data("wid") == wid}).remove();
}

function start_chat(nametxt) {
    var wid = nametxt;
    if (wid.indexOf("@") < 0) {
	wid += "@gmail.com";
    }
    add_chat(wid, nametxt, true);
}

function onuserclick() {
    start_chat($(this).text());
}

function stop_propagation(e) { 
    e.stopPropagation(); 
}
function onroomclick () {
    if($(this).next(".roompanel").is(":visible")){ 
	$(this).next(".roompanel").hide(); 
	$(".roomname").removeClass("active");
    } else { 
	$(".roompanel").hide(); 
	$(this).next(".roompanel").show(); 
	$(".roomname").removeClass("active"); 
	$(this).toggleClass("active"); 
	$(this).parent().find("div textarea").focus();
	var blinker = $(this).data("blink");
	if (blinker != null) {
	    window.clearInterval(blinker); 
	    $(this).data("blink", null);
	} 
    }
    return false; 
}
 

function anchor_blink(anchor, interval) {
    anchor.toggleClass("blink");
    window.setTimeout(function(){anchor.toggleClass("blink");}, interval);
}

// default handlers
function handle_chat_add(v) {
    add_chat(v.wid, v.title, true);
}

function show_message(v, room) {
    var wid = v.wid;
    var message = decodeURIComponent(v.message);
    var sender = v.sender;
    var res;
    if (sender == "own") {
	res = "<li class='own_message'>" + message + "</li>";
    } else if (sender == "sys") {
	res = "<li class='sys_message'>" + message + "</li>";
    } else if (sender != null && sender != "") {
	res = "<li>" + sender + ": " + message + "</li>";
    } else {
	res = "<li>" + message + "</li>";
    }
    room.find("div ul").append(res);
}

function handle_chat_message(v) {
    var room = $(".room").filter(function(idx){return $(this).data("wid") == v.wid});
    if (room.length == 0) {
	var wid = v.wid;
	room = add_chat(wid, wid.substring(0, wid.lastIndexOf("@")), true);
    }
    show_message(v, room);
    if (room.find(".roompanel").is(":not(:visible)") && v.sender != "own") {
	var anc = room.find(".roomname");
	if (anc.data("blink") != null) {
	    return;
	}
	anc.data("blink", window.setInterval(function(){anchor_blink(anc, 500)}, 1000))
    }
    var stored =  JSON.parse($.cookie("we-chat"));
    var rooms =  JSON.parse($.cookie("we-chat-rooms"));
    var i = 0;
    while (v.wid != rooms[i].wid) {
	i += 1;
    }
    if (stored == null) {
	stored = []
    }
    var sender = v.sender;
    if (sender == null) {
	sender = "";
    }
    stored.splice(0, 0, i + "." + sender + ":" + v.message);
    var tostore = JSON.stringify(stored);
    while (tostore.lendth > max_cookie) {
	stored.pop();
	tostore = JSON.stringify(stored);
    }
    $.cookie("we-chat", tostore);
}


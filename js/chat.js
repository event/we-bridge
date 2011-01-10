var max_cookie = 4096;

function init_chat() {
    $(window).resize(function () { 
	    adjust_panel($(".roompanel"));
	});

    $(".roomname").click(onroomclick);
			     
    $(document).click(function() { 
	    $(".roompanel").hide(); 
	    $(".roomname").removeClass("active"); 
	});
    $(".roompanel ul").click(stop_propagation);
    $(".roompanel textarea").click(stop_propagation);
			  
    $(".roompanel textarea").autoResize({extraSpace: 0, animateDuration: 100, limit: 100})
	.keypress(onenter);
    $("#global").data("wid", "global");
    $("#users").data("wid", "users");
    // $("#users div ul li").click(add_chat);
    var rooms = JSON.parse($.cookie("we-chat-rooms"));
    $.cookie("we-chat-rooms", "[]");
    var messages = JSON.parse($.cookie("we-chat"));
    if (messages == null) {
	return;
    }
    messages.reverse();
    for (m in messages) {
	var idx = m.substr(0, m.indexOf("."));
	var rest = m.substr(m.indexOf(".") + 1);
	var sender = rest.substr(0, rest.indexOf(":"));
	var msg = rest.substr(rest.indexOf(":") + 1);
	show_message({"wid": rooms[idx].wid, "sender": sender, "message": msg});
    }
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
    var ta = $("<textarea></textarea>").attr("rows", "1").keypress(onenter).click(stop_propagation);
    var d = $("<div></div>").addClass("roompanel")
	.append($("<h3></h3>").html(title + "<span>&mdash;</span>"))
	.append($("<ul></ul>").click(stop_propagation))
	.append(ta);
    var res = $("<span></span>").data("wid", wid).addClass("room")
	.append($("<a></a>").addClass("roomname").click(onroomclick).text(title))
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
	res.find("a").click();
    }
    return res;
}

function remove_chat(id) {
    $("#" + id).remove();
}

function stop_propagation(e) { 
    e.stopPropagation(); 
}
function onroomclick () {
    if($(this).next(".roompanel").is(":visible")){ 
	$(this).next(".roompanel").hide(); 
	$(".roomname").removeClass("active");
	var blinker = $(this).data("blink");
	if (blinker != null) {
	    window.clearInterval(blinker); 
	    $(this).data("blink", null);
	} 
    } else { 
	$(".roompanel").hide(); 
	$(this).next(".roompanel").show(); 
	$(".roomname").removeClass("active"); 
	$(this).toggleClass("active"); 
	$(this).parent().find("div textarea").focus();
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

function show_message(v) {
    var wid = v.wid;
    var message = decodeURIComponent(v.message);
    var sender = v.sender;
    var res;
    if (sender == "own") {
	res = "<li class='own_message'>" + message + "</li>";
    } else if (sender == "sys") {
	res = "<li class='sys_message'>" + message + "</li>";
    } else if (sender != null) {
	res = "<li>" + sender + ": " + message + "</li>";
    } else {
	res = "<li>" + message + "</li>";
    }
    var room = $(".room").filter(function(idx){return $(this).data("wid") == wid});
    if (room.length == 0) {
	room = add_chat(wid, wid.substring(0, wid.lastIndexOf("@")), true);
    }
    room.find("div ul").append(res);
}

function handle_chat_message(v) {
    show_message(v);
    var room = $(".room").filter(function(idx){return $(this).data("wid") == wid});
    if (room.find(".roompanel").is(":not(:visible)")) {
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
    stored.splice(0, 0, i + "." + v.sender + ":" + v.message);
    var tostore = JSON.stringify(stored);
    while (tostore.lendth > max_cookie) {
	stored.pop();
	tostore = JSON.stringify(stored);
    }
    $.cookie("we-chat", tostore);
}


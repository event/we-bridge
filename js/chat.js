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
    // $("#friends div ul li").click(add_chat);
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

function add_chat(wid, title){
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
    res.find("a").click();
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
    add_chat(v.wid, v.title);
}

function handle_chat_message(v) {
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
	room = add_chat(wid, wid.substring(0, wid.lastIndexOf("@")));
    }
    room.find("div ul").append(res);
    if (room.find(".roompanel").is(":not(:visible)")) {
	var anc = room.find(".roomname");
	if (anc.data("blink") != null) {
	    return;
	}
	anc.data("blink", window.setInterval(function(){anchor_blink(anc, 500)}, 1000))
    }
}


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
    var target = $(this).parent().parent().attr("id");
    var url = "action.json?chat/" + target + "/" + text;
    $.post(url);
}

function add_chat(id, title){
    var ta = $("<textarea></textarea>").attr("rows", "1").keypress(onenter).click(stop_propagation);
    var d = $("<div></div>").addClass("roompanel").attr("id", id)
	.append($("<h3></h3>").html(title + "<span>&mdash;</span>"))
	.append($("<ul></ul>").click(stop_propagation))
	.append(ta);

    $("#footpanel").append($("<span></span>").addClass("room")
			   .append($("<a></a>").addClass("roomname").click(openChat).text(title))
			   .append(d));
    adjust_panel(d);
    ta.autoResize({extraSpace: 0, animateDuration: 100, limit: 100});
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
    }
    return false; 
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
	res = "<li class='self_message'>" + message + "</li>";
    } else if (sender != null) {
	res = "<li>" + sender + ": " + message + "</li>";
    } else {
	res = "<li>" + message + "</li>";
    }
    
    $("#" + wid + " div ul").append(res);
}


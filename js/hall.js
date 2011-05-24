var positions = ["N", "S", "E", "W"];
var empty_sit = "<a href=table.html?{id}>take a sit</a>";

var update_handlers = new Array();
update_handlers["table.add"] = add_table;
update_handlers["table.remove"] = remove_table;
update_handlers["player.sit"] = add_player;
update_handlers["player.leave"] = remove_player;
update_handlers["chat.add"] = handle_chat_add;
update_handlers["chat.message"] = handle_chat_message;


function on_body_load() {
    $("body").ajaxError(ajaxErrorHandler);
    start_updator(update_handlers);
    window.setInterval(function(){$.post("action.json?ping");}, 2 * 60 * 1000);
    init_chat();
    init_users();
}

function show_usermenu(evt) {
    var img = $(evt.target);
    var popup = img.next(".umenu_popup");
    if (popup.is(":visible")) {
	popup.hide();
    } else {
	var imgoffset = img.offset();
	popup.css({"left": imgoffset.left + img.width()/2, "top": imgoffset.top + img.height + 1 });
	popup.show();
    }
}

function init_users() {
    $("td.user:not(:has(a))").append($("<img class=\"imageButton\" src=\"images/menu_arrow.png\"/>"))
	.append(function(i, html){
		var uname = html.substring(0, html.indexOf("<img"));
		if (uname.indexOf("@") < 0) {
		    uname += "@gmail.com";
		}
		var menu = $("<div class=\"umenu_popup\"><div><a href=\"userprofile.html?" 
			     + uname + "\">View Info</a>"
			     + "</div><div><a class=\"chstart\" href=\"javascript:;\">"
			     + "Send Message</a></div></div>").hide();
		return menu;
	    });
    $(".user .umenu_popup .chstart")
	.bind("click", function(evt){
		var popup = $(evt.target).parent().parent();
		var html = popup.parent().html();
		start_chat(html.substring(0, html.indexOf("<img")));
		popup.hide();
	    });
    $(".user .imageButton").bind("click", show_usermenu);
}

function empty_if_none(player, id, pos) {
    if (player == null) {
	return empty_sit.replace("{id}", id + "/" + pos);
    } else {
	return player;
    }
}

function add_table(v) {
    var id = v.tid;
    var kibcount = v.kibcount;
    if (kibcount == null) {
	kibcount = 0
    }
    $("#table_list").append("<tr id='table_" + id + "' class='table'>" 
			    + "<td class='user'>" + empty_if_none(v.N, id, "N") + "</td>" 
			    + "<td class='user'>" + empty_if_none(v.S, id, "S") + "</td>" 
			    + "<td class='user'>" + empty_if_none(v.E, id, "E") + "</td>" 
			    + "<td class='user'>" + empty_if_none(v.W, id, "W") + "</td>" 
			    + "<td class='user'><a href='table.html?" + id + "'>" 
			                  + kibcount + "</a></td></tr>");
}

function remove_table(v) {
    $("#table_" + v.tid).remove();
}

function add_player(v) {
    var id = v.tid;
    var name = v.name;
    var pos = v.position;
    if (pos == null) {
	$("#table_" + id + " td:eq(4) a").text(function(i,cnt){return parseInt(cnt) + 1});
    } else {
	$("#table_" + id + " td:eq(" + $.inArray(pos, positions) + ")").html(name);
    }
}

function remove_player(v) {
    var id = v.tid;
    var pos = v.position;	
    if (pos == null) {
	$("#table_" + id + " td:eq(4) a").text(function(i,cnt){return parseInt(cnt) - 1});
    } else {
	$("#table_" + id + " td:eq(" + $.inArray(pos, positions) + ")").html(empty_if_none(null, id, pos));
    }
}

function add_new_table() {
    window.location = "table.html?new/N";
}

function ajaxErrorHandler(event, xhr, opts, error) {
    // retry should be here for some requests
    window.alert("request failed");
}


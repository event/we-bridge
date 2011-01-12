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
			    + "<td class='player'>" + empty_if_none(v.N, id, "N") + "</td>" 
			    + "<td class='player'>" + empty_if_none(v.S, id, "S") + "</td>" 
			    + "<td class='player'>" + empty_if_none(v.E, id, "E") + "</td>" 
			    + "<td class='player'>" + empty_if_none(v.W, id, "W") + "</td>" 
			    + "<td class='player'><a href='table.html?" + id + "'>" 
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


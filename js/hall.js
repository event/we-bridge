var positions = ["N", "S", "E", "W"];
var empty_sit = "<a href=table.html?{id}>take a sit</a>";

var update_handlers = new Array();
update_handlers["table.add"] = add_table;
update_handlers["table.remove"] = remove_table;
update_handlers["player.sit"] = add_player;
update_handlers["player.leave"] = remove_player;

function on_body_load() {
    $("body").ajaxError(ajaxErrorHandler);
    start_updator(update_handlers);
}

function empty_if_none(player, id, pos) {
    if (player == null) {
	return empty_sit.replace("{id}", id + "/" + pos);
    } else {
	return player;
    }
}

function add_table(v) {
    var id = v.id;
    $("#table_list").append("<tr id='table_" + id + "' class='table'>" 
			    + "<td class='player'>" + empty_if_none(v.N, id, "N") + "</td>" 
			    + "<td class='player'>" + empty_if_none(v.S, id, "S") + "</td>" 
			    + "<td class='player'>" + empty_if_none(v.E, id, "E") + "</td>" 
			    + "<td class='player'>" + empty_if_none(v.W, id, "W") + "</td>" 
			    + "<td class='player'>" + v.kibcount + "</td></tr>");
}

function remove_table(v) {
    $("#table_" + data.value).remove();
}

function add_player() {
    var table_num = v.table + 1;
    var name = v.name;
    var pos = v.position;
    $("#table_list tr:eq(" + table_num + ") td:eq(" + $.inArray(pos, positions) + ")").html(name);
}

function remove_player() {
    var table_num = v.table + 1;
    var pos = v.position;	
    var table_id = $("#table_list tr:eq(" + table_num + ")").data("table_id");
    $("#table_list tr:eq(" + table_num + ") td:eq(" + $.inArray(pos, positions) + ")")
	.html(empty_sit.replace("{id}", table_id + "/" + pos));
}

function add_new_table() {
    window.location = "table.html?new/N";
}

function ajaxErrorHandler(event, xhr, opts, error) {
    // retry should be here for some requests
    window.alert("request failed");
}


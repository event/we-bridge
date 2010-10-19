var positions = ["N", "S", "E", "W"];
var empty_sit = "<a>take a sit</a>";

function on_body_load() {
    $("body").ajaxError(ajaxErrorHandler);
    $(document.documentElement).keypress(updator)
}

function updator(event) {
    if (event.charCode == 32) {
	get_json();
    }
}

function get_json() {
    $.getJSON("update.json", function(data){$.each(data, process_update);});
}

function process_update(i, data) {
    if (data.type == "table.add"){
	$("#table_list").append("<tr><td></td><td></td><td></td><td></td></tr>");
	$("#table_list tr:last").addClass("table");
	$("#table_list tr:last td").addClass("player");
	$("#table_list tr:last td").html(empty_sit);
    } else if (data.type == "table.remove") {
	$("#table_list tr:eq(" + (data.value + 1) + ")").remove();
    } else if (data.type == "player.sit") {
	var v = data.value;
	var table_num = v.table + 1;
	var name = v.name;
	var pos = v.position;
	$("#table_list tr:eq(" + table_num + ") td:eq(" + $.inArray(pos, positions) + ")").html(name);
    } else if (data.type == "player.leave") {
	var v = data.value;
	var table_num = v.table + 1;
	var pos = v.position;
	$("#table_list tr:eq(" + table_num + ") td:eq(" + $.inArray(pos, positions) + ")").html(empty_sit);
    } else if (data.type == "text") {
	window.alert("text message is not supported yet!");
    }
}

function ajaxErrorHandler(event, xhr, opts, error) {
    // retry should be here for some requests
    window.alert("request failed");
}


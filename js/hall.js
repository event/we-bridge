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
    } else if (data.type == "table.remove") {
    } else if (data.type == "player.sit") {
    } else if (data.type == "player.leave") {
    } else if (data.type == "text") {
	window.alert("text message is not supported yet!");
    }
}

function ajaxErrorHandler(event, xhr, opts, error) {
    // retry should be here for some requests
    window.alert("request failed");
}


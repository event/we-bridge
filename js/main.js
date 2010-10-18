var suits = ["spades", "hearts", "diamonds", "clubs"];
var players = ["own", "left", "part", "right"];
var suit_image_template = "<img src='../images/{suit}.gif' alt='{alt_suit}'/>";
var update_cnt = 1000;

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
    if (data.type == "lead"){
	var v = data.value;
	var allowed = v.allowed;
	if (allowed == null) {
	    allowed = 'any';
	}
	process_lead(v.player, v.suit, v.rank, allowed);
    } else if (data.type == "bid") {
	window.alert("bid is not supported yet!");
    } else if (data.type == "text") {
	window.alert("text message is not supported yet!");
    } else if (data.type == "hand") {
	var v = data.value;
	var player = v.player;
	var suits = v.suits;
	$.each(suits, function(i, suit){load_suit(player, suit)});
	$(".card_" + player).bind("click", player, do_lead)
	    
    } else if (data.type == "claim") {
	window.alert("claim is not supported yet!");
    }
}

function load_suit(player, suit) {
    var s = suit.suit;
    var cards = suit.cards;
    var divid = "#" + player + "_" + s;
    var card_str = cards.replace(/([2-9JQKA]|10)/g, "<div"
				 + " class='card card_" + player + " card_" + player + "_" + s + "'"
				 + " id='" + s + "_$1'>$1</div>");
    $(divid).html(card_str);
}

function process_lead(player, suit, rank, allowed) {
    var card_div_id = "#" + suit + "_" + rank;
    $(card_div_id).detach();
    var lead_div_id = "#" + player + "_lead";
    $(lead_div_id).html(img_by_suit(suit) + rank);
    var np = next_player(player);
    var np_class = ".card_" + np;
    $(".card").unbind('click');
    $(".card").addClass("default_cursor");
    if (allowed == 'any') {
	$(np_class).bind("click", np, do_lead);
	$(np_class).removeClass("default_cursor");
    } else {
	for (var i = 0; i < allowed.length; i += 1) {
	    var np_suit_class = np_class + "_" + allowed[i];
	    $(np_suit_class).bind("click", np, do_lead);
	    $(np_suit_class).removeClass("default_cursor");
	}
    }
}

function next_player(player) {
    var idx = $.inArray(player, players);
    if (idx == 3) {
	return players[0];
    } else {
	return players[idx + 1];
    }
}

function do_lead(event) {
    // process_lead(player, suit, rank);
    var player = event.data;
    var splitted_id = event.target.id.split("_");
    var suit = splitted_id[0];
    var rank = splitted_id[1];
    var url = "action.json?lead/" + player + "/" + suit + "/" + rank;
    $.post(url);
}


function ajaxErrorHandler(event, xhr, opts, error) {
    // retry should be here for some requests
    window.alert("request failed");
}

function img_by_suit(suit) {
    if (suits.indexOf(suit) >= 0) {
	var c = suit.charAt(0);
	return suit_image_template.replace("{suit}", c).replace("{alt_suit}", c.toUpperCase());
    }
    
}
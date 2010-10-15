var suits = ["spades", "hearts", "diamonds", "clubs"];
var suit_image_template = "<img src='../images/{suit}.gif' alt='{alt_suit}'/>";
var update_cnt = 5;

function on_body_load() {
    $("body").ajaxError(ajaxErrorHandler);
    window.setTimeout(get_json, 1000);
}

function get_json() {
    if (update_cnt <= 0) {
	return;
    }
    $.getJSON("update.json", function(data){$.each(data, process_update);window.setTimeout(get_json, 1000);});
    update_cnt -= 1;
}

function process_update(i, data) {
    if (data.type == "lead"){
	window.alert("lead is not supported yet!");
    } else if (data.type == "bid") {
	window.alert("bid is not supported yet!");
    } else if (data.type == "text") {
	window.alert("text message is not supported yet!");
    } else if (data.type == "hand") {
	var v = data.value;
	var player = v.player;
	var suits = v.suits;
	$.each(suits, function(i, suit){load_suit(player, suit)})
    } else if (data.type == "claim") {
	window.alert("claim is not supported yet!");
    }
}

function load_suit(player, suit) {
    var s = suit.suit;
    var cards = suit.cards;
    var divid = "#" + player + "_" + s;
    var card_str = cards.replace(/([2-9JQKA]|10)/g, "<div class='card' id='" + s + "_$1'onclick=\"do_lead('" 
				 + player + "', '"+ s + "', '$1')\">$1</div>");
    $(divid).html(card_str);
}

function do_lead(player, suit, rank) {
    var card_div_id = "#" + suit + "_" + rank;
    $(card_div_id).detach();
    var lead_div_id = "#" + player + "_lead";
    $(lead_div_id).html(img_by_suit(suit) + rank);
}

function ajaxErrorHandler(event, xhr, opts, error) {
    window.alert("request failed");
}

function img_by_suit(suit) {
    if (suits.indexOf(suit) >= 0) {
	var c = suit.charAt(0);
	return suit_image_template.replace("{suit}", c).replace("{alt_suit}", c.toUpperCase());
    }
    
}
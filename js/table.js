var suits = ["spades", "hearts", "diamonds", "clubs"];
var players = ["own", "left", "part", "right"];
var suit_image_template = "<img src='images/{suit}.gif' alt='{alt_suit}'/>";
var update_cnt = 1000;
var pass_dbl_rdbl = ["pass", "dbl", "rdbl"];

var current_bidder;


var update_handlers = new Array();
update_handlers["move"] = process_lead;
update_handlers["bid"] = process_bid;
update_handlers["hand"] = process_hand;
update_handlers["start.bidding"] = kick_bidding;

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
    handler = update_handlers[data.type];
    if (handler == undefined) {
	window.alert("action " + data.type + " is not yet supported!");
    } else {
	handler(data.value);
    }
}


function process_hand(v) {
    var player = v.player;
    var suits = v.suits;
    $.each(suits, function(i, suit){load_suit(player, suit)});
    $(".card_" + player).bind("click", player, do_lead)
}

function load_suit(player, suit) {
    var s = suit.suit;
    var cards = suit.cards;
    var divid = "#" + player + "_" + s;
    var card_str = cards.replace(/([2-9JQKA]|10)/g, "<div"
				 + " class='clickable card card_" + player + " card_" + player + "_" + s + "'"
				 + " id='" + s + "_$1'>$1</div>");
    $(divid).html(card_str);
}

function process_bid(v) {
	var side = v.side;
	var bid = v.bid;
	var bid_html;
	var idx = $.inArray(bid, pass_dbl_rdbl);
	if (idx >= 0) {
	    bid_html = bid;
	    if (idx == 1) {
		prohibit_bid("#bid_dbl");	
		allow_bid("#bid_rdbl");
	    } else if (idx == 2) {
		prohibit_bid("#bid_dbl");
		prohibit_bid("#bid_rdbl");
	    }
	} else {
	    var r = bid[0];
	    var s = bid[1];
	    if (s != 'Z') {
		var img = suit_image_template.replace("{suit}", s.toLowerCase()).replace("{alt_suit}", s);
		bid_html = r + img;
	    } else {
		bid_html = r + "NT";
	    }

	    allow_bid("#bid_dbl");
	    disallow_lower_bids(parseInt(r), s);
	}
	$("#bidding_area tr:last td:eq(" + side + ")").html(bid_html);
	if (side == 3) {
	    $("#bidding_area").append("<tr class='bidding_row'><td></td><td></td><td></td><td></td></tr>")
	}
}

function prohibit_bid(bid_selector) {
    $(bid_selector).unbind("click").removeClass("clickable").addClass("prohibited_bid");
}

function allow_bid(bid_selector) {
    $(bid_selector).bind("click", do_bid).addClass("clickable").removeClass("prohibited_bid");
}

function disallow_lower_bids(r, s) {
    var bid_id = "bid_" + r + s;
    var alowed_bids = $(".clickable.bidbox_bid");
    var filtered = alowed_bids.filter(function(index){return this.id < bid_id});
    filtered.unbind("click").removeClass("clickable").addClass("prohibited_bid");
}

function process_lead(v) {
    var v = data.value;
    var player = v.player;
    var suit = v.suit;
    var rank = v.rank;
    var allowed = v.allowed;
    if (allowed == null) {
	allowed = "any";
    }
    var card_div_id = "#" + suit + "_" + rank;
    $(card_div_id).detach();
    var lead_div_id = "#" + player + "_lead";
    $(lead_div_id).html(img_by_suit(suit) + rank);
    var np = next_player(player);
    var np_class = ".card_" + np;
    $(".card").unbind("click").removeClass("clickable");
    if (allowed == 'any') {
	$(np_class).bind("click", np, do_lead).addClass("clickable");
    } else {
	var np_suit_class = np_class + "_" + allowed;
	$(np_suit_class).bind("click", np, do_lead).addClass("clickable");
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
    var player = event.data;
    var splitted_id = event.target.id.split("_");
    var suit = splitted_id[0];
    var rank = splitted_id[1];
    var url = "action.json?move/" + player + "/" + suit + "/" + rank;
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

function kick_bidding() {
    $("#lead_area").addClass("hidden");
    $(".bidbox_bid,.bidbox_pass,.bidbox_dbl,.bidbox_rdbl").bind("click", do_bid).addClass("clickable");
    current_bidder = 0;
}

function do_bid(event) {
    var splitted_id = event.currentTarget.id.split("_");
    var bid = splitted_id[1];
    
    var url = "action.json?bid/" + players[current_bidder] + "/" + bid;
    current_bidder = (current_bidder + 1) % 4;
    $.post(url);
}
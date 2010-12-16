var player_positions = ["part", "right", "own", "left"];
var sides = ["N", "E", "S", "W"];
var suit_image_template = "<img src='images/{suit}.png' alt='{alt_suit}'/>";
var big_suit_image_template = "<img src='images/{suit}big.png' alt='{alt_suit}'/>";
var pass_dbl_rdbl = ["pass", "dbl", "rdbl"];

var lead_count;
var my_side;
var tid;

var update_handlers = new Array();
update_handlers["move"] = process_move;
update_handlers["bid"] = process_bid;
update_handlers["hand"] = process_hand;
update_handlers["user"] = user_update;
update_handlers["start.bidding"] = kick_bidding;
update_handlers["start.play"] = kick_play;
update_handlers["end.play"] = end_play;

function on_body_load() {
    $("body").ajaxError(ajaxErrorHandler);
    parse_params();
    start_updator(update_handlers);
}

function parse_params() {
    params = location.search.split("/");
    tid = params[0].substr(1);
    if (params.length > 1) {
	my_side = $.inArray(params[1], sides);
    }
}

function ajaxErrorHandler(event, xhr, opts, error) {
    // retry should be here for some requests
    window.alert("request failed");
}

function process_hand(v) {
    var player = v.player;
    var cards = v.cards;
    load_hand(player, cards);
}

function card_sort(c1, c2) {
    if (Math.floor(c1/13) + Math.floor(c2/13) == 1) { /* show clubs before diamonds */
	return c1 - c2;
    } else {
	return c2 - c1;
    }
}

function create_card(player, card) {
    var s = document.createElement("span");
    $(s).addClass("card card_" + player + " suit_" + Math.floor(card/13));
    $(s).attr("id", "card_" + card);
    var bg = "url(images/cards.png) " + (card * -71) +  "px 0";
    return $(s).css("background", bg);
}

function load_hand(player, cards) {
    var pos = $.inArray(player, player_positions);
    cards.sort(card_sort);
    var h = $("#" + player + "_hand");
    $.each(cards, 
	   function(idx, value) {
	       h.append(create_card(player, value).css({"z-index": idx + 1, "left": idx * 6 + "%"}));
	   });
}

function process_bid(v) {
    var side = v.side;
    var bid = v.bid;
    var dbl_rdbl_allowed = v.dbl_mode;
    var bid_html;
    var idx = $.inArray(bid, pass_dbl_rdbl);
    if (idx == -1) {
	var r = bid[0];
	var s = bid[1];
	if (s != 'Z') {
	    var img = suit_image_template.replace("{suit}", s.toLowerCase()).replace("{alt_suit}", s);
	    bid_html = r + img;
	} else {
	    bid_html = r + "NT";
	}
	
	disallow_lower_bids(parseInt(r), s);
    } else {
	bid_html = bid;
    }
    $("#bidding_area tr:last td:eq(" + side + ")").html(bid_html);
    if (side == 3) {
	$("#bidding_area").append("<tr class='bidding_row'><td></td><td></td><td></td><td></td></tr>");
    }
    if ((side + 1) % 4 == my_side) {
	if (dbl_rdbl_allowed == "dbl") {
	    allow_bid("#bid_dbl");
	} else if (dbl_rdbl_allowed == "rdbl") {
	    allow_bid("#bid_rdbl");
	}
	allow_bid(".bidbox_pass");
	$(".bidbox_bid:not(.prohibited_bid)").bind("click", do_bid).addClass("clickable");
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
    var allowed_bids = $(".bidbox_bid:not(.prohibited_bid)");
    var filtered = allowed_bids.filter(function(index){return this.id <= bid_id});
    filtered.addClass("prohibited_bid");
}

function process_move(v) {
    if (lead_count % 4 == 0) {
	for (var i = 0; i < 4; i += 1) {
	    $("#" + player_positions[i] + "_last span").remove();
	    $("#" + player_positions[i] + "_last")
		.append($("#" + player_positions[i] + "_lead span").detach());
   	}
    }

    var player = v.player;
    var card = v.card;
    var allowed = v.allowed;
    var trick = v.trick;
    var card_div_id = "#card_" + card;
    var lead_div_id = "#" + player + "_lead";
    
    $(lead_div_id).append(create_card(player, card).css({"z-index": lead_count, "left": 0}));
    lead_count += 1;
    if (trick != null) {
	if (trick == "-") {
	    $("#their_tricks").text(trick_inc);
	} else {
	    $("#our_tricks").text(trick_inc);
	}
    }
    if (allowed == null) {
	return;
    }
    var np;
    if (v.next != null) {
	np = v.next;
    } else {
	np = next_player(player);
    }
    prohibit_cards(".card");
    if (allowed == "any") {
	allow_cards(".card_" + np, np);
    } else {
	var np_suit_class = ".card_" + np + ".suit_" + allowed;
	allow_cards(np_suit_class, np);
    }
}

function prohibit_cards(selector) {
    return $(selector).unbind("click dblclick").removeClass("clickable");
}

function allow_cards(selector, player) {
    return $(selector).bind("click", player, highlight_for_move)
	.bind("dblclick", player, do_move).addClass("clickable");
}

function next_player(player) {
    var idx = $.inArray(player, player_positions);
    if (idx == 3) {
	return player_positions[0];
    } else {
	return player_positions[idx + 1];
    }
}

function do_move(event) {
    var player = event.data;
    var splitted_id = event.target.id.split("_");
    var number = splitted_id[1];
    var url = "action.json?move/" + tid + "/" + player + "/" + number;
    $.post(url);
    prohibit_cards(".card_own");
    $(event.target).remove();
}


function img_by_suit(suit) {
    var c = suit.charAt(0);
    return suit_image_template.replace("{suit}", c.toLowerCase()).replace("{alt_suit}", c.toUpperCase());
}

function kick_bidding(v) {
    prohibit_bid(".bidbox_pass,.bidbox_dbl,.bidbox_rdbl");
    var vuln_side = (my_side % 2) + 1
    if (v.vuln & vuln_side) {
	$(".vuln_we").addClass("vulnerable");
    }

    if (v.vuln & vuln_side) {
	$(".vuln_they").addClass("vulnerable");
    }

    side = sides[v.dealer];
    $("#dealer_" + side).addClass("dealer");
    if (my_side == v.dealer) {
    	$(".bidbox_bid").bind("click", do_bid).addClass("clickable");
	allow_bid(".bidbox_pass");
    }
}

function kick_play(v) {
    var contract = v.contract;
    var lead_maker = v.lead;
    lead_count = 0;
    $("#bidbox").css("display", "none").after($("#bidding_area").detach());
    $("#bidbox_cell").css("text-align", "center");

    $("#lead_area").removeClass("hidden");
    if (lead_maker == my_side) {
	allow_cards(".card_own", "own");
	/* indicate my lead somehow */
    }
    var csuit = contract[1];
    var cntrct_html;
    if (csuit != "Z") {
	cntrct_html = contract[0] + 
	    big_suit_image_template.replace("{suit}", csuit.toLowerCase())
	    .replace("{alt_suit}", csuit.toUpperCase());;
    } else {
	cntrct_html = contract[0] + "NT";
    }
    $("#contract").html(cntrct_html + contract.substr(2, 2));
}

function highlight_for_move(event) {
    var splitted_id = event.target.id.split("_");
    var number = splitted_id[1];
    allow_cards(".highlighted", event.data).removeClass("highlighted");
    $("#card_" + number).addClass("highlighted").bind("click", event.data, do_move);    
}

function do_bid(event) {
    var splitted_id = event.currentTarget.id.split("_");
    var bid = splitted_id[1];
    $(".bidbox_bid:not(.prohibited_bid)").unbind("click").removeClass("clickable");
    prohibit_bid(".bidbox_pass,.bidbox_dbl,.bidbox_rdbl");
    var url = "action.json?bid/" + tid + "/" + my_side + "/" + bid;
    $.post(url);
}

function trick_inc(i, s) {
    if (s.length == 0) {
	return 1;
    } else {
	return parseInt(s) + 1;
    }
}


function end_play(v) {
    $(".vuln_we,.vuln_they").removeClass("vulnerable");
    $("#dealer_N,#dealer_E,#dealer_S,#dealer_W").removeClass("dealer");
    $("#bidding_area").removeClass("hidden");
    $("#bidbox").css("display", "inline-block");
    $("#bidbox_cell").css("text-align", "right");
    $("#lead_area").addClass("hidden");
    $("#contract,.tricks").html("");
    $("#bidding_area tr:gt(1)").remove();
    $("#bidding_area tr:gt(0) td").text("");
    $(".bidbox_bid,.bidbox_pass,.bidbox_dbl,.bidbox_rdbl")
	.unbind("click").removeClass("prohibited_bid clickable");
    $(".lead").text("");
    $("#lead_area").before($("#bidding_area").detach());
    var contract = v.contract;
    var decl = v.declearer;
    var points = v.points;
    var tricks = v.tricks;
    var url = v.protocol_url;
    var sign = "";
    if (points > 0) {
	sign = "+";
    }
    var contract_html;
    var r = contract[0];
    var s = contract[1];
    if (s != 'Z') {
	var img = suit_image_template.replace("{suit}", s.toLowerCase()).replace("{alt_suit}", s);
	contract_html = r + img;
    } else {
	contract_html = r + "NT";
    }
    contract_html += contract.substr(2, 2);
    $("#popup_res").html("<a href='" + url + "' target='_blank'>" +  tricks 
			 + " tricks, " + sign + points + "</a>");
    $("#popup_contract").html(contract_html + " by " + decl);
    $(".popup").bPopup();
	
}

function user_update(v) {
    var pos = v.position;
    var name = v.name;
    $("#" + pos + "_user").text(name);
}
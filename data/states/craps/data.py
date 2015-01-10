
from .bet import Bet

POINT_CHIP_LOC = {
    '0':(100,25), #off position
    '4':(320,25),
    '5':(430,25),
    '6':(540,25),
    '8':(650,25),
    '9':(760,25),
    '10':(870,25),
}

ALWAYS = 'always'
ON_POINT = 'on_point'
OFF_POINT = 'off_point'

ALL_ROLLS = list(range(2,13))
BETS = {

    #name: Bet(highlighter_size, highlighter_topleft, is_bettable, display_name, {payoff}, 
    #        extra highlighter points, extra pos, extra size)

    'come'          :Bet((652,120),(178,252), ON_POINT, 'Come',            {'1/1':ALL_ROLLS}),
    'field'         :Bet((542,117),(288,373), ALWAYS, 'Field',             {'1/1':[3,4,9,10,11], '2/1':[2,12]}, 
                        [[(0,0), (109,0), (109,121)]], (180,372), (110,120)),
    'dont_pass'     :Bet((542,65),(288,493), OFF_POINT, 'Dont\'t Pass',    {'1/1':ALL_ROLLS}),
    'pass'          :Bet((662,65),(170,570), OFF_POINT, 'Pass',            {'1/1':ALL_ROLLS}),
    'dont_pass_odds':Bet((331,65),(502,645), ON_POINT, 'Dont\'t Pass Odds',{'2/1':ALL_ROLLS}),
    'pass_odds'     :Bet((331,65),(170,645), ON_POINT, 'Pass Odds',        {'2/1':ALL_ROLLS}),
    'dont_come'     :Bet((100,190),(180,53), ON_POINT, 'Dont\'t Come',     {'1/1':ALL_ROLLS}),
    'any_seven'     :Bet((388,45),(964,295), ALWAYS, 'Any Seven',          {'5/1':ALL_ROLLS}),
    'hard_6'        :Bet((194,80),(964,342), ALWAYS, 'Hard Six',           {'10/1':ALL_ROLLS}),
    'hard_10'       :Bet((194,80),(1161,342), ALWAYS, 'Hard Ten',          {'8/1':ALL_ROLLS}),
    'hard_4'        :Bet((194,80),(1161,431), ALWAYS, 'Hard Four',         {'8/1':ALL_ROLLS}),
    'hard_8'        :Bet((194,80),(965,431), ALWAYS, 'Hard Eight',         {'10/1':ALL_ROLLS}),
    '11_craps'      :Bet((194,80),(965,603), ALWAYS, 'Horn 11 Craps',      {'16/1':ALL_ROLLS}),
    '3_craps'       :Bet((194,80),(1161,603), ALWAYS, 'Horn 3 Craps',      {'16/1':ALL_ROLLS}),
    '2_craps'       :Bet((194,80),(965,517), ALWAYS, 'Horn 2 Craps',       {'31/1':ALL_ROLLS}),
    '12_craps'      :Bet((194,80),(1161,517), ALWAYS, 'Horn 12 Craps',     {'31/1':ALL_ROLLS}),
    'any_craps'     :Bet((388,45),(964,689), ALWAYS, 'Any Craps',          {'8/1':ALL_ROLLS}),
    'big 6'         :Bet((67,125),(113,371), ALWAYS, 'Big 6',              {'1/1':ALL_ROLLS},
                        [[(67,0), (117,60), (65,121)], [(0,124),(65,121),(16,175)]], (113,371), (120,200)),
    'big 8'         :Bet((105,67),(179,497), ALWAYS, 'Big 8',              {'1/1':ALL_ROLLS},
                        [[(120,10), (178,76), (60,77)], [(18,124),(65,77),(66,145)]], (113,420), (200,150)),
    'place_lose_4'  :Bet((106,15),(288,53), ON_POINT, 'Place Against 4',   {'5/11':ALL_ROLLS}),
    'lay_4'         :Bet((106,15),(288,75), ON_POINT, 'Lay 4',             {'1/1':ALL_ROLLS}),
    'buy_4'         :Bet((106,15),(288,206), ON_POINT, 'Buy 4',            {'1/1':ALL_ROLLS}),
    'place_win_4'   :Bet((106,15),(288,229), ON_POINT, 'Place 4 to Win',   {'9/5':ALL_ROLLS}),
    'place_lose_5'  :Bet((106,15),(396,53), ON_POINT, 'Place Against 5',   {'4/6':ALL_ROLLS}),
    'lay_5'         :Bet((106,15),(396,75), ON_POINT, 'Lay 5',             {'1/1':ALL_ROLLS}),
    'buy_5'         :Bet((106,15),(396,206), ON_POINT, 'Buy 5',            {'1/1':ALL_ROLLS}),
    'place_win_5'   :Bet((106,15),(396,229), ON_POINT, 'Place 5 to Win',   {'7/6':ALL_ROLLS}),
    'place_lose_6'  :Bet((106,15),(506,53), ON_POINT, 'Place Against 6',   {'4/6':ALL_ROLLS}),
    'lay_6'         :Bet((106,15),(506,75), ON_POINT, 'Lay 6',             {'1/1':ALL_ROLLS}),
    'buy_6'         :Bet((106,15),(506,206), ON_POINT, 'Buy 6',            {'1/1':ALL_ROLLS}),
    'place_win_6'   :Bet((106,15),(506,229), ON_POINT, 'Place 6 to Win',   {'7/6':ALL_ROLLS}),
    'place_lose_8'  :Bet((106,15),(615,53), ON_POINT, 'Place Against 8',   {'4/6':ALL_ROLLS}),
    'lay_8'         :Bet((106,15),(615,75), ON_POINT, 'Lay 8',             {'1/1':ALL_ROLLS}),
    'buy_8'         :Bet((106,15),(615,206), ON_POINT, 'Buy 8',            {'1/1':ALL_ROLLS}),
    'place_win_8'   :Bet((106,15),(615,229), ON_POINT, 'Place 8 to Win',   {'7/6':ALL_ROLLS}),
    'place_lose_9'  :Bet((106,15),(725,53), ON_POINT, 'Place Against 9',   {'5/8':ALL_ROLLS}),
    'lay_9'         :Bet((106,15),(725,75), ON_POINT, 'Lay 9',             {'1/1':ALL_ROLLS}),
    'buy_9'         :Bet((106,15),(725,206), ON_POINT, 'Buy 9',            {'1/1':ALL_ROLLS}),
    'place_win_9'   :Bet((106,15),(725,229), ON_POINT, 'Place 9 to Win',   {'7/5':ALL_ROLLS}),
    'place_lose_10' :Bet((106,15),(834,53), ON_POINT, 'Place Against 10',  {'5/11':ALL_ROLLS}),
    'lay_10'        :Bet((106,15),(834,75), ON_POINT, 'Lay 10',            {'1/1':ALL_ROLLS}),
    'buy_10'        :Bet((106,15),(834,206), ON_POINT, 'Buy 10',           {'1/1':ALL_ROLLS}),
    'place_win_10'  :Bet((106,15),(834,229), ON_POINT, 'Place 10 to Win',  {'9/5':ALL_ROLLS}),
    'CE_eleven'     :Bet((30,30),(876,390), ALWAYS, 'Yo Eleven',           {'7/1':ALL_ROLLS}),
    'CE_craps'      :Bet((30,30),(920,401), ALWAYS, 'Any Craps',           {'7/1':ALL_ROLLS}),
}

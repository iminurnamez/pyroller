import random
import pygame as pg
from ...components.labels import Label, MultiLineLabel, NeonButton, ButtonGroup
from ... import tools, prepare

#http://casinogamblingtips.info/tag/pay-table
PAYTABLE = [
    [(0, 0.00)], #0
    [(1, 3.00)], #1
    [(2, 12.00)], #2
    [(2, 1.00), (3, 40.00)], #3
    [(2, 1.00), (3, 2.00), (4, 120.00)], #4
    [(3, 1.00), (4, 18.00), (5, 800.00)], #5
    [(3, 1.00), (4, 3.00), (5, 80.00), (6, 1500.00)], #6
    [(4, 1.00), (5, 18.00), (6, 360.00), (7, 5000.00)], #7
    [(5, 10.00), (6, 75.00), (7, 1000.00), (8, 15000.00)], #8
    [(5, 4.00), (6, 35.00), (7, 250.00), (8, 3000.00), (9, 20000.00)], #9
    [(5, 2.00), (6, 15.00), (7, 100.00), (8, 1500.00), (9, 8000.00), (10, 25000.00)], #10
]

def pick_numbers(spot):
    numbers = []
    while len(numbers) < spot:
        number = random.randint(0, 79)
        if number not in numbers:
            numbers.append(number)
    return numbers

class Clear(object):
    def __init__(self, card):
        self.rect = pg.Rect(0, 160, 150, 75)
        self.font = prepare.FONTS["Saniretro"]
        self.label = Label(self.font, 32, 'CLEAR', 'gold3', {'center':(0,0)})
        self.label.rect.center = self.rect.center
        self.color = '#181818'
        self.card = card

    def update(self):
        self.card.ready_play(clear_all=True)

    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)
        self.label.draw(surface)

class PayTable(object):
    '''Paytable readout for desired spot count'''
    def __init__(self, card):
        self.rect = pg.Rect(1000, 100, 340, 554)
        self.font = prepare.FONTS["Saniretro"]
        self.color = '#181818'
        self.card = card

        self.header_labels = []
        self.header_labels.extend([Label(self.font, 32, 'HIT', 'white', {'center':(1024,124)})])
        self.header_labels.extend([Label(self.font, 32, 'WIN', 'white', {'center':(1200,124)})])

        self.pay_labels = []

    def update(self, spot):
        self.pay_labels = []
        row = PAYTABLE[spot]
        hit_x = 1024
        win_x = 1200
        row_y = 124+32
        for entry in row:
            hit, win = entry
            self.pay_labels.extend([Label(self.font, 32, str(hit), 'white', {'center':(hit_x, row_y)})])
            self.pay_labels.extend([Label(self.font, 32, str(win), 'white', {'center':(win_x, row_y)})])
            row_y+=32


    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)

        for label in self.header_labels:
            label.draw(surface)

        for label in self.pay_labels:
            label.draw(surface)

class Play(object):
    '''plays a game of keno'''
    def __init__(self, card):
        self.rect = pg.Rect(0, 80, 150, 75)
        self.font = prepare.FONTS["Saniretro"]
        self.label = Label(self.font, 32, 'PLAY', 'gold3', {'center':(0,0)})
        self.label.rect.center = self.rect.center
        self.color = '#181818'
        self.card = card

    def update(self):
        numbers = pick_numbers(20)

        self.card.ready_play()
        for number in numbers:
            self.card.toggle_hit(number)

    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)
        self.label.draw(surface)

class QuickPick(object):
    '''random picks max(10) numbers for play'''
    def __init__(self, card):
        self.rect = pg.Rect(0, 0, 150, 75)
        self.font = prepare.FONTS["Saniretro"]
        self.label = Label(self.font, 32, 'QUICK PICK', 'gold3', {'center':(0,0)})
        self.label.rect.center = self.rect.center
        self.color = '#181818'
        self.card = card

    def update(self):
        self.card.reset()
        numbers = pick_numbers(10)

        for number in numbers:
            self.card.toggle_owned(number)

    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)
        self.label.draw(surface)


class KenoSpot(object):
    COLORS = {
        'open': '#181818',
        'owned': '#9c8013',
        'hit': '#eedb1e',
        'miss': '#690808',
    }

    """A spot on a Keno card."""
    def __init__(self, left, top, width, height, label):
        self.rect = pg.Rect(left, top, width, height)
        label.rect.center = self.rect.center
        self.label = label
        self.color = self.COLORS['open']

        self.owned = False
        self.hit   = False

    def reset(self):
        self.owned = False
        self.hit   = False
        self.update_color()

    def toggle_owned(self):
        self.owned = not self.owned
        self.update_color()

    def toggle_hit(self):
        self.hit = not self.hit
        self.update_color()

    def update_color(self):
        if self.owned:
            self.color = self.COLORS['owned']
        else:
            self.color = self.COLORS['open']

        if self.hit and self.owned:
            self.color = self.COLORS['hit']
        elif self.hit:
            self.color = self.COLORS['miss']

    def draw(self, surface):
        pg.draw.rect(surface, pg.Color(self.color), self.rect, 0)
        self.label.draw(surface)

class KenoCard(object):
    def __init__(self):
        self.font = prepare.FONTS["Saniretro"]
        self.spots = []
        self.build()

    def build(self):
        font_size = 48
        text = "0"
        text_color = "white"
        rect_attrib = {'center':(0,0)}

        x_origin = 300
        x = x_origin
        y = 100
        for row in range(0,8):
            for col in range(1,11):
                text = str(col+(10*row))
                label = Label(self.font, font_size, text, text_color, rect_attrib)
                spot = KenoSpot(x, y, 64, 64, label)
                self.spots.extend([spot])
                x += 70
            y += 70
            x = x_origin

    def get_spot_count(self):
        count = 0
        for spot in self.spots:
            if spot.owned:
                count+=1
        return count

    def get_hit_count(self):
        count = 0
        for spot in self.spots:
            if spot.hit and spot.owned:
                count+=1
        return count

    def toggle_owned(self, number):
        self.spots[number].toggle_owned()

    def toggle_hit(self, number):
        self.spots[number].toggle_hit()

    def ready_play(self, clear_all=False):
        for spot in self.spots:
            spot.hit = False
            spot.update_color()

        if clear_all:
            for spot in self.spots:
                spot.owned = False
                spot.update_color()

    def reset(self):
        for spot in self.spots:
            spot.reset()

    def update(self, mouse_pos):
        for spot in self.spots:
            if spot.rect.collidepoint(mouse_pos):
                if (self.get_spot_count() < 10 and not spot.owned) or spot.owned:
                    spot.toggle_owned()


    def draw(self, surface):
        for spot in self.spots:
            spot.draw(surface)

class Keno(tools._State):
    """Class to represent a casino game."""
    def __init__(self):
        super(Keno, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.game_started = False
        self.font = prepare.FONTS["Saniretro"]

        self.mock_label = Label(self.font, 64, 'KENO [WIP]', 'gold3', {'center':(640,40)})

        b_width = 360
        b_height = 90
        side_margin = 10
        w = self.screen_rect.right - (b_width + side_margin)
        h = self.screen_rect.bottom - (b_height+15)
        self.buttons = ButtonGroup()
        NeonButton((w, h), "Lobby", self.back_to_lobby, None, self.buttons)

        self.keno_card = KenoCard()

        self.quick_pick = QuickPick(self.keno_card)
        self.play = Play(self.keno_card)

        self.spot_count_label = Label(self.font, 64, 'SPOT COUNT: 0', 'gold3', {'center':(640,700)})
        self.prev_spot_count = 0

        self.hit_count_label = Label(self.font, 64, 'HIT COUNT: 0', 'gold3', {'center':(640,764)})

        self.pay_table = PayTable(self.keno_card)
        self.pay_table.update(0)

        self.clear_action = Clear(self.keno_card)

    def back_to_lobby(self, *args):
        self.game_started = False
        self.done = True
        self.next = "LOBBYSCREEN"

    def startup(self, current_time, persistent):
        """This method will be called each time the state resumes."""
        self.persist = persistent
        #This is the object that represents the user.
        self.casino_player = self.persist["casino_player"]

        self.casino_player.stats["Keno"]["games played"] += 1

    def get_event(self, event, scale=(1,1)):
        """This method will be called for each event in the event queue
        while the state is active.
        """
        if event.type == pg.QUIT:
            self.done = True
            self.next = "LOBBYSCREEN"
        elif event.type == pg.MOUSEBUTTONDOWN:
            #Use tools.scaled_mouse_pos(scale, event.pos) for correct mouse
            #position relative to the pygame window size.
            event_pos = tools.scaled_mouse_pos(scale, event.pos)
            #print(event_pos) #[for debugging positional items]
            self.persist["music_handler"].get_event(event, scale)

            if self.quick_pick.rect.collidepoint(event_pos):
                self.quick_pick.update()
                self.hit_count_label = Label(self.font, 64, 'HIT COUNT: 0', 'gold3', {'center':(640,764)})

            if self.play.rect.collidepoint(event_pos):
                self.play.update()
                hit_count = self.keno_card.get_hit_count()
                self.hit_count_label = Label(self.font, 64, 'HIT COUNT: {0}'.format(hit_count), 'gold3', {'center':(640,764)})

            if self.clear_action.rect.collidepoint(event_pos):
                self.clear_action.update()
                self.hit_count_label = Label(self.font, 64, 'HIT COUNT: 0', 'gold3', {'center':(640,764)})

            self.keno_card.update(event_pos)

            spot_count = self.keno_card.get_spot_count()
            if spot_count != self.prev_spot_count:
                self.pay_table.update(spot_count)
                self.prev_spot_count = spot_count

            self.spot_count_label = Label(self.font, 64, 'SPOT COUNT: {0}'.format(spot_count), 'gold3', {'center':(640,700)})
        self.buttons.get_event(event)

    def draw(self, surface):
        """This method handles drawing/blitting the state each frame."""
        surface.fill(prepare.FELT_GREEN)

        self.mock_label.draw(surface)

        self.buttons.draw(surface)

        self.keno_card.draw(surface)

        self.quick_pick.draw(surface)
        self.play.draw(surface)

        self.spot_count_label.draw(surface)
        self.hit_count_label.draw(surface)

        self.pay_table.draw(surface)

        self.clear_action.draw(surface)

        self.persist["music_handler"].draw(surface)

    def update(self, surface, keys, current_time, dt, scale):
        """
        This method will be called once each frame while the state is active.
        Surface is a reference to the rendering surface which will be scaled
        to pygame's display surface, keys is the return value of the last call
        to pygame.key.get_pressed. current_time is the number of milliseconds
        since pygame was initialized. dt is the number of milliseconds since
        the last frame.
        """
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)

        self.persist["music_handler"].update(scale)
        self.draw(surface)


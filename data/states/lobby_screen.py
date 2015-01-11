import os
import json
from math import ceil
import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, GameButton, NeonButton
from ..components.labels import Button, ButtonGroup
from ..components.flair_pieces import ChipCurtain
from ..components.animation import Animation


CURTAIN_SETTINGS = {"single_color" : True,
                    "start_y" : prepare.RENDER_SIZE[1]-5,
                    "scroll_speed" : 0.05,
                    "cycle_colors" : True,
                    "spinner_settings" : {"variable" : False,
                                          "frequency" : 120}}


class LobbyScreen(tools._State):
    """
    This state represents the casino lobby where the player can choose
    which game they want to play or view their game statistics. This is also
    the exit point for the game.
    """
    def __init__(self):
        super(LobbyScreen, self).__init__()
        screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.games = [("Bingo", "BINGO"), ("Blackjack", "BLACKJACK"),
                      ("Craps", "CRAPS"), ("Keno", "KENO"),
                      ("video_poker", "VIDEOPOKER"), ("Pachinko", "PACHINKO"),
                      ("Baccarat", "BACCARAT")]
        per_page = 6
        number_of_pages = int(ceil(len(self.games)/float(per_page)))
        self.loop_length = prepare.RENDER_SIZE[0]*number_of_pages
        self.game_buttons = self.make_game_pages(screen_rect, per_page)
        nav_buttons = self.make_navigation_buttons(screen_rect)
        main_buttons = self.make_main_buttons(screen_rect)
        self.buttons = ButtonGroup(nav_buttons, main_buttons)
        self.chip_curtain = None #Created on startup.
        self.animations = pg.sprite.Group()

    def make_game_pages(self, screen_rect, per):
        groups = (self.games[i:i+per] for i in range(0,len(self.games),per))
        columns = 3
        width, height = GameButton.width, GameButton.height
        spacer_x, spacer_y = 50, 80
        start_x = (screen_rect.w-width*columns-spacer_x*(columns-1))//2
        start_y = screen_rect.top+105
        step_x, step_y = width+spacer_x, height+spacer_y
        buttons = ButtonGroup()
        for offset,group in enumerate(groups):
            offset *= prepare.RENDER_SIZE[0]
            for i,data in enumerate(group):
                game,payload = data
                y,x = divmod(i, columns)
                pos = (start_x+step_x*x+offset, start_y+step_y*y)
                GameButton(pos, game, self.change_state, payload, buttons)
        return buttons

    def make_navigation_buttons(self, screen_rect):
        sheet = prepare.GFX["nav_buttons"]
        size = (106,101)
        y = 790
        from_center = 15
        icons = tools.strip_from_sheet(sheet, (0,0), size, 4)
        buttons = ButtonGroup()
        l_kwargs = {"idle_image" : icons[0], "hover_image" : icons[1],
                    "call" : self.scroll_page, "args" : 1,
                    "bindings" : [pg.K_LEFT, pg.K_KP4],
                    "click_sound" : prepare.SFX["cardplace4"]}
        r_kwargs = {"idle_image"  : icons[2], "hover_image" : icons[3],
                    "call" : self.scroll_page, "args" : -1,
                    "bindings" : [pg.K_RIGHT, pg.K_KP6],
                    "click_sound" : prepare.SFX["cardplace4"]}
        left = Button(((0,y),size), buttons, **l_kwargs)
        left.rect.right = screen_rect.centerx-from_center
        right = Button(((0,y),size), buttons, **r_kwargs)
        right.rect.x = screen_rect.centerx+from_center
        return buttons

    def make_main_buttons(self, screen_rect):
        buttons = ButtonGroup()
        pos = (9, screen_rect.bottom-(NeonButton.height+11))
        NeonButton(pos, "Credits", self.change_state, "CREDITSSCREEN", buttons)
        pos = (screen_rect.right-(NeonButton.width+10),
               screen_rect.bottom-(NeonButton.height+11))
        NeonButton(pos, "Stats", self.change_state, "STATSMENU", buttons)
        pos = (screen_rect.centerx-(NeonButton.width//2),
               screen_rect.bottom-(NeonButton.height+11))
        NeonButton(pos, "Exit", self.exit_game, None,
                   buttons, bindings=[pg.K_ESCAPE])
        return buttons

    def scroll_page(self, mag):
        self.scrolling = True
        for game in self.game_buttons:
            self.normalize_scroll(game, mag)
            fx, fy = game.rect.x+prepare.RENDER_SIZE[0]*mag, game.rect.y
            ani = Animation(x=fx, y=fy, duration=350.0,
                            transition='in_out_quint', round_values=True)
            ani.start(game.rect)
            self.animations.add(ani)

    def normalize_scroll(self, game, mag):
        if game.rect.x < 0 and mag == -1:
            game.rect.x += self.loop_length
        elif game.rect.x >= prepare.RENDER_SIZE[0] and mag == 1:
            game.rect.x -= self.loop_length

    def startup(self, current_time, persistent):
        self.persist = persistent
        self.chip_curtain = ChipCurtain(None, **CURTAIN_SETTINGS)

    def exit_game(self, *args):
        with open(os.path.join("resources", "save_game.json"), "w") as f:
            json.dump(self.persist["casino_player"].stats, f)
        self.done = True
        self.quit = True

    def change_state(self, next_state):
        self.done = True
        self.next = next_state

    def get_event(self, event, scale=(1,1)):
        if event.type == pg.QUIT:
            self.exit_game()
        self.buttons.get_event(event)
        self.game_buttons.get_event(event)

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.chip_curtain.update(dt)
        self.buttons.update(mouse_pos)
        self.game_buttons.update(mouse_pos)
        self.animations.update(dt)
        self.draw(surface)

    def draw(self, surface):
        rect = surface.get_rect()
        surface.fill(prepare.BACKGROUND_BASE)
        self.chip_curtain.draw(surface)
        self.buttons.draw(surface)
        for button in self.game_buttons:
            if button.rect.colliderect(rect):
                button.draw(surface)

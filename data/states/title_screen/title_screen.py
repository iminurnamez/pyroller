import pygame as pg

from data import tools, prepare
from data.components import spotlight
from data.components.labels import MarqueeFrame, NeonButton, ButtonGroup
import data.state


class Scroller(pg.sprite.Sprite):
    def __init__(self, rect_attr, image, speed, *groups):
        super(Scroller, self).__init__(*groups)
        self.image = image
        self.rect = image.get_rect(**rect_attr)
        self.true_x = self.rect.x
        self.speed = speed
        self.done = False

    def update(self, screen_rect, dt):
        if not self.done:
            self.true_x += self.speed*dt
            self.rect.x = self.true_x
            if self.speed > 0 and self.rect.centerx > screen_rect.centerx:
                self.done = True
                self.rect.centerx = screen_rect.centerx
            elif self.speed < 0 and self.rect.centerx < screen_rect.centerx:
                self.done = True
                self.rect.centerx = screen_rect.centerx

    def draw(self, surface):
        surface.blit(self.image, self.rect)



class TitleScreen(data.state.State):
    """
    Initial state of the game. Introduces the game and lets user load a
    saved game if there's one present.
    """
    name = "title_screen"

    def __init__(self):
        super(TitleScreen, self).__init__()
        self.screen_rect = pg.Rect((0, 0), prepare.RENDER_SIZE)
        self.marquees = []
        self.scrollers, self.marquees = self.make_titles()
        self.buttons = ButtonGroup()
        self.new_game, self.load_game = self.make_buttons()
        self.lights = self.make_spotlights()
        self.use_music_handler = False

    def make_spotlights(self):
        lights = pg.sprite.LayeredDirty()
        y = self.screen_rect.bottom+20
        for i in range(1,5):
            start = 0 if i%2 else 0.5
            pos = (i*self.screen_rect.w/5, y)
            spotlight.SpotLight(pos, 4, 140, start, lights)
        return lights

    def make_titles(self):
        font = prepare.FONTS["Saniretro"]
        scrollers = pg.sprite.Group()
        marquees = pg.sprite.Group()
        pos = {"right" : 0, "centery": self.screen_rect.y+123}
        Scroller(pos, prepare.GFX["pyrollers_shiny"], 0.6, scrollers)
        pos = {"center": (self.screen_rect.centerx, pos["centery"])}
        MarqueeFrame(pos, prepare.GFX["pyrollers_shiny"], 20, 120, marquees)
        pos = {"left" : self.screen_rect.w, "centery": 370}
        Scroller(pos, prepare.GFX["casino_shiny"], -0.6, scrollers)
        pos = {"center": (self.screen_rect.centerx, pos["centery"])}
        MarqueeFrame(pos, prepare.GFX["casino_shiny"], 20, 120, marquees)
        return scrollers, marquees

    def make_buttons(self):
        x = self.screen_rect.centerx-(NeonButton.width//2)
        y = 600
        new_game = NeonButton((x, y), "New", self.load_or_new,
                              False, self.buttons, visible=False)
        y = new_game.rect.bottom + 50
        load_game = NeonButton((x, y), "Load", self.load_or_new,
                               True, self.buttons, visible=False)
        return new_game, load_game

    def load_or_new(self, try_to_load_data):
        if try_to_load_data:
            self.persist = self.controller.load_persist_from_disk()
        self.next = "lobby"
        self.done = True

    def get_event(self, event, scale):
        if event.type == pg.QUIT:
            self.done = True
            self.quit = True
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for scroller in self.scrollers:
                scroller.done = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.done = True
                self.quit = True
        self.buttons.get_event(event)

    def cleanup(self):
        spotlight.SpotLight.clear_cache()  # Clear cache to reclaim memory.
        return super(TitleScreen, self).cleanup()

    def update(self, surface, keys, current_time, dt, scale):
        mouse_pos = tools.scaled_mouse_pos(scale)
        self.buttons.update(mouse_pos)
        self.scrollers.update(self.screen_rect, dt)
        if self.scrollers:
            if all(scroller.done for scroller in self.scrollers):
                self.scrollers.empty()
        else:
            self.marquees.update(dt)
            self.new_game.visible = True
            self.load_game.visible = self.controller.saved_stats_are_available
        self.lights.update(dt)
        self.draw(surface, dt)

    def draw(self, surface, dt):
        surface.fill(prepare.BACKGROUND_BASE)
        self.scrollers.draw(surface)
        if not self.scrollers:
            self.marquees.draw(surface)
        self.lights.draw(surface)
        self.buttons.draw(surface)

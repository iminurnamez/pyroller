import pygame as pg
from .. import prepare, tools
from .labels import MultiLineLabel, NeonButton, ButtonGroup


class NoticeWindow(object):
    """
    A popup window for displaying a notice to the user.
    """
    def __init__(self, center, text):
        font = prepare.FONTS["Saniretro"]
        self.window = prepare.GFX["warning_window"]
        self.rect = self.window.get_rect(center=center)
        self.label = MultiLineLabel(font, 48, text, "gold3",
                                    {"midtop": (self.rect.centerx,
                                                self.rect.top + 50)},
                                    char_limit=36, align="center")
        pos = (self.rect.centerx-159, self.rect.bottom-125)
        self.ok = NeonButton(pos, "Exit", self.confirm)
        self.done = False

    def confirm(self, *args):
        self.done = True

    def get_event(self, event):
        self.ok.get_event(event)

    def update(self, mouse_pos):
        self.ok.update(mouse_pos)

    def draw(self, surface):
        surface.blit(self.window, self.rect)
        self.label.draw(surface)
        self.ok.draw(surface)


class WarningWindow(NoticeWindow):
    """
    A popup window to confirm a player's action. The callback function
    will only be called if the user clicks on the "OK" button.
    """
    def __init__(self, center, text, callback):
        super(WarningWindow, self).__init__(center, text)
        self.callback = callback
        x = 24
        self.buttons = ButtonGroup(self.ok)
        self.ok.rect.topleft = (self.rect.x+x, self.rect.bottom-(101+x))
        self.ok.args = True
        pos = (self.rect.right-(318+x), self.rect.bottom-(101+x))
        NeonButton(pos, "Back", self.confirm, False, self.buttons)

    def confirm(self, leave):
        self.done = True
        leave and self.callback()

    def get_event(self, event, scale):
        self.buttons.get_event(event)

    def update(self, mouse_pos):
        self.buttons.update(mouse_pos)

    def draw(self, surface):
        surface.blit(self.window, self.rect)
        self.label.draw(surface)
        self.buttons.draw(surface)

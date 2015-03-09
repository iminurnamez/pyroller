from itertools import product
from pygame import Rect, RLEACCEL
import pygame

__all__ = ('GraphicBox', 'draw_text')


class GraphicBox(object):
    """Generic class for drawing graphical boxes

    box = GraphicBox('border.png')
    box.draw(rect)

    The border graphic must contain 9 tiles laid out in a box.
    Each tile must be the same size
    """
    def __init__(self, image, hollow=False):
        iw, ih = image.get_size()
        self.tw = int(iw / 3)
        self.th = int(ih / 3)
        self.hollow = hollow

        tiles = [image.subsurface((x, y, self.tw, self.th))
                 for x, y in product(range(0, iw, self.tw),
                                     range(0, ih, self.th))]

        self.tiles = dict(zip("nw w sw n c s ne e se".split(), tiles))
        self.background = self.tiles['c'].get_at((0, 0))

        if self.hollow:
            ck = self.tiles['c'].get_at((0, 0))
            [t.set_colorkey(ck, RLEACCEL) for t in self.tiles.values()]

    def draw(self, surface, rect=None):
        if rect is None:
            rect = surface.get_rect()

        ox, oy, w, h = Rect(rect)
        surface_blit = surface.blit
        tiles = self.tiles
        tw = self.tw
        th = self.th

        if not self.hollow:
            p = product(range(tw + ox, w - tw + ox, tw),
                        range(th + oy, h - th + oy, th))
            [surface_blit(tiles['c'], (x, y)) for x, y in p]

        for x in range(tw + ox, w - tw + ox, tw):
            surface_blit(tiles['n'], (x, oy))
            surface_blit(tiles['s'], (x, h - th + oy))

        for y in range(th + oy, h - th + oy, th):
            surface_blit(tiles['e'], (w - tw + ox, y))
            surface_blit(tiles['w'], (ox, y))

        surface_blit(tiles['nw'], (ox, oy))
        surface_blit(tiles['ne'], (w - tw + ox, oy))
        surface_blit(tiles['sw'], (ox, h - th + oy))
        surface_blit(tiles['se'], (w - tw + ox, h - th + oy))


def draw_text(surface, text, rect, font=None, fg_color=None, bg_color=None, aa=False):
    """ draw some text into an area of a surface

    automatically wraps words
    returns size and any text that didn't get blit
    passing None as the surface is ok
    """
    if fg_color is None:
        fg_color = (0, 0, 0)

    total_width = 0
    rect = Rect(rect)
    y = rect.top
    line_spacing = -2

    if font is None:
        full_path = pygame.font.get_default_font()
        font = pygame.font.Font(full_path, 16)

    # get the height of the font
    font_height = font.size("Tg")[1]

    # for very small fonts, turn off antialiasing
    if font_height < 16:
        aa = 0
        bg_color = None

    while text:
        char_index = 1

        # determine if the row of text will be outside our area
        if y + font_height > rect.bottom:
            break

        # determine maximum width of line
        line_width = font.size(text[:char_index])[0]
        while line_width < rect.width and char_index < len(text):
            if text[char_index] == "\n":
                text = text[:char_index] + text[char_index + 1:]
                break

            char_index += 1
            line_width = font.size(text[:char_index])[0]
            total_width = max(total_width, line_width)
        else:
            # if we've wrapped the text, then adjust the wrap to the last word
            if char_index < len(text):
                char_index = text.rfind(" ", 0, char_index) + 1

        if surface:
            # render the line and blit it to the surface
            if bg_color:
                image = font.render(text[:char_index], 1, fg_color, bg_color)
                image.set_colorkey(bg_color)
            else:
                image = font.render(text[:char_index], aa, fg_color)

            surface.blit(image, (rect.left, y))

        y += font_height + line_spacing

        # remove the text we just blitted
        text = text[char_index:]

    return total_width, text

from collections import OrderedDict
import pygame as pg
from .. import prepare


class Chip(object):
    """Class to represent a single casino chip."""
    chip_values = OrderedDict(
                [("black", 100),
                ("blue", 25),
                ("green", 10),
                ("red", 5),
                ("white", 1)]
                )
    images = {color: prepare.GFX["chip{}side".format(color)] 
                    for color in chip_values}
    chip_size = prepare.CHIP_SIZE 
    chip_thickness = 6
    
    def __init__(self, color, chip_size=None):
        self.color = color
        if chip_size is not None:
            self.chip_size = chip_size
        self.value = self.chip_values[self.color]
        self.image = self.images[color]
        self.image = pg.transform.scale(self.image, self.chip_size)
        self.flat_image = pg.transform.scale(prepare.GFX["chip{}".format(self.color)],
                                                              self.chip_size)
        self.rect = self.image.get_rect()
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
        
class ChipStack(object):
    """Class to represent a stack of same-colored casino chips."""
    def __init__(self, chips, bottomleft):
        self.chips = chips
        self.bottomleft = bottomleft
        self.align()
        
    def pop(self):
        """Pops the top(last) chip off the stack and returns it."""
        return self.chips.pop() if self.chips else None
        
    def split(self, chip_index, bottomleft):
        """Removes chips from chip_index to end of self.chips
            and returns a new ChipStack of those chips."""
        bet_chips = self.chips[chip_index:]
        self.chips = self.chips[:chip_index]
        return ChipStack(bet_chips, bottomleft)       
    
    def grab_chips(self, click_pos):
        """Returns a new stack according to click position or
            None if no chips collide with click_pos."""
        if self.chips[-1].rect.collidepoint(click_pos):
            bet_stack = self.split(-1, self.chips[-1].rect.bottomleft)
            return bet_stack
        else:
            for chip in self.chips:
                if chip.rect.collidepoint(click_pos):
                    coll_rect = pg.Rect(0, 0, chip.rect.width, Chip.chip_thickness)
                    coll_rect.midbottom = chip.rect.midbottom
                    if coll_rect.collidepoint(click_pos):
                        chip_index = self.chips.index(chip)
                        bet_stack = self.split(chip_index, chip.rect.bottomleft)
                        return bet_stack               
                        
    def align(self):
        """Positions the chips in a stack."""
        chip_thickness = Chip.chip_thickness
        left, bottom = self.bottomleft
        for chip in self.chips:
            chip.rect.bottomleft = (left, bottom)
            bottom -= chip_thickness
            
    def draw(self, surface):
        """Aligns chips and draws them to surface."""
        self.align()
        for chip in self.chips:
            chip.draw(surface)
            
            
class ChipRack(object):
    """Class to represent a dealer/teller's rack of chips."""
    def __init__(self, topleft):
        self.image = prepare.GFX["chip_rack"]
        self.rect = self.image.get_rect(topleft=topleft)
        self.front = prepare.GFX["rack_front"]
        self.front_rect = self.front.get_rect(bottomleft=self.rect.bottomleft)
        self.chips = OrderedDict()
        for color in Chip.chip_values:
            self.chips[color] = [Chip(color) for _ in range(20)]
        
    def add_chips(self, chips):
        """Adds each chip in chips to the rack."""
        for chip in chips:
            self.add_chip(chip)
    
    def add_chip(self, chip):
        """Add a single chip to the rack."""
        self.chips[chip.color].append(chip)
        
    def break_chip(self, chip):
        """Returns a list of Chips equal to the value of chip."""
        if chip.value == 1:
            return [chip]
        cash = chip.value - 1
        chips = cash_to_chips(cash)
        chips.extend(cash_to_chips(1))
        self.add_chip(chip)
        for chip in chips:
            try:
                self.chips[chip.color].pop()
            except IndexError:
                pass
        return chips
            
    def break_chips(self, chips):
        """Returns a list of Chips created by calling
            break_chip on each chip in chips."""
        broken = []
        for chip in chips:
            broken.extend(self.break_chip(chip))
        return broken
        
    def update(self):
        """Make sure chips don't overflow or run out."""
        for color in self.chips:
            num = len(self.chips[color])
            if num < 1:
                self.chips[color] = [Chip(color) for _ in range(20)]
            elif num > 20:
                self.chips[color] = self.chips[color][:20]
                
    def draw(self, surface):
        """Positions chips and draws rack and chips to surface."""
        surface.blit(self.image, self.rect)
        vert_spacer = 6
        horiz_spacer = 6
        left = self.rect.left + horiz_spacer 
        for color in self.chips:
            top = self.rect.top - vert_spacer
            for chip in self.chips[color]:
                surface.blit(chip.flat_image, (left, top))
                top += vert_spacer
            left += prepare.CHIP_SIZE[0] + horiz_spacer
        surface.blit(self.front, self.front_rect)
        
def cash_to_chips(cash):
    """Returns a list of Chips equal to the cash amount."""
    vals = Chip.chip_values
    chips_ = []
    cash_ = cash
    for color in vals:
        num, cash_ = divmod(cash_, vals[color])
        chips_.append((color, num))
    chips = []
    for color, num in chips_:
        chips.extend([Chip(color) for _ in range(num)])
    return chips
    
def chips_to_cash(chips):
    """Takes in a list of Chip instances and returns cash value."""
    return sum([chip.value for chip in chips])
        

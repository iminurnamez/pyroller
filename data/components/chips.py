from collections import OrderedDict, defaultdict
from random import choice

import pygame as pg
from .. import prepare


CHIP_Y = {"blue"  : 0,
          "red"   : 64,
          "black" : 128,
          "green" : 192,
          "white" : 256}


def get_chip_images():
    sheet = prepare.GFX["chips"]
    images = {(32,19) : {col: sheet.subsurface(64,CHIP_Y[col],64,38)
                         for col in CHIP_Y}}
    images[(48,30)] = {col : pg.transform.scale(images[(32,19)][col], (48, 30))
                       for col in CHIP_Y}
    flat_images = {(32,19) : {col: sheet.subsurface(0,CHIP_Y[col],64,64)
                   for col in CHIP_Y}}
    flat_images[(48,30)] = {col : pg.transform.scale(flat_images[(32,19)][col],
                            (48,48)) for col in CHIP_Y}
    return images, flat_images


class Chip(object):
    """Class to represent a single casino chip."""
    chip_values = OrderedDict([("black", 100),
                               ("blue", 25),
                               ("green", 10),
                               ("red", 5),
                               ("white", 1)])
    images, flat_images = get_chip_images()
    thicknesses = {19: 5, 30: 7}


    def __init__(self, color, chip_size=None):
        self.color = color
        if chip_size is None:
            self.chip_size = prepare.CHIP_SIZE
        else:
            self.chip_size = chip_size
        self.thickness = self.thicknesses[self.chip_size[1]]
        self.value = self.chip_values[self.color]
        self.image = self.images[self.chip_size][self.color]
        self.flat_image = self.flat_images[self.chip_size][self.color]
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
                    coll_rect = pg.Rect(0, 0, chip.rect.width, chip.thickness)
                    coll_rect.midbottom = chip.rect.midbottom
                    if coll_rect.collidepoint(click_pos):
                        chip_index = self.chips.index(chip)
                        bet_stack = self.split(chip_index, chip.rect.bottomleft)
                        return bet_stack

    def align(self):
        """Positions the chips in a stack."""
        left, bottom = self.bottomleft
        for chip in self.chips:
            chip.rect.bottomleft = (left, bottom)
            bottom -= chip.thickness

    def draw(self, surface):
        """Aligns chips and draws them to surface."""
        self.align()
        for chip in self.chips:
            chip.draw(surface)


class BetPile(object):
    """A compact pile of chips arranged by height."""
    def __init__(self, bottomleft, chip_size, chips=None):
        self.chips = [] if chips is None else chips
        w, h = chip_size
        left, bottom = bottomleft
        adjust = (1, 1) if w == 32 else (2)
        bottom -= 5

        offsets = [(0, -h - adjust), (w + adjust, -h - adjust), ((w * 2) + (adjust * 2), -h - adjust),
                       ((w/2) + adjust, 0), (((w/2) * 3) + (adjust * 2), 0)]
        self.stack_spots = [(left + x, bottom + y) for x,y in offsets]
        self.stacks = self.make_stacks()

    def make_stacks(self):
        """Returns a list of stacks sorted and arranged by height."""
        chips = defaultdict(list)
        for chip in self.chips:
            chips[chip.color].append(chip)
        stacks = [ChipStack(chips[color], (0, 0)) for color in chips]
        stacks = sorted(stacks, key=lambda x: len(x.chips), reverse=True)
        for stack, spot in zip(stacks, self.stack_spots):
            stack.bottomleft = spot
            stack.align()
        return sorted(stacks, key=lambda x: x.bottomleft[1])

    def grab_chips(self, click_pos):
        """Return a new ChipStack if click_pos splits one
        of the pile's stacks."""
        for stack in self.stacks:
            bet_stack = stack.grab_chips(click_pos)
            if bet_stack is not None:
                color = bet_stack.chips[0].color
                for chip in bet_stack.chips:
                    self.chips.remove(chip)
                self.stacks = self.make_stacks()
                return bet_stack

    def get_chip_total(self):
        """Returns total cash value of self.chips."""
        return sum([x.value for x in self.chips])

    def add_chips(self, chips):
        """Adds chips to and adjusts stacks."""
        self.chips.extend(chips)
        self.stacks = self.make_stacks()

    def draw(self, surface):
        """Draw pile to surface."""
        for stack in self.stacks:
            stack.draw(surface)


class ChipPile(object):
    """Represents a player's pile of chips."""

    def __init__(self, bottomleft, chip_size, cash=0, chips=None,
                         stack_height=10, num_rows=5, columns_per_color=2,
                         horiz_space=1, vert_space=1):
        self.chip_size = chip_size
        self.stack_height = stack_height
        self.num_rows = num_rows
        self.columns_per_color = columns_per_color
        num_colors = len(Chip.chip_values)
        self.horiz_space = horiz_space
        self.vert_space = vert_space
        w, h  = self.chip_size
        columns = num_colors * columns_per_color
        w = (w * columns) + (horiz_space * (columns - 1))
        h = (self.num_rows * (self.chip_size[1] + self.vert_space)) - self.vert_space
        self.rect = pg.Rect((0, 0), (w, h))
        self.rect.bottomleft = bottomleft
        chips = [] if chips is None else chips
        if cash:
            chips.extend(cash_to_chips(cash, self.chip_size))
        self.chips = OrderedDict()
        for color in Chip.chip_values:
            self.chips[color] = [x for x in chips if x.color == color]
        self.stacks = self.make_stacks()
        names = ["chipsstack{}".format(x) for x in (3, 5, 6)]

    def get_chip_total(self):
        """"Returns total cash value of self.chips."""
        total = 0
        for color in self.chips:
            total += Chip.chip_values[color] * len(self.chips[color])
        return total

    def add_chips(self, chips):
        """Adds chips and adjusts stacks."""
        for chip in chips:
            self.chips[chip.color].append(chip)
        self.stacks = self.make_stacks()
        
    def all_chips(self):
        all_chips = []
        for color in self.chips:
            all_chips.extend(self.chips[color])
        return all_chips
        
    def draw_stacks(self, surface):
        """Draw stacks to surface."""
        for stack in self.stacks:
            stack.draw(surface)

    def withdraw_chips(self, amount):
        """Withdraw chips totalling amount and adjust stacks."""
        chips = cash_to_chips(self.get_chip_total() - amount, self.chip_size)
        withdrawal = cash_to_chips(amount, self.chip_size)
        for color in self.chips:
            self.chips[color] = [x for x in chips if x.color == color]
        self.stacks = self.make_stacks()
        return withdrawal

    def make_stacks(self):
        """Returns a list of ChipStacks sorted by y-position."""
        w, h = self.chip_size
        left = self.rect.left
        bottom = self.rect.top + h
        stacks = []
        for color in self.chips:
            chips = self.chips[color]
            stackers = [chips[i: i + self.stack_height] for i in range(0, len(chips), self.stack_height)]
            limit = self.columns_per_color * self.num_rows
            if len(stackers) >  limit:
                stackers = stackers[:limit]
            left2 = left + w + self.horiz_space
            bottom_ = bottom
            for i, stacker in enumerate(stackers):
                if not i % self.columns_per_color:
                    stack = ChipStack(stacker, (left, bottom_))
                else:
                    stack = ChipStack(stacker, (left2, bottom_))
                    bottom_ += h + self.vert_space
                stacks.append(stack)
            left += (w + self.horiz_space) * 2
        return sorted(stacks, key=lambda x: x.bottomleft[1])

    def grab_chips(self, click_pos):
        """
        Calls grab_chips on each stack, returning the first result
        that is not None. None is returned if no chips are grabbed.
        """
        for stack in self.stacks[::-1]:
            bet_stack = stack.grab_chips(click_pos)
            if bet_stack is not None:
                color = bet_stack.chips[0].color
                for chip in bet_stack.chips:
                    self.chips[color].remove(chip)
                self.stacks = self.make_stacks()
                return bet_stack

    def get_chip_total(self):
        """Returns cash total of all chips in pile."""
        total = 0
        for color in self.chips:
            total += Chip.chip_values[color] * len(self.chips[color])
        return total


class ChipRack(object):
    """Class to represent a dealer/teller's rack of chips."""
    def __init__(self, topleft, chip_size):
        self.chip_size = chip_size
        img_name = "chip_rack"
        front_name = "rack_front"
        self.vert_spacer = 6
        self.horiz_spacer = 6
        if self.chip_size == (48, 30):
            img_name += "_medium"
            front_name += "_medium"
            self.vert_spacer = 9
            self.horiz_spacer = 9
        self.image = prepare.GFX[img_name]
        self.rect = self.image.get_rect(topleft=topleft)
        self.front = prepare.GFX[front_name]
        self.front_rect = self.front.get_rect(bottomleft=self.rect.bottomleft)
        self.chips = OrderedDict()
        for color in Chip.chip_values:
            self.chips[color] = [Chip(color, self.chip_size) for _ in range(20)]

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
        cash = chip.value
        values = Chip.chip_values
        chips = []
        for color in values:
            if cash >= values[color] and color != chip.color:
                num, rem = divmod(cash, values[color])
                for _ in range(num):
                    chips.append(Chip(color, self.chip_size))
                cash = rem
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
                self.chips[color] = [Chip(color, self.chip_size) for _ in range(20)]
            elif num > 20:
                self.chips[color] = self.chips[color][:20]

    def draw(self, surface):
        """Positions chips and draws rack and chips to surface."""
        surface.blit(self.image, self.rect)
        left = self.rect.left + self.horiz_spacer
        for color in self.chips:
            top = (self.rect.top + 1) - self.vert_spacer
            for chip in self.chips[color]:
                surface.blit(chip.flat_image, (left, top))
                top += self.vert_spacer
            left += self.chip_size[0] + self.horiz_spacer
        surface.blit(self.front, self.front_rect)

def cash_to_chips(cash, chip_size=None):
    """Returns a list of Chips equal to the cash amount."""
    vals = Chip.chip_values
    chips_ = []
    cash_ = cash
    for color in vals:
        num, cash_ = divmod(cash_, vals[color])
        chips_.append((color, num))
    chips = []
    for color, num in chips_:
        chips.extend([Chip(color, chip_size) for _ in range(num)])
    return chips

def chips_to_cash(chips):
    """Takes in a list of Chip instances and returns cash value."""
    return sum([chip.value for chip in chips])


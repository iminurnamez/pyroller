import random
from ... import prepare, tools
import pygame as pg

class Die:
    def __init__(self, screen_rect, spacer_y=None):
        self.spacer_y = spacer_y
        self.is_die2 = spacer_y
        sheet = prepare.GFX['dice']
        self.dice = tools.strip_from_sheet(sheet, (0,0), (36,36), 1, 6)
        self.dice_rect = self.dice[0].get_rect()
        self.rolling = False
        
        self.roll_value = 0
        dice_buffer_x = 15
        if not spacer_y:
            self.dice_starting_pos = (screen_rect.right, screen_rect.centery - (screen_rect.height //4) + dice_buffer_x)
        else:
            self.dice_starting_pos = (screen_rect.right, screen_rect.centery - (screen_rect.height //4) + dice_buffer_x + spacer_y)
        self.dice_timer = 0
        self.dice_speed = 40
        self.dice_moving_left = True
        self.draw_dice = False #player has rolled initially
        
        dice_large_offset = 125
        x = 1050
        y = 100
        if self.is_die2: #on only second die
            x += dice_large_offset
        self.dice_large_pos = (x,y)
        
        self.dice_large = []
        for die in self.dice:
            self.dice_large.append(pg.transform.scale(die, (100,100)))
            
        self.debug = False
        
    def update(self, current_time):
        if current_time-self.dice_timer > 10:
            self.dice_timer = current_time
            if self.rolling:
                if self.dice_moving_left:
                    if self.dice_rect.x <= 36: #hits left side
                        self.dice_rect.x *= -1
                        if self.is_die2:
                            self.dice_rect.y += random.randint(-10, 10)
                        else:
                            self.dice_rect.y -= random.randint(0,10)
                        self.dice_moving_left = False
                    else:
                        self.dice_rect.x -= self.dice_speed
                else:
                    self.dice_rect.x += self.dice_speed
                    self.dice_speed -= random.randint(1,5)
                    if self.dice_speed < 0:
                        self.dice_speed = 0
                        self.rolling = False
                    
    def draw(self, surface):
        if self.draw_dice:
            surface.blit(self.dice[self.roll_value], self.dice_rect)
            if not self.rolling:
                surface.blit(self.dice_large[self.roll_value], self.dice_large_pos)
                
    def reset(self):
        if not self.rolling:
            self.draw_dice = True
            self.dice_speed = 40
            self.dice_moving_left = True
            self.rolling = True
            self.dice_rect.center = self.dice_starting_pos
            self.roll_value = random.randint(0,5)
            self.debug = False
            
    def value(self):
        if not self.rolling and not self.draw_dice:
            return None
        else:
            return self.roll_value + 1

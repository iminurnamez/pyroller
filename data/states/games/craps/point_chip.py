
from data import tools, prepare
import pygame as pg
from . import craps_data


class PointChip:
    def __init__(self):
        self.point_chip_loc = craps_data.POINT_CHIP_LOC
        sheet = prepare.GFX['point_chip']
        self.point_chip = tools.strip_from_sheet(sheet, (0,0), (135,135), 1, 2)
        self.off = pg.transform.scale(self.point_chip[0], (40,40))
        self.on = pg.transform.scale(self.point_chip[1], (40,40))
        self.image = self.off
        self.rect = self.off.get_rect(center=self.point_chip_loc['0'])
        self.timer = 0
        self.speed = 10
        self.point = None
        
    def update(self, current_time, point, die):
        self.move_to_point(current_time, point, die)
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)
                            
    def move_to_point(self, current_time, number, die):
        number = str(number)
        if not die.rolling:
            if number in self.point_chip_loc.keys():
                if current_time-self.timer > 10:
                    if die.draw_dice:
                        if not self.point:
                            self.timer = current_time
                            number_x = self.point_chip_loc[number][0]
                            self.image = self.on
                            if self.rect.x >= number_x:
                                self.rect.x = number_x
                                self.point = number
                            else:
                                self.rect.x += self.speed
            elif number == '7':
                #if self.point:
                    self.point = None
                    x = self.point_chip_loc['0'][0]
                    self.image = self.off
                    if self.rect.x >= x:
                        self.rect.x -= self.speed
                    else:
                        x -= 5 #glitch fix (moving back and forth on x axis)
                        self.rect.x = x
                    
        

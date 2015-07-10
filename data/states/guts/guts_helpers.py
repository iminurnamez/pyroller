from data import prepare


class DealerButton(object):
    def __init__(self, topleft):
        self.image = prepare.GFX["dealer_button"]
        self.rect = self.image.get_rect(topleft=topleft)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

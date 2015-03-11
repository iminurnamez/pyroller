import pygame as pg
from . import dialog, animation
from .. import prepare


class AdvisorMessage(object):
    def __init__(self, draw_group):
        self.draw_group = draw_group
        self.font = pg.font.Font(prepare.FONTS["Saniretro"], 64)
        self.animations = pg.sprite.Group()
        self._current_advice = None
        self._advisor_stack = []
        self._dialog_box = dialog.GraphicBox(
            pg.transform.smoothscale(prepare.GFX['callout'], (300, 300)))

    def clear_advisor(self):
        self.animations = pg.sprite.Group()
        self._current_advice = None
        self._advisor_stack = []

    def queue_advisor_message(self, text, autodismiss=2000):
        if self._current_advice is None:
            self.create_advisor_message(text, autodismiss)
        else:
            self._advisor_stack.append((text, autodismiss))

    def create_advisor_message(self, text, draw_group, autodismiss=2000):
        fg_color = 0, 0, 0
        bg_color = 255, 255, 255
        margins = 25, 55
        max_size = 900, 150
        position = 10, 55

        # first estimate how wide the text will be
        text_rect = pg.Rect(margins, max_size)
        width, leftover_text = dialog.draw_text(None, text,
                                                text_rect, self.font)
        assert (leftover_text == '')

        sprite = pg.sprite.Sprite()
        sprite.rect = pg.Rect(position,
                              (width + margins[0] * 2, max_size[1]))

        sprite.image = pg.Surface(sprite.rect.size, pg.SRCALPHA)
        self._dialog_box.draw(sprite.image)
        dialog.draw_text(sprite.image, text, text_rect, self.font,
                         fg_color, bg_color, True)

        self._current_advice = sprite
        self.draw_group.add(sprite)

        ani = animation.Animation(y=position[1], initial=-max_size[1],
                                  round_values=True, duration=500,
                                  transition='out_quint')
        ani.start(sprite.rect)
        self.animations.add(ani)

        sound = prepare.SFX['misc_menu_4']
        sound.set_volume(.2)
        sound.play()

        if autodismiss:
            self.delay(autodismiss, self.dismiss_advisor, args=(sprite, ))

    def dismiss_advisor(self, target=None):
        sprite = self._current_advice
        if sprite is None:
            return

        if target is not None:
            if target is not self._current_advice:
                return

        animation.remove_animations_of(self.animations, sprite.rect)
        ani = animation.Animation(y=-sprite.rect.height, round_values=True,
                                  duration=500, transition='out_quint')
        ani.callback = sprite.kill
        ani.start(sprite.rect)
        self.animations.add(ani)

        self._current_advice = None

        if self._advisor_stack:
            self.create_advisor_message(*self._advisor_stack.pop(0))

    def delay(self, amount, callback, args=None, kwargs=None):
        """Convenience function to delay a function call

        :param amount: milliseconds to wait until callback is called
        :param callback: function to call
        :param args: arguments to pass to callback
        :param kwargs: keywords to pass to callback
        :return: Task instance
        """
        task = animation.Task(callback, amount, 1, args, kwargs)
        self.animations.add(task)
        return task

    def update(self, surface, keys, current_time, dt, scale):
        self.animations.update(dt)

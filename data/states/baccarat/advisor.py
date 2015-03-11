from ... import prepare
from ...components.animation import *
from ...components.dialog import *

import pygame as pg

__all__ = ('Advisor', )


class Advisor(object):
    fg_color = 0, 0, 0
    bg_color = 255, 255, 255
    margins = 25, 55
    max_size = 900, 150
    position = 10, 55

    def __init__(self, draw_group, animation_group):
        self._draw_group = draw_group
        self._animations = animation_group
        self._message_queue = list()
        self._font = pg.font.Font(prepare.FONTS["Saniretro"], 64)
        self._dialog_box = GraphicBox(
            pg.transform.smoothscale(prepare.GFX['callout'], (300, 300)))

    @property
    def current_message(self):
        try:
            return self._message_queue[0][1]
        except IndexError:
            return None

    @property
    def queued_text(self):
        return [i[0] for i in self._message_queue]

    def update(self, dt):
        self._animations.update(dt)

    def queue_message(self, text, dismiss_after=2000, sound=None):
        """Queue a new message

        A unique sprite will be returned from this function.  That sprite
        can be passed to Advisor.dismiss() to remove that specific message.

        :param text: Text to be displayed
        :param sound: Sound to be played when message is shown
        :param dismiss_after: Number of milliseconds to show message,
                            Negative numbers will cause message to be displayed
                            until dismissed.

        :return: pygame.sprite.Sprite
        """
        sprite = self.render_dialog(text)

        self._message_queue.append((text, sprite, dismiss_after, sound))
        if len(self._message_queue) == 1:
            self.show_next()

        return sprite

    def dismiss(self, target=None):
        """Cause current displayed message to be dismissed

        If there are messages still in the queue, they will be
        displayed next.
        """
        show_next = True

        if target is None:
            sprite = self.current_message
            if sprite is None:
                return
        else:
            if target in [i[1] for i in self._message_queue]:
                show_next = target is self.current_message
                sprite = target
            else:
                return

        # animations may be playing of the sprite
        remove_animations_of(self._animations, sprite.rect)

        # hide the sprite
        ani = self.animate_hide_sprite(sprite)
        self._animations.add(ani)

        # show next sprite if there is one
        if show_next:
            self._message_queue.pop(0)
            self.show_next()

    def show_next(self):
        if self._message_queue:
            self.show_message(*self._message_queue[0])

    def clear_queue(self):
        """Clear all message and dismiss the current one

        :return: None
        """
        if self._message_queue:
            self._message_queue = [self._message_queue[0]]
            self.dismiss()

    def show_message(self, text, sprite, dismiss_after=2000, sound=None):
        """Show a sprite, play sound, and set timer to remove it

        :param sprite: test to be displayed
        :param dismiss_after: Number of milliseconds to show message,
                            0 or Negative numbers will cause message to be
                            displayed until dismissed.
        :return: Unique sprite for the message
        """
        # animate the sprite showing
        ani = self.animate_show_sprite(sprite)
        self._animations.add(ani)

        # add the sprite to the group that contains the advisor
        self._draw_group.add(sprite)

        # play sound associated with the message
        sound = prepare.SFX['misc_menu_4']
        sound.set_volume(.2)
        sound.play()

        # set timer to dismiss the sprite
        if dismiss_after:
            task = Task(self.dismiss, dismiss_after, args=(sprite, ))
            self._animations.add(task)

    def animate_show_sprite(self, sprite):
        """Animate and show the sprite dropping down from advisor

        :param sprite: pygame.sprite.Sprite
        :return: None
        """
        ani = Animation(y=self.position[1], initial=-self.max_size[1],
                        round_values=True, duration=500, transition='out_quint')
        ani.start(sprite.rect)
        return ani

    def animate_hide_sprite(self, sprite):
        """Animate and hide the sprite

        :param sprite: pygame.sprite.Sprite
        :return: None
        """
        ani = Animation(y=-sprite.rect.height, round_values=True,
                        duration=500, transition='out_quint')
        ani.callback = sprite.kill
        ani.start(sprite.rect)
        return ani

    def render_dialog(self, text):
        """Render the sprite that will drop down from the advisor

        :param text: Test to be rendered
        :return: pygame.sprite.Sprite
        """
        # first estimate how wide the text will be
        text_rect = pg.Rect(self.margins, self.max_size)
        width, leftover_text = draw_text(None, text, text_rect, self._font)
        assert (leftover_text == '')

        # next make the sprite with the estimated rect size
        sprite = pg.sprite.Sprite()
        sprite.rect = pg.Rect(self.position,
                              (width + self.margins[0] * 2, self.max_size[1]))

        sprite.image = pg.Surface(sprite.rect.size, pg.SRCALPHA)
        self._dialog_box.draw(sprite.image)
        draw_text(sprite.image, text, text_rect, self._font,
                  self.fg_color, self.bg_color, True)

        return sprite

import numpy as np

import PIL.Image, PIL.ImageTk

import gui_util

# must be either 'pillow' or 'pygame'; currently 'pygame' is somewhat faster
RENDERER = 'pygame' 

class ImageWrapper():
    IMAGE_FORMAT = 'RGBA'

    def __init__(self, size):
        self.size = size
        self.w, self.h = size

    def __str__(self):
        return f'<Image {self.size}>'

    def get_pillow_image(self):
        """return a PIL.Image with this image's data"""

    def get_imagetk(self):
        """return a PIL.ImageTk.PhotoImage for use in the tkinter UI"""
        return PIL.ImageTk.PhotoImage(self.get_pillow_image())

    def blit(self, other, offset):
        """blit other image onto this one with top left at offset"""

    def draw_line(self, start, end, colour, width):
        """draw a line of width on this image from start to end in colour"""

    def flip(self, flip_x, flip_y):
        """flip the image in either the x, y, or both directions"""

    def resize(self, new_size, fast=False):
        """return a resized version of this image of new_size"""

        if not (new_size[0] >= 0 and new_size[1] >= 0):
            raise ValueError('Cannot resize to negative dimensions.')
        return self._resize(new_size, fast)

    def _resize(self, new_size, fast=False):
        """resize implementation, after value verification"""

    def as_greyscale_array(self):
        """return a 2d array of this image converted to greyscale"""
        return np.asarray(self.get_pillow_image().convert('L'))

    @staticmethod
    def from_file(path):
        """return an ImageWrapper with image loaded from path"""

class PygameImage(ImageWrapper):
    def __init__(self, size, image=None, bg_colour=None):
        super().__init__(size)
        self.transparency_colour = gui_util.BG_COLOUR
        if not image:
            self.image = pygame.Surface(size)
            self.image.set_colorkey(self.transparency_colour)
        
            if bg_colour:
                if not bg_colour[3]:
                    self.image.fill(self.transparency_colour)
                else:
                    self.image.fill(bg_colour)
        else:
            self.image = image
            self.image.set_colorkey(self.transparency_colour)

    def get_pillow_image(self):
        return PIL.Image.frombytes(
            Image.IMAGE_FORMAT,
            self.size,
            pygame.image.tostring(self.image, Image.IMAGE_FORMAT, False)
        )

    def blit(self, other, offset):
        self.image.blit(other.image, offset)

    def draw_line(self, start, end, colour, width):
        pygame.draw.line(self.image, colour, start, end, width)

    def flip(self, flip_x, flip_y):
        return PygameImage(
            self.size,
            pygame.transform.flip(self.image, flip_x, flip_y)
        )

    def _resize(self, new_size, fast=False):
        if fast:
            new_img = pygame.transform.scale(self.image, new_size)
        else:
            new_img = pygame.transform.smoothscale(self.image, new_size)

        return PygameImage(new_size, new_img)

    @staticmethod
    def from_file(path):
        image = pygame.image.load(path)
        return PygameImage(image.get_size(), image)
    
class PillowImage(ImageWrapper):
    def __init__(self, size, image=None, bg_colour=0):
        super().__init__(size)
        if not image:
            self.image = PIL.Image.new(Image.IMAGE_FORMAT, size, bg_colour)
        else:
            self.image = image
        self.draw = None

    def get_pillow_image(self):
        return self.image

    def ensure_draw(self):
        if self.draw is None:
            self.draw = PIL.ImageDraw.Draw(self.image)

    def blit(self, other, offset):
        self.image.paste(other.image, offset, other.image)

    def draw_line(self, start, end, colour, width):
        self.ensure_draw()
        self.draw.line([start, end], colour, width)

    def flip(self, flip_x, flip_y):
        if flip_x and flip_y:
            new = self.image.transpose(PIL.Image.ROTATE_180)
        elif flip_x:
            new = self.image.transpose(PIL.Image.FLIP_LEFT_RIGHT)
        elif flip_y:
            new = self.image.transpose(PIL.Image.FLIP_TOP_BOTTOM)

        return PillowImage(self.size, new)

    def _resize(self, new_size, fast=False):
        if fast:
            new_img = self.image.resize(new_size, resample=PIL.Image.NEAREST)
        else:
            new_img = self.image.resize(new_size)

        return PillowImage(new_size, new_img)

    @staticmethod
    def from_file(path):
        image = PIL.Image.open(path).convert(Image.IMAGE_FORMAT)
        return PillowImage(image.size, image)

if RENDERER == 'pygame':
    import contextlib
    with contextlib.redirect_stdout(None):
        import pygame
    Image = PygameImage
elif RENDERER == 'pillow':
    import PIL.ImageDraw
    Image = PillowImage
else:
    if RENDERER == '':
        raise ValueError(
            'No renderer set. RENDERER must be either ' + \
            '"pygame" or "pillow"'
        )
    else:
        raise ValueError(f'Renderer "{RENDERER}" not available.')

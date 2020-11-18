import io
import numpy as np

import PIL.Image, PIL.ImageTk

import gui_util

# must be either 'pillow' or 'pygame'; currently 'pygame' is somewhat faster
# if using pillow, pillow-simd is likely to offer better performance
RENDERER = 'pygame' 

class ImageWrapper():
    IMAGE_FORMAT = 'RGBA'
    BLOB_FORMAT = 'PNG'
    THUMBNAIL_SIZE = (128, 128)
    FORMATS = [
        'BMP',
        'PNG',
        'JPG',
        'JPEG'
    ]

    def __init__(self, **kwargs):
        size = kwargs.get('size', (0, 0))
        w, h = size
        self.w = kwargs.get('w', kwargs.get('width', w))
        self.h = kwargs.get('h', kwargs.get('height', h))

    @property
    def size(self):
        return self.w, self.h

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

    def as_thumbnail(self):
        """get a thumbnail of this image, to save in db or similar"""
        return self.resize(Image.THUMBNAIL_SIZE)

    def as_bytes(self):
        """convert this image to a byte array"""
        blob = io.BytesIO()
        self.get_pillow_image().save(blob, format=Image.BLOB_FORMAT)
        return blob.getvalue()
    
    @staticmethod
    def load(filelike):
        """load the given filelike"""

    @staticmethod
    def from_file(path):
        """return an Image with image loaded from path"""
        return Image.load(open(path, 'rb'))

    @staticmethod
    def from_bytes(data):
        """read provided bytes (data) as an Image"""
        return Image.load(io.BytesIO(data))

class PygameImage(ImageWrapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.transparency_colour = gui_util.BG_COLOUR
        
        image = kwargs.get('image')
        bg_colour = kwargs.get('bg_colour')
        
        if not image:
            self.image = pygame.Surface(self.size)
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
            size=self.size,
            image=pygame.transform.flip(self.image, flip_x, flip_y)
        )

    def _resize(self, new_size, fast=False):
        if fast:
            new_img = pygame.transform.scale(self.image, new_size)
        else:
            new_img = pygame.transform.smoothscale(self.image, new_size)

        return PygameImage(size=new_size, image=new_img)

    @staticmethod
    def load(filelike):
        image = pygame.image.load(filelike)
        return PygameImage(size=image.get_size(), image=image)
    
class PillowImage(ImageWrapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        image = kwargs.get('image')
        bg_colour = kwargs.get('bg_colour', 0)

        if not image:
            self.image = PIL.Image.new(
                Image.IMAGE_FORMAT,
                self.size,
                bg_colour
            )
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

        return PillowImage(size=self.size, image=new)

    def _resize(self, new_size, fast=False):
        if fast:
            new_img = self.image.resize(new_size, resample=PIL.Image.NEAREST)
        else:
            new_img = self.image.resize(new_size)

        return PillowImage(size=new_size, image=new_img)

    @staticmethod
    def load(filelike):
        image = PIL.Image.open(filelike).convert(Image.IMAGE_FORMAT)
        return PillowImage(size=image.size, image=image)

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

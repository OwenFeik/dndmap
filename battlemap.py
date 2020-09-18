import enum

import PIL.Image, PIL.ImageTk

import gui_util

# must be either 'pillow' or 'pygame'; currently 'pygame' is somewhat faster
RENDERER = 'pygame' 

IMAGE_FORMAT = 'RGBA'

class ImageWrapper():
    def __init__(self, size):
        self.size = size
        self.w, self.h = size

    def get_imagetk(self):
        """return a PIL.ImageTk for use in the tkinter UI"""

    def blit(self, other, offset):
        """blit other image onto this one with top left at offset"""

    def draw_line(self, start, end, colour, width):
        """draw a line of width on this image from start to end in colour"""

    def resize(self, new_size):
        """return a resized version of this image of new_size"""        

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

    def get_imagetk(self):
        return PIL.ImageTk.PhotoImage(PIL.Image.frombytes(
            IMAGE_FORMAT,
            self.size,
            pygame.image.tostring(self.image, IMAGE_FORMAT, False)
        ))

    def blit(self, other, offset):
        self.image.blit(other.image, offset)

    def draw_line(self, start, end, colour, width):
        pygame.draw.line(self.image, colour, start, end, width)

    def resize(self, new_size):
        return PygameImage(
            new_size, 
            pygame.transform.smoothscale(self.image, new_size)
        )

    @staticmethod
    def from_file(path):
        image = pygame.image.load(path)
        return PygameImage(image.get_size(), image)
    
class PillowImage(ImageWrapper):
    def __init__(self, size, image=None, bg_colour=0):
        super().__init__(size)
        if not image:
            self.image = PIL.Image.new(IMAGE_FORMAT, size, bg_colour)
        else:
            self.image = image
        self.draw = None

    def ensure_draw(self):
        if self.draw is None:
            self.draw = PIL.ImageDraw.Draw(self.image)

    def get_imagetk(self):
        return PIL.ImageTk.PhotoImage(self.image)

    def blit(self, other, offset):
        self.image.paste(other.image, offset, other.image)

    def draw_line(self, start, end, colour, width):
        self.ensure_draw()
        self.draw.line([start, end], colour, width)

    def resize(self, new_size):
        return PillowImage(new_size, self.image.resize(new_size))

    @staticmethod
    def from_file(path):
        image = PIL.Image.open(path).convert(IMAGE_FORMAT)
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

MARGIN = 10

class DragPoints(enum.Enum):
    NONE = 0
    BODY = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    TOP = enum.auto()
    BOT = enum.auto()
    TOPLEFT = enum.auto()
    TOPRIGHT = enum.auto()
    BOTLEFT = enum.auto()
    BOTRIGHT = enum.auto()

dragpoint_cursor_mapping = {
    DragPoints.NONE: '',
    DragPoints.BODY: 'fleur',
    DragPoints.LEFT: 'sb_h_double_arrow',
    DragPoints.RIGHT: 'sb_h_double_arrow',
    DragPoints.TOP: 'sb_v_double_arrow',
    DragPoints.BOT: 'sb_v_double_arrow',
    DragPoints.TOPLEFT: 'sizing',
    DragPoints.TOPRIGHT: 'sizing',
    DragPoints.BOTLEFT: 'sizing',
    DragPoints.BOTRIGHT: 'sizing'
}

class BattleMap():
    SCROLL_SPEED = 20
    ZOOM_SPEED = 0.1
    ZOOM_MAX = 2
    ZOOM_MIN = 0.1

    def __init__(self, master, **kwargs):
        self.master = master

        self.images = [] # List[MapImage]

        self.vp_base_w, self.vp_base_h = kwargs.get('vp_size', (1280, 720))
        self.vp_x, self.vp_y = kwargs.get('vp_pos', (0, 0))
        self.width, self.height = kwargs.get('map_size', (128, 128))
        self.tile_size = kwargs.get('tile_size', 32)
        self.zoom_level = kwargs.get('zoom_level', 1.25)
        self.bg_colour = kwargs.get('bg_colour', (0, 0, 0, 0))

        self.image = None
        self.grid_image = None
        self.grid_line_width = 2
        self.render_grid()
        self.redraw = True

        self.holding = None
        self.holding_drag_point = None

    @property
    def vp_w(self):
        return int(self.zoom_level * self.vp_base_w)
    
    @property
    def vp_h(self):
        return int(self.zoom_level * self.vp_base_h)

    @property
    def vp_size(self):
        return self.vp_w, self.vp_h

    def get_photo_image(self):
        return self.image.get_imagetk()

    def render_grid(self):
        right = self.vp_w + self.tile_size
        bottom = self.vp_h + self.tile_size

        grid = Image((right, bottom), bg_colour=gui_util.Colours.CLEAR)

        for i in range(0, self.vp_h // self.tile_size + 2):
            y = i * self.tile_size
            grid.draw_line(
                (0, y),
                (right, y),
                gui_util.Colours.BLACK,
                self.grid_line_width
            )
        
        for i in range(0, self.vp_w // self.tile_size + 2):
            x = i * self.tile_size 
            grid.draw_line(
                (x, 0),
                (x, bottom),
                gui_util.Colours.BLACK,
                self.grid_line_width
            )

        self.grid_image = grid

    def render(self):
        vp = Image(self.vp_size, bg_colour=self.bg_colour)

        for i in sorted(self.images, key=lambda i: i.z):
            x, y = i.x - self.vp_x, i.y - self.vp_y
            if 0 < x + i.w and x < self.vp_w and 0 < y + i.h and y < self.vp_h:
                vp.blit(i.image, (x, y))

        vp.blit(
            self.grid_image,
            (-(self.vp_x % self.tile_size), -(self.vp_y % self.tile_size))
        )

        self.image = vp.resize((self.vp_base_w, self.vp_base_h))
        self.redraw = False

    def get_hover_state(self, x, y):
        for i in sorted(self.images, key=lambda i: -i.z):
            drag_point = i.touching(x, y)
            if drag_point != DragPoints.NONE:
                return drag_point, i
        return DragPoints.NONE, None

    def get_map_coords(self, e_x, e_y):
        return int(e_x * self.zoom_level) + self.vp_x, \
            int(e_y * self.zoom_level) + self.vp_y

    def handle_mouse_motion(self, event):
        x, y = self.get_map_coords(event.x, event.y)
        if self.holding == None:
            point, _ = self.get_hover_state(x, y)
            if point in dragpoint_cursor_mapping:
                gui_util.set_cursor(dragpoint_cursor_mapping[point])
            elif type(point) == tuple:
                gui_util.set_cursor(dragpoint_cursor_mapping[DragPoints.BODY])
        else:
            self.holding.handle_resize(self.holding_drag_point, x, y)
            self.redraw = True

    def handle_mouse_scroll(self, event):
        zoom = gui_util.get_ctrl_down()
        x = gui_util.get_shift_down()
        direction = -1 if (event.num == 4) else 1
        if zoom:
            self.zoom_level += BattleMap.ZOOM_SPEED * direction
            self.zoom_level = max(
                min(self.zoom_level, BattleMap.ZOOM_MAX),
                BattleMap.ZOOM_MIN
            )
            self.render_grid()
        elif x:
            self.vp_x += BattleMap.SCROLL_SPEED * direction
            self.vp_x = max(min(self.vp_x, self.width * self.tile_size), 0)
        else:
            self.vp_y += BattleMap.SCROLL_SPEED * direction
            self.vp_y = max(min(self.vp_y, self.width * self.tile_size), 0)
        self.redraw = True

    def handle_mouse_down(self, event):
        if event.num == 1:
            drag_point, image = self.get_hover_state(
                *self.get_map_coords(event.x, event.y)
            )
            if drag_point != DragPoints.NONE:
                self.holding = image
                self.holding_drag_point = drag_point
        elif event.num == 2:
            pass # Middle mouse
        elif event.num == 3:
            pass # Right click
        elif event.num in [4, 5]: # Mwheel
            self.handle_mouse_scroll(event)

    def handle_mouse_up(self, event):
        if event.num == 1:
            self.holding = None
            self.holding_drag_point = None

class MapImage():
    def __init__(self, image, **kwargs):
        self.base_image = image

        w, h = image.size
        self.w = kwargs.get('width', kwargs.get('w', w))
        self.h = kwargs.get('height', kwargs.get('h', h))
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.z = kwargs.get('z', 0)

        self.image = None
        self.apply_transform()

    def apply_transform(self):
        self.image = self.base_image.resize((self.w, self.h))

    def handle_resize(self, drag_point, x, y):
        if drag_point in [
            DragPoints.TOP,
            DragPoints.TOPLEFT,
            DragPoints.TOPRIGHT
        ]:
            self.h += self.y - y
            self.y = y
        elif drag_point in [
            DragPoints.BOT,
            DragPoints.BOTLEFT,
            DragPoints.BOTRIGHT
        ]:
            self.h = y - self.y
        
        if drag_point in [
            DragPoints.LEFT,
            DragPoints.TOPLEFT,
            DragPoints.BOTLEFT
        ]:
            self.w += self.x - x
            self.x = x
        elif drag_point in [
            DragPoints.RIGHT,
            DragPoints.TOPRIGHT,
            DragPoints.BOTRIGHT
        ]:
            self.w = x - self.x

        if type(drag_point) == tuple:
            dx, dy = drag_point
            self.x = x - dx
            self.y = y - dy

        self.apply_transform()
        
    def touching(self, x, y):
        in_range_y = -MARGIN < y - self.y < self.h + MARGIN
        in_range_x = -MARGIN < x - self.x < self.w + MARGIN

        touching_left = abs(x - self.x) < MARGIN and in_range_y
        touching_top = abs(y - self.y) < MARGIN and in_range_x
        touching_right = abs(x - (self.x + self.w)) < MARGIN and in_range_y
        touching_bot = abs(y - (self.y + self.h)) < MARGIN and in_range_x

        if touching_left and touching_top:
            return DragPoints.TOPLEFT
        if touching_left and touching_bot:
            return DragPoints.BOTLEFT
        if touching_left:
            return DragPoints.LEFT
        if touching_right and touching_top:
            return DragPoints.TOPRIGHT
        if touching_right and touching_bot:
            return DragPoints.BOTRIGHT
        if touching_right:
            return DragPoints.RIGHT
        if touching_top:
            return DragPoints.TOP
        if touching_bot:
            return DragPoints.BOT
        if in_range_x and in_range_y:
            return (x - self.x, y - self.y)

        return DragPoints.NONE

    @staticmethod
    def from_file(path, **kwargs):
        return MapImage(Image.from_file(path), **kwargs)

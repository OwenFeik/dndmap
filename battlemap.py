import enum

import gui_util
import image

GRAB_MARGIN = 10

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
    SCROLL_SPEED_COEFF = 0.2 
    ZOOM_SPEED_COEFF = 0.001
    ZOOM_MAX = 1.5
    ZOOM_MIN = 0.1

    def __init__(self, master, **kwargs):
        self.master = master

        self.images = MapImageManager()

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

    def add_image(self, img):
        self.images.add_image(img)
        self.redraw = True

    def get_photo_image(self):
        return self.image.get_imagetk()

    def render_grid(self):
        right = self.vp_w + self.tile_size
        bottom = self.vp_h + self.tile_size

        grid = image.Image((right, bottom), bg_colour=gui_util.Colours.CLEAR)

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
        vp = image.Image(self.vp_size, bg_colour=self.bg_colour)

        for i in self.images:
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
        result = DragPoints.NONE, None
        for i in self.images:
            drag_point = i.touching(x, y)
            if drag_point != DragPoints.NONE:
                result = (drag_point, i)
        return result

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
            # try:
            self.holding.handle_resize(self.holding_drag_point, x, y)
            # except ValueError:
            #     pass
            self.redraw = True

    def handle_mouse_scroll(self, event):
        if event.num != '??':
            delta = -120 if event.num == 4 else 120
        else:
            delta = -event.delta

        zoom = gui_util.get_ctrl_down()
        x = gui_util.get_shift_down()
        if zoom:
            self.zoom_level += BattleMap.ZOOM_SPEED_COEFF * delta
            self.zoom_level = max(
                min(self.zoom_level, BattleMap.ZOOM_MAX),
                BattleMap.ZOOM_MIN
            )
            self.render_grid()
        elif x:
            self.vp_x += int(BattleMap.SCROLL_SPEED_COEFF * delta)
            self.vp_x = max(min(self.vp_x, self.width * self.tile_size), 0)
        else:
            self.vp_y += int(BattleMap.SCROLL_SPEED_COEFF * delta)
            self.vp_y = max(min(self.vp_y, self.width * self.tile_size), 0)
        self.redraw = True

    def handle_mouse_down(self, event):
        if event.num == 1:
            drag_point, img = self.get_hover_state(
                *self.get_map_coords(event.x, event.y)
            )
            if drag_point != DragPoints.NONE:
                self.holding = img
                self.holding_drag_point = drag_point
        elif event.num == 2:
            pass # Middle mouse
        elif event.num == 3:
            pass # Right click
        elif event.num in [4, 5]: # Mwheel
            self.handle_mouse_scroll(event)

    def handle_mouse_up(self, event):
        if event.num == 1:
            if self.holding:
                self.holding.end_resize()
            self.holding = None
            self.holding_drag_point = None
            self.redraw = True

class MapImageManager():
    """
    Stores a list of MapImage objects and ensures that they remain ordered by
    z-index for easier iteration in the BattleMap class. Lower z-indexes will
    be reached first during iteration. Negative z-index is acceptable. A new
    image will be placed first in z-index ordering.
    """

    def __init__(self):
        self.images = []
        self._iter_index = -1

    def __len__(self):
        return len(self.images)

    def __iter__(self):
        self._iter_index = -1
        return self

    def __next__(self):
        self._iter_index += 1
        if self._iter_index < len(self.images):
            return self.images[self._iter_index]
        else:
            raise StopIteration()

    def add_image(self, img):
        if type(img) == MapImage:
            new = img
        elif type(img) == image.Image:
            new = MapImage(img)
        elif type(img) == str:
            new = MapImage.from_file(img)
        else:
            raise ValueError(f'Not sure how to add {img} to battlemap.')

        self.images.insert(0, new)

class MapImage():
    MIN_HEIGHT = 32
    MIN_WIDTH = 32

    def __init__(self, img, **kwargs):
        self.base_image = img

        w, h = img.size
        self._w = kwargs.get('width', kwargs.get('w', w))
        self._h = kwargs.get('height', kwargs.get('h', h))
        self._x = kwargs.get('x', 0)
        self._y = kwargs.get('y', 0)

        self.flipped_x = self.flipped_y = False

        self.image = None
        self.apply_transform()

    @property
    def x(self):
        if self._w < 0:
            return self._x + self._w
        return self._x

    @property
    def y(self):
        if self._h < 0:
            return self._y + self._h
        return self._y

    @property
    def w(self):
        return abs(self._w)
    
    @property
    def h(self):
        return abs(self._h)

    def end_resize(self):
        if self._w < 0:
            self.flipped_x = not self.flipped_x
        if self._h < 0:
            self.flipped_y = not self.flipped_y

        self._x = self.x
        self._y = self.y
        self._w = self.w
        self._h = self.h

        self._w = max(self._w, self.MIN_WIDTH)
        self._h = max(self._h, self.MIN_HEIGHT)

        self.apply_transform()

    def apply_transform(self, fast=False):
        flip_x = (self._w < 0) ^ self.flipped_x
        flip_y = (self._h < 0) ^ self.flipped_y

        if flip_x or flip_y:
            self.image = self.base_image.flip(
                flip_x, flip_y
            ).resize((self.w, self.h), fast)
        else:
            self.image = self.base_image.resize((self.w, self.h), fast)

    def handle_resize(self, drag_point, x, y):
        if drag_point in [
            DragPoints.TOP,
            DragPoints.TOPLEFT,
            DragPoints.TOPRIGHT
        ]:
            self._h += self._y - y
            self._y = y
        elif drag_point in [
            DragPoints.BOT,
            DragPoints.BOTLEFT,
            DragPoints.BOTRIGHT
        ]:
            self._h = y - self._y
        
        if drag_point in [
            DragPoints.LEFT,
            DragPoints.TOPLEFT,
            DragPoints.BOTLEFT
        ]:
            self._w += self._x - x
            self._x = x
        elif drag_point in [
            DragPoints.RIGHT,
            DragPoints.TOPRIGHT,
            DragPoints.BOTRIGHT
        ]:
            self._w = x - self._x

        if type(drag_point) == tuple:
            dx, dy = drag_point
            self._x = x - dx
            self._y = y - dy

        self.apply_transform(True)
        
    def touching(self, x, y):
        in_range_y = -GRAB_MARGIN < y - self.y < self.h + GRAB_MARGIN
        in_range_x = -GRAB_MARGIN < x - self.x < self.w + GRAB_MARGIN

        touching_lft = abs(x - self.x) < GRAB_MARGIN and in_range_y
        touching_top = abs(y - self.y) < GRAB_MARGIN and in_range_x
        touching_rgt = abs(x - (self.x + self.w)) < GRAB_MARGIN and in_range_y
        touching_bot = abs(y - (self.y + self.h)) < GRAB_MARGIN and in_range_x

        if touching_lft and touching_top:
            return DragPoints.TOPLEFT
        if touching_lft and touching_bot:
            return DragPoints.BOTLEFT
        if touching_lft:
            return DragPoints.LEFT
        if touching_rgt and touching_top:
            return DragPoints.TOPRIGHT
        if touching_rgt and touching_bot:
            return DragPoints.BOTRIGHT
        if touching_rgt:
            return DragPoints.RIGHT
        if touching_top:
            return DragPoints.TOP
        if touching_bot:
            return DragPoints.BOT
        if in_range_x and in_range_y:
            return (x - self._x, y - self._y)

        return DragPoints.NONE

    @staticmethod
    def from_file(path, **kwargs):
        return MapImage(image.Image.from_file(path), **kwargs)

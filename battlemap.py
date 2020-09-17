import enum

import PIL.Image, PIL.ImageDraw, PIL.ImageTk

import gui_util

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

        self.holding = None
        self.holding_drag_point = None

    @property
    def vp_w(self):
        return int(self.zoom_level * self.vp_base_w)
    
    @property
    def vp_h(self):
        return int(self.zoom_level * self.vp_base_h)

    def get_photo_image(self):
        return PIL.ImageTk.PhotoImage(self.image)

    def redraw(self):
        print('redrew')
        self.render()
        self.master.set_image(self.get_photo_image())

    def render_grid(self):
        bottom = self.vp_h + self.tile_size
        right = self.vp_w + self.tile_size
        
        grid = PIL.Image.new('RGBA', (right, bottom), gui_util.Colours.CLEAR)
        draw = PIL.ImageDraw.Draw(grid)

        for i in range(0, self.vp_h // self.tile_size + 2):
            y = i * self.tile_size
            draw.line(
                [(0, y), (right, y)],
                gui_util.Colours.BLACK,
                self.grid_line_width
            )
        
        for i in range(0, self.vp_w // self.tile_size + 2):
            x = i * self.tile_size 
            draw.line(
                [(x, 0), (x, bottom)],
                gui_util.Colours.BLACK,
                self.grid_line_width
            )

        self.grid_image = grid

    def render(self):
        self.image = PIL.Image.new('RGBA', (self.vp_w, self.vp_h), self.bg_colour)
        vp = self.image

        for i in sorted(self.images, key=lambda i: i.z):
            x, y = i.x - self.vp_x, i.y - self.vp_y
            if 0 < x + i.w and x < self.vp_w and 0 < y + i.h and y < self.vp_h:
                vp.paste(i.image, (x, y))

        vp.paste(
            self.grid_image,
            (-(self.vp_x % self.tile_size), -(self.vp_y % self.tile_size)),
            self.grid_image
        )

        vp = vp.resize((self.vp_base_w, self.vp_base_h))


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
            self.redraw()

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
        self.redraw()

    def handle_mouse_down(self, event):
        print(event.num)
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
        return MapImage(PIL.Image.open(path), **kwargs)

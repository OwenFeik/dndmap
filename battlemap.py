import enum

import pygame

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
    DragPoints.NONE: 'normal',
    DragPoints.BODY: 'cross',
    DragPoints.LEFT: 'resize_x',
    DragPoints.RIGHT: 'resize_x',
    DragPoints.TOP: 'resize_y',
    DragPoints.BOT: 'resize_y',
    DragPoints.TOPLEFT: 'resize_tr_bl',
    DragPoints.TOPRIGHT: 'resize_tl_br',
    DragPoints.BOTLEFT: 'resize_tl_br',
    DragPoints.BOTRIGHT: 'resize_tr_bl'
}

class BattleMap():
    SCROLL_SPEED = 20
    ZOOM_SPEED = 0.1
    ZOOM_MAX = 2
    ZOOM_MIN = 0.1

    def __init__(self, **kwargs):
        self.images = [] # List[MapImage]

        self.vp_base_w, self.vp_base_h = kwargs.get('vp_size', (1280, 720))
        self.vp_x, self.vp_y = kwargs.get('vp_pos', (0, 0))
        self.width, self.height = kwargs.get('map_size', (128, 128))
        self.tile_size = kwargs.get('tile_size', 32)
        self.zoom_level = kwargs.get('zoom_level', 1.25)

        self.grid_image = None
        self.grid_line_width = 2
        self.render_grid()

        self.redraw = True
        self._image = None

        self.holding = None
        self.holding_drag_point = None

    @property
    def vp_w(self):
        return int(self.zoom_level * self.vp_base_w)
    
    @property
    def vp_h(self):
        return int(self.zoom_level * self.vp_base_h)

    @property
    def image(self):
        if self.redraw:
            self.render()
            self.redraw = False
        return self._image

    def render_grid(self):
        bottom = self.vp_h + self.tile_size
        right = self.vp_w + self.tile_size
        
        grid = pygame.Surface((right, bottom))
        grid.set_colorkey(gui_util.Colours.BLACK)
        grid.fill(gui_util.Colours.BLACK)
        
        for i in range(0, self.vp_h // self.tile_size + 2):
            y = i * self.tile_size
            pygame.draw.line(
                grid,
                gui_util.Colours.WHITE,
                (0, y),
                (right, y),
                self.grid_line_width
            )
        
        for i in range(0, self.vp_w // self.tile_size + 2):
            x = i * self.tile_size 
            pygame.draw.line(
                grid,
                gui_util.Colours.WHITE,
                (x, 0),
                (x, bottom),
                self.grid_line_width
            )

        self.grid_image = grid

    def render(self):
        vp = pygame.Surface((self.vp_w, self.vp_h))
        
        for i in sorted(self.images, key=lambda i: i.z):
            x, y = i.x - self.vp_x, i.y - self.vp_y
            if 0 < x + i.w and x < self.vp_w and 0 < y + i.h and y < self.vp_h:
                vp.blit(i.image, (x, y))

        vp.blit(
            self.grid_image,
            (-(self.vp_x % self.tile_size), -(self.vp_y % self.tile_size))
        )

        vp = pygame.transform.scale(vp, (self.vp_base_w, self.vp_base_h))

        self._image = vp

    def get_hover_state(self, x, y):
        for i in sorted(self.images, key=lambda i: -i.z):
            drag_point = i.touching(x, y)
            if drag_point != DragPoints.NONE:
                return drag_point, i
        return DragPoints.NONE, None

    def get_map_coords(self, event_pos):
        x, y = event_pos
        return int(x * self.zoom_level) + self.vp_x, \
            int(y * self.zoom_level) + self.vp_y

    def handle_mouse_motion(self, event):
        x, y = self.get_map_coords(event.pos)
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
        direction = -1 if (event.button == 4) else 1
        if zoom:
            self.zoom_level += BattleMap.ZOOM_SPEED * direction
            self.zoom_level = max(
                min(self.zoom_level, BattleMap.ZOOM_MAX),
                BattleMap.ZOOM_MIN
            )
            self.render_grid()
            print(self.zoom_level)
        elif x:
            self.vp_x += BattleMap.SCROLL_SPEED * direction
            self.vp_x = max(min(self.vp_x, self.width * self.tile_size), 0)
        else:
            self.vp_y += BattleMap.SCROLL_SPEED * direction
            self.vp_y = max(min(self.vp_y, self.width * self.tile_size), 0)
        self.redraw = True

    def handle_mouse_down(self, event):
        if event.button == 1:
            drag_point, image = self.get_hover_state(
                *self.get_map_coords(event.pos)
            )
            if drag_point != DragPoints.NONE:
                self.holding = image
                self.holding_drag_point = drag_point
        elif event.button == 2:
            pass # Middle mouse
        elif event.button == 3:
            pass # Right click
        elif event.button in [4, 5]: # Mwheel
            self.handle_mouse_scroll(event)

    def handle_mouse_up(self, event):
        if event.button == 1:
            self.holding = None
            self.holding_drag_point = None

    def handle_mouse_event(self, event):
        {
            pygame.MOUSEBUTTONDOWN: self.handle_mouse_down,
            pygame.MOUSEBUTTONUP: self.handle_mouse_up,
            pygame.MOUSEMOTION: self.handle_mouse_motion
        }[event.type](event)

class MapImage():
    def __init__(self, surface, **kwargs):
        self.base_image = surface

        w, h = surface.get_size()
        self.w = kwargs.get('width', kwargs.get('w', w))
        self.h = kwargs.get('height', kwargs.get('h', h))
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.z = kwargs.get('z', 0)

        self.image = None
        self.apply_transform()

    def apply_transform(self):
        self.image = pygame.transform.scale(
            self.base_image,
            (self.w, self.h)
        )

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
        return MapImage(pygame.image.load(path), **kwargs)

import enum

import pygame

import gui_util

MARGIN = 10
SCROLL_SPEED = 10

class DragPoints(enum.Enum):
    NONE = 0
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
    def __init__(self, **kwargs):
        self.images = [] # List[MapImage]

        self.vp_w, self.vp_h = kwargs.get('vp_size', (1280, 720))
        self.vp_x, self.vp_y = kwargs.get('vp_pos', (0, 0))
        self.width, self.height = kwargs.get('map_size', (128, 128))
        self.tile_size = kwargs.get('tile_size', 64)
        self.zoom_level = kwargs.get('zoom_level', 1)

        self.holding = None
        self.holding_drag_point = None

    def render(self):
        vp = pygame.Surface((self.vp_w, self.vp_h))
        
        for i in self.images:
            x, y = i.x - self.vp_x, i.y - self.vp_y
            if 0 < x + i.w and x < self.vp_w and 0 < y + i.h and y < self.vp_h:
                vp.blit(i.image, (x, y))

        pygame.draw.circle(vp, (255, 0, 0), (0, 0), 10)

        return vp

    def get_hover_state(self, x, y):
        for i in self.images:
            drag_point = i.touching(x, y)
            if drag_point != DragPoints.NONE:
                return drag_point, i
        return DragPoints.NONE, None

    def get_map_coords(self, event_pos):
        x, y = event_pos
        return x - self.vp_x, y - self.vp_y

    def handle_mouse_motion(self, event):
        x, y = self.get_map_coords(event.pos)
        if self.holding == None:
            point, _ = self.get_hover_state(x, y)
            gui_util.set_cursor(dragpoint_cursor_mapping[point])
        else:
            self.holding.handle_resize(self.holding_drag_point, x, y)

    def handle_mouse_down(self, event):
        if event.button == 1:
            drag_point, image = self.get_hover_state(*self.get_map_coords(event.pos))
            if drag_point != DragPoints.NONE:
                self.holding = image
                self.holding_drag_point = drag_point
        elif event.button == 2:
            pass # Middle mouse
        elif event.button == 3:
            pass # Right click
        elif event.button == 4: # Mwheel up
            if gui_util.get_shift_down():
                self.vp_x -= SCROLL_SPEED
            else:
                self.vp_y -= SCROLL_SPEED
        elif event.button == 5: # Mwheel down
            if gui_util.get_shift_down():
                self.vp_x += SCROLL_SPEED
            else:
                self.vp_y += SCROLL_SPEED

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
        self.w = kwargs.get('width', w)
        self.h = kwargs.get('height', h)
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)

        self.image = None
        self.apply_transform()

    @property
    def width(self):
        return self.w

    @property
    def height(self):
        return self.h

    def apply_transform(self):
        self.image = pygame.transform.scale(
            self.base_image,
            (self.width, self.height)
        )

    def handle_resize(self, drag_point, x, y):
        if drag_point == DragPoints.TOP:
            self.h += self.y - y
            self.y = y
        elif drag_point == DragPoints.BOT:
            self.h = y - self.y

        self.apply_transform()
        
    def touching(self, x, y):
        touching_left = abs(x - self.x) < MARGIN
        touching_top = abs(y - self.y) < MARGIN
        touching_right = abs(x - (self.x + self.w)) < MARGIN
        touching_bot = abs(y - (self.y + self.h)) < MARGIN

        if touching_left and touching_top:
            return DragPoints.TOPLEFT
        elif touching_left and touching_bot:
            return DragPoints.BOTLEFT
        elif touching_left:
            return DragPoints.LEFT
        elif touching_right and touching_top:
            return DragPoints.TOPRIGHT
        elif touching_right and touching_bot:
            return DragPoints.BOTRIGHT
        elif touching_right:
            return DragPoints.RIGHT
        elif touching_top:
            return DragPoints.TOP
        elif touching_bot:
            return DragPoints.BOT
        else:
            return DragPoints.NONE

    @staticmethod
    def from_file(path, **kwargs):
        return MapImage(pygame.image.load(path), **kwargs)

# pygame.init()
# pygame.display.set_caption('dndmap')

# screen = pygame.display.set_mode((1280, 720))
# map_image = pygame.image.load('map.jpg')

# m = pygame.transform.scale(map_image, (480, 600))
# screen.blit(m, (0, 0))


# def draw_handle(x, y):
#     screen.fill((0, 0, 0))
#     pygame.draw.circle(screen, (255, 0, 0), (x, y), 10)

# handle_pos = m.get_size()
# holding = False




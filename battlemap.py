import gui_util
import grid_det
import image
import stage

# TODO image flickering problem; more sever with more images

class BattleMap():
    SCROLL_SPEED_COEFF = 0.2
    SCROLL_DELTA_DEFAULT = 120 
    ZOOM_SPEED_COEFF = 0.001
    ZOOM_MAX = 1.5
    ZOOM_MIN = 0.1

    def __init__(self, **kwargs):
        self.vp_base_w, self.vp_base_h = kwargs.get('vp_size', (1280, 720))
        self.vp_x, self.vp_y = kwargs.get('vp_pos', (0, 0))

        self.stage = kwargs.get('stage', stage.Stage())

        self.image = None
        self.grid_image = None
        self.grid_line_width = 1
        self.render_grid()
        self.redraw = True

        self.holding = None
        self.holding_drag_point = None

    @property
    def vp_w(self):
        return int(self.stage.zoom_level * self.vp_base_w)
    
    @property
    def vp_h(self):
        return int(self.stage.zoom_level * self.vp_base_h)

    @property
    def vp_size(self):
        return self.vp_w, self.vp_h

    def set_vp_size(self, new_size):
        self.vp_base_w, self.vp_base_h = new_size
        self.render_grid()
        self.redraw = True

    def get_photo_image(self):
        return self.image.get_imagetk()

    def snap_to_grid(self, map_image):
        img = map_image.base_image
        row, col = grid_det.calc_grid_size(img.as_greyscale_array())
        
        map_image.set_size(
            int(map_image.w * (self.stage.tile_size / row)),
            int(map_image.h * (self.stage.tile_size / col))
        )
        self.redraw = True

    def render_grid(self):
        right = self.vp_w + self.stage.tile_size
        bottom = self.vp_h + self.stage.tile_size

        grid = image.Image(
            size=(right, bottom),
            bg_colour=gui_util.Colours.CLEAR
        )

        # add 2 to allow for cropping of grid to viewport
        for i in range(0, self.vp_h // self.stage.tile_size + 2):
            y = i * self.stage.tile_size
            grid.draw_line(
                (0, y),
                (right, y),
                gui_util.Colours.BLACK,
                self.grid_line_width
            )
        
        for i in range(0, self.vp_w // self.stage.tile_size + 2):
            x = i * self.stage.tile_size 
            grid.draw_line(
                (x, 0),
                (x, bottom),
                gui_util.Colours.BLACK,
                self.grid_line_width
            )

        self.grid_image = grid

    def render(self):
        vp = image.Image(
            size=self.vp_size,
            bg_colour=self.stage.bg_colour
        )

        for i in self.stage:
            x, y = i.x - self.vp_x, i.y - self.vp_y
            if 0 < x + i.w and x < self.vp_w and 0 < y + i.h and y < self.vp_h:
                vp.blit(i.image, (x, y))

        vp.blit(
            self.grid_image,
            (
                -(self.vp_x % self.stage.tile_size),
                -(self.vp_y % self.stage.tile_size)
            )
        )

        self.image = vp.resize((self.vp_base_w, self.vp_base_h))
        self.redraw = False

    def get_hover_state(self, x, y):
        result = gui_util.DragPoints.NONE, None
        for i in self.stage:
            drag_point = i.touching(x, y)
            if drag_point != gui_util.DragPoints.NONE:
                result = (drag_point, i)
        return result

    def get_map_coords(self, e_x, e_y):
        return int(e_x * self.stage.zoom_level) + self.vp_x, \
            int(e_y * self.stage.zoom_level) + self.vp_y

    def handle_mouse_motion(self, event):
        x, y = self.get_map_coords(event.x, event.y)
        if self.holding == None:
            point, _ = self.get_hover_state(x, y)
            if point in gui_util.dragpoint_cursor_mapping:
                gui_util.set_cursor(gui_util.dragpoint_cursor_mapping[point])
            elif type(point) == tuple:
                gui_util.set_cursor(
                    gui_util.dragpoint_cursor_mapping[gui_util.DragPoints.BODY]
                )
        else:
            try:
                self.holding.handle_resize(self.holding_drag_point, x, y)
            except ValueError:
                pass
            self.redraw = True

    def handle_mouse_scroll(self, event):
        if event.num != '??':
            delta = -BattleMap.SCROLL_DELTA_DEFAULT if event.num == 4 else \
                BattleMap.SCROLL_DELTA_DEFAULT
        else:
            delta = -event.delta

        zoom = gui_util.get_ctrl_down()
        x = gui_util.get_shift_down()
        if zoom:
            self.stage.zoom_level += BattleMap.ZOOM_SPEED_COEFF * delta
            self.stage.zoom_level = max(
                min(self.stage.zoom_level, BattleMap.ZOOM_MAX),
                BattleMap.ZOOM_MIN
            )
            self.render_grid()
        elif x:
            self.vp_x += int(BattleMap.SCROLL_SPEED_COEFF * delta)
            self.vp_x = max(
                min(self.vp_x, self.stage.width * self.stage.tile_size),
                0
            )
        else:
            self.vp_y += int(BattleMap.SCROLL_SPEED_COEFF * delta)
            self.vp_y = max(
                min(self.vp_y, self.stage.height * self.stage.tile_size),
                0
            )
        self.redraw = True

    def handle_mouse_down(self, event):
        if event.num == 1:
            drag_point, img = self.get_hover_state(
                *self.get_map_coords(event.x, event.y)
            )
            if drag_point != gui_util.DragPoints.NONE:
                self.holding = img
                self.holding_drag_point = drag_point
        elif event.num == 2:
            pass # Middle mouse
        elif event.num == 3:
            _, img = self.get_hover_state(
                *self.get_map_coords(event.x, event.y)
            )
            return img
        elif event.num in [4, 5]: # Mwheel
            self.handle_mouse_scroll(event)

    def handle_mouse_up(self, event):
        if event.num == 1:
            if self.holding:
                self.holding.end_resize()
            self.holding = None
            self.holding_drag_point = None
            self.redraw = True

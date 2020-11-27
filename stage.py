import json

import assets
import gui_util

class PositionedAsset(assets.AssetWrapper):
    """A wrapper which holds another asset, and its position in a stage."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._x = kwargs.get('x', 0)
        self._y = kwargs.get('y', 0)
        self._z = kwargs.get('z', 0)

    @property
    def x(self):
        return self._x
    
    @property
    def y(self):
        return self._y

    @property
    def z(self):
        return self.get_z()

    # this gets overridden if the asset is put into a stage.
    def get_z(self):
        return self._z

    def get_dict(self):
        return super().get_dict().update({
            'x': self.x,
            'y': self.y,
            'z': self.z
        })

class StageAsset(PositionedAsset):
    GRAB_MARGIN = 10
    MIN_HEIGHT = 32
    MIN_WIDTH = 32

    def __init__(self, img, **kwargs):
        super().__init__(asset=img)
        self.base_image = self.asset.image

        w, h = img.size
        self._w = kwargs.get('width', kwargs.get('w', w))
        self._h = kwargs.get('height', kwargs.get('h', h))
        self._x = kwargs.get('x', 0)
        self._y = kwargs.get('y', 0)

        self.flipped_x = kwargs.get('flipped_x', False)
        self.flipped_y = kwargs.get('flipped_y', False)

        self.pixel_pos = kwargs.get('pixel_pos', True)

        self.image = None
        self.apply_transform()

    def __str__(self):
        return f'<StageAsset {self.image} at ({self.x}, {self.y}) flipped ' \
            f'({self.flipped_x}, {self.flipped_y})>'

    def __repr__(self):
        return str(self)

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

    @property
    def size(self):
        return self.w, self.h

    @property
    def properties(self):
        return json.dumps(self.get_properties())

    def get_properties(self):
        return {
            'w': self.w,
            'h': self.h,
            'flipped_x': self.flipped_x,
            'flipped_y': self.flipped_y
        }

    def get_dict(self):
        return super().get_dict().update(self.get_properties())

    def set_size(self, w, h):
        self._w = w
        self._h = h
        self.apply_transform()

    def finalise_dimensions(self):
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

    def end_resize(self):
        self.finalise_dimensions()
        self.apply_transform()

    def apply_transform(self, fast=False):
        _old_image = self.image

        flip_x = (self._w < 0) ^ self.flipped_x
        flip_y = (self._h < 0) ^ self.flipped_y

        if flip_x or flip_y:
            self.image = self.base_image.flip(
                flip_x, flip_y
            ).resize((self.w, self.h), fast)
        else:
            self.image = self.base_image.resize((self.w, self.h), fast)

    def render_to(self, vp, x, y):
        vp.blit(self.image, (x, y))

    def handle_resize(self, drag_point, x, y):
        if drag_point in [
            gui_util.DragPoints.TOP,
            gui_util.DragPoints.TOPLEFT,
            gui_util.DragPoints.TOPRIGHT
        ]:
            self._h += self._y - y
            self._y = y
        elif drag_point in [
            gui_util.DragPoints.BOT,
            gui_util.DragPoints.BOTLEFT,
            gui_util.DragPoints.BOTRIGHT
        ]:
            self._h = y - self._y
        
        if drag_point in [
            gui_util.DragPoints.LEFT,
            gui_util.DragPoints.TOPLEFT,
            gui_util.DragPoints.BOTLEFT
        ]:
            self._w += self._x - x
            self._x = x
        elif drag_point in [
            gui_util.DragPoints.RIGHT,
            gui_util.DragPoints.TOPRIGHT,
            gui_util.DragPoints.BOTRIGHT
        ]:
            self._w = x - self._x

        if type(drag_point) == tuple:
            dx, dy = drag_point
            self._x = x - dx
            self._y = y - dy

        self.apply_transform(True)
        
    def touching(self, x, y):
        in_range_y = -StageAsset.GRAB_MARGIN < y - self.y < \
            self.h + StageAsset.GRAB_MARGIN
        in_range_x = -StageAsset.GRAB_MARGIN < x - self.x < \
            self.w + StageAsset.GRAB_MARGIN

        touching_lft = abs(x - self.x) < StageAsset.GRAB_MARGIN and in_range_y
        touching_top = abs(y - self.y) < StageAsset.GRAB_MARGIN and in_range_x
        touching_rgt = \
            abs(x - (self.x + self.w)) < StageAsset.GRAB_MARGIN and in_range_y
        touching_bot = \
            abs(y - (self.y + self.h)) < StageAsset.GRAB_MARGIN and in_range_x

        if touching_lft and touching_top:
            return gui_util.DragPoints.TOPLEFT
        if touching_lft and touching_bot:
            return gui_util.DragPoints.BOTLEFT
        if touching_lft:
            return gui_util.DragPoints.LEFT
        if touching_rgt and touching_top:
            return gui_util.DragPoints.TOPRIGHT
        if touching_rgt and touching_bot:
            return gui_util.DragPoints.BOTRIGHT
        if touching_rgt:
            return gui_util.DragPoints.RIGHT
        if touching_top:
            return gui_util.DragPoints.TOP
        if touching_bot:
            return gui_util.DragPoints.BOT
        if in_range_x and in_range_y:
            return (x - self._x, y - self._y)

        return gui_util.DragPoints.NONE

    @staticmethod
    def from_file(path, **kwargs):
        return StageAsset(assets.ImageAsset.from_file(path), **kwargs)

class TokenAsset(StageAsset):
    MIN_WIDTH = MIN_HEIGHT = 1

    def __init__(self, img, **kwargs):
        self.get_grid_info = kwargs.get(
            'get_grid_info',
            lambda: (Stage.DEFAULT_TILE_SIZE + Stage.DEFAULT_LINE_WIDTH,
                Stage.DEFAULT_LINE_WIDTH)
        )
        self.tile_width = kwargs.get('tile_width', 1)
        self.tile_height = kwargs.get('tile_height', 1)

        kwargs['w'] = self.tile_width * Stage.DEFAULT_TILE_SIZE
        kwargs['h'] = self.tile_height * Stage.DEFAULT_TILE_SIZE
        kwargs['pixel_pos'] = False

        super().__init__(img, **kwargs)

        self.end_resize()

    def finalise_dimensions(self):
        super().finalise_dimensions()

        ts, lw = self.get_grid_info()

        self._x = round(self._x / ts) * ts + lw // 2
        self._y = round(self._y / ts) * ts + lw // 2

        self.tile_width = round(self._w / ts)
        self.tile_height = round(self._h / ts)

        self._w = self.tile_width * ts
        self._h = self.tile_height * ts

    @property
    def properties(self):
        return json.dumps({
            'token': True,
            'tile_width': self.tile_width,
            'tile_height': self.tile_height,
            'flipped_x': self.flipped_x,
            'flipped_y': self.flipped_y
        })

def create_stage_asset(asset, **kwargs):
    if kwargs.get('token'):
        return TokenAsset(asset, **kwargs)
    else:
        return StageAsset(asset, **kwargs)

class Stage(assets.AssetLibrary):
    """A collection of PositionedAssets."""

    DEFAULT_SIZE = (32, 32)
    DEFAULT_TILE_SIZE = 32
    DEFAULT_ZOOM_LEVEL = 1
    DEFAULT_LINE_WIDTH = 1
    DEFAULT_BG_COLOUR = (0, 0, 0, 0)

    def __init__(self, **kwargs):
        super().__init__()

        self.id = kwargs.get('id', None)
        self.name = kwargs.get('title', 'untitled')
        self.description = kwargs.get('description', '')

        w, h = Stage.DEFAULT_SIZE
        self.width = kwargs.get('width', kwargs.get('w', w))
        self.height = kwargs.get('height', kwargs.get('h', h))
        
        self.tile_size = kwargs.get('tile_size', Stage.DEFAULT_TILE_SIZE)
        self.line_width = kwargs.get('line_width', Stage.DEFAULT_LINE_WIDTH)
        self.zoom_level = kwargs.get('zoom_level', Stage.DEFAULT_ZOOM_LEVEL)
        self.bg_colour = kwargs.get('bg_colour', Stage.DEFAULT_BG_COLOUR)
        self.notes = kwargs.get('notes', [])

    @property
    def total_tile_size(self):
        return self.tile_size + self.line_width

    @property
    def map_size(self):
        return self.total_tile_size * self.width, \
            self.total_tile_size * self.height

    @property
    def notes_json(self):
        return json.dumps(self.notes)

    def add(self, asset):
        if type(asset) == StageAsset:
            new = asset
        elif type(asset) == TokenAsset:
            new = asset
            new.get_grid_info = lambda: (self.total_tile_size, self.line_width)
        elif type(asset) == assets.ImageAsset:
            new = StageAsset(asset)
        else:
            raise ValueError(f'Can\'t add asset of type {type(asset)}')

        map_w, map_h = self.map_size
        if new.w > map_w or new.h > map_h:
            scale_factor = max(new.w / map_w, new.h / map_h)
            new.set_size(int(new.w / scale_factor), int(new.h / scale_factor))

        new.get_z = lambda: self.assets.index(new)
        self.assets.append(new)

    def remove(self, asset):
        if asset is None:
            return

        try:
            self.assets.remove(asset)
            asset.get_z = lambda: None
        except ValueError:
            pass

    def bring_to_front(self, asset):
        if asset is None:
            return

        if asset in self.assets:
            self.assets.remove(asset)
        self.assets.append(asset)

    def send_to_back(self, asset):
        if asset is None:
            return

        if asset in self.assets:
            self.assets.remove(asset)
        self.assets.insert(0, asset)

    def add_many(self, stage_assets):
        for a in sorted(stage_assets, key=lambda a: a.z):
            self.add(a)

    def get_bg_colour_string(self):
        return gui_util.get_hex_colour(self.bg_colour)
    
    def get_bg_colour_int(self):
        return gui_util.encode_as_integer(self.bg_colour)

    @staticmethod
    def from_db_tup(tup):
        stage_id, name, index, description, width, height, tile_size, \
            line_width, zoom_level, bg_colour_int, notes = tup

        return index, Stage(
            id=stage_id,
            name=name,
            description=description,
            width=width,
            height=height,
            tile_size=tile_size,
            line_width=line_width,
            zoom_level=zoom_level,
            bg_colour=gui_util.decode_to_colour(bg_colour_int),
            notes=json.loads(notes)
        )

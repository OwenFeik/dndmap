import json

import asset_utils
import gui_util
import image

class PositionedAsset(asset_utils.AssetWrapper):
    """A wrapper which holds another asset, and it's position in a stage."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._x = kwargs.get('x', 0)
        self._y = kwargs.get('y', 0)
        self.z = kwargs.get('z', 0)

    @property
    def x(self):
        return self._x
    
    @property
    def y(self):
        return self._y

class MapImage(PositionedAsset):
    GRAB_MARGIN = 10
    MIN_HEIGHT = 32
    MIN_WIDTH = 32

    def __init__(self, img, **kwargs):
        super().__init__(asset=img, asset_type=asset_utils.AssetType.IMAGE)
        self.base_image = self.asset.image

        w, h = img.size
        self._w = kwargs.get('width', kwargs.get('w', w))
        self._h = kwargs.get('height', kwargs.get('h', h))


        self.flipped_x = self.flipped_y = False

        self.image = None
        self.apply_transform()

    def __str__(self):
        return f'<MapImage {self.image} at ({self.x}, {self.y}) flipped ' \
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
    def properties(self):
        return json.dumps({
            'w': self.w,
            'h': self.h,
            'flipped_x': self.flipped_x,
            'flipped_y': self.flipped_y
        })

    def set_size(self, w, h):
        self._w = w
        self._h = h

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
        in_range_y = \
            -MapImage.GRAB_MARGIN < y - self.y < self.h + MapImage.GRAB_MARGIN
        in_range_x = \
            -MapImage.GRAB_MARGIN < x - self.x < self.w + MapImage.GRAB_MARGIN

        touching_lft = abs(x - self.x) < MapImage.GRAB_MARGIN and in_range_y
        touching_top = abs(y - self.y) < MapImage.GRAB_MARGIN and in_range_x
        touching_rgt = \
            abs(x - (self.x + self.w)) < MapImage.GRAB_MARGIN and in_range_y
        touching_bot = \
            abs(y - (self.y + self.h)) < MapImage.GRAB_MARGIN and in_range_x

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
        return MapImage(image.ImageAsset.from_file(path), **kwargs)


class Stage(asset_utils.AssetLibrary):
    """A collection of PositionedAssets."""

    DEFAULT_SIZE = (64, 64)
    DEFAULT_TILE_SIZE = 32
    DEFAULT_ZOOM_LEVEL = 1.25
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
        self.zoom_level = kwargs.get('zoom_level', Stage.DEFAULT_ZOOM_LEVEL)
        self.bg_colour = kwargs.get('bg_colour', Stage.DEFAULT_BG_COLOUR)
        self.notes = kwargs.get('notes', [])

    @property
    def notes_json(self):
        return json.dumps(self.notes)

    def add(self, asset):
        if type(asset) == MapImage:
            new = asset
        elif type(asset) == image.ImageAsset:
            new = MapImage(asset)
        elif type(asset) == image.Image:
            new = MapImage(image.ImageAsset(image=asset))
        elif type(asset) == str:
            new = MapImage.from_file(asset)
        else:
            raise ValueError(f'Not sure how to add {asset} to battlemap.')

        new.z = property(lambda: self.assets.index(new))
        self.assets.insert(0, new)

    def remove(self, asset):
        try:
            self.assets.remove(asset)
            asset.z = None
        except ValueError:
            pass

    def bring_to_front(self, asset):
        if asset in self.assets:
            self.assets.remove(asset)
        self.assets.insert(len(self.assets), asset)

    def send_to_back(self, asset):
        if asset in self.assets:
            self.assets.remove(asset)
        self.assets.insert(0, asset)

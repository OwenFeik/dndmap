import enum
import json
import time

import database
import image

class AssetType(enum.Enum):
    IMAGE = 0
    TOKEN = 1

class Asset():
    """A resource which can be used on a battlemap."""

    def __init__(self, **kwargs):
        """name: the human-readable name associated with the asset."""
        
        self.id = kwargs.get('id', None)
        self.path = kwargs.get('path', None)
        self.name = kwargs.get('name', 'untitled')
        self.type = kwargs.get('asset_type')
        if self.type is None:
            raise ValueError('Attempted asset creation without asset type.')

    @property
    def properties(self):
        """A json string which specifies properties of this asset type."""
        return '{}'

    @property
    def thumbnail(self):
        """A thumbnail representation of this asset."""
        return None

    def get_data(self):
        """A blob of this asset and a hash of the blob."""
        return None, None

    def save(self, path):
        """Save the asset at the location specified by path."""

class TokenAsset(Asset):
    """A token like a player or monster image."""

    def __init__(self, **kwargs):
        kwargs['asset_type'] = AssetType.TOKEN
        super().__init__(**kwargs)

        w, h = kwargs.get('size', (1, 1))
        self.w = kwargs.get('w', kwargs.get('width', w))
        self.h = kwargs.get('h', kwargs.get('height', h))
    
        self.image = kwargs.get('image', image.ImageAsset())

    @property
    def size(self):
        return self.w, self.h

    @property
    def properties(self):
        return json.dumps({'w': self.w, 'h': self.h})

class AssetWrapper(Asset):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._asset = kwargs.get('asset')

    @property
    def asset(self):
        return self._asset

class PreviewAsset(AssetWrapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._thumbnail = kwargs.get('thumbnail', image.Image())

    @property
    def thumbnail(self):
        return self._thumbnail

class PositionedAsset(AssetWrapper):
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

    @property
    def properties(self):
        return json.dumps({
            'x': self.x,
            'y': self.y,
            'z': self.z
        })

class AssetLibrary():
    """A collection of assets."""

    def __init__(self):
        self.assets = []
        self._i = None

    def __len__(self):
        return len(self.assets)

    def __iter__(self):
        self._i = -1
        return self

    def __next__(self):
        self._i += 1
        if self._i < len(self.assets):
            return self.assets[self._i]
        else:
            raise StopIteration()

    def add(self, asset):
        self.assets.append(asset)

    def delete(self, asset):
        self.assets.remove(asset)

class Stage(AssetLibrary):
    """A collection of PositionedAssets."""

    DEFAULT_SIZE = (64, 64)
    DEFAULT_TILE_SIZE = 32

    def __init__(self, **kwargs):
        super().__init__()

        self.id = kwargs.get('id', None)
        self.name = kwargs.get('title', 'untitled')
        self.description = kwargs.get('description', '')

        w, h = Stage.DEFAULT_SIZE
        self.width = kwargs.get('width', kwargs.get('w', w))
        self.height = kwargs.get('height', kwargs.get('h', h))
        
        self.tile_size = kwargs.get('tile_size', Stage.DEFAULT_TILE_SIZE)
        self.notes = []

    @property
    def notes_json(self):
        return json.dumps(self.notes)

class ArchiveLibrary(AssetLibrary):
    """
    Library which stores a list of all of the assets ever used. Doesn't store
    the actual assets, but instead keeps track of their locations and offers a
    list of them.
    """

class ProjectProperties(enum.Enum):
    NAME = 1
    DESCRIPTION = 2
    LAST_EDITED = 3
    ACTIVE_STAGE = 4

class Project():
    """A collect of stages for a specific project."""

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'untitled')
        self.path = kwargs.get('path', '')
        self.stages = kwargs.get('stages', [])
        self.active_stage = None
        self.assets = kwargs.get('assets', AssetLibrary())
        self.description = kwargs.get('description', '')

    def save(self):
        self.export(self.path)

    def export(self, path):
        """Save all of the assets in this project to a file."""

        db = database.ProjectDatabase(path)
        db.add_assets(self.assets)
        db.add_stages(self.stages)
        db.add_meta([
            (ProjectProperties.NAME, self.name),
            (ProjectProperties.DESCRIPTION, self.description),
            (ProjectProperties.LAST_EDITED, str(time.time())),
            (
                ProjectProperties.ACTIVE_STAGE,
                self.stages.index(self.active_stage)
            )
        ])

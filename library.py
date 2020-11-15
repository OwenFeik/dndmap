import enum
import json

import database

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

    @property
    def data(self):
        """A blob of this asset for storage in database."""
        return None

    @property
    def hash(self):
        """A hash of this asset."""
        return 0

    def save(self, path):
        """Save the asset at the location specified by path."""

class ImageAsset(Asset):
    """An image, like a map or a token."""

    def __init__(self, name, image, asset_type=AssetType.IMAGE):
        super().__init__(name, asset_type)
        self.image = image
    
    def save(self, path):
        pass

class TokenAsset(ImageAsset):
    """A token like a player or monster image."""

    def __init__(self, name, image, size):
        """The image for the token, the size of the token (in tiles)."""

        super().__init__(name, image, AssetType.TOKEN)

        self.size = size
        self.w, self.h = size
    
    @property
    def properties(self):
        return json.dumps({'w': self.w, 'h': self.h})

class PositionedAsset(Asset):
    """A wrapper which holds another asset, and it's position in a stage."""

    def __init__(self, name, asset, x, y, z):
        super().__init__(name)
        self.asset = asset
        self.x = x
        self.y = y
        self.z = z


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

class Project():
    """A collect of stages for a specific project."""

    def __init__(self):
        self.stages = []
        self.assets = AssetLibrary()

    def export(self, path):
        """Save all of the assets in this project to a file."""

        db = database.ProjectDatabase(path)
        db.add_assets(self.assets)
        db.add_stages(self.stages)


import enum
import json

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

    def remove(self, asset):
        self.assets.remove(asset)

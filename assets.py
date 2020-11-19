import enum
import json

import image
import util

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
        self.description = kwargs.get('description', '')
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

    def get_blob(self):
        return None

    def get_data(self):
        """A blob of this asset and a hash of the blob."""
        return self.get_blob(), None

    def save(self, path):
        """Save the asset at the location specified by path."""

    def get_dict(self):
        return {
            'id': self.id,
            'path': self.path,
            'name': self.name,
            'description': self.description,
            'asset_type': self.type
        }

class TokenAsset(Asset):
    """A token like a player or monster image."""

    def __init__(self, **kwargs):
        kwargs['asset_type'] = AssetType.TOKEN
        super().__init__(**kwargs)

        w, h = kwargs.get('size', (1, 1))
        self.w = kwargs.get('w', kwargs.get('width', w))
        self.h = kwargs.get('h', kwargs.get('height', h))
    
        self.image = kwargs.get('image', ImageAsset())

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

class AssetPreview(AssetWrapper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        thumbnail = kwargs.get('thumbnail', image.Image())
        if type(thumbnail) == bytes:
            self._thumbnail = image.Image.from_bytes(thumbnail)
        elif type(thumbnail) == image.Image:
            self._thumbnail = thumbnail
        else:
            raise TypeError('Inappropriate type passed for thumbnail.')

    @property
    def thumbnail(self):
        return self._thumbnail

class LazyAsset(AssetPreview):
    """A lazy asset pretends to be an asset and loads it when required."""

    NO_LOAD_ATTRS = [
        '_asset',
        '_init_done',
        '_thumbnail',
        'asset',
        'asset_type',
        'id',
        'load_asset',
        'loader',
        'thumbnail'
    ]

    def __init__(self, **kwargs):
        self._init_done = False

        super().__init__(**kwargs)
        self.loader = kwargs.get('loader')

        # a lazy asset needs to be able to load its asset by id
        assert self.id is not None

        self._init_done = True

    def __getattribute__(self, name):
        if not name in LazyAsset.NO_LOAD_ATTRS and self._init_done:
            self.load_asset()
            return object.__getattribute__(self._asset, name)
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if not name in LazyAsset.NO_LOAD_ATTRS and self._init_done:
            self.load_asset()
            object.__setattr__(self._asset, name, value)
        object.__setattr__(self, name, value)

    @property
    def asset(self):
        self.load_asset()
        return self._asset

    def load_asset(self):
        if self._asset is None:
            self._asset = build_from_db_tup(self.loader(self.id))

class AssetLibrary():
    """A collection of assets."""

    def __init__(self, asset_list=None):
        self.assets = []
        self._i = None

        if asset_list is not None:
            for a in asset_list:
                self.add(a)

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

class AssetMapping(AssetLibrary):
    def __init__(self, asset_list=None):
        self.mapping = {}
        super().__init__(asset_list)

    def add(self, asset):
        super().add(asset)

        if asset.id is not None:
            self.mapping[asset.id] = asset

    def remove(self, asset):
        super().remove(asset)

        if asset.id in self.mapping:
            del self.mapping[asset.id]

    def get_by_id(self, asset_id):
        return self.mapping[asset_id]

class ImageAsset(Asset):
    """An image, like a map or a token."""

    def __init__(self, **kwargs):
        kwargs['asset_type'] = AssetType.IMAGE
        super().__init__(**kwargs)
        self.image = kwargs.get('image', image.Image())
    
    @property
    def size(self):
        return self.image.size

    @property
    def properties(self):
        return '{' + f'"w": {self.image.w}, "h": {self.image.h}' + '}'

    @property
    def thumbnail(self):
        return self.image.as_thumbnail()

    def get_blob(self):
        return self.image.as_bytes()

    def get_data(self):
        """blob of this image and hash thereof"""
        blob = self.get_blob()
        return blob, hash(blob)

    def save(self, path):
        pass

    def get_dict(self):
        return super().get_dict().update({'image': self.image})

    @staticmethod
    def from_file(path):
        return ImageAsset(
            path=util.abs_path(path),
            name=util.asset_name_from_path(path),
            image=image.Image.from_file(path)
        )

def load_asset(path):
    if util.get_file_extension(path) in image.Image.FORMATS:
        return ImageAsset.from_file(path)

    raise ValueError(f'Not sure how to open {path}')

def build_from_db_tup(tup, lazy=False, loader=None):
    """
    Builds an asset from data drawn from the database. If lazy is true, the
    asset will be a LazyAsset with loader function loader.
    """

    if lazy:
        asset_id, name, asset_type, thumbnail = tup
    else:
        asset_id, name, asset_type, properties, thumbnail, description, data, \
            _asset_hash = tup
        properties = json.loads(properties)

    asset_type = AssetType(asset_type)

    if lazy:
        return LazyAsset(
            id=asset_id,
            name=name,
            asset_type=asset_type,
            thumbnail=thumbnail,
            loader=loader
        )
    elif asset_type == AssetType.IMAGE:
        return ImageAsset(
            id=asset_id,
            name=name,
            asset_type=asset_type,
            properties=properties,
            thumbnail=thumbnail,
            description=description,
            image=image.Image.from_bytes(data)
        )
    
    raise ValueError(f'I couldn\'t build an asset from the data {tup}')

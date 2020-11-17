import json

import database
import image
import library
import util

class DataContext():
    """
    The context manages project data. Where the battlemap renders the images
    and grid, the context stores the relevant assets and ensures their
    persistence between sessions.
    """

    ASSET_FORMATS = image.Image.FORMATS
    CACHE_FILE = './cache/cache.json'

    def __init__(self):
        self.archive = database.ArchiveDatabase()
        self.assets = library.ArchiveLibrary(self.archive)
        self.load_cache()

    def load_cache(self):
        with open(DataContext.CACHE_FILE, 'r') as f:
            cache = json.load(f)
        self.active_file = cache.get('active_project')
        self.project = library.Project.load(self.active_file)
        self.project_list = self.archive.load_project_list()

    def load_asset(self, path):
        ext = util.get_file_extension(path)
        if not ext in DataContext.ASSET_FORMATS:
            raise ValueError(f'Can\'t load "{ext}" files.')

        asset = image.ImageAsset.from_file(ext)

        self.project.add_asset(asset)
        self.assets.add(asset)

instance = DataContext()

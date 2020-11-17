import enum
import json
import time

import asset_utils
import database
import image
import util

class ArchiveLibrary(asset_utils.AssetLibrary):
    """
    Library which stores a list of all of the assets ever used. Doesn't store
    the actual assets, but instead keeps track of their locations and offers a
    list of them.
    """
    def __init__(self, db):
        super().__init__()
        self.db = db

    def add(self, asset):
        super().add(asset)
        self.db.add_asset(asset)

    def remove(self, asset):
        super().remove(asset)
        self.db.remove_asset(asset)

class ProjectProperties(enum.Enum):
    NAME = 1
    DESCRIPTION = 2
    LAST_EDITED = 3
    ACTIVE_STAGE = 4

class Project():
    """A collect of stages for a specific project."""

    def __init__(self, **kwargs):
        # name of the project
        self.name = kwargs.get('name', 'untitled')
        # where the project is saved
        self.path = kwargs.get('path', '')
        # list of Stage objects in the project
        self.stages = kwargs.get('stages', [])
        # the Stage currently being worked on
        self.active_stage = None
        # assets used in the project; may be used in multiple stages
        self.assets = kwargs.get('assets', asset_utils.AssetLibrary())
        # description of the project
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

    def add_asset(self, asset, insert=True):
        self.assets.add(asset)
        if insert and self.active_stage:
            self.active_stage.add(asset)

    @staticmethod
    def load(path):
        return Project(path=path)

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
        self.assets = ArchiveLibrary(self.archive)
        self.load_cache()

    def load_cache(self):
        with open(DataContext.CACHE_FILE, 'r') as f:
            cache = json.load(f)
        self.active_file = cache.get('active_project')
        self.project = Project.load(self.active_file)
        self.project_list = self.archive.load_project_list()

    def load_asset(self, path):
        ext = util.get_file_extension(path)
        if not ext in DataContext.ASSET_FORMATS:
            raise ValueError(f'Can\'t load "{ext}" files.')

        asset = image.ImageAsset.from_file(ext)

        self.project.add_asset(asset)
        self.assets.add(asset)

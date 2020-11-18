import enum
import json
import os
import time

import asset_utils
import database
import image
import stage
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
    # TODO; needs a way to prune unused assets

    FILE_FORMAT = '.ddmproj'
    SAVE_DIR = './saves/' if util.DEBUG else '~/.dndmap/saves/'

    def __init__(self, **kwargs):
        # name of the project
        self.name = kwargs.get('name', 'untitled')
        # where the project is saved
        self.path = kwargs.get('path', '')
        # the Stage currently being worked on
        self.active_stage = kwargs.get('active_stage', stage.Stage())
        # list of Stage objects in the project
        self.stages = kwargs.get('stages', [self.active_stage])
        # assets used in the project; may be used in multiple stages
        self.assets = kwargs.get('assets', asset_utils.AssetLibrary())
        # description of the project
        self.description = kwargs.get('description', '')

    def save(self):
        self.export(self.path)

    def export(self, path):
        """Save all of the assets in this project to a file."""

        self.path = path
        db = database.ProjectDatabase(path)
        db.init()
        db.add_assets(self.assets)
        db.add_stages(self.stages)
        db.add_meta([
            (ProjectProperties.NAME.value, self.name),
            (ProjectProperties.DESCRIPTION.value, self.description),
            (ProjectProperties.LAST_EDITED.value, str(time.time())),
            (
                ProjectProperties.ACTIVE_STAGE.value,
                self.stages.index(self.active_stage)
            )
        ])
        db.commit()
        db.close()

    def add_asset(self, asset, insert=True):
        self.assets.add(asset)
        if insert and self.active_stage is not None:
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

    CACHE_DIR = './cache/' if util.DEBUG else '~/.dndmap/cache/'
    ASSET_FORMATS = image.Image.FORMATS
    CACHE_FILE = CACHE_DIR + 'cache.json'
    ARCHIVE_FILE = CACHE_DIR + 'archive.db'

    def __init__(self):
        self.archive = database.ArchiveDatabase(DataContext.ARCHIVE_FILE)
        self.archive.init()
        self.assets = ArchiveLibrary(self.archive)
        self.ensure_fs()
        self.load_cache()

    def ensure_fs(self):
        for path in [DataContext.CACHE_DIR, Project.SAVE_DIR]:
            if not os.path.exists(path):
                os.mkdir(path)

    def load_cache(self):
        try:
            with open(DataContext.CACHE_FILE, 'r') as f:
                cache = json.load(f)
            self.project = Project.load(cache.get('active_project'))
        except FileNotFoundError:
            self.project = Project()
        self.project_list = self.archive.load_project_list()

    def save_cache(self):
        self.ensure_fs()
        with open(DataContext.CACHE_FILE, 'w') as f:
            json.dump({
                'active_project': self.project.path
            }, f)

    def load_asset(self, path):
        asset = asset_utils.load_asset(path)

        self.project.add_asset(asset)
        self.assets.add(asset)

    def save_project(self, path=None):
        if path is None and self.project.path is None:
            raise ValueError('Can\'t save project without path')
        elif path:
            self.project.export(path)
        else:        
            self.project.save()

        self.archive.add_project(self.project)

    def exit(self):
        self.save_cache()
        self.archive.commit()
        self.archive.close()

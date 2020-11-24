import enum
import json
import os
import time

import assets
import database
import image
import stage
import util

class ArchiveLibrary(assets.AssetLibrary):
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
    LAZY_ASSETS = True

    def __init__(self, **kwargs):
        # name of the project
        self.name = kwargs.get('name', 'untitled')
        # where the project is saved
        self.path = kwargs.get('path', None)
        
        # list of Stage objects in the project
        self.stages = kwargs.get('stages')
        if not self.stages:
            self.stages = [stage.Stage()]
        # the Stage currently being worked on
        self.active_stage = kwargs.get('active_stage', self.stages[0])

        # assets used in the project; may be used in multiple stages
        self.assets = kwargs.get('assets', assets.AssetLibrary())
        # description of the project
        self.description = kwargs.get('description', '')
        # last time the project was saved to db
        self.last_edited = kwargs.get('last_edited', None)

    def save(self):
        if self.path is None:
            raise ValueError('No file to save to.')

        self.export(self.path)

    def export(self, path):
        """Save all of the assets in this project to a file."""

        self.path = path
        db = database.ProjectDatabase(path).init()
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
        if not os.path.isfile(path):
            raise FileNotFoundError('Couldn\'t find the specified save file.')

        kwargs = {'path': path}

        db = database.ProjectDatabase(path).init()

        index_stage_pairs = \
            [stage.Stage.from_db_tup(tup) for tup in db.load_stages()]
        kwargs['stages'] = \
            [s[1] for s in sorted(index_stage_pairs, key=lambda s: s[0])]

        if Project.LAZY_ASSETS:
            asset_mapping = assets.AssetMapping()

            asset_list = [assets.build_from_db_tup(tup, lazy=True,
                loader=db.load_asset) for tup in db.load_asset_list()] 
            for a in asset_list:
                asset_mapping.add(a)
        
            kwargs['assets'] = asset_mapping
        else:
            kwargs['assets'] = assets.AssetMapping([assets.build_from_db_tup( \
                tup) for tup in db.load_assets()])

        # For each stage asset, create a stage asset object with asset drawn
        # from the project asset library. Store these in a dict mapping index
        # to a list of assets associated with that stage, then add those
        # elements to the relevant stage.
        stage_assets_by_index = {}
        for tup in db.load_stage_assets():
            stage_asset_id, asset_id, stage_index, x, y, z, properties = tup

            stage_asset = stage.StageAsset(
                kwargs['assets'].get_by_id(asset_id),
                id=stage_asset_id,
                x=x,
                y=y,
                z=z,
                **json.loads(properties)
            )
            if not stage_index in stage_assets_by_index:
                stage_assets_by_index[stage_index] = []
            stage_assets_by_index[stage_index].append(stage_asset)
        for index in stage_assets_by_index:
            kwargs['stages'][index].add_many(stage_assets_by_index[index])
            
        for key, value in db.load_meta():
            kwargs[ProjectProperties(key).name.lower()] = \
                int(value) if value.isnumeric() else value

        if 'active_stage' in kwargs:
            kwargs['active_stage'] = kwargs['stages'][kwargs['active_stage']]

        return Project(**kwargs)

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
        self.assets = ArchiveLibrary(self.archive)

        self.ensure_fs()
        self.archive.init()

        self.project = None
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
        except (FileNotFoundError, TypeError):
            self.project = Project()
        self.project_list = self.archive.load_project_list()

    def save_cache(self):
        self.ensure_fs()
        with open(DataContext.CACHE_FILE, 'w') as f:
            json.dump({
                'active_project': self.project.path
            }, f)

    def load_asset(self, path):
        asset = assets.load_asset(path)

        self.project.add_asset(asset)
        self.assets.add(asset)

    def load_project(self, path):
        self.project = Project.load(path)

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

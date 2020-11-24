import sqlite3

# Plan is: use sqlite databases as project file format.
# Also have a second database for the archive.

class Table():
    def __init__(self, name, columns, **kwargs):
        self.name = name
        
        self.count = len(columns)
        self.names = []

        self.commands = {}

        self.create_schema(columns, kwargs.get('constraints', []))            
        self.create_commands()


    def create_schema(self, columns, constraints):
        schema = f'CREATE TABLE IF NOT EXISTS {self.name}('
        for n, t in columns:
            self.names.append(n)
            schema += f'{n} {t}, '

        for c in constraints:
            schema += f'{c}, '

        if schema[-2:] == ', ':
            schema = schema[:-2]

        schema += ');'

        self.commands['SCHEMA'] = schema

    def create_commands(self):
        self.commands['INSERT'] = \
            f'INSERT INTO {self.name} ({self.all_cols()}) VALUES ' \
            f'({self.var_str()});'
        self.commands['REPLACE'] = \
            f'REPLACE INTO {self.name} ({self.all_cols()}) VALUES ' \
            f'({self.var_str()});'
        self.commands['SELECT_ALL'] = \
            f'SELECT {self.all_cols()} FROM {self.name};'
        self.commands['SELECT_ROWID'] = \
            f'SELECT last_insert_rowid() FROM {self.name};'

    def all_cols(self):
        return ', '.join(self.names)

    def var_str(self):
        return ('?, ' * self.count)[:-2]

    def command(self, name):
        return self.commands[name]

class Database():
    VERSION = 0

    def __init__(self, file):
        self.file = file
        self.conn = None
        self.tables = {}
        self.startup_commands = [
            f'PRAGMA user_version = {Database.VERSION};',
            'PRAGMA foreign_keys = ON;'
        ]

    def init(self):
        self.conn = sqlite3.connect(self.file)
        self.migrate()

        for t in self.tables:
            self.startup_commands.append(self.tables[t].commands['SCHEMA'])
        for c in self.startup_commands:
            self.execute(c)

        return self # useful for chaining

    def migrate(self):
        from_version = self.fetch_single('PRAGMA user_version;')
        if from_version != self.VERSION:
            raise ValueError('Wrong database version!')

    def execute(self, command, tup=None):
        if tup is None:
            self.conn.execute(command)
        else:
            self.conn.execute(command, tup)

    def execute_many(self, command, tups):
        self.conn.executemany(command, tups)

    def execute_cursor(self, command, tup=None):
        curs = self.conn.cursor()
        if tup is None:
            curs.execute(command)
        else:
            curs.execute(command, tup)

        return curs

    def fetch_one(self, command, tup=None):        
        return self.execute_cursor(command, tup).fetchone()

    def fetch_all(self, command, tup=None):
        return self.execute_cursor(command, tup).fetchall()

    def fetch_single(self, command, tup=None):
        ret, = self.fetch_one(command, tup)
        return ret

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

class ProjectDatabase(Database):
    """
    This class is used for saving a project to a file. It will store images and
    similar assets as blobs for portability.
    """

    VERSION = 0

    def __init__(self, file):
        super().__init__(file)

        self.tables = {}

        self.tables['assets'] = Table('assets', [
            ('id', 'INTEGER PRIMARY KEY'),
            ('name', 'TEXT'),
            ('type', 'INTEGER'),
            ('properties', 'TEXT'),
            ('thumbnail', 'BLOB'),
            ('description', 'TEXT'),
            ('data', 'BLOB'),
            ('hash', 'INTEGER')
        ])
        self.tables['stages'] = Table('stages', [
            ('id', 'INTEGER PRIMARY KEY'),
            ('name', 'TEXT'),
            ('idx', 'INTEGER NOT NULL UNIQUE'),
            ('description', 'TEXT'),
            ('width', 'INTEGER'),
            ('height', 'INTEGER'),
            ('tile_size', 'INTEGER'),
            ('line_width', 'INTEGER'),
            ('zoom_level', 'FLOAT'),
            ('bg_colour', 'INTEGER'),
            ('notes', 'TEXT')
        ])
        self.tables['stage_assets'] = Table('stage_assets', [
            ('id', 'INTEGER PRIMARY KEY'),
            ('asset', 'INTEGER'),
            ('stage', 'INTEGER'),
            ('x', 'INTEGER'),
            ('y', 'INTEGER'),
            ('z', 'INTEGER'),
            ('properties', 'TEXT')
        ], constraints=[
            'FOREIGN KEY(asset) REFERENCES assets(id)',
            'FOREIGN KEY(stage) REFERENCES stages(id)'
        ])
        self.tables['meta'] = Table('meta', [
            ('key', 'INTEGER PRIMARY KEY'),
            ('value', 'TEXT')
        ])

    def db_tup_from_asset(self, asset):
        blob, blob_hash = asset.get_data()
        return (
            asset.id,
            asset.name,
            asset.type.value,
            asset.properties,
            asset.thumbnail.as_bytes(),
            asset.description,
            blob,
            blob_hash
        )
 
    def add_asset(self, asset):
        """Adds an asset to the db, setting its id property if unset."""

        self.execute(
            self.tables['assets'].command('REPLACE'),
            self.db_tup_from_asset(asset)
        )

        if asset.id is None:
            asset.id = self.fetch_single(
                'SELECT last_insert_rowid() FROM assets;'
            ) 
    
    def add_assets(self, assets):
        """Add assets to the db, setting their ids if unset."""

        self.execute_many(
            self.tables['assets'].command('REPLACE'),
            [self.db_tup_from_asset(a) for a in assets if a.id is not None]
        )
        for a in [a for a in assets if a.id is None]:
            self.add_asset(a)

    def load_asset(self, asset_id):
        return self.fetch_one(
            'SELECT * FROM assets WHERE id = ?;',
            (asset_id,)
        )

    def load_assets(self):
        return self.fetch_all('SELECT * FROM assets;')

    def load_asset_list(self):
        return self.fetch_all(
            'SELECT id, name, type, thumbnail FROM assets;'
        )

    def db_tup_from_stage_asset(self, stage_asset, stage_id):
        return (
            stage_asset.id,
            stage_asset.asset.id,
            stage_id,
            stage_asset.x,
            stage_asset.y,
            stage_asset.z,
            stage_asset.properties
        )

    def add_stage_asset(self, stage_asset, stage_id):
        self.execute(
            self.tables['stage_assets'].command('REPLACE'),
            self.db_tup_from_stage_asset(stage_asset, stage_id)
        )

        if stage_asset.id is None:
            stage_asset.id = self.fetch_single(
                self.tables['stage_assets'].command('SELECT_ROWID')
            )

    def load_stage_assets(self):
        return self.fetch_all(
            'SELECT stage_assets.id, asset, idx, x, y, z, properties FROM '
            'stage_assets INNER JOIN stages ON stages.id = stage_assets.stage;'
        )

    def purge_stage_assets(self):
        self.execute('DELETE FROM stage_assets;')

    def db_tup_from_stage(self, stage, index):
        return (
            stage.id,
            stage.name,
            index,
            stage.description,
            stage.width,
            stage.height,
            stage.tile_size,
            stage.line_width,
            stage.zoom_level,
            stage.get_bg_colour_int(),
            stage.notes_json
        )

    def add_stage(self, stage, index):
        """Insert a stage to the db, setting its id if unset."""

        self.execute(
            self.tables['stages'].command('REPLACE'),
            self.db_tup_from_stage(stage, index)
        )

        if stage.id is None:
            stage.id = self.fetch_single(
                self.tables['stages'].command('SELECT_ROWID')
            )

    def add_stages(self, stages):
        batch = []
        indiv = []

        for i, s in enumerate(stages):
            if s.id is None:
                indiv.append((s, i))
            else:
                batch.append(self.db_tup_from_stage(s, i))

        self.execute_many(self.tables['stages'].command('REPLACE'), batch)
        for tup in indiv:
            self.add_stage(*tup)

        self.purge_stage_assets()

        batch = []
        indiv = []
        for s in stages:
            for a in s:
                if a.id is None:
                    indiv.append((a, s.id))
                else:
                    batch.append(self.db_tup_from_stage_asset(a, s.id))

        self.execute_many(
            self.tables['stage_assets'].command('REPLACE'),
            batch
        )
        for tup in indiv:
            self.add_stage_asset(*tup)

    def load_stages(self):
        return self.fetch_all(self.tables['stages'].command('SELECT_ALL'))

    def add_meta(self, entries):
        self.execute_many(self.tables['meta'].command('REPLACE'), entries)

    def load_meta(self):
        return self.fetch_all(self.tables['meta'].command('SELECT_ALL'))

class ArchiveDatabase(Database):
    """
    This class is used to keep track of the available assets on the local pc.
    It stores images an the like by file path; more of a directory reference
    than an asset store.
    """

    VERSION = 0

    def __init__(self, file):
        super().__init__(file)

        self.tables['assets'] = Table('assets', [
            ('path', 'TEXT COLLATE NOCASE PRIMARY KEY'),
            ('name', 'TEXT'),
            ('type', 'INTEGER'),
            ('properties', 'TEXT'),
            ('thumbnail', 'BLOB'),
            ('description', 'TEXT')
        ])
        self.tables['projects'] = Table('projects', [
            ('path', 'TEXT COLLATE NOCASE PRIMARY KEY'),
            ('name', 'TEXT'),
            ('description', 'TEXT')
        ])

    def db_tup_from_asset(self, asset):
        return (
            asset.path,
            asset.name,
            asset.type.value,
            asset.properties,
            asset.thumbnail.as_bytes(),
            asset.description
        )

    def add_asset(self, asset):
        self.execute(
            self.tables['assets'].command('REPLACE'),
            self.db_tup_from_asset(asset)
        )

    def remove_assset(self, asset):
        self.execute(
            'DELETE FROM assets WHERE path = ?;',
            asset.path
        )

    def db_tup_from_project(self, project):
        return (
            project.path,
            project.name,
            project.description
        )

    def add_project(self, project):
        self.execute(
            self.tables['projects'].command('REPLACE'),
            self.db_tup_from_project(project)
        )

    def load_project_list(self):
        return self.fetch_all(self.tables['projects'].command('SELECT_ALL'))

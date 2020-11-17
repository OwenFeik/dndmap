import sqlite3

# Plan is: use sqlite databases as project file format.
# Also have a second database for the archive.

class Database():
    VERSION = 0

    def __init__(self, file):
        self.file = file
        self.conn = None
        self.startup_commands = [
            f'PRAGMA user_version = {Database.VERSION};',
            'PRAGMA foreign_keys = ON;'
        ]

    def init(self):
        self.migrate()
        self.conn = sqlite3.connect(self.file)
        for c in self.startup_commands:
            self.execute(c)

    def migrate(self):
        curs = self.conn.cursor()
        curs.execute('PRAGMA user_version;')
        from_version = curs.fetchone()

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

        self.startup_commands.append(
            'CREATE TABLE IF NOT EXISTS assets ('
                'id INTEGER PRIMARY KEY, '
                'name TEXT, '
                'type INTEGER, '
                'properties TEXT, '
                'thumbnail BLOB, '
                'description TEXT, '
                'data BLOB, '
                'hash INTEGER'
            ');'    
        )
        self.startup_commands.append(
            'CREATE TABLE IF NOT EXISTS stages ('
                'id INTEGER PRIMARY KEY, '
                'name TEXT UNIQUE, '
                'index INTEGER UNIQUE, '
                'description TEXT, '
                'width INTEGER, '
                'height INTEGER, '
                'tile_size INTEGER, '
                'notes TEXT'
            ');'
        )
        self.startup_commands.append(
            'CREATE TABLE IF NOT EXISTS stage_assets ('
                'id INTEGER PRIMARY KEY, '
                'asset INTEGER, ',
                'stage INTEGER, '
                'x INTEGER, ',
                'y INTEGER, ',
                'z INTEGER, ',
                'FOREIGN KEY(asset) REFERENCES assets(id), '
                'FOREIGN KEY(stage) REFERENCES stages(id)'
            ');'
        )
        self.startup_commands.append(
            'CREATE TABLE IF NOT EXISTS meta ('
                'key INTEGER PRIMARY KEY',
                'value TEXT'
            ');'
        )

    def db_tup_from_asset(self, asset):
        blob, blob_hash = asset.get_data()
        return (
            asset.id,
            asset.name,
            asset.type,
            asset.properties,
            asset.thumbnail,
            blob,
            blob_hash
        )
 
    def add_asset(self, asset):
        """Adds an asset to the db, setting it's id property if unset."""

        self.execute(
            'REPLACE INTO assets('
                'id, name, type, properties, thumbnail, data, hash'
            ') VALUES (?, ?, ?, ?, ?, ?, ?);',
            self.db_tup_from_asset(asset)
        )

        if asset.id is None:
            asset.id = self.fetch_single(
                'SELECT last_insert_rowid() FROM assets;'
            ) 
    
    def add_assets(self, assets):
        """Add assets to the db, setting their ids if unset."""

        self.execute_many(
            'REPLACE INTO assets('
                'id, name, type, properties, thumbnail, data, hash'
            ') VALUES (?, ?, ?, ?, ?, ?, ?);',
            [self.db_tup_from_asset(a) for a in assets if a.id is not None]
        )
        for a in [a for a in assets if a.id is None]:
            self.add_asset(a)

    def load_asset(self, asset_id):
        return self.fetch_one(
            'SELECT * FROM assets WHERE id = ?;',
            (asset_id,)
        )

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
            stage_asset.z
        )

    def add_stage_asset(self, stage_asset, stage_id):
        self.execute(
            'REPLACE INTO stage_assets (id, asset, stage, x, y, z) '
            'VALUES (?, ?, ?, ?, ?, ?);',
            self.db_tup_from_stage_asset(stage_asset, stage_id)
        )

        if stage_asset.id is None:
            stage_asset.id = self.fetch_single(
                'SELECT last_insert_rowid() FROM stage_assets;'
            )

    def db_tup_from_stage(self, stage, index):
        return (
            stage.id,
            stage.name,
            index,
            stage.description,
            stage.width,
            stage.height,
            stage.tile_size,
            stage.notes_json
        )

    def add_stage(self, stage, index):
        """Insert a stage to the db, setting its id if unset."""

        self.execute(
            'REPLACE INTO stages('
                'id, name, index, description, width, height, tile_size, notes'
            ') VALUES (?, ?, ?, ?, ?, ?, ?, ?);',
            self.db_tup_from_stage(stage, index)
        )

        if stage.id is None:
            stage.id = self.fetch_one('SELECT last_insert_rowid() FROM stages;')

    def add_stages(self, stages):
        batch = []
        indiv = []

        for i, s in enumerate(stages):
            if s.id is None:
                indiv.append((s, i))
            else:
                batch.append(self.db_tup_from_stage(s, i))

        self.execute_many(
            'REPLACE INTO stages('
                'id, name, index, description, width, height, tile_size, notes'
            ') VALUES (?, ?, ?, ?, ?, ?, ?, ?);',
            batch
        )
        for tup in indiv:
            self.add_stage(*tup)

        batch = []
        indiv = []
        for s in stages:
            for a in s:
                if a.id is None:
                    indiv.append((a, s.id))
                else:
                    batch.append(self.db_tup_from_stage_asset(a, s.id))

        self.execute_many(
            'REPLACE INTO stage_assets (id, asset, stage, x, y, z) '
            'VALUES (?, ?, ?, ?, ?, ?);',
            batch
        )
        for tup in indiv:
            self.add_stage_asset(*tup)

    def add_meta(self, entries):
        self.execute_many(
            'REPLACE INTO meta (key, value) VALUES (?, ?);',
            entries
        )

    def load_meta(self):
        return self.fetch_all('SELECT * FROM meta;')

class ArchiveDatabase(Database):
    """
    This class is used to keep track of the available assets on the local pc.
    It stores images an the like by file path; more of a directory reference
    than an asset store.
    """

    ARCHIVE_FILE = './cache/archive.db'
    VERSION = 0

    def __init__(self):
        super().__init__(ArchiveDatabase.ARCHIVE_FILE)

        self.startup_commands.append(
            'CREATE TABLE IF NOT EXISTS assets ('
                'path TEXT COLLATE NOCASE PRIMARY KEY, '
                'name TEXT, '
                'type INTEGER, '
                'properties TEXT, '
                'thumbnail BLOB, '
                'description TEXT'
            ');'
        )
        self.startup_commands.append(
            'CREATE TABLE IF NOT EXISTS projects ('
                'path TEXT COLLATE NOCASE PRIMARY KEY, '
                'name TEXT, '
                'description TEXT'
            ');'
        )

    def db_tup_from_asset(self, asset):
        return (
            asset.path.
            asset.name,
            asset.type,
            asset.properties,
            asset.thumbnail,
            asset.description
        )

    def add_asset(self, asset):
        self.execute(
            'REPLACE INTO assets('
                'path, name, type, properties, thumbnail, description'
            ') VALUES (?, ?, ?, ?, ?, ?);',
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
            'REPLACE INTO projects(path, name, description) VALUES (?, ?, ?);',
            self.db_tup_from_project(project)
        )

    def load_project_list(self):
        return self.fetch_all('SELECT * FROM projects;')

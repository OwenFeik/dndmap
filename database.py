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

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

class ProjectDatabase(Database):
    """
    This class is used for saving a project to a file. It will store images an
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
                'name TEXT, '
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

    def db_tup_from_asset(self, asset):
        return (
            asset.id,
            asset.name,
            asset.type,
            asset.properties,
            asset.thumbnail,
            asset.data,
            asset.hash
        )
 
    def add_asset(self, asset):
        self.execute(
            'INSERT INTO assets('
                'id, name, type, properties, thumbnail, data, hash'
            ') VALUES (?, ?, ?, ?, ?, ?, ?);',
            self.db_tup_from_asset(asset)
        )
    
    def add_assets(self, assets):
        self.execute_many(
            'INSERT INTO assets('
                'id, name, type, properties, thumbnail, data, hash'
            ') VALUES (?, ?, ?, ?, ?, ?, ?);',
            [self.db_tup_from_asset(a) for a in assets]
        )

    def db_tup_from_stage(self, stage):
        return (
            stage.id,
            stage.name,
            stage.description,
            stage.width,
            stage.height,
            stage.tile_size,
            stage.notes_json
        )

    def add_stages(self, stages):
        self.execute(
            'INSERT INTO stages('
                'id, name, description, width, height, tile_size, notes'
            ') VALUES (?, ?, ?, ?, ?, ?, ?);',
            [self.db_tup_from_stage(s) for s in stages]
        )

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

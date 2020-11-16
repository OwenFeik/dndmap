import json

import database
import library

class DataContext():
    """
    The context manages project data. Where the battlemap renders the images
    and grid, the context stores the relevant assets and ensures their
    persistence between sessions.
    """

    CACHE_FILE = './cache/cache.json'

    def __init__(self):
        self.archive = database.ArchiveDatabase()


    def load_cache(self):
        with open(DataContext.CACHE_FILE, 'r') as f:
            cache = json.load(f)
        self.active_file = cache.get('active_project')
        self.project = library.Project.load(self.active_file)

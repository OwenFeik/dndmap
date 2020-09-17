class ModKeys():
    SHIFT_L = 65505
    SHIFT_R = 65506
    CONTROL_L = 65508
    CONTROL_R = 65507
    ALT_L = 65513
    ALT_R = 65514    

class Colours():
    BLACK = (0, 0, 0, 255)
    CLEAR = (0, 0, 0, 0)
    WHITE = (255, 255, 255, 255)

class KeyHandler():
    def __init__(self):
        self.keystates = {}

    def handle_key_down(self, e):
        self.keystates[e.keysym_num] = True

    def handle_key_up(self, e):
        self.keystates[e.keysym_num] = False 

    def get_key_down(self, ksn):
        return self.keystates.get(ksn, False)

key_handler = KeyHandler()

handle_key_down = key_handler.handle_key_down
handle_key_up = key_handler.handle_key_up
get_key_down = key_handler.get_key_down

def get_shift_down():
    return get_key_down(ModKeys.SHIFT_L) or get_key_down(ModKeys.SHIFT_R)

def get_ctrl_down():
    return get_key_down(ModKeys.CONTROL_L) or get_key_down(ModKeys.CONTROL_R)

class CursorManager():
    def __init__(self):
        self.root = None

    def init_cursor_manager(self, root):
        self.root = root

    def set_cursor(self, name):
        self.root.config(cursor=name)

cursor_manager = CursorManager()

init_cursor_manager = cursor_manager.init_cursor_manager
set_cursor = cursor_manager.set_cursor

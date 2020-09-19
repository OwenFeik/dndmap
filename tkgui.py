import threading
import time
import tkinter as tk

import battlemap

import gui_util

root = tk.Tk()
running = True

class BattleMapLabel(tk.Frame):
    FRAME_RATE_TARGET = 60

    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self.bm = battlemap.BattleMap(master=self, **kwargs)
        self.bm.images.append(battlemap.MapImage.from_file('map.bmp', z=1))
        self.bm.images.append(battlemap.MapImage.from_file('village.jpg', width=400, height=400, x=100, y=500))
        self.bm.render()

        self.old_image = None
        self.image = self.bm.get_photo_image()
        self.label = tk.Label(self, image=self.image)
        self.label.pack()

        self.label.bind('<Button>', self.bm.handle_mouse_down)
        self.label.bind('<ButtonRelease>', self.bm.handle_mouse_up)
        self.label.bind('<MouseWheel>', self.bm.handle_mouse_scroll)
        self.label.bind('<Motion>', self.bm.handle_mouse_motion)

        self.prev_frame = time.time_ns()
        self.frame_time = 1e9 / self.FRAME_RATE_TARGET
        self.render_thread = None
        self.rendering = True
        self.start_render_thread()

    def destroy(self):
        self.rendering = False
        super().destroy()

    def refresh_image(self):
        while self.rendering:
            if self.bm.redraw:
                self.bm.render()
                self.old_image = self.image
                self.image = self.bm.get_photo_image()
                self.label.configure(image=self.image)
                self.prev_frame = time.time_ns()
                root.update_idletasks()
            
            delta_t = time.time_ns() - self.prev_frame 
            if delta_t < self.frame_time:
                time.sleep(delta_t / 1e9)

    def start_render_thread(self):
        self.render_thread = threading.Thread(target=self.refresh_image)
        self.render_thread.start()

    def end_render_thread(self, _):
        self.rendering = False

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.hi_there = tk.Button(self)
        self.hi_there['text'] = 'Hello World\n(click me)'
        self.hi_there['command'] = lambda: print(gui_util.get_shift_down())
        self.hi_there.pack(side='top')

        self.image = BattleMapLabel(self)
        self.image.pack(side='bottom')
        # self.image.bind('<Button>', lambda e: print(e.__dict__))
        # self.image.bind('<ButtonRelease>', lambda e: print(e.__dict__))

        self.quit = tk.Button(self, text='Exit', fg='red', 
            command=self.master.destroy)
        self.quit.pack(side='bottom')

gui_util.init_cursor_manager(root)
root.bind('<Key>', gui_util.handle_key_down)
root.bind('<KeyRelease>', gui_util.handle_key_up)
root.config(bg=gui_util.get_hex_colour(gui_util.BG_COLOUR))
app = Application(root)

app.mainloop()

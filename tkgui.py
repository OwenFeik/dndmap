import tkinter as tk

import battlemap

import gui_util

root = tk.Tk()

class BattleMapLabel(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self.bm = battlemap.BattleMap(master=self, **kwargs)
        self.bm.images.append(battlemap.MapImage.from_file('map.jpg', z=1))
        self.bm.images.append(battlemap.MapImage.from_file('map2.jpg', width=400, height=400, x=100, y=500))
        self.bm.render()

        self.image = self.bm.get_photo_image()
        self.label = tk.Label(self, image=self.image)
        self.label.pack()

        self.label.bind('<Button>', self.handle_mouse_down)
        self.label.bind('<ButtonRelease>', self.handle_mouse_up)

    def set_image(self, image):
        self.image = image
        self.label.configure(image=self.image)
        root.update_idletasks()

    def handle_mouse_down(self, e):
        self.bm.handle_mouse_down(e)

    def handle_mouse_up(self, e):
        self.bm.handle_mouse_up(e)

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
app = Application(root)
app.mainloop()

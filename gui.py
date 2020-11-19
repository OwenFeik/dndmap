import threading
import time
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox

import battlemap
import gui_util
import library

root = tk.Tk()
running = True
context = library.DataContext()

class BattleMapContextMenu(tk.Menu):
    def __init__(self, master):
        super().__init__(master, tearoff=0)
        self.bm = master.bm

        self.add_command(label='Add image', command=self.add_asset)

    def show(self, e):
        self.tk_popup(e.x_root, e.y_root, 0)

    def add_asset(self):
        try:
            context.load_asset(
                tkinter.filedialog.askopenfilename(
                    filetypes=[(
                        'Image files',
                        ' '.join([f'*.{ext.lower()}' for ext in \
                            library.DataContext.ASSET_FORMATS])
                    )]
                )
            )
        except ValueError:
            tkinter.messagebox.showerror('Error', 'Failed to load image.')

class BattleMapImageContextMenu(BattleMapContextMenu):
    def __init__(self, master):
        super().__init__(master)
        self.target = None
        
        self.insert_separator(0)
        self.insert_command(
            0,
            label="Delete",
            command=lambda: context.project.active_stage.remove(self.target)
        )
        self.insert_command(
            0,
            label="Snap to grid",
            command=self.snap_to_grid
        )
        self.insert_command(
            0,
            label="Bring to front",
            command=lambda: \
                context.project.active_stage.bring_to_front(self.target)
        )
        self.insert_command(
            0,
            label="Send to back",
            command=lambda: \
                context.project.active_stage.send_to_back(self.target)
        )

    def show_on_image(self, e, img):
        self.target = img
        super().show(e)

    def snap_to_grid(self):
        if self.target is None:
            return
        
        try:
            self.bm.snap_to_grid(self.target)
        except ValueError:
            tkinter.messagebox.showerror(
                'Error',
                'Failed to detect grid size of this image.'
            )

class BattleMapLabel(tk.Frame):
    FRAME_RATE_TARGET = 60
    IDLE_FRAME_RATE = 10
    BORDER_THICKNESS = 10

    def __init__(self, master=None):
        super().__init__(master)
        self.bm = battlemap.BattleMap(stage=context.project.active_stage)

        self.bm.render()

        self.image = None
        self.create_image()

        self.background_menu = BattleMapContextMenu(self)
        self.image_menu = BattleMapImageContextMenu(self)

        self.bind_events()

        self.rendering = True
        self.start_render_thread()

        self.pack(fill="both", expand=True)

    def create_image(self):
        self.image = self.bm.get_photo_image()
        self.label = tk.Label(
            self,
            image=self.image,
            highlightthickness=BattleMapLabel.BORDER_THICKNESS,
            relief="solid",
            highlightbackground=gui_util.get_hex_colour(gui_util.BG_COLOUR)
        )
        self.label.pack(fill="both", expand=True)

    def show_context_menu(self, e):
        img = self.bm.handle_mouse_down(e)
        if img is None:
            self.background_menu.show(e)
        else:
            self.image_menu.show_on_image(e, img)

    def bind_events(self):
        self.label.bind('<Button>', self.bm.handle_mouse_down)
        self.label.bind('<ButtonRelease>', self.bm.handle_mouse_up)
        self.label.bind('<MouseWheel>', self.bm.handle_mouse_scroll)
        self.label.bind('<Motion>', self.bm.handle_mouse_motion)
        self.label.bind('<Button-3>', self.show_context_menu)
        self.label.bind('<Configure>', self.resize)

    def resize(self, e):
        self.label.config(width=e.width, height=e.height)
        self.bm.set_vp_size((
            e.width - 2 * BattleMapLabel.BORDER_THICKNESS,
            e.height - 2 * BattleMapLabel.BORDER_THICKNESS
        ))
        
    def destroy(self):
        self.rendering = False
        super().destroy()

    def refresh_image(self):
        prev_frame = time.time_ns()
        frame_time_min = 1e9 / self.FRAME_RATE_TARGET # in ns, hence 1e9
        frame_time_max = 1e9 / self.IDLE_FRAME_RATE

        while self.rendering:
            if self.bm.redraw or \
                time.time_ns() > (prev_frame + frame_time_max):
                
                self.bm.render()

                _old_image = self.image # need to stop from being eaten by gc
                self.image = self.bm.get_photo_image()
                self.label.configure(image=self.image)
                
                root.update_idletasks()
                prev_frame = time.time_ns()
            
            delta_t = time.time_ns() - (prev_frame + frame_time_min) 
            if delta_t > 0:
                time.sleep(delta_t / 1e9)

    def start_render_thread(self):
        render_thread = threading.Thread(target=self.refresh_image)
        render_thread.setDaemon(True)
        render_thread.start()

class TitleBarMenu(tk.Menu):
    def __init__(self, master):
        super().__init__(master)
        root.config(menu=self)

        filemenu = tk.Menu(self, tearoff=0)
        filemenu.add_command(label='Save', command=self.save_project)
        filemenu.add_command(label='Open', command=self.open_project)
        filemenu.add_separator()
        filemenu.add_command(label='Quit', command=root.destroy)

        self.add_cascade(label='File', menu=filemenu)

    def save_project(self):
        try:
            context.save_project()
            return
        except ValueError:
            pass

        path = tkinter.filedialog.asksaveasfilename(
            defaultextension=library.Project.FILE_FORMAT,
            initialfile='myproject' + library.Project.FILE_FORMAT,
            initialdir=library.Project.SAVE_DIR
        )
        context.save_project(path)

    def open_project(self):
        if tkinter.messagebox.askyesno(
            title='Save project?',
            message='If you open a different project, unsaved work will be'
                ' lost. Save now?'
        ):
            self.save_project()

        path = tkinter.filedialog.askopenfilename(
            filetypes=[(
                'Project files',
                f'*{library.Project.FILE_FORMAT}'
            )],
            initialdir=library.Project.SAVE_DIR
        )

        if path:
            context.load_project(path)

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.menu = TitleBarMenu(self)
        self.image = BattleMapLabel(self)
        self.image.pack(side='bottom')

    def destroy(self):
        context.exit()
        super().destroy()

def configure_root():
    gui_util.init_cursor_manager(root)
    root.bind('<Key>', gui_util.handle_key_down)
    root.bind('<KeyRelease>', gui_util.handle_key_up)
    root.config(bg=gui_util.get_hex_colour(gui_util.BG_COLOUR))

configure_root()
app = Application(root)

app.image.bm.redraw = True

app.mainloop()

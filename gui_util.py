import pygame

class CursorManager():
    def __init__(self):
        size_and_pos = ((24, 16), (0, 0))
        self.cursors = {
            'normal': pygame.cursors.arrow,
            'resize_x': (
                *size_and_pos,
                *pygame.cursors.compile(pygame.cursors.sizer_x_strings)
            ),
            'resize_y': (
                (16, 24),
                (0, 0),
                *pygame.cursors.compile(pygame.cursors.sizer_y_strings)
            ),
            'resize_tr_bl': (
                *size_and_pos,
                *pygame.cursors.compile(pygame.cursors.sizer_xy_strings)
            ),
            'resize_tl_br': (
                *size_and_pos,
                *pygame.cursors.compile(
                    [s[::-1] for s in pygame.cursors.sizer_xy_strings]
                )
            )
        }

    def set_cursor(self, name):
        pygame.mouse.set_cursor(*self.cursors[name])

cm = CursorManager()
set_cursor = cm.set_cursor

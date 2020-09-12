import enum

import pygame

cursors = {}

def init_cursors():
    size_and_pos = ((24, 16), (0, 0))
    cursors.update({
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
    })

def set_cursor(name):
    pygame.mouse.set_cursor(*cursors[name])

def get_key_down(key_ord):
    return bool(pygame.key.get_pressed()[key_ord])

def get_shift_down():
    return get_key_down(pygame.K_LSHIFT) or get_key_down(pygame.K_RSHIFT)

def get_ctrl_down():
    return get_key_down(pygame.K_RCTRL) or get_key_down(pygame.K_RCTRL)

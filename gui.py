import pygame

import battlemap

WINDOW_SIZE = (1280, 720)
MAP_SIZE = (1280, 720)

def is_on_map(x, y):
    return True

def main():
    bm = battlemap.BattleMap()
    bm.images.append(battlemap.MapImage(pygame.image.load('map.bmp')))
    bm.images.append(battlemap.MapImage.from_file('map.png', width=400, height=400, x=100, y=500))

    pygame.init()
    pygame.display.set_caption('dndmap')

    screen = pygame.display.set_mode(WINDOW_SIZE)

    # pygame.mouse.set_cursor((24, 16), (0, 0), *pygame.cursors.compile(pygame.cursors.sizer_xy_strings))
    pygame.mouse.set_cursor(*pygame.cursors.arrow)

    running = True
    while running:
        screen.blit(bm.render(), (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        #     elif event.type == pygame.MOUSEBUTTONDOWN:
        #         x, y = event.pos
        #         if ((x - handle_pos[0]) ** 2 + (y - handle_pos[1]) ** 2) ** 0.5 < 10:
        #             holding = True
        #     elif event.type == pygame.MOUSEBUTTONUP:
        #         holding = False
            elif event.type == pygame.MOUSEMOTION:
                if is_on_map(*event.pos):
                    bm.handle_motion(event)

        pygame.display.update()


if __name__ == '__main__':
    main()

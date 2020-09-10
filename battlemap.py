import pygame

pygame.init()
pygame.display.set_caption('dndmap')

screen = pygame.display.set_mode((1280, 720))
m = pygame.image.load('map.bmp')

m = pygame.transform.scale(m, (480, 600))
screen.blit(m, (0, 0))


def draw_handle(x, y):
    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (255, 0, 0), (x, y), 10)

handle_pos = (320, 320)
holding = False

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if ((x - handle_pos[0]) ** 2 + (y - handle_pos[1]) ** 2) ** 0.5 < 10:
                holding = True
        elif event.type == pygame.MOUSEBUTTONUP:
            holding = False
        elif event.type == pygame.MOUSEMOTION:
            if holding:
                handle_pos = event.pos

    draw_handle(*handle_pos)
    screen.blit(m, (0, 0))
    pygame.display.update()


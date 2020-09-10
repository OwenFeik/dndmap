import pygame

pygame.init()
pygame.display.set_caption('dndmap')

screen = pygame.display.set_mode((1280, 720))
m = pygame.image.load('map.bmp')

m = pygame.transform.scale(m, (480, 600))
screen.blit(m, (0, 0))
pygame.display.update()

while True:
    pass

import pygine as pg
import pygame
import sys

pygame.init()

width = 900
heigth = 600

window = pygame.display.set_mode((width, heigth))
pygame.display.set_caption('Shakal studio: Bolgarion boy 3 pre-pre-ALPHA TEST')
clock = pygame.time.Clock()

running = True
while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()

    window.fill((0,0,0))

    pygame.display.update()
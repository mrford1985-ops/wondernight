"""
Wondernight
My first video game!

When you run this, a window pops up with a black background,
and the word "Wondernight" flashes in the middle of the screen,
switching between blue and green.

Press the X button (or Esc) to close the game.
"""

import pygame
import sys

# ---- Settings you can play with ----
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 0)       # black
BLUE = (60, 120, 255)
GREEN = (60, 220, 120)
FLASH_SPEED_MS = 400               # how fast the colors switch (milliseconds)
FONT_SIZE = 72
TITLE_TEXT = "Wondernight"


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wondernight")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", FONT_SIZE, bold=True)

    colors = [BLUE, GREEN]
    color_index = 0
    last_switch_time = pygame.time.get_ticks()

    running = True
    while running:
        # ---- handle events (like closing the window) ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # ---- flash logic: switch color every FLASH_SPEED_MS ----
        now = pygame.time.get_ticks()
        if now - last_switch_time >= FLASH_SPEED_MS:
            color_index = (color_index + 1) % len(colors)
            last_switch_time = now

        current_color = colors[color_index]

        # ---- draw everything ----
        screen.fill(BACKGROUND_COLOR)

        text_surface = font.render(TITLE_TEXT, True, current_color)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text_surface, text_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

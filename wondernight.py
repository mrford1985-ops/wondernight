"""
Wondernight
My first video game!

A turn-based RPG set in a forest, starring Mark, a knight in golden
armor with white hair.

When you run this:
1. A black window pops up and "Wondernight" flashes blue/green in the
   middle of the screen (the intro).
2. After 5 seconds, "Start" and "Quit" buttons appear at the bottom
   of the screen. Click one, or use the Up/Down arrow keys + Enter.
3. Hit Start and you'll drop into the forest as Mark. Move with the
   arrow keys — trees block your path.

Press the X button (or Esc) any time to close the game.
"""

import pygame
import sys

# ---- Settings you can play with ----
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 0)       # black
BLUE = (60, 120, 255)
GREEN = (60, 220, 120)
WHITE = (255, 255, 255)
YELLOW = (255, 220, 80)

FLASH_SPEED_MS = 400               # how fast the intro title switches color
INTRO_DURATION_MS = 5000           # how long the intro screen shows before the menu appears

TITLE_FONT_SIZE = 72
MENU_FONT_SIZE = 48
TITLE_TEXT = "Wondernight"

# ---- Game states ----
STATE_INTRO = "intro"
STATE_MENU = "menu"
STATE_OVERWORLD = "overworld"

# ---- Forest map ----
# 'T' = tree (blocked), '.' = grass (walkable)
TILE_SIZE = 80
MAP_ROWS = [
    "TTTTTTTTTT",
    "T........T",
    "T.TT..T..T",
    "T........T",
    "T..T..TT.T",
    "T........T",
    "TTTTTTTTTT",
]
MAP_COLS = len(MAP_ROWS[0])
HUD_HEIGHT = HEIGHT - TILE_SIZE * len(MAP_ROWS)  # leftover strip at the bottom for text

GRASS_COLOR = (34, 120, 34)
GRASS_COLOR_ALT = (30, 108, 30)
TREE_TRUNK_COLOR = (90, 60, 30)
TREE_LEAF_COLOR = (20, 90, 40)

# Mark's colors
ARMOR_COLOR = (212, 175, 55)   # gold
ARMOR_SHADOW = (170, 138, 40)
HAIR_COLOR = (245, 245, 245)   # white

MARK_START_COL, MARK_START_ROW = 5, 3


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wondernight")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", TITLE_FONT_SIZE, bold=True)
    menu_font = pygame.font.SysFont("arial", MENU_FONT_SIZE, bold=True)
    hud_font = pygame.font.SysFont("arial", 20)

    colors = [BLUE, GREEN]
    color_index = 0
    last_switch_time = pygame.time.get_ticks()

    state = STATE_INTRO
    intro_start_time = pygame.time.get_ticks()

    menu_options = ["Start", "Quit"]
    selected_index = 0  # which menu option is currently highlighted

    mark_col, mark_row = MARK_START_COL, MARK_START_ROW

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if state == STATE_MENU:
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        selected_index = (selected_index + 1) % len(menu_options)
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if menu_options[selected_index] == "Start":
                            state = STATE_OVERWORLD
                        elif menu_options[selected_index] == "Quit":
                            running = False

                elif state == STATE_OVERWORLD:
                    d_col, d_row = 0, 0
                    if event.key == pygame.K_LEFT:
                        d_col = -1
                    elif event.key == pygame.K_RIGHT:
                        d_col = 1
                    elif event.key == pygame.K_UP:
                        d_row = -1
                    elif event.key == pygame.K_DOWN:
                        d_row = 1

                    if d_col or d_row:
                        new_col = mark_col + d_col
                        new_row = mark_row + d_row
                        if is_walkable(new_col, new_row):
                            mark_col, mark_row = new_col, new_row

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == STATE_MENU:
                    mouse_pos = event.pos
                    for i, rect in enumerate(menu_rects(menu_options, menu_font)):
                        if rect.collidepoint(mouse_pos):
                            selected_index = i
                            if menu_options[i] == "Start":
                                state = STATE_OVERWORLD
                            elif menu_options[i] == "Quit":
                                running = False

        now = pygame.time.get_ticks()

        if now - last_switch_time >= FLASH_SPEED_MS:
            color_index = (color_index + 1) % len(colors)
            last_switch_time = now
        current_color = colors[color_index]

        if state == STATE_INTRO and now - intro_start_time >= INTRO_DURATION_MS:
            state = STATE_MENU

        if state == STATE_MENU:
            mouse_pos = pygame.mouse.get_pos()
            for i, rect in enumerate(menu_rects(menu_options, menu_font)):
                if rect.collidepoint(mouse_pos):
                    selected_index = i

        screen.fill(BACKGROUND_COLOR)

        if state == STATE_INTRO:
            draw_title(screen, title_font, current_color, HEIGHT // 2)

        elif state == STATE_MENU:
            draw_title(screen, title_font, current_color, HEIGHT // 3)
            draw_menu(screen, menu_font, menu_options, selected_index)

        elif state == STATE_OVERWORLD:
            draw_forest(screen)
            draw_mark(screen, mark_col, mark_row)
            draw_hud(screen, hud_font)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


def draw_title(screen, font, color, center_y):
    text_surface = font.render(TITLE_TEXT, True, color)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, center_y))
    screen.blit(text_surface, text_rect)


def menu_rects(menu_options, font):
    rects = []
    bottom_margin = 60
    spacing = 55
    start_y = HEIGHT - bottom_margin - spacing * (len(menu_options) - 1)

    for i, option in enumerate(menu_options):
        text_surface = font.render(option, True, WHITE)
        rect = text_surface.get_rect(center=(WIDTH // 2, start_y + i * spacing))
        rects.append(rect)
    return rects


def draw_menu(screen, font, menu_options, selected_index):
    rects = menu_rects(menu_options, font)
    for i, (option, rect) in enumerate(zip(menu_options, rects)):
        color = YELLOW if i == selected_index else WHITE
        text_surface = font.render(option, True, color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)


def is_walkable(col, row):
    if row < 0 or row >= len(MAP_ROWS):
        return False
    if col < 0 or col >= MAP_COLS:
        return False
    return MAP_ROWS[row][col] == "."


def draw_forest(screen):
    for row in range(len(MAP_ROWS)):
        for col in range(MAP_COLS):
            x = col * TILE_SIZE
            y = row * TILE_SIZE
            tile = MAP_ROWS[row][col]

            grass = GRASS_COLOR if (row + col) % 2 == 0 else GRASS_COLOR_ALT
            pygame.draw.rect(screen, grass, (x, y, TILE_SIZE, TILE_SIZE))

            if tile == "T":
                trunk_width = TILE_SIZE // 4
                trunk_height = TILE_SIZE // 3
                trunk_rect = pygame.Rect(0, 0, trunk_width, trunk_height)
                trunk_rect.midbottom = (x + TILE_SIZE // 2, y + TILE_SIZE - 6)
                pygame.draw.rect(screen, TREE_TRUNK_COLOR, trunk_rect)

                canopy_center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2 - 6)
                pygame.draw.circle(screen, TREE_LEAF_COLOR, canopy_center, TILE_SIZE // 3)
                pygame.draw.circle(
                    screen, TREE_LEAF_COLOR,
                    (canopy_center[0] - 14, canopy_center[1] + 8), TILE_SIZE // 4,
                )
                pygame.draw.circle(
                    screen, TREE_LEAF_COLOR,
                    (canopy_center[0] + 14, canopy_center[1] + 8), TILE_SIZE // 4,
                )


def draw_mark(screen, col, row):
    x = col * TILE_SIZE
    y = row * TILE_SIZE
    center_x = x + TILE_SIZE // 2

    body_width, body_height = TILE_SIZE // 2, TILE_SIZE // 2
    body_rect = pygame.Rect(0, 0, body_width, body_height)
    body_rect.midbottom = (center_x, y + TILE_SIZE - 6)
    pygame.draw.rect(screen, ARMOR_COLOR, body_rect, border_radius=6)
    pygame.draw.rect(screen, ARMOR_SHADOW, body_rect, width=3, border_radius=6)

    head_radius = TILE_SIZE // 6
    head_center = (center_x, body_rect.top - head_radius + 2)
    pygame.draw.circle(screen, (255, 224, 189), head_center, head_radius)

    hair_rect = pygame.Rect(0, 0, head_radius * 2 + 4, head_radius + 4)
    hair_rect.midbottom = (head_center[0], head_center[1] - head_radius + 6)
    pygame.draw.ellipse(screen, HAIR_COLOR, hair_rect)

    sword_top = (body_rect.right, body_rect.top + 6)
    sword_bottom = (body_rect.right + 10, body_rect.bottom - 4)
    pygame.draw.line(screen, (200, 200, 200), sword_top, sword_bottom, 3)


def draw_hud(screen, font):
    hud_rect = pygame.Rect(0, HEIGHT - HUD_HEIGHT, WIDTH, HUD_HEIGHT)
    pygame.draw.rect(screen, BACKGROUND_COLOR, hud_rect)
    text = font.render("Mark the Golden Knight  |  Arrow keys to move  |  Esc to quit", True, WHITE)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - HUD_HEIGHT // 2))
    screen.blit(text, text_rect)


if __name__ == "__main__":
    main()

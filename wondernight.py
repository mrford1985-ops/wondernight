"""
Wondernight
My first video game!

A turn-based RPG set in a forest, starring Mark, a knight in golden
armor with white hair, and his companion Cam, a boy with long brown
hair and a red shirt with a yellow sunflower. Watch out for the 5
Dark Knights guarding the forest!

When you run this:
1. A black window pops up and "Wondernight" flashes blue/green in the
   middle of the screen (the intro).
2. After 5 seconds, "Start" and "Quit" buttons appear at the bottom
   of the screen. Click one, or use the Up/Down arrow keys + Enter.
3. Hit Start and you'll drop into the forest. Controls:
     Arrow keys - move (whoever isn't active follows one step behind)
     U          - switch which character you're controlling
     I          - attack! Mark swings his sword, Cam shoots fire
                  from his sunflower
     D          - transform! Mark becomes a white dragon, Cam becomes
                  a red dragon (press D again to change back)
     Esc        - quit any time
   Walking into a Dark Knight starts an encounter:
     I - fight it (defeats it, for now - the real battle system is
         still being built!)
     R - retreat back to the forest

Everything is drawn as chunky pixel art, built right out of colored
squares - no image files needed!
"""

import pygame
import sys

WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 0)
BLUE = (60, 120, 255)
GREEN = (60, 220, 120)
WHITE = (255, 255, 255)
YELLOW = (255, 220, 80)
DANGER_RED = (220, 20, 20)

FLASH_SPEED_MS = 400
INTRO_DURATION_MS = 5000

TITLE_FONT_SIZE = 72
MENU_FONT_SIZE = 48
TITLE_TEXT = "Wondernight"

STATE_INTRO = "intro"
STATE_MENU = "menu"
STATE_OVERWORLD = "overworld"
STATE_BATTLE = "battle"

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
HUD_HEIGHT = HEIGHT - TILE_SIZE * len(MAP_ROWS)

GRASS_COLOR = (34, 120, 34)
GRASS_COLOR_ALT = (30, 108, 30)
GRASS_BLADE_COLOR = (24, 96, 24)

MARK_START_COL, MARK_START_ROW = 5, 3
CAM_START_COL, CAM_START_ROW = 4, 3

ENEMY_START_POSITIONS = [(2, 1), (7, 1), (7, 3), (2, 5), (5, 5)]

ATTACK_DURATION_MS = 350

FACING_OFFSET = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}


def mirror(left_half):
    return left_half + left_half[::-1]


SPRITE_PIXEL = 8

MARK_PALETTE = {
    "W": (245, 245, 245),
    "S": (255, 224, 189),
    "E": (25, 25, 25),
    "D": (150, 120, 40),
    "G": (212, 175, 55),
    "B": (70, 70, 85),
}

MARK_SPRITE = [
    mirror("..WWW"),
    mirror(".WWWW"),
    mirror("WWSSS"),
    mirror("WSSES"),
    mirror(".SSSS"),
    mirror("..DGG"),
    mirror(".DGGG"),
    mirror(".DGGG"),
    mirror(".DGGG"),
    mirror(".DGGG"),
    mirror("..DDD"),
    mirror("..GG."),
    mirror("..GG."),
    mirror("..BB."),
]

CAM_PALETTE = {
    "H": (101, 67, 33),
    "S": (255, 224, 189),
    "E": (25, 25, 25),
    "R": (200, 40, 40),
    "r": (150, 25, 25),
    "Y": (255, 214, 51),
    "O": (200, 140, 30),
    "P": (60, 90, 140),
    "B": (70, 45, 25),
}

CAM_SPRITE = [
    mirror("..HHH"),
    mirror(".HHHH"),
    mirror("HHSSS"),
    mirror("HSSES"),
    mirror("HSSSS"),
    mirror("HRRRR"),
    mirror("HRRRR"),
    mirror("RRRYY"),
    mirror("RRYOY"),
    mirror(".RRRR"),
    mirror("..rrr"),
    mirror("..PP."),
    mirror("..PP."),
    mirror("..BB."),
]

DRAGON_SHAPE = [
    mirror("...HH..."),
    mirror("..HCCH.."),
    mirror(".CCCCCCC"),
    mirror(".CCECCCC"),
    mirror("..CCCCCC"),
    mirror("...CCCCC"),
    mirror("MM.CCCCC"),
    mirror("MMMMCCCC"),
    mirror(".MM.CCCC"),
    mirror("...CCCCC"),
    mirror("..BBBBBB"),
    mirror("..BBBBBB"),
    mirror("...CC..."),
    mirror("...HH..."),
]

WHITE_DRAGON_PALETTE = {
    "C": (235, 235, 240),
    "H": (120, 120, 130),
    "E": (220, 40, 40),
    "M": (200, 220, 235),
    "B": (255, 250, 235),
}

RED_DRAGON_PALETTE = {
    "C": (200, 40, 40),
    "H": (70, 35, 20),
    "E": (255, 220, 50),
    "M": (230, 120, 40),
    "B": (255, 200, 140),
}

DARK_KNIGHT_PALETTE = {
    "K": (45, 45, 52),
    "k": (20, 20, 24),
    "R": (220, 20, 20),
    "H": (70, 70, 78),
}

DARK_KNIGHT_SPRITE = [
    mirror("..HHH"),
    mirror(".KKKK"),
    mirror("KKKKK"),
    mirror("KKRKK"),
    mirror(".KKKK"),
    mirror("..kKK"),
    mirror(".kKKK"),
    mirror(".kKKK"),
    mirror(".kKKK"),
    mirror(".kKKK"),
    mirror("..kkk"),
    mirror("..KK."),
    mirror("..KK."),
    mirror("..kk."),
]

TREE_PIXEL = 8

TREE_PALETTE = {
    "L": (20, 90, 40),
    "l": (40, 120, 60),
    "T": (90, 60, 30),
}

TREE_SPRITE = [
    mirror("..LLL"),
    mirror(".LLLL"),
    mirror("LLLLL"),
    mirror("LlLLL"),
    mirror("LLLLL"),
    mirror(".LLLL"),
    mirror("..TTT"),
    mirror("..TTT"),
    mirror("..TTT"),
    mirror("..TTT"),
]


def draw_pixel_grid(screen, grid, palette, pixel_size, origin_x, origin_y):
    for row_index, row in enumerate(grid):
        for col_index, ch in enumerate(row):
            if ch == ".":
                continue
            color = palette[ch]
            rect = (
                origin_x + col_index * pixel_size,
                origin_y + row_index * pixel_size,
                pixel_size,
                pixel_size,
            )
            pygame.draw.rect(screen, color, rect)


def draw_character(screen, grid, palette, col, row):
    sprite_w = len(grid[0]) * SPRITE_PIXEL
    sprite_h = len(grid) * SPRITE_PIXEL
    tile_x = col * TILE_SIZE
    tile_y = row * TILE_SIZE
    origin_x = tile_x + (TILE_SIZE - sprite_w) // 2
    origin_y = tile_y + TILE_SIZE - sprite_h
    draw_pixel_grid(screen, grid, palette, SPRITE_PIXEL, origin_x, origin_y)


def draw_active_marker(screen, col, row):
    cx = col * TILE_SIZE + TILE_SIZE // 2
    cy = row * TILE_SIZE + TILE_SIZE - 6
    pygame.draw.polygon(
        screen, YELLOW,
        [(cx, cy - 5), (cx + 6, cy), (cx, cy + 5), (cx - 6, cy)],
    )


def draw_attack_effect(screen, kind, col, row, facing):
    d_col, d_row = FACING_OFFSET.get(facing, (0, 1))
    base_x = (col + d_col) * TILE_SIZE
    base_y = (row + d_row) * TILE_SIZE

    if kind == "sword":
        color = (225, 225, 235)
        blocks = [(2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (3, 5), (5, 3)]
        for bx, by in blocks:
            rect = (base_x + bx * 8, base_y + by * 8, 8, 8)
            pygame.draw.rect(screen, color, rect)

    elif kind == "fire":
        blocks = [
            ((3, 6), (255, 90, 20)),
            ((4, 6), (255, 140, 20)),
            ((5, 6), (255, 90, 20)),
            ((4, 5), (255, 170, 30)),
            ((3, 4), (255, 200, 50)),
            ((5, 4), (255, 200, 50)),
            ((4, 4), (255, 230, 80)),
            ((4, 7), (255, 90, 20)),
        ]
        for (bx, by), color in blocks:
            rect = (base_x + bx * 8, base_y + by * 8, 8, 8)
            pygame.draw.rect(screen, color, rect)


def direction_from_delta(d_col, d_row):
    if d_row == -1:
        return "up"
    if d_row == 1:
        return "down"
    if d_col == -1:
        return "left"
    if d_col == 1:
        return "right"
    return "down"


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
            pygame.draw.rect(screen, GRASS_BLADE_COLOR, (x + 14, y + 20, 6, 6))
            pygame.draw.rect(screen, GRASS_BLADE_COLOR, (x + 50, y + 50, 6, 6))
            pygame.draw.rect(screen, GRASS_BLADE_COLOR, (x + 60, y + 16, 6, 6))
            if tile == "T":
                draw_pixel_grid(screen, TREE_SPRITE, TREE_PALETTE, TREE_PIXEL, x, y)


def draw_hud(screen, font, active, dragon_mode):
    hud_rect = pygame.Rect(0, HEIGHT - HUD_HEIGHT, WIDTH, HUD_HEIGHT)
    pygame.draw.rect(screen, BACKGROUND_COLOR, hud_rect)
    who = "Mark" if active == "mark" else "Cam"
    if dragon_mode:
        who += " (dragon!)"
    text = font.render(
        f"Controlling: {who}  |  Arrows: move  |  U: switch  |  I: attack  |  D: transform  |  Esc: quit",
        True, WHITE,
    )
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - HUD_HEIGHT // 2))
    screen.blit(text, text_rect)


def draw_battle_screen(screen, big_font, small_font):
    screen.fill(BACKGROUND_COLOR)

    title = big_font.render("A Dark Knight blocks the path!", True, DANGER_RED)
    title_rect = title.get_rect(center=(WIDTH // 2, 60))
    screen.blit(title, title_rect)

    scale = 14
    sprite_w = len(DARK_KNIGHT_SPRITE[0]) * scale
    sprite_h = len(DARK_KNIGHT_SPRITE) * scale
    origin_x = (WIDTH - sprite_w) // 2
    origin_y = (HEIGHT - sprite_h) // 2 - 20
    draw_pixel_grid(screen, DARK_KNIGHT_SPRITE, DARK_KNIGHT_PALETTE, scale, origin_x, origin_y)

    note = small_font.render(
        "(the real battle system is still being built - for now:)", True, (170, 170, 170),
    )
    note_rect = note.get_rect(center=(WIDTH // 2, HEIGHT - 70))
    screen.blit(note, note_rect)

    instructions = small_font.render(
        "Press I to fight it  |  Press R to retreat", True, WHITE,
    )
    instructions_rect = instructions.get_rect(center=(WIDTH // 2, HEIGHT - 40))
    screen.blit(instructions, instructions_rect)

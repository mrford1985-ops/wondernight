"""
Wondernight
My first video game!

A turn-based RPG set in a forest, starring Mark, a knight in golden
armor with white hair, and his companion Cam, a boy with long brown
hair and a red shirt with a yellow sunflower.

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

Everything is drawn as chunky pixel art, built right out of colored
squares - no image files needed!
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
GRASS_BLADE_COLOR = (24, 96, 24)

MARK_START_COL, MARK_START_ROW = 5, 3
CAM_START_COL, CAM_START_ROW = 4, 3

ATTACK_DURATION_MS = 350

FACING_OFFSET = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}


# ---------------- Pixel-art sprites ----------------
# Every sprite is drawn from a small grid of letters. Each letter stands
# for a color (see the palettes below), and '.' means "see-through".
# mirror() builds the right half of a sprite by flipping the left half,
# so everything comes out perfectly symmetric.

def mirror(left_half):
    return left_half + left_half[::-1]


SPRITE_PIXEL = 8   # each grid square is drawn this many real pixels wide/tall

MARK_PALETTE = {
    "W": (245, 245, 245),  # white hair
    "S": (255, 224, 189),  # skin
    "E": (25, 25, 25),     # eyes
    "D": (150, 120, 40),   # dark gold trim
    "G": (212, 175, 55),   # gold armor
    "B": (70, 70, 85),     # boots
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
    "H": (101, 67, 33),    # long brown hair
    "S": (255, 224, 189),  # skin
    "E": (25, 25, 25),     # eyes
    "R": (200, 40, 40),    # red shirt
    "r": (150, 25, 25),    # dark red trim
    "Y": (255, 214, 51),   # sunflower petals
    "O": (200, 140, 30),   # sunflower center
    "P": (60, 90, 140),    # pants
    "B": (70, 45, 25),     # boots
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

# One shared dragon shape - Mark's and Cam's dragon forms just recolor it.
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

WHITE_DRAGON_PALETTE = {  # Mark's dragon form
    "C": (235, 235, 240),  # white scales
    "H": (120, 120, 130),  # horns / claws
    "E": (220, 40, 40),    # eye
    "M": (200, 220, 235),  # wing membrane
    "B": (255, 250, 235),  # belly
}

RED_DRAGON_PALETTE = {  # Cam's dragon form
    "C": (200, 40, 40),    # red scales
    "H": (70, 35, 20),     # horns / claws
    "E": (255, 220, 50),   # eye
    "M": (230, 120, 40),   # wing membrane
    "B": (255, 200, 140),  # belly
}

TREE_PIXEL = 8

TREE_PALETTE = {
    "L": (20, 90, 40),   # leaf
    "l": (40, 120, 60),  # leaf highlight
    "T": (90, 60, 30),   # trunk
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
    """Draw a character sprite anchored so its feet sit at the bottom of its tile.
    Works for sprites of any width (dragons are wider than one tile, for wings)."""
    sprite_w = len(grid[0]) * SPRITE_PIXEL
    sprite_h = len(grid) * SPRITE_PIXEL
    tile_x = col * TILE_SIZE
    tile_y = row * TILE_SIZE
    origin_x = tile_x + (TILE_SIZE - sprite_w) // 2
    origin_y = tile_y + TILE_SIZE - sprite_h
    draw_pixel_grid(screen, grid, palette, SPRITE_PIXEL, origin_x, origin_y)


def draw_active_marker(screen, col, row):
    """A little yellow diamond under whichever character you're controlling."""
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


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wondernight")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", TITLE_FONT_SIZE, bold=True)
    menu_font = pygame.font.SysFont("arial", MENU_FONT_SIZE, bold=True)
    hud_font = pygame.font.SysFont("arial", 18)

    colors = [BLUE, GREEN]
    color_index = 0
    last_switch_time = pygame.time.get_ticks()

    state = STATE_INTRO
    intro_start_time = pygame.time.get_ticks()

    menu_options = ["Start", "Quit"]
    selected_index = 0  # which menu option is currently highlighted

    # ---- party state ----
    mark_col, mark_row = MARK_START_COL, MARK_START_ROW
    cam_col, cam_row = CAM_START_COL, CAM_START_ROW
    mark_facing = "down"
    cam_facing = "down"
    active = "mark"  # "mark" or "cam" - whichever one arrow keys control right now
    mark_attack_until = 0
    cam_attack_until = 0
    dragon_mode = False  # press D to toggle - both characters transform together

    running = True
    while running:
        # ---- handle events ----
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
                    if event.key == pygame.K_u:
                        active = "cam" if active == "mark" else "mark"

                    elif event.key == pygame.K_d:
                        dragon_mode = not dragon_mode

                    elif event.key == pygame.K_i:
                        if active == "mark":
                            mark_attack_until = pygame.time.get_ticks() + ATTACK_DURATION_MS
                        else:
                            cam_attack_until = pygame.time.get_ticks() + ATTACK_DURATION_MS

                    else:
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
                            new_direction = direction_from_delta(d_col, d_row)

                            if active == "mark":
                                mark_facing = new_direction
                                new_col, new_row = mark_col + d_col, mark_row + d_row
                                if is_walkable(new_col, new_row):
                                    old_mark_col, old_mark_row = mark_col, mark_row
                                    mark_col, mark_row = new_col, new_row
                                    fd_col, fd_row = old_mark_col - cam_col, old_mark_row - cam_row
                                    if fd_col or fd_row:
                                        cam_facing = direction_from_delta(fd_col, fd_row)
                                    cam_col, cam_row = old_mark_col, old_mark_row
                            else:
                                cam_facing = new_direction
                                new_col, new_row = cam_col + d_col, cam_row + d_row
                                if is_walkable(new_col, new_row):
                                    old_cam_col, old_cam_row = cam_col, cam_row
                                    cam_col, cam_row = new_col, new_row
                                    fd_col, fd_row = old_cam_col - mark_col, old_cam_row - mark_row
                                    if fd_col or fd_row:
                                        mark_facing = direction_from_delta(fd_col, fd_row)
                                    mark_col, mark_row = old_cam_col, old_cam_row

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

        # ---- update ----
        now = pygame.time.get_ticks()

        # flash logic (used during intro, and as a subtle title flash in the menu too)
        if now - last_switch_time >= FLASH_SPEED_MS:
            color_index = (color_index + 1) % len(colors)
            last_switch_time = now
        current_color = colors[color_index]

        if state == STATE_INTRO and now - intro_start_time >= INTRO_DURATION_MS:
            state = STATE_MENU

        # highlight whichever menu option the mouse is hovering over
        if state == STATE_MENU:
            mouse_pos = pygame.mouse.get_pos()
            for i, rect in enumerate(menu_rects(menu_options, menu_font)):
                if rect.collidepoint(mouse_pos):
                    selected_index = i

        # ---- draw ----
        screen.fill(BACKGROUND_COLOR)

        if state == STATE_INTRO:
            draw_title(screen, title_font, current_color, HEIGHT // 2)

        elif state == STATE_MENU:
            draw_title(screen, title_font, current_color, HEIGHT // 3)
            draw_menu(screen, menu_font, menu_options, selected_index)

        elif state == STATE_OVERWORLD:
            draw_forest(screen)

            if active == "mark":
                draw_active_marker(screen, mark_col, mark_row)
            else:
                draw_active_marker(screen, cam_col, cam_row)

            if dragon_mode:
                draw_character(screen, DRAGON_SHAPE, RED_DRAGON_PALETTE, cam_col, cam_row)
                draw_character(screen, DRAGON_SHAPE, WHITE_DRAGON_PALETTE, mark_col, mark_row)
            else:
                draw_character(screen, CAM_SPRITE, CAM_PALETTE, cam_col, cam_row)
                draw_character(screen, MARK_SPRITE, MARK_PALETTE, mark_col, mark_row)

            if now < mark_attack_until:
                draw_attack_effect(screen, "sword", mark_col, mark_row, mark_facing)
            if now < cam_attack_until:
                draw_attack_effect(screen, "fire", cam_col, cam_row, cam_facing)

            draw_hud(screen, hud_font, active, dragon_mode)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


def draw_title(screen, font, color, center_y):
    text_surface = font.render(TITLE_TEXT, True, color)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, center_y))
    screen.blit(text_surface, text_rect)


def menu_rects(menu_options, font):
    """Compute the click/hover rectangles for each menu option,
    stacked in the bottom-middle of the screen."""
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


# ---------------- Forest / overworld ----------------

def is_walkable(col, row):
    """A tile is walkable if it's inside the map and isn't a tree."""
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

            # checkerboard the grass a little so the ground doesn't look flat
            grass = GRASS_COLOR if (row + col) % 2 == 0 else GRASS_COLOR_ALT
            pygame.draw.rect(screen, grass, (x, y, TILE_SIZE, TILE_SIZE))

            # a couple of fixed little "blades" of grass for texture
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


if __name__ == "__main__":
    main()

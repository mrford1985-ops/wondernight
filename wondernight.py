"""
Wondernight
My first video game!

A turn-based RPG set in a forest, starring Mark, a knight in golden
armor with white hair, and his companion Cam, a boy with long brown
hair and a red shirt with a yellow sunflower. Watch out for the 5
Dark Knights guarding the forest!

Mark, Cam, the dragons, the sword, the fire, and the tree are all
real hand-drawn art (from the assets/ folder). The Dark Knights and
the ground are still simple pixel art built out of colored squares,
since we don't have drawn art for those yet.

When you run this:
1. A black window pops up and "Wondernight" flashes blue/green in the
   middle of the screen (the intro).
2. After 5 seconds, "Start" and "Quit" buttons appear at the bottom
   of the screen. Click one, or use the Up/Down arrow keys + Enter.
3. Hit Start and you'll drop into the forest. Controls:
     Arrow keys - move whoever you're controlling (the other
                  character just waits where they are)
     U          - switch which character you're controlling
     I          - swing! Mark swings his sword, Cam shoots fire
                  from his sunflower (just for show in the overworld)
     D          - transform! Mark becomes a gold dragon, Cam becomes
                  a red dragon (press D again to change back)
     Esc        - quit any time
   Walking into a Dark Knight starts a real battle:
     Up/Down - choose Attack or Run
     Enter   - confirm
   Defeat all 5 Dark Knights and they respawn 30 seconds later.
"""

import os
import random
import pygame
import sys

# ---- Settings you can play with ----
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0, 0, 0)       # black
BLUE = (60, 120, 255)
GREEN = (60, 220, 120)
WHITE = (255, 255, 255)
YELLOW = (255, 220, 80)
DANGER_RED = (220, 20, 20)
HP_GREEN = (70, 200, 90)
HP_RED = (210, 60, 60)
HP_EMPTY = (60, 60, 60)

FLASH_SPEED_MS = 400               # how fast the intro title switches color
INTRO_DURATION_MS = 5000           # how long the intro screen shows before the menu appears

TITLE_FONT_SIZE = 72
MENU_FONT_SIZE = 48
TITLE_TEXT = "Wondernight"

# ---- Game states ----
STATE_INTRO = "intro"
STATE_MENU = "menu"
STATE_OVERWORLD = "overworld"
STATE_BATTLE = "battle"

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

MARK_START_COL, MARK_START_ROW = 5, 3
CAM_START_COL, CAM_START_ROW = 4, 3

# (col, row) for each of the 5 Dark Knights guarding the forest
ENEMY_START_POSITIONS = [(2, 1), (7, 1), (7, 3), (2, 5), (5, 5)]
RESPAWN_DELAY_MS = 30000  # 30 seconds after the last one falls, they all come back

ATTACK_DURATION_MS = 350

FACING_OFFSET = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

# ---- Combat stats ----
MARK_MAX_HP = 30
CAM_MAX_HP = 30
ENEMY_MAX_HP = 20
PLAYER_ATK_RANGE = (4, 9)
ENEMY_ATK_RANGE = (2, 6)
BATTLE_OPTIONS = ["Attack", "Run"]

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# How big each drawn-art image should appear on screen (pygame scales the
# original art to fit these sizes, keeping its proportions).
MARK_TARGET_H = 130
CAM_TARGET_H = 122
DRAGON_TARGET_W = 170
TREE_TARGET_H = 100
GRASS_TARGET_W = 28  # small ground texture tuft, scattered one per grass tile
SWORD_TARGET_H = 65
FIRE_TARGET_W = 65
BATTLE_PORTRAIT_H = 150  # bigger version of Mark/Cam for the battle screen


def load_scaled(filename, target_h=None, target_w=None):
    """Load a PNG from assets/ and scale it to a target height or width,
    keeping its original proportions."""
    path = os.path.join(ASSET_DIR, filename)
    image = pygame.image.load(path).convert_alpha()
    w, h = image.get_size()
    scale = (target_h / h) if target_h else (target_w / w)
    new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
    return pygame.transform.smoothscale(image, new_size)


# ---------------- Dark Knight enemy (still pixel art - no drawn art for this yet) ----------------
# Every pixel-art sprite here is drawn from a small grid of letters. Each
# letter stands for a color, and '.' means "see-through". mirror() builds
# the right half of a sprite by flipping the left half, so it comes out
# perfectly symmetric.

def mirror(left_half):
    return left_half + left_half[::-1]


SPRITE_PIXEL = 8

DARK_KNIGHT_PALETTE = {
    "K": (45, 45, 52),   # dark armor
    "k": (20, 20, 24),   # darker trim / shadow
    "R": (220, 20, 20),  # glowing red eyes
    "H": (70, 70, 78),   # helmet spikes
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


def draw_pixel_character(screen, grid, palette, col, row):
    """Draw a pixel-art sprite anchored so its feet sit at the bottom of its tile."""
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


def draw_image_character(screen, surface, col, row):
    """Draw a real-art sprite anchored so its feet sit at the bottom of its tile."""
    w, h = surface.get_size()
    tile_x = col * TILE_SIZE
    tile_y = row * TILE_SIZE
    x = tile_x + (TILE_SIZE - w) // 2
    y = tile_y + TILE_SIZE - h
    screen.blit(surface, (x, y))


def draw_attack_effect_image(screen, images_by_facing, col, row, facing):
    """Draw a real-art attack effect centered in the tile the character is facing."""
    d_col, d_row = FACING_OFFSET.get(facing, (0, 1))
    target_col, target_row = col + d_col, row + d_row
    image = images_by_facing.get(facing, images_by_facing["down"])
    w, h = image.get_size()
    x = target_col * TILE_SIZE + (TILE_SIZE - w) // 2
    y = target_row * TILE_SIZE + (TILE_SIZE - h) // 2
    screen.blit(image, (x, y))


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
    battle_font = pygame.font.SysFont("arial", 28, bold=True)
    battle_small_font = pygame.font.SysFont("arial", 18)

    # ---- load the real art (drawn assets) ----
    mark_image = load_scaled("mark.png", target_h=MARK_TARGET_H)
    cam_image = load_scaled("cam.png", target_h=CAM_TARGET_H)
    gold_dragon_image = load_scaled("gold_dragon.png", target_w=DRAGON_TARGET_W)
    red_dragon_image = load_scaled("red_dragon.png", target_w=DRAGON_TARGET_W)
    tree_image = load_scaled("tree.png", target_h=TREE_TARGET_H)
    grass_image = load_scaled("grass.png", target_w=GRASS_TARGET_W)
    sword_up = load_scaled("sword.png", target_h=SWORD_TARGET_H)
    fire_right = load_scaled("fire.png", target_w=FIRE_TARGET_W)
    mark_portrait = load_scaled("mark.png", target_h=BATTLE_PORTRAIT_H)
    cam_portrait = load_scaled("cam.png", target_h=BATTLE_PORTRAIT_H)

    # pre-rotate/flip the attack effects for each direction, once, up front
    sword_by_facing = {
        "up": sword_up,
        "down": pygame.transform.rotate(sword_up, 180),
        "left": pygame.transform.rotate(sword_up, 90),
        "right": pygame.transform.rotate(sword_up, -90),
    }
    fire_by_facing = {
        "right": fire_right,
        "left": pygame.transform.flip(fire_right, True, False),
        "up": pygame.transform.rotate(fire_right, 90),
        "down": pygame.transform.rotate(fire_right, -90),
    }

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

    mark_hp = MARK_MAX_HP
    cam_hp = CAM_MAX_HP

    # ---- enemies ----
    enemies_alive = set(ENEMY_START_POSITIONS)
    all_defeated_at = None  # timestamp when the last Dark Knight fell, or None

    # ---- battle state (only meaningful while state == STATE_BATTLE) ----
    battle_enemy_pos = None
    battle_fighter = "mark"     # who's fighting: "mark" or "cam"
    battle_enemy_hp = ENEMY_MAX_HP
    battle_phase = "choose"     # "choose", "victory", or "defeat"
    battle_selected = 0
    battle_log = []

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

                            # Only the character you're controlling moves -
                            # the other one just waits wherever it is.
                            if active == "mark":
                                mark_facing = new_direction
                                new_col, new_row = mark_col + d_col, mark_row + d_row
                                if (new_col, new_row) in enemies_alive:
                                    state = STATE_BATTLE
                                    battle_enemy_pos = (new_col, new_row)
                                    battle_fighter = "mark"
                                    battle_enemy_hp = ENEMY_MAX_HP
                                    battle_phase = "choose"
                                    battle_selected = 0
                                    battle_log = []
                                elif is_walkable(new_col, new_row):
                                    mark_col, mark_row = new_col, new_row
                            else:
                                cam_facing = new_direction
                                new_col, new_row = cam_col + d_col, cam_row + d_row
                                if (new_col, new_row) in enemies_alive:
                                    state = STATE_BATTLE
                                    battle_enemy_pos = (new_col, new_row)
                                    battle_fighter = "cam"
                                    battle_enemy_hp = ENEMY_MAX_HP
                                    battle_phase = "choose"
                                    battle_selected = 0
                                    battle_log = []
                                elif is_walkable(new_col, new_row):
                                    cam_col, cam_row = new_col, new_row

                elif state == STATE_BATTLE:
                    if battle_phase == "choose":
                        if event.key in (pygame.K_UP, pygame.K_DOWN):
                            battle_selected = (battle_selected + 1) % len(BATTLE_OPTIONS)

                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            choice = BATTLE_OPTIONS[battle_selected]

                            if choice == "Run":
                                state = STATE_OVERWORLD
                                battle_enemy_pos = None

                            elif choice == "Attack":
                                fighter_name = "Mark" if battle_fighter == "mark" else "Cam"
                                player_dmg = random.randint(*PLAYER_ATK_RANGE)
                                battle_enemy_hp -= player_dmg
                                battle_log = [f"{fighter_name} hits the Dark Knight for {player_dmg}!"]

                                if battle_enemy_hp <= 0:
                                    battle_enemy_hp = 0
                                    battle_phase = "victory"
                                else:
                                    enemy_dmg = random.randint(*ENEMY_ATK_RANGE)
                                    if battle_fighter == "mark":
                                        mark_hp = max(0, mark_hp - enemy_dmg)
                                        fighter_hp_after = mark_hp
                                    else:
                                        cam_hp = max(0, cam_hp - enemy_dmg)
                                        fighter_hp_after = cam_hp
                                    battle_log.append(
                                        f"The Dark Knight hits {fighter_name} for {enemy_dmg}!"
                                    )
                                    if fighter_hp_after <= 0:
                                        battle_phase = "defeat"

                    elif battle_phase == "victory":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            enemies_alive.discard(battle_enemy_pos)
                            battle_enemy_pos = None
                            state = STATE_OVERWORLD

                    elif battle_phase == "defeat":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if battle_fighter == "mark":
                                mark_hp = MARK_MAX_HP
                            else:
                                cam_hp = CAM_MAX_HP
                            mark_col, mark_row = MARK_START_COL, MARK_START_ROW
                            cam_col, cam_row = CAM_START_COL, CAM_START_ROW
                            battle_enemy_pos = None
                            state = STATE_OVERWORLD

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

        # once every Dark Knight has fallen, start the respawn clock;
        # 30 seconds later, bring them all back
        if not enemies_alive and all_defeated_at is None:
            all_defeated_at = now
        if all_defeated_at is not None and now - all_defeated_at >= RESPAWN_DELAY_MS:
            enemies_alive = set(ENEMY_START_POSITIONS)
            all_defeated_at = None

        respawn_seconds = None
        if all_defeated_at is not None:
            remaining_ms = RESPAWN_DELAY_MS - (now - all_defeated_at)
            respawn_seconds = max(0, (remaining_ms + 999) // 1000)

        # ---- draw ----
        screen.fill(BACKGROUND_COLOR)

        if state == STATE_INTRO:
            draw_title(screen, title_font, current_color, HEIGHT // 2)

        elif state == STATE_MENU:
            draw_title(screen, title_font, current_color, HEIGHT // 3)
            draw_menu(screen, menu_font, menu_options, selected_index)

        elif state == STATE_OVERWORLD:
            draw_forest(screen, tree_image, grass_image)

            for (ecol, erow) in enemies_alive:
                draw_pixel_character(screen, DARK_KNIGHT_SPRITE, DARK_KNIGHT_PALETTE, ecol, erow)

            if active == "mark":
                draw_active_marker(screen, mark_col, mark_row)
            else:
                draw_active_marker(screen, cam_col, cam_row)

            if dragon_mode:
                draw_image_character(screen, red_dragon_image, cam_col, cam_row)
                draw_image_character(screen, gold_dragon_image, mark_col, mark_row)
            else:
                draw_image_character(screen, cam_image, cam_col, cam_row)
                draw_image_character(screen, mark_image, mark_col, mark_row)

            if now < mark_attack_until:
                draw_attack_effect_image(screen, sword_by_facing, mark_col, mark_row, mark_facing)
            if now < cam_attack_until:
                draw_attack_effect_image(screen, fire_by_facing, cam_col, cam_row, cam_facing)

            draw_hud(screen, hud_font, active, dragon_mode, respawn_seconds)

        elif state == STATE_BATTLE:
            fighter_image = mark_portrait if battle_fighter == "mark" else cam_portrait
            fighter_name = "Mark" if battle_fighter == "mark" else "Cam"
            fighter_hp = mark_hp if battle_fighter == "mark" else cam_hp
            fighter_max_hp = MARK_MAX_HP if battle_fighter == "mark" else CAM_MAX_HP

            draw_battle_screen(
                screen, battle_font, battle_small_font,
                fighter_image, fighter_name, fighter_hp, fighter_max_hp,
                battle_enemy_hp, battle_phase, battle_selected, battle_log,
            )

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


def draw_forest(screen, tree_image, grass_image):
    for row in range(len(MAP_ROWS)):
        for col in range(MAP_COLS):
            x = col * TILE_SIZE
            y = row * TILE_SIZE
            tile = MAP_ROWS[row][col]

            # checkerboard the ground a little so it doesn't look flat
            grass = GRASS_COLOR if (row + col) % 2 == 0 else GRASS_COLOR_ALT
            pygame.draw.rect(screen, grass, (x, y, TILE_SIZE, TILE_SIZE))

            if tile == "T":
                tw, th = tree_image.get_size()
                screen.blit(tree_image, (x + (TILE_SIZE - tw) // 2, y + TILE_SIZE - th))
            else:
                gw, gh = grass_image.get_size()
                screen.blit(grass_image, (x + (TILE_SIZE - gw) // 2, y + TILE_SIZE - gh))


def draw_hud(screen, font, active, dragon_mode, respawn_seconds):
    hud_rect = pygame.Rect(0, HEIGHT - HUD_HEIGHT, WIDTH, HUD_HEIGHT)
    pygame.draw.rect(screen, BACKGROUND_COLOR, hud_rect)

    if respawn_seconds is not None:
        text = font.render(
            f"All Dark Knights defeated! They respawn in {respawn_seconds}s",
            True, YELLOW,
        )
    else:
        who = "Mark" if active == "mark" else "Cam"
        if dragon_mode:
            who += " (dragon!)"
        text = font.render(
            f"Controlling: {who}  |  Arrows: move  |  U: switch  |  I: attack  |  D: transform  |  Esc: quit",
            True, WHITE,
        )
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - HUD_HEIGHT // 2))
    screen.blit(text, text_rect)


# ---------------- Battle screen (real turn-based combat) ----------------

def draw_hp_bar(screen, x, y, width, height, current, maximum, fill_color):
    current = max(0, min(current, maximum))
    pygame.draw.rect(screen, HP_EMPTY, (x, y, width, height))
    fill_width = int(width * (current / maximum)) if maximum > 0 else 0
    if fill_width > 0:
        pygame.draw.rect(screen, fill_color, (x, y, fill_width, height))
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)


def draw_battle_screen(
    screen, big_font, small_font,
    fighter_image, fighter_name, fighter_hp, fighter_max_hp,
    enemy_hp, battle_phase, battle_selected, battle_log,
):
    screen.fill(BACKGROUND_COLOR)

    # ---- Dark Knight (top) ----
    label = big_font.render("Dark Knight", True, DANGER_RED)
    screen.blit(label, label.get_rect(center=(WIDTH // 2, 36)))

    bar_w, bar_h = 260, 20
    draw_hp_bar(screen, WIDTH // 2 - bar_w // 2, 56, bar_w, bar_h, enemy_hp, ENEMY_MAX_HP, HP_RED)
    hp_text = small_font.render(f"{max(0, enemy_hp)}/{ENEMY_MAX_HP}", True, WHITE)
    screen.blit(hp_text, hp_text.get_rect(center=(WIDTH // 2, 56 + bar_h // 2)))

    scale = 10
    sprite_w = len(DARK_KNIGHT_SPRITE[0]) * scale
    sprite_h = len(DARK_KNIGHT_SPRITE) * scale
    origin_x = (WIDTH - sprite_w) // 2
    origin_y = 90
    draw_pixel_grid(screen, DARK_KNIGHT_SPRITE, DARK_KNIGHT_PALETTE, scale, origin_x, origin_y)

    # ---- fighter (bottom) ----
    fighter_y = origin_y + sprite_h + 30
    fw, fh = fighter_image.get_size()
    screen.blit(fighter_image, (WIDTH // 2 - fw // 2, fighter_y))

    name_label = big_font.render(fighter_name, True, (120, 200, 255))
    screen.blit(name_label, name_label.get_rect(center=(WIDTH // 2, fighter_y + fh + 20)))

    draw_hp_bar(
        screen, WIDTH // 2 - bar_w // 2, fighter_y + fh + 42, bar_w, bar_h,
        fighter_hp, fighter_max_hp, HP_GREEN,
    )
    fighter_hp_text = small_font.render(f"{max(0, fighter_hp)}/{fighter_max_hp}", True, WHITE)
    screen.blit(
        fighter_hp_text,
        fighter_hp_text.get_rect(center=(WIDTH // 2, fighter_y + fh + 42 + bar_h // 2)),
    )

    # ---- battle log ----
    log_y = HEIGHT - 96
    for i, line in enumerate(battle_log[-2:]):
        line_surface = small_font.render(line, True, WHITE)
        screen.blit(line_surface, line_surface.get_rect(center=(WIDTH // 2, log_y + i * 22)))

    # ---- menu / outcome ----
    if battle_phase == "choose":
        spacing = 140
        start_x = WIDTH // 2 - spacing * (len(BATTLE_OPTIONS) - 1) // 2
        for i, option in enumerate(BATTLE_OPTIONS):
            color = YELLOW if i == battle_selected else WHITE
            option_surface = big_font.render(option, True, color)
            screen.blit(
                option_surface,
                option_surface.get_rect(center=(start_x + i * spacing, HEIGHT - 30)),
            )

    elif battle_phase == "victory":
        msg = big_font.render("You defeated the Dark Knight!", True, HP_GREEN)
        screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT - 40)))
        hint = small_font.render("Press Enter to continue", True, (180, 180, 180))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 16)))

    elif battle_phase == "defeat":
        msg = big_font.render(f"{fighter_name} was knocked out!", True, DANGER_RED)
        screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT - 40)))
        hint = small_font.render("Press Enter to wake up back at the start", True, (180, 180, 180))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 16)))


if __name__ == "__main__":
    main()

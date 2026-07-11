"""
Wondernight
My first video game!

A race through a big forest, starring Mark, a knight in golden armor
with white hair, and his companion Cam, a boy with long brown hair and
a red shirt with a yellow sunflower. Dark Knights roam the forest, each
one wandering to a new spot every 2 seconds.

Mark and Cam take turns trying to run from a random START to a FINISH
on the opposite side of the map. Bump into a Dark Knight and you'll
have to fight it. Reach the finish and you score 100 points and the
forest gets 5 more Dark Knights for the next run. Defeat a Dark Knight
and you score 50 points. Press D to transform into a dragon - dragons
have 50% more health, but move 50% slower. If both racers fall in a
row, everything resets: scores, wins, and the number of Dark Knights
all go back to the start.

Mark, Cam, the Dark Knight, the dragons, the sword, the fire, and the
tree are all real hand-drawn art (from the assets/ folder). Only the
ground tiles are still simple flat colors.

When you run this:
1. A black window pops up and "Wondernight" flashes blue/green in the
   middle of the screen (the intro).
2. After 5 seconds, "Start" and "Quit" buttons appear at the bottom
   of the screen. Click one, or use the Up/Down arrow keys + Enter.
3. Hit Start and Mark takes the first turn from a random spot in the
   forest.
   Controls:
     Arrow keys - move
     I          - swing! Mark swings his sword, Cam shoots fire
                  from his sunflower (just for show)
     D          - transform! Mark becomes a gold dragon, Cam becomes
                  a red dragon (press D again to change back). Dragons
                  have more health but move more slowly.
     Esc        - quit any time
   Walking into a Dark Knight (or one wandering into you) starts a
   real battle:
     Up/Down - choose Attack or Run
     Enter   - confirm
   Reach the finish and it becomes the other character's turn, with a
   brand new random start and finish. Run out of health and it also
   becomes the other character's turn - unless that makes two losses
   in a row, in which case everything resets.
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
STATE_FINISH = "finish"

# ---- Forest map (20 x 14) ----
# 'T' = tree (blocked), '.' = grass (walkable)
TILE_SIZE = 80
HUD_HEIGHT = 40
VIEWPORT_WIDTH = WIDTH
VIEWPORT_HEIGHT = HEIGHT - HUD_HEIGHT

MAP_ROWS = [
    "TTTTTTTTTTTTTTTTTTTT",
    "T..................T",
    "T........T.........T",
    "TT....T...........TT",
    "T...T..............T",
    "T....T.............T",
    "T........T......T..T",
    "T..TT.T....T......TT",
    "TT..T...T.T......TTT",
    "T......T..T......T.T",
    "T........T..T......T",
    "T.......T..........T",
    "T..T..T............T",
    "TTTTTTTTTTTTTTTTTTTT",
]
MAP_COLS = len(MAP_ROWS[0])
MAP_ROW_COUNT = len(MAP_ROWS)
MAP_PIXEL_WIDTH = MAP_COLS * TILE_SIZE
MAP_PIXEL_HEIGHT = MAP_ROW_COUNT * TILE_SIZE

GRASS_COLOR = (34, 120, 34)
GRASS_COLOR_ALT = (30, 108, 30)
START_COLOR = (70, 190, 90)
FINISH_COLOR = (210, 180, 60)

# Start and finish move every run - see pick_start_and_finish(). The finish is
# always placed on the far side of the map from wherever the start landed.
MIN_START_FINISH_DISTANCE = (MAP_COLS + MAP_ROW_COUNT) // 2

BASE_ENEMY_COUNT = 20      # how many Dark Knights the forest starts with
ENEMIES_PER_WIN = 5        # extra Dark Knights added after each successful run
ENEMY_MOVE_INTERVAL_MS = 2000
RESPAWN_DELAY_MS = 30000  # 30 seconds after the last one falls, they all come back

ATTACK_DURATION_MS = 350

FACING_OFFSET = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

# ---- Combat & scoring stats ----
MARK_BASE_MAX_HP = 30
CAM_BASE_MAX_HP = 30
ENEMY_MAX_HP = 20
PLAYER_ATK_RANGE = (4, 9)
ENEMY_ATK_RANGE = (2, 6)
BATTLE_OPTIONS = ["Attack", "Run"]

SCORE_PER_WIN = 100
SCORE_PER_KILL = 50

DRAGON_HP_MULTIPLIER = 1.5          # dragons have 50% more health
BASE_MOVE_COOLDOWN_MS = 150         # minimum time between steps
DRAGON_MOVE_COOLDOWN_MS = BASE_MOVE_COOLDOWN_MS * 2   # dragons move 50% slower

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# How big each drawn-art image should appear on screen (pygame scales the
# original art to fit these sizes, keeping its proportions).
MARK_TARGET_H = 130
CAM_TARGET_H = 118
DARK_KNIGHT_TARGET_H = 130
DRAGON_TARGET_W = 170
TREE_TARGET_H = 100
GRASS_TARGET_W = 28  # small ground texture tuft, scattered one per grass tile
SWORD_TARGET_H = 65
FIRE_TARGET_W = 65
BATTLE_PORTRAIT_H = 140       # bigger version of Mark/Cam for the battle screen
DARK_KNIGHT_BATTLE_H = 170    # bigger version of the Dark Knight for the battle screen


def load_scaled(filename, target_h=None, target_w=None):
    """Load a PNG from assets/ and scale it to a target height or width,
    keeping its original proportions."""
    path = os.path.join(ASSET_DIR, filename)
    image = pygame.image.load(path).convert_alpha()
    w, h = image.get_size()
    scale = (target_h / h) if target_h else (target_w / w)
    new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
    return pygame.transform.smoothscale(image, new_size)


def is_walkable(col, row):
    """A tile is walkable if it's inside the map and isn't a tree."""
    if row < 0 or row >= MAP_ROW_COUNT:
        return False
    if col < 0 or col >= MAP_COLS:
        return False
    return MAP_ROWS[row][col] == "."


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


def base_max_hp(character):
    return MARK_BASE_MAX_HP if character == "mark" else CAM_BASE_MAX_HP


def effective_max_hp(character, is_dragon):
    """Dragons carry 50% more health than their human max."""
    base = base_max_hp(character)
    return round(base * DRAGON_HP_MULTIPLIER) if is_dragon else base


def compute_camera(col, row):
    """Center the camera on a tile, clamped so it never shows past the map edge."""
    px_x = col * TILE_SIZE + TILE_SIZE // 2
    px_y = row * TILE_SIZE + TILE_SIZE // 2
    cam_x = px_x - VIEWPORT_WIDTH // 2
    cam_y = px_y - VIEWPORT_HEIGHT // 2
    cam_x = max(0, min(cam_x, MAP_PIXEL_WIDTH - VIEWPORT_WIDTH))
    cam_y = max(0, min(cam_y, MAP_PIXEL_HEIGHT - VIEWPORT_HEIGHT))
    return cam_x, cam_y


def nearest_open_tile(target_col, target_row, open_tiles):
    """Find whichever walkable tile is closest to a (possibly off-map) target spot."""
    target_col = max(0, min(MAP_COLS - 1, target_col))
    target_row = max(0, min(MAP_ROW_COUNT - 1, target_row))
    return min(open_tiles, key=lambda t: (t[0] - target_col) ** 2 + (t[1] - target_row) ** 2)


def pick_start_and_finish():
    """Pick a random start tile, then put the finish on the opposite side of the map."""
    open_tiles = [
        (col, row)
        for row in range(MAP_ROW_COUNT)
        for col in range(MAP_COLS)
        if MAP_ROWS[row][col] == "."
    ]
    for _ in range(300):
        start = random.choice(open_tiles)
        mirror_col = (MAP_COLS - 1) - start[0]
        mirror_row = (MAP_ROW_COUNT - 1) - start[1]
        finish = nearest_open_tile(mirror_col, mirror_row, open_tiles)
        if finish == start:
            continue
        distance = abs(finish[0] - start[0]) + abs(finish[1] - start[1])
        if distance < MIN_START_FINISH_DISTANCE:
            continue
        return start, finish
    # Fallback (shouldn't happen on a well-connected map): just take two far-apart tiles.
    open_tiles_sorted = sorted(open_tiles, key=lambda t: t[0] + t[1])
    return open_tiles_sorted[0], open_tiles_sorted[-1]


def random_enemy_positions(count, start, finish, exclude=None):
    """Pick random walkable tiles for the Dark Knights, clear of the start/finish and each other."""
    no_spawn = {start, finish}
    for d_col, d_row in FACING_OFFSET.values():
        no_spawn.add((start[0] + d_col, start[1] + d_row))
    if exclude:
        no_spawn |= set(exclude)

    open_tiles = [
        (col, row)
        for row in range(MAP_ROW_COUNT)
        for col in range(MAP_COLS)
        if MAP_ROWS[row][col] == "." and (col, row) not in no_spawn
    ]
    random.shuffle(open_tiles)
    count = min(count, len(open_tiles))
    chosen = open_tiles[:count]
    return [{"col": col, "row": row} for col, row in chosen]


def move_enemies(enemies):
    """Every Dark Knight wanders to a random adjacent open tile, if one is free."""
    occupied = {(e["col"], e["row"]) for e in enemies}
    for enemy in enemies:
        here = (enemy["col"], enemy["row"])
        options = []
        for d_col, d_row in FACING_OFFSET.values():
            candidate = (enemy["col"] + d_col, enemy["row"] + d_row)
            if is_walkable(*candidate) and candidate not in occupied:
                options.append(candidate)
        if options:
            new_col, new_row = random.choice(options)
            occupied.discard(here)
            enemy["col"], enemy["row"] = new_col, new_row
            occupied.add((new_col, new_row))


def draw_active_marker(screen, col, row, cam_x, cam_y):
    """A little yellow diamond under whichever character is taking their turn."""
    cx = col * TILE_SIZE - cam_x + TILE_SIZE // 2
    cy = row * TILE_SIZE - cam_y + TILE_SIZE - 6
    pygame.draw.polygon(
        screen, YELLOW,
        [(cx, cy - 5), (cx + 6, cy), (cx, cy + 5), (cx - 6, cy)],
    )


def draw_image_character(screen, surface, col, row, cam_x, cam_y):
    """Draw a real-art sprite anchored so its feet sit at the bottom of its tile."""
    w, h = surface.get_size()
    tile_x = col * TILE_SIZE - cam_x
    tile_y = row * TILE_SIZE - cam_y
    x = tile_x + (TILE_SIZE - w) // 2
    y = tile_y + TILE_SIZE - h
    screen.blit(surface, (x, y))


def draw_attack_effect_image(screen, images_by_facing, col, row, facing, cam_x, cam_y):
    """Draw a real-art attack effect centered in the tile the character is facing."""
    d_col, d_row = FACING_OFFSET.get(facing, (0, 1))
    target_col, target_row = col + d_col, row + d_row
    image = images_by_facing.get(facing, images_by_facing["down"])
    w, h = image.get_size()
    x = target_col * TILE_SIZE - cam_x + (TILE_SIZE - w) // 2
    y = target_row * TILE_SIZE - cam_y + (TILE_SIZE - h) // 2
    screen.blit(image, (x, y))


def draw_marker_tile(screen, x, y, color, letter, flag_color, font):
    pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))
    pole_x = x + TILE_SIZE // 2 - 2
    pygame.draw.rect(screen, (90, 60, 30), (pole_x, y + 8, 4, TILE_SIZE - 16))
    flag_points = [(pole_x + 4, y + 10), (pole_x + 30, y + 20), (pole_x + 4, y + 30)]
    pygame.draw.polygon(screen, flag_color, flag_points)
    letter_surface = font.render(letter, True, (20, 20, 20))
    screen.blit(letter_surface, letter_surface.get_rect(center=(pole_x + 14, y + 20)))


def draw_forest(screen, tree_image, grass_image, marker_font, cam_x, cam_y, start, finish):
    col_start = max(0, cam_x // TILE_SIZE)
    col_end = min(MAP_COLS, (cam_x + VIEWPORT_WIDTH) // TILE_SIZE + 2)
    row_start = max(0, cam_y // TILE_SIZE)
    row_end = min(MAP_ROW_COUNT, (cam_y + VIEWPORT_HEIGHT) // TILE_SIZE + 2)

    for row in range(row_start, row_end):
        for col in range(col_start, col_end):
            x = col * TILE_SIZE - cam_x
            y = row * TILE_SIZE - cam_y
            tile = MAP_ROWS[row][col]

            if (col, row) == start:
                draw_marker_tile(screen, x, y, START_COLOR, "S", WHITE, marker_font)
                continue
            if (col, row) == finish:
                draw_marker_tile(screen, x, y, FINISH_COLOR, "F", DANGER_RED, marker_font)
                continue

            grass = GRASS_COLOR if (row + col) % 2 == 0 else GRASS_COLOR_ALT
            pygame.draw.rect(screen, grass, (x, y, TILE_SIZE, TILE_SIZE))

            if tile == "T":
                tw, th = tree_image.get_size()
                screen.blit(tree_image, (x + (TILE_SIZE - tw) // 2, y + TILE_SIZE - th))
            else:
                gw, gh = grass_image.get_size()
                screen.blit(grass_image, (x + (TILE_SIZE - gw) // 2, y + TILE_SIZE - gh))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wondernight")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", TITLE_FONT_SIZE, bold=True)
    menu_font = pygame.font.SysFont("arial", MENU_FONT_SIZE, bold=True)
    hud_font = pygame.font.SysFont("arial", 15)
    battle_font = pygame.font.SysFont("arial", 28, bold=True)
    battle_small_font = pygame.font.SysFont("arial", 18)
    marker_font = pygame.font.SysFont("arial", 22, bold=True)

    # ---- load the real art (drawn assets) ----
    mark_image = load_scaled("mark.png", target_h=MARK_TARGET_H)
    cam_image = load_scaled("cam.png", target_h=CAM_TARGET_H)
    dark_knight_image = load_scaled("dark_knight.png", target_h=DARK_KNIGHT_TARGET_H)
    gold_dragon_image = load_scaled("gold_dragon.png", target_w=DRAGON_TARGET_W)
    red_dragon_image = load_scaled("red_dragon.png", target_w=DRAGON_TARGET_W)
    tree_image = load_scaled("tree.png", target_h=TREE_TARGET_H)
    grass_image = load_scaled("grass.png", target_w=GRASS_TARGET_W)
    sword_up = load_scaled("sword.png", target_h=SWORD_TARGET_H)
    fire_right = load_scaled("fire.png", target_w=FIRE_TARGET_W)
    mark_portrait = load_scaled("mark.png", target_h=BATTLE_PORTRAIT_H)
    cam_portrait = load_scaled("cam.png", target_h=BATTLE_PORTRAIT_H)
    dark_knight_portrait = load_scaled("dark_knight.png", target_h=DARK_KNIGHT_BATTLE_H)

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

    # ---- turn-based race state ----
    active = "mark"  # whoever's turn it is: "mark" or "cam"
    mark_col, mark_row = 0, 0
    cam_col, cam_row = 0, 0
    mark_facing = "down"
    cam_facing = "down"
    mark_hp = MARK_BASE_MAX_HP
    cam_hp = CAM_BASE_MAX_HP
    wins = {"mark": 0, "cam": 0}
    scores = {"mark": 0, "cam": 0}
    deaths_in_a_row = 0
    pending_reset = False

    mark_attack_until = 0
    cam_attack_until = 0
    dragon_mode = False  # press D to toggle - dragons are tougher but slower
    last_move_time = 0

    # ---- shared map state - re-randomized every time a fresh run begins ----
    current_start, current_finish = pick_start_and_finish()

    # ---- enemies ----
    enemy_count = BASE_ENEMY_COUNT
    enemies = random_enemy_positions(enemy_count, current_start, current_finish)
    last_enemy_move_time = pygame.time.get_ticks()
    all_defeated_at = None  # timestamp when the last Dark Knight fell, or None

    # ---- battle state (only meaningful while state == STATE_BATTLE) ----
    battle_enemy_ref = None     # the actual enemy dict currently being fought
    battle_fighter = "mark"     # who's fighting: "mark" or "cam"
    battle_enemy_hp = ENEMY_MAX_HP
    battle_phase = "choose"     # "choose", "victory", or "defeat"
    battle_selected = 0
    battle_log = []

    def start_turn_for(character):
        """Send a character to a brand new random start, fully healed and human, for a fresh run."""
        nonlocal mark_col, mark_row, cam_col, cam_row, mark_hp, cam_hp
        nonlocal current_start, current_finish, dragon_mode, last_move_time
        current_start, current_finish = pick_start_and_finish()
        dragon_mode = False
        last_move_time = 0
        if character == "mark":
            mark_col, mark_row = current_start
            mark_hp = MARK_BASE_MAX_HP
        else:
            cam_col, cam_row = current_start
            cam_hp = CAM_BASE_MAX_HP

    # give Mark his first run, and line Cam up at the same spot for when it's his turn
    start_turn_for("mark")
    cam_col, cam_row = current_start

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
                    if event.key == pygame.K_d:
                        old_max = effective_max_hp(active, dragon_mode)
                        dragon_mode = not dragon_mode
                        new_max = effective_max_hp(active, dragon_mode)
                        if active == "mark":
                            mark_hp = max(1, min(new_max, round(mark_hp * new_max / old_max)))
                        else:
                            cam_hp = max(1, min(new_max, round(cam_hp * new_max / old_max)))

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
                            move_check_time = pygame.time.get_ticks()
                            move_cooldown = DRAGON_MOVE_COOLDOWN_MS if dragon_mode else BASE_MOVE_COOLDOWN_MS
                            if move_check_time - last_move_time >= move_cooldown:
                                last_move_time = move_check_time

                                new_direction = direction_from_delta(d_col, d_row)
                                cur_col = mark_col if active == "mark" else cam_col
                                cur_row = mark_row if active == "mark" else cam_row

                                if active == "mark":
                                    mark_facing = new_direction
                                else:
                                    cam_facing = new_direction

                                new_col, new_row = cur_col + d_col, cur_row + d_row

                                enemy_here = next(
                                    (e for e in enemies if (e["col"], e["row"]) == (new_col, new_row)),
                                    None,
                                )

                                if enemy_here is not None:
                                    state = STATE_BATTLE
                                    battle_enemy_ref = enemy_here
                                    battle_fighter = active
                                    battle_enemy_hp = ENEMY_MAX_HP
                                    battle_phase = "choose"
                                    battle_selected = 0
                                    battle_log = []

                                elif is_walkable(new_col, new_row):
                                    if active == "mark":
                                        mark_col, mark_row = new_col, new_row
                                    else:
                                        cam_col, cam_row = new_col, new_row

                                    if (new_col, new_row) == current_finish:
                                        wins[active] += 1
                                        scores[active] += SCORE_PER_WIN
                                        deaths_in_a_row = 0
                                        state = STATE_FINISH

                elif state == STATE_BATTLE:
                    if battle_phase == "choose":
                        if event.key in (pygame.K_UP, pygame.K_DOWN):
                            battle_selected = (battle_selected + 1) % len(BATTLE_OPTIONS)

                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            choice = BATTLE_OPTIONS[battle_selected]

                            if choice == "Run":
                                state = STATE_OVERWORLD
                                battle_enemy_ref = None

                            elif choice == "Attack":
                                fighter_name = "Mark" if battle_fighter == "mark" else "Cam"
                                player_dmg = random.randint(*PLAYER_ATK_RANGE)
                                battle_enemy_hp -= player_dmg
                                battle_log = [f"{fighter_name} hits the Dark Knight for {player_dmg}!"]

                                if battle_enemy_hp <= 0:
                                    battle_enemy_hp = 0
                                    battle_phase = "victory"
                                    scores[battle_fighter] += SCORE_PER_KILL
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
                                        deaths_in_a_row += 1
                                        pending_reset = deaths_in_a_row >= 2

                    elif battle_phase == "victory":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if battle_enemy_ref in enemies:
                                enemies.remove(battle_enemy_ref)
                            battle_enemy_ref = None
                            state = STATE_OVERWORLD

                    elif battle_phase == "defeat":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if pending_reset:
                                # both racers have fallen in a row - start completely over
                                scores["mark"] = 0
                                scores["cam"] = 0
                                wins["mark"] = 0
                                wins["cam"] = 0
                                enemy_count = BASE_ENEMY_COUNT
                                deaths_in_a_row = 0
                                pending_reset = False
                                active = "cam" if active == "mark" else "mark"
                                start_turn_for(active)
                                enemies = random_enemy_positions(enemy_count, current_start, current_finish)
                                all_defeated_at = None
                            else:
                                # this character's turn is over - pass it to the other one
                                active = "cam" if active == "mark" else "mark"
                                start_turn_for(active)
                            battle_enemy_ref = None
                            state = STATE_OVERWORLD

                elif state == STATE_FINISH:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        enemy_count += ENEMIES_PER_WIN
                        active = "cam" if active == "mark" else "mark"
                        start_turn_for(active)
                        extra_knights = random_enemy_positions(
                            ENEMIES_PER_WIN, current_start, current_finish,
                            exclude={(e["col"], e["row"]) for e in enemies},
                        )
                        enemies.extend(extra_knights)
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

        if state == STATE_OVERWORLD:
            # every Dark Knight wanders to a new tile every couple of seconds
            if now - last_enemy_move_time >= ENEMY_MOVE_INTERVAL_MS:
                last_enemy_move_time = now
                move_enemies(enemies)

                active_col = mark_col if active == "mark" else cam_col
                active_row = mark_row if active == "mark" else cam_row
                ambusher = next(
                    (e for e in enemies if (e["col"], e["row"]) == (active_col, active_row)),
                    None,
                )
                if ambusher is not None:
                    state = STATE_BATTLE
                    battle_enemy_ref = ambusher
                    battle_fighter = active
                    battle_enemy_hp = ENEMY_MAX_HP
                    battle_phase = "choose"
                    battle_selected = 0
                    battle_log = ["The Dark Knight ambushes you!"]

            # once every Dark Knight has fallen, start the respawn clock;
            # 30 seconds later, bring them all back at new random spots
            if not enemies and all_defeated_at is None:
                all_defeated_at = now
            if all_defeated_at is not None and now - all_defeated_at >= RESPAWN_DELAY_MS:
                enemies = random_enemy_positions(enemy_count, current_start, current_finish)
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
            active_col = mark_col if active == "mark" else cam_col
            active_row = mark_row if active == "mark" else cam_row
            active_facing = mark_facing if active == "mark" else cam_facing
            cam_x, cam_y = compute_camera(active_col, active_row)

            draw_forest(screen, tree_image, grass_image, marker_font, cam_x, cam_y, current_start, current_finish)

            for enemy in enemies:
                draw_image_character(screen, dark_knight_image, enemy["col"], enemy["row"], cam_x, cam_y)

            draw_active_marker(screen, active_col, active_row, cam_x, cam_y)

            if dragon_mode:
                dragon_image = gold_dragon_image if active == "mark" else red_dragon_image
                draw_image_character(screen, dragon_image, active_col, active_row, cam_x, cam_y)
            else:
                char_image = mark_image if active == "mark" else cam_image
                draw_image_character(screen, char_image, active_col, active_row, cam_x, cam_y)

            attack_until = mark_attack_until if active == "mark" else cam_attack_until
            if now < attack_until:
                effect = sword_by_facing if active == "mark" else fire_by_facing
                draw_attack_effect_image(screen, effect, active_col, active_row, active_facing, cam_x, cam_y)

            draw_hud(screen, hud_font, active, dragon_mode, respawn_seconds, wins, scores)

        elif state == STATE_BATTLE:
            fighter_image = mark_portrait if battle_fighter == "mark" else cam_portrait
            fighter_name = "Mark" if battle_fighter == "mark" else "Cam"
            fighter_hp = mark_hp if battle_fighter == "mark" else cam_hp
            fighter_max_hp = effective_max_hp(battle_fighter, dragon_mode)

            draw_battle_screen(
                screen, battle_font, battle_small_font,
                fighter_image, fighter_name, fighter_hp, fighter_max_hp,
                dark_knight_portrait, battle_enemy_hp, battle_phase, battle_selected, battle_log,
                pending_reset,
            )

        elif state == STATE_FINISH:
            winner_name = "Mark" if active == "mark" else "Cam"
            next_name = "Cam" if active == "mark" else "Mark"
            draw_finish_screen(screen, battle_font, battle_small_font, winner_name, next_name, wins, scores)

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


def draw_hud(screen, font, active, dragon_mode, respawn_seconds, wins, scores):
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
            f"{who}'s turn!  Mark {wins['mark']}W/{scores['mark']}pt  "
            f"Cam {wins['cam']}W/{scores['cam']}pt  |  Move:Arrows  Attack:I  Dragon:D  Quit:Esc",
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
    dark_knight_portrait, enemy_hp, battle_phase, battle_selected, battle_log,
    pending_reset=False,
):
    screen.fill(BACKGROUND_COLOR)

    # ---- Dark Knight (top) ----
    label = big_font.render("Dark Knight", True, DANGER_RED)
    screen.blit(label, label.get_rect(center=(WIDTH // 2, 30)))

    bar_w, bar_h = 260, 18
    draw_hp_bar(screen, WIDTH // 2 - bar_w // 2, 50, bar_w, bar_h, enemy_hp, ENEMY_MAX_HP, HP_RED)
    hp_text = small_font.render(f"{max(0, enemy_hp)}/{ENEMY_MAX_HP}", True, WHITE)
    screen.blit(hp_text, hp_text.get_rect(center=(WIDTH // 2, 50 + bar_h // 2)))

    kw, kh = dark_knight_portrait.get_size()
    knight_y = 76
    screen.blit(dark_knight_portrait, (WIDTH // 2 - kw // 2, knight_y))

    # ---- fighter (bottom) ----
    fighter_y = knight_y + kh + 14
    fw, fh = fighter_image.get_size()
    screen.blit(fighter_image, (WIDTH // 2 - fw // 2, fighter_y))

    name_label = big_font.render(fighter_name, True, (120, 200, 255))
    screen.blit(name_label, name_label.get_rect(center=(WIDTH // 2, fighter_y + fh + 16)))

    draw_hp_bar(
        screen, WIDTH // 2 - bar_w // 2, fighter_y + fh + 36, bar_w, bar_h,
        fighter_hp, fighter_max_hp, HP_GREEN,
    )
    fighter_hp_text = small_font.render(f"{max(0, fighter_hp)}/{fighter_max_hp}", True, WHITE)
    screen.blit(
        fighter_hp_text,
        fighter_hp_text.get_rect(center=(WIDTH // 2, fighter_y + fh + 36 + bar_h // 2)),
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
        msg = big_font.render(f"You defeated the Dark Knight! +{SCORE_PER_KILL} points", True, HP_GREEN)
        screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT - 40)))
        hint = small_font.render("Press Enter to continue", True, (180, 180, 180))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 16)))

    elif battle_phase == "defeat":
        msg = big_font.render(f"{fighter_name} was knocked out!", True, DANGER_RED)
        screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT - 40)))
        if pending_reset:
            hint = small_font.render(
                "Both racers have fallen! Press Enter to reset everything", True, (180, 180, 180)
            )
        else:
            hint = small_font.render("Press Enter - the other player is up next", True, (180, 180, 180))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 16)))


def draw_finish_screen(screen, big_font, small_font, winner_name, next_name, wins, scores):
    screen.fill(BACKGROUND_COLOR)

    msg = big_font.render(f"{winner_name} made it to the finish! +{SCORE_PER_WIN} points", True, HP_GREEN)
    screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 56)))

    tally = small_font.render(
        f"Wins - Mark: {wins['mark']}   Cam: {wins['cam']}     "
        f"Score - Mark: {scores['mark']}   Cam: {scores['cam']}",
        True, WHITE,
    )
    screen.blit(tally, tally.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10)))

    warning = small_font.render(
        f"{ENEMIES_PER_WIN} more Dark Knights have joined the forest!", True, YELLOW,
    )
    screen.blit(warning, warning.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 24)))

    hint = small_font.render(f"Press Enter for {next_name}'s turn", True, (180, 180, 180))
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 58)))


if __name__ == "__main__":
    main()

"""
Wondernight 3D
A full 3D rebuild of Wondernight using the Ursina engine (Python/Panda3D).

Same race-and-battle game as the 2D version, but rendered in a real 3D
world with a perspective camera: a blocky/low-poly placeholder look
stands in for the original hand-drawn 2D art, since true 3D models of
Mark, Cam, Oni, the Dark Knights, and every transformation don't exist.

Run it with:  python3 wondernight3d.py
"""

from ursina import *
import random

# =====================================================================
# ---- Map (same layout & rules as the 2D game) ----
# =====================================================================
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
MIN_START_FINISH_DISTANCE = (MAP_COLS + MAP_ROW_COUNT) // 2

CHARACTER_ORDER = ["mark", "cam", "oni"]
DISPLAY_NAME = {"mark": "Mark", "cam": "Cam", "oni": "Oni"}

# Per-character color scheme (primary body, accent) - stands in for the
# hand-drawn art since these are blocky placeholder models.
CHARACTER_COLORS = {
    "mark": (color.rgb32(230, 190, 60), color.rgb32(250, 250, 255)),   # gold knight
    "cam": (color.rgb32(190, 60, 40), color.rgb32(230, 200, 60)),      # red/sunflower
    "oni": (color.rgb32(60, 20, 30), color.rgb32(220, 60, 40)),        # dark demon/flame
}
FORM_COLOR_TINT = {
    "dragon": {"mark": color.rgb32(255, 210, 60), "cam": color.rgb32(220, 40, 30), "oni": color.rgb32(90, 20, 110)},
    "whale": {"mark": color.rgb32(210, 190, 230), "cam": color.rgb32(200, 60, 60), "oni": color.rgb32(70, 70, 90)},
    "bird": {"mark": color.rgb32(230, 180, 40), "cam": color.rgb32(200, 50, 40), "oni": color.rgb32(120, 60, 160)},
    "werewolf": {"mark": color.rgb32(110, 95, 80), "cam": color.rgb32(110, 95, 80), "oni": color.rgb32(90, 75, 65)},
}
DARK_KNIGHT_COLOR = color.rgb32(35, 25, 45)
PRINCESS_COLOR = (color.rgb32(250, 210, 230), color.rgb32(255, 255, 255))
SHIP_COLOR = color.rgb32(90, 60, 30)

# ---- voxel-style character art (billboarded sprites in the 3D world) ----
import os as _os
ASSET3D_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "assets3d")

_texture3d_cache = {}

def asset3d(name):
    """Load a texture from assets3d/ by filename. Builds a Texture directly
    from the full path (rather than Ursina's load_texture folder-search,
    whose keyword args vary across Ursina/Panda3D versions)."""
    if name not in _texture3d_cache:
        full_path = _os.path.join(ASSET3D_DIR, name)
        if not _os.path.exists(full_path):
            print_warning(f"3D asset missing: {full_path}")
            _texture3d_cache[name] = None
        else:
            _texture3d_cache[name] = Texture(full_path)
    return _texture3d_cache[name]

TEXTURE_BY_FORM = {
    "human": {"mark": "mark.png", "cam": "cam.png", "oni": "oni.png"},
    "dragon": {"mark": "gold_dragon.png", "cam": "red_dragon.png", "oni": "oni_dragon.png"},
    "bird": {"mark": "gold_bird.png", "cam": "red_bird.png", "oni": "oni_bird.png"},
    "werewolf": {"mark": "werewolf.png", "cam": "werewolf.png", "oni": "werewolf.png"},
    # no source art exists for "whale" - it stays a primitive-shape model
}
FORM_BILLBOARD_HEIGHT = {"human": 1.5, "dragon": 2.0, "bird": 1.1, "werewolf": 2.1}
DARK_KNIGHT_BILLBOARD_HEIGHT = 1.9
SHIP_BILLBOARD_WIDTH = 2.6
PRINCESS_BILLBOARD_HEIGHT = 1.3

# width/height aspect ratio of each sprite, measured once ahead of time -
# used so billboards don't look squashed/stretched
ASPECT_BY_FILE = {
    "mark.png": 345 / 615, "cam.png": 285 / 595, "oni.png": 959 / 1440,
    "gold_dragon.png": 470 / 452, "red_dragon.png": 470 / 461, "oni_dragon.png": 470 / 461,
    "gold_bird.png": 1246 / 1219, "red_bird.png": 1246 / 1219, "oni_bird.png": 1234 / 1217,
    "werewolf.png": 1053 / 1161,
    "dark_knight.png": 998 / 1338,
    "ship.png": 1235 / 1251,
    "princess.png": 1023 / 1535,
}

# =====================================================================
# ---- Combat & scoring stats (ported 1:1 from the 2D game) ----
# =====================================================================
BASE_MAX_HP = {"mark": 30, "cam": 30, "oni": 30}
ENEMY_MAX_HP = 20
PLAYER_ATK_RANGE = (4, 9)
ENEMY_ATK_RANGE = (2, 6)

SCORE_PER_WIN = 100
SCORE_PER_KILL = 50

DRAGON_HP_MULTIPLIER = 1.5
DRAGON_DAMAGE_TAKEN_MULTIPLIER = 0.5
BASE_MOVE_COOLDOWN_MS = 150
DRAGON_MOVE_COOLDOWN_MS = 1000
BIRD_HP_MULTIPLIER = 0.75
BIRD_MOVE_COOLDOWN_MS = 75
WEREWOLF_DAMAGE_DEALT_MULTIPLIER = 1.5

FORM_HP_MULTIPLIER = {"dragon": DRAGON_HP_MULTIPLIER, "whale": DRAGON_HP_MULTIPLIER, "bird": BIRD_HP_MULTIPLIER}
FORM_MOVE_COOLDOWN_MS = {"dragon": DRAGON_MOVE_COOLDOWN_MS, "whale": DRAGON_MOVE_COOLDOWN_MS, "bird": BIRD_MOVE_COOLDOWN_MS}
FORM_DAMAGE_TAKEN_MULTIPLIER = {"dragon": DRAGON_DAMAGE_TAKEN_MULTIPLIER, "whale": DRAGON_DAMAGE_TAKEN_MULTIPLIER}
FORM_DAMAGE_DEALT_MULTIPLIER = {"werewolf": WEREWOLF_DAMAGE_DEALT_MULTIPLIER}
FORM_IGNORES_TREES = {"bird", "werewolf"}

MAX_ENEMY_COUNT = 30
ENEMY_COUNT_START = 20
ENEMY_COUNT_STEP = 5
ENEMY_WANDER_MS = 2000
ENEMY_SPEED_STEP_MS = 400

RUN_TIMER_GRACE_MS = 10000
HP_DRAIN_INTERVAL_MS = 1000
HP_DRAIN_PERCENT = 10

SHIELD_CATCHUP_DISTANCE = 4

FACING_OFFSET = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

# =====================================================================
# ---- Pure map/logic helpers (ported from the 2D game, no engine deps) ----
# =====================================================================

def is_walkable(col, row, ignore_trees=False):
    if row < 0 or row >= MAP_ROW_COUNT:
        return False
    if col < 0 or col >= MAP_COLS:
        return False
    if ignore_trees:
        return True
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


def effective_max_hp(character, form):
    base = BASE_MAX_HP[character]
    multiplier = FORM_HP_MULTIPLIER.get(form, 1.0)
    return max(1, round(base * multiplier))


def hp_percent(current, maximum):
    if maximum <= 0:
        return 0
    return max(0, min(100, round(100 * current / maximum)))


def random_open_tile(rng):
    while True:
        col = rng.randint(1, MAP_COLS - 2)
        row = rng.randint(1, MAP_ROW_COUNT - 2)
        if MAP_ROWS[row][col] == ".":
            return (col, row)


def pick_start_and_finish(rng):
    while True:
        start = random_open_tile(rng)
        finish = random_open_tile(rng)
        dist = abs(start[0] - finish[0]) + abs(start[1] - finish[1])
        if dist >= MIN_START_FINISH_DISTANCE:
            return start, finish


def random_enemy_positions(count, start, finish, rng):
    open_tiles = [
        (col, row)
        for row in range(MAP_ROW_COUNT)
        for col in range(MAP_COLS)
        if MAP_ROWS[row][col] == "." and (col, row) not in (start, finish)
    ]
    rng.shuffle(open_tiles)
    chosen = open_tiles[:count]
    return [{"col": c, "row": r} for c, r in chosen]


def pick_next_active(current, alive, roster):
    idx = roster.index(current)
    for step in range(1, len(roster) + 1):
        candidate = roster[(idx + step) % len(roster)]
        if alive[candidate]:
            return candidate
    return current

# =====================================================================
# ---- Engine setup ----
# =====================================================================
TILE_SIZE = 2
GRASS_COLOR = color.rgb32(40, 130, 60)
WATER_COLOR = color.rgb32(35, 95, 170)
TREE_TRUNK_COLOR = color.rgb32(90, 60, 30)
TREE_LEAF_COLOR = color.rgb32(35, 110, 45)

app = Ursina(borderless=False, development_mode=False)
window.title = "Wondernight 3D"
window.color = color.rgb32(10, 10, 20)


def grid_to_world(col, row, y=0):
    return Vec3(col * TILE_SIZE, y, row * TILE_SIZE)


def build_world():
    """Ground plane + trees + boundary sized to MAP_ROWS. Returns (ground, trees)."""
    width = MAP_COLS * TILE_SIZE
    depth = MAP_ROW_COUNT * TILE_SIZE
    ground = Entity(
        model='plane',
        scale=(width, 1, depth),
        position=(width / 2 - TILE_SIZE / 2, 0, depth / 2 - TILE_SIZE / 2),
        color=GRASS_COLOR,
        collider=None,
    )
    trees = []
    for row in range(MAP_ROW_COUNT):
        for col in range(MAP_COLS):
            if MAP_ROWS[row][col] == "T":
                pos = grid_to_world(col, row)
                trunk = Entity(model='cube', color=TREE_TRUNK_COLOR,
                                scale=(0.35, 1.1, 0.35), position=pos + Vec3(0, 0.55, 0))
                leaves = Entity(model='diamond', color=TREE_LEAF_COLOR,
                                 scale=(1.3, 1.7, 1.3), position=pos + Vec3(0, 1.5, 0))
                trees.append((trunk, leaves))
    return ground, trees


ground_entity, tree_entities = build_world()

# ---- Lighting ----
sun = DirectionalLight(y=2, z=3, rotation=(45, -30, 0))
sun.color = color.rgba32(255, 250, 235, 255)
ambient = AmbientLight(color=color.rgba32(120, 120, 140, 255))

# ---- Camera rig: elevated chase camera that follows the active racer ----
CHASE_DISTANCE = 6.5   # how far behind the character the camera sits
CHASE_HEIGHT = 5.5     # how high above the ground the camera sits
LOOK_HEIGHT = 1.2      # look at a point this high above the character's feet
camera.fov = 70

FACING_TO_WORLD_DIR = {
    "up": Vec3(0, 0, -1),
    "down": Vec3(0, 0, 1),
    "left": Vec3(-1, 0, 0),
    "right": Vec3(1, 0, 0),
}


def update_camera(target_pos, facing_dir="down"):
    """Third-person chase camera: sits behind the character (opposite
    their facing direction) and looks at them, swinging around as they
    turn so it's always 'behind you'."""
    direction = FACING_TO_WORLD_DIR.get(facing_dir, Vec3(0, 0, 1))
    camera.position = target_pos - direction * CHASE_DISTANCE + Vec3(0, CHASE_HEIGHT, 0)
    camera.look_at(target_pos + Vec3(0, LOOK_HEIGHT, 0))

# =====================================================================
# ---- Character / enemy / princess 3D rigs ----
# ---- (blocky placeholder models - primitives only, no external art) ----
# =====================================================================

def make_billboard(parent, filename, height, y_offset=0.0):
    """A camera-facing sprite quad, bottom-anchored so it 'stands' on the
    ground, textured with the voxel-style character art."""
    aspect = ASPECT_BY_FILE.get(filename, 1.0)
    b = Entity(
        parent=parent, model='quad', texture=asset3d(filename),
        scale=(height * aspect, height, 1), origin=(0, -0.5),
        position=(0, y_offset, 0), billboard=True, unlit=True,
        double_sided=True, alpha=1,
    )
    return b


def build_character_rig(character):
    """A voxel-art billboard sprite for human/dragon/bird/werewolf forms,
    plus a small set of primitive parts used only for whale form (no
    source art exists for the whale transformation)."""
    primary, accent = CHARACTER_COLORS[character]
    root = Entity(position=(0, 0, 0))
    sprite = make_billboard(root, TEXTURE_BY_FORM["human"][character], FORM_BILLBOARD_HEIGHT["human"])

    tint = FORM_COLOR_TINT["whale"][character]
    whale_body = Entity(parent=root, model='sphere', color=tint, scale=(1.0, 0.7, 1.3),
                         position=(0, 0.5, 0), enabled=False)
    whale_head = Entity(parent=root, model='sphere', color=tint, scale=(0.3, 0.3, 0.3),
                         position=(0, 0.85, 0.65), enabled=False)
    whale_fin_left = Entity(parent=root, model='diamond', color=accent, scale=(0.2, 0.4, 0.5),
                             position=(-0.45, 0.4, 0), enabled=False)
    whale_fin_right = Entity(parent=root, model='diamond', color=accent, scale=(0.2, 0.4, 0.5),
                              position=(0.45, 0.4, 0), enabled=False)
    whale_tail = Entity(parent=root, model='diamond', color=primary, scale=(0.25, 0.25, 0.9),
                         position=(0, 0.4, -0.55), enabled=False)
    return {
        "root": root, "sprite": sprite,
        "whale_body": whale_body, "whale_head": whale_head,
        "whale_fin_left": whale_fin_left, "whale_fin_right": whale_fin_right, "whale_tail": whale_tail,
    }


def apply_form_visuals(rig, form, character):
    """Swap the rig between a voxel-art billboard (human/dragon/bird/werewolf)
    and the primitive whale shape (no source art exists for that form)."""
    whale_parts = ("whale_body", "whale_head", "whale_fin_left", "whale_fin_right", "whale_tail")

    if form == "whale":
        rig["sprite"].enabled = False
        for part in whale_parts:
            rig[part].enabled = True
    else:
        for part in whale_parts:
            rig[part].enabled = False
        rig["sprite"].enabled = True
        rig["sprite"].texture = asset3d(TEXTURE_BY_FORM[form][character])
        height = FORM_BILLBOARD_HEIGHT[form]
        aspect = ASPECT_BY_FILE.get(TEXTURE_BY_FORM[form][character], 1.0)
        rig["sprite"].scale = (height * aspect, height, 1)


def build_dark_knight_rig():
    root = Entity(position=(0, 0, 0))
    sprite = make_billboard(root, "dark_knight.png", DARK_KNIGHT_BILLBOARD_HEIGHT)
    return {"root": root, "sprite": sprite}


def build_ship_rig():
    root = Entity(position=(0, 0, 0), enabled=False)
    aspect = ASPECT_BY_FILE.get("ship.png", 1.0)
    height = SHIP_BILLBOARD_WIDTH / aspect
    sprite = Entity(parent=root, model='quad', texture=asset3d("ship.png"),
                     scale=(SHIP_BILLBOARD_WIDTH, height, 1), origin=(0, -0.5),
                     billboard=True, unlit=True, double_sided=True)
    return {"root": root, "sprite": sprite}


def build_princess_rig():
    root = Entity(position=(0, 0, 0))
    sprite = make_billboard(root, "princess.png", PRINCESS_BILLBOARD_HEIGHT)
    return {"root": root, "sprite": sprite}

# =====================================================================
# ---- Game state ----
# =====================================================================
STATE_INTRO = "intro"
STATE_MENU = "menu"
STATE_CHARACTER_SELECT = "character_select"
STATE_READY = "ready"
STATE_OVERWORLD = "overworld"
STATE_BATTLE = "battle"
STATE_FINISH = "finish"
STATE_GAME_OVER = "game_over"
STATE_TIMEOUT = "timeout"

INTRO_DURATION_MS = 3000

rng = random.Random()

state = STATE_INTRO
intro_elapsed_ms = 0.0

menu_options = ["Start", "Quit"]
menu_selected_index = 0

roster = list(CHARACTER_ORDER)
char_selected = {c: False for c in CHARACTER_ORDER}
char_select_cursor = 0

active = "mark"
active_form = "human"
pos = {c: (1, 1) for c in CHARACTER_ORDER}
facing = {c: "down" for c in CHARACTER_ORDER}
hp = {c: BASE_MAX_HP[c] for c in CHARACTER_ORDER}
wins = {c: 0 for c in CHARACTER_ORDER}
scores = {c: 0 for c in CHARACTER_ORDER}
alive = {c: True for c in CHARACTER_ORDER}
runs_taken = {c: 0 for c in CHARACTER_ORDER}

current_start = (1, 1)
current_finish = (18, 12)
current_run_enemy_count = ENEMY_COUNT_START
capped_run_participants = set()
speed_round = 0

enemies = []  # list of {"col","row","rig","ship"}
move_cooldown_remaining = 0.0
enemy_wander_remaining = ENEMY_WANDER_MS
respawn_remaining = None  # ms, or None

run_elapsed_ms = 0.0
drain_ticks_applied = 0

princess_trail = [(1, 1)]
princess_trail_index = 1
princess_shield_ready = True

battle_fighter = None
battle_enemy_hp = 0
battle_phase = "choose"
battle_log = []
pending_game_over = False

ui_entities = []  # currently-active UI elements, destroyed on every screen rebuild

player_rig = build_character_rig("mark")
princess_rig = build_princess_rig()
princess_rig["root"].enabled = False

BATTLE_ARENA_ORIGIN = Vec3(-40, 0, -40)
battle_enemy_rig = build_dark_knight_rig()
battle_enemy_rig["root"].enabled = False


def clear_ui():
    global ui_entities
    for e in ui_entities:
        destroy(e)
    ui_entities = []


def ui_text(text, position, scale=1.2, color_=color.white, origin=(0, 0)):
    t = Text(text=text, position=position, scale=scale, color=color_, origin=origin, parent=camera.ui)
    ui_entities.append(t)
    return t

# =====================================================================
# ---- Core game flow ----
# =====================================================================

def spawn_enemies(count):
    global enemies
    for e in enemies:
        destroy(e["rig"]["root"])
        destroy(e["ship"]["root"])
    positions = random_enemy_positions(count, current_start, current_finish, rng)
    new_enemies = []
    for p in positions:
        rig = build_dark_knight_rig()
        rig["root"].position = grid_to_world(p["col"], p["row"])
        ship = build_ship_rig()
        ship["root"].position = grid_to_world(p["col"], p["row"])
        new_enemies.append({"col": p["col"], "row": p["row"], "rig": rig, "ship": ship})
    enemies = new_enemies


def start_turn_for(character):
    global active, active_form, current_start, current_finish, current_run_enemy_count
    global run_elapsed_ms, drain_ticks_applied, princess_trail, princess_trail_index
    global princess_shield_ready, respawn_remaining, move_cooldown_remaining

    active = character
    active_form = "human"
    current_start, current_finish = pick_start_and_finish(rng)
    pos[character] = current_start
    facing[character] = "down"
    hp[character] = BASE_MAX_HP[character]
    runs_taken[character] += 1

    current_run_enemy_count = min(MAX_ENEMY_COUNT, ENEMY_COUNT_START + ENEMY_COUNT_STEP * (runs_taken[character] - 1))
    spawn_enemies(current_run_enemy_count)
    respawn_remaining = None

    run_elapsed_ms = 0.0
    drain_ticks_applied = 0
    move_cooldown_remaining = 0.0

    princess_trail = [current_start]
    princess_trail_index = 1
    princess_shield_ready = True

    apply_form_visuals(player_rig, "human", character)
    player_rig["root"].position = grid_to_world(*current_start)
    princess_rig["root"].position = grid_to_world(*current_start)

    if current_run_enemy_count >= MAX_ENEMY_COUNT:
        capped_run_participants.add(character)
        still_alive = {c for c in roster if alive[c]}
        if still_alive and still_alive.issubset(capped_run_participants):
            globals()["speed_round"] += 1
            capped_run_participants.clear()


def full_reset():
    global speed_round
    for c in roster:
        scores[c] = 0
        wins[c] = 0
        alive[c] = True
        runs_taken[c] = 0
    capped_run_participants.clear()
    speed_round = 0
    start_turn_for(roster[0])
    for c in roster:
        if c != active:
            pos[c] = current_start
            hp[c] = BASE_MAX_HP[c]


def enemy_wander_speed_ms():
    return max(400, ENEMY_WANDER_MS - ENEMY_SPEED_STEP_MS * speed_round)

# =====================================================================
# ---- Screens / UI ----
# =====================================================================

def set_world_visible(visible):
    ground_entity.enabled = visible
    for trunk, leaves in tree_entities:
        trunk.enabled = visible
        leaves.enabled = visible
    princess_rig["root"].enabled = visible
    for e in enemies:
        e["rig"]["root"].enabled = visible
        if visible:
            e["ship"]["root"].enabled = (active_form == "whale")
        else:
            e["ship"]["root"].enabled = False
    if visible:
        player_rig["root"].position = grid_to_world(*pos[active])
    player_rig["root"].enabled = True
    battle_enemy_rig["root"].enabled = False


def enter_battle_arena():
    """Move the player + a Dark Knight model into a dedicated arena and
    point the camera at them for the battle screen, side by side so
    neither model occludes the other."""
    apply_form_visuals(player_rig, active_form, battle_fighter)
    player_rig["root"].position = BATTLE_ARENA_ORIGIN + Vec3(-1.4, 0, 0)
    player_rig["root"].rotation_y = -25
    battle_enemy_rig["root"].position = BATTLE_ARENA_ORIGIN + Vec3(1.4, 0, 0)
    battle_enemy_rig["root"].rotation_y = 25
    battle_enemy_rig["root"].enabled = True
    camera.position = BATTLE_ARENA_ORIGIN + Vec3(0, 1.4, -6.5)
    camera.rotation_x = 12
    camera.rotation_y = 0


def _menu_click(option):
    if option == "Start":
        set_state(STATE_CHARACTER_SELECT)
    else:
        application.quit()


def show_menu_screen():
    clear_ui()
    ui_text("WONDERNIGHT 3D", (0, 0.25), scale=3, origin=(0, 0))
    for i, opt in enumerate(menu_options):
        prefix = "> " if i == menu_selected_index else "  "
        btn = Button(
            text=prefix + opt, position=(0, 0.05 - i * 0.08), scale=(0.3, 0.06),
            color=color.rgb32(30, 30, 45) if i != menu_selected_index else color.rgb32(60, 55, 20),
            text_color=color.yellow if i == menu_selected_index else color.white,
            highlight_color=color.rgb32(70, 65, 30),
        )
        btn.on_click = lambda opt=opt: _menu_click(opt)
        ui_entities.append(btn)


def _toggle_character_click(c):
    global char_select_cursor
    char_select_cursor = CHARACTER_ORDER.index(c)
    char_selected[c] = not char_selected[c]
    show_character_select_screen()


def _play_click():
    global roster
    if not any(char_selected.values()):
        return
    roster = [c for c in CHARACTER_ORDER if char_selected[c]]
    full_reset()
    set_state(STATE_READY)


def show_character_select_screen():
    clear_ui()
    ui_text("SELECT RACERS", (0, 0.3), scale=2.2, origin=(0, 0))
    num_rows = len(CHARACTER_ORDER) + 1
    for i, c in enumerate(CHARACTER_ORDER):
        mark_str = "[x] " if char_selected[c] else "[ ] "
        prefix = "> " if char_select_cursor == i else "  "
        btn = Button(
            text=prefix + mark_str + DISPLAY_NAME[c], position=(0, 0.1 - i * 0.09), scale=(0.34, 0.07),
            color=color.rgb32(30, 30, 45) if char_select_cursor != i else color.rgb32(60, 55, 20),
            text_color=color.yellow if char_select_cursor == i else color.white,
            highlight_color=color.rgb32(70, 65, 30),
        )
        btn.on_click = lambda c=c: _toggle_character_click(c)
        ui_entities.append(btn)
    play_i = len(CHARACTER_ORDER)
    prefix = "> " if char_select_cursor == play_i else "  "
    play_btn = Button(
        text=prefix + "Play", position=(0, 0.1 - play_i * 0.09), scale=(0.34, 0.07),
        color=color.rgb32(30, 30, 45) if char_select_cursor != play_i else color.rgb32(60, 55, 20),
        text_color=color.lime if char_select_cursor == play_i else color.white,
        highlight_color=color.rgb32(40, 70, 40),
    )
    play_btn.on_click = _play_click
    ui_entities.append(play_btn)


def show_ready_screen():
    clear_ui()
    ui_text(f"{DISPLAY_NAME[active]}'s turn", (0, 0.15), scale=2.5, origin=(0, 0))
    btn = Button(text="Click or press Enter when ready", position=(0, 0), scale=(0.5, 0.08),
                 color=color.rgb32(30, 30, 45), text_color=color.white, highlight_color=color.rgb32(50, 50, 70))
    btn.on_click = lambda: set_state(STATE_OVERWORLD)
    ui_entities.append(btn)


def show_overworld_hud():
    clear_ui()
    dragon_note = f" ({active_form}!)" if active_form != "human" else ""
    eliminated = [DISPLAY_NAME[c] for c in roster if c != active and not alive[c]]
    solo_note = f" ({'/'.join(eliminated)} out!)" if eliminated else ""
    stats = "  ".join(f"{DISPLAY_NAME[c]} {wins[c]}W/{scores[c]}pt" for c in roster)
    if respawn_remaining is not None:
        bottom = f"All Dark Knights defeated! They respawn in {int(respawn_remaining/1000)+1}s"
    else:
        bottom = f"{DISPLAY_NAME[active]}'s turn{dragon_note}{solo_note}  {stats} | Arrows:move I:atk D/W/B/R:form Esc:quit"
    ui_text(bottom, (0, -0.46), scale=1, origin=(0, 0))
    ui_text("Princess Shield: Ready" if princess_shield_ready else "Princess Shield: Recharging",
            (-0.6, 0.46), scale=1, origin=(-0.5, 0))
    seconds_left = max(0, RUN_TIMER_GRACE_MS - int(run_elapsed_ms)) // 1000
    if run_elapsed_ms < RUN_TIMER_GRACE_MS:
        timer_text = f"Hurry! {seconds_left + 1}s until HP starts draining"
    else:
        timer_text = "HP DRAINING!"
    ui_text(timer_text, (0, 0.46), scale=1, origin=(0, 0), color_=color.yellow)


def hp_bar(pct, position, w=0.3):
    bg = Entity(parent=camera.ui, model='quad', color=color.rgb32(60, 20, 20), scale=(w, 0.03), position=position)
    fg = Entity(parent=camera.ui, model='quad', color=color.rgb32(60, 200, 90), scale=(w * pct / 100, 0.03),
                position=(position[0] - w / 2 + (w * pct / 100) / 2, position[1]))
    ui_entities.extend([bg, fg])


def show_battle_screen():
    clear_ui()
    fighter_max = effective_max_hp(battle_fighter, active_form)
    ui_text("Dark Knight", (0, 0.35), scale=2, origin=(0, 0), color_=color.red)
    hp_bar(hp_percent(battle_enemy_hp, ENEMY_MAX_HP), (0, 0.28))
    ui_text(DISPLAY_NAME[battle_fighter], (0, -0.15), scale=2, origin=(0, 0), color_=color.azure)
    hp_bar(hp_percent(hp[battle_fighter], fighter_max), (0, -0.22))
    for i, line in enumerate(battle_log[-3:]):
        ui_text(line, (0, -0.32 - i * 0.06), scale=1, origin=(0, 0))
    if battle_phase == "choose":
        ui_text("> Attack (Enter)", (0, -0.44), scale=1.2, origin=(0, 0), color_=color.yellow)
    elif battle_phase == "victory":
        ui_text("Victory! Press Enter to continue", (0, -0.44), scale=1.2, origin=(0, 0), color_=color.lime)
    elif battle_phase == "defeat":
        msg = "Game Over - press Enter" if pending_game_over else f"{DISPLAY_NAME[battle_fighter]} is down! Press Enter"
        ui_text(msg, (0, -0.44), scale=1.2, origin=(0, 0), color_=color.red)


def show_finish_screen():
    clear_ui()
    ui_text(f"{DISPLAY_NAME[active]} made it to the finish!", (0, 0.2), scale=2, origin=(0, 0), color_=color.lime)
    ui_text("Press Enter to continue", (0, 0), scale=1.4, origin=(0, 0))


def show_timeout_screen():
    clear_ui()
    ui_text(f"{DISPLAY_NAME[active]} ran out of time!", (0, 0.2), scale=2, origin=(0, 0), color_=color.orange)
    msg = "Game Over - press Enter" if pending_game_over else "Press Enter to continue"
    ui_text(msg, (0, 0), scale=1.4, origin=(0, 0))


def show_game_over_screen():
    clear_ui()
    ui_text("GAME OVER", (0, 0.3), scale=3, origin=(0, 0), color_=color.red)
    for i, c in enumerate(roster):
        ui_text(f"{DISPLAY_NAME[c]}: {wins[c]}W / {scores[c]}pt", (0, 0.1 - i * 0.08), scale=1.5, origin=(0, 0))
    ui_text("Press Enter to restart", (0, -0.3), scale=1.4, origin=(0, 0))


def set_state(new_state):
    global state
    state = new_state
    set_world_visible(new_state == STATE_OVERWORLD or new_state == STATE_READY)
    if new_state in (STATE_OVERWORLD, STATE_READY):
        update_camera(player_rig["root"].position, facing[active])
    if new_state == STATE_MENU:
        show_menu_screen()
    elif new_state == STATE_CHARACTER_SELECT:
        show_character_select_screen()
    elif new_state == STATE_READY:
        show_ready_screen()
    elif new_state == STATE_OVERWORLD:
        show_overworld_hud()
    elif new_state == STATE_BATTLE:
        enter_battle_arena()
        show_battle_screen()
    elif new_state == STATE_FINISH:
        show_finish_screen()
    elif new_state == STATE_TIMEOUT:
        show_timeout_screen()
    elif new_state == STATE_GAME_OVER:
        show_game_over_screen()

# =====================================================================
# ---- Input handling ----
# =====================================================================

def enemy_at(col, row):
    return next((e for e in enemies if e["col"] == col and e["row"] == row), None)


def remove_enemy(e):
    enemies.remove(e)
    destroy(e["rig"]["root"])
    destroy(e["ship"]["root"])


def toggle_form(target_form):
    global active_form
    old_max = effective_max_hp(active, active_form)
    active_form = "human" if active_form == target_form else target_form
    new_max = effective_max_hp(active, active_form)
    hp[active] = max(1, min(new_max, round(hp[active] * new_max / old_max)))
    apply_form_visuals(player_rig, active_form, active)
    for e in enemies:
        e["ship"]["root"].enabled = (active_form == "whale")
    ground_entity.color = WATER_COLOR if active_form == "whale" else GRASS_COLOR
    show_overworld_hud()


def advance_after_turn():
    """After a finish/timeout/defeat resolves: move to the next living
    racer's ready screen, or to game over if nobody's left."""
    global pending_game_over
    if pending_game_over:
        set_state(STATE_GAME_OVER)
        return
    next_char = pick_next_active(active, alive, roster)
    start_turn_for(next_char)
    set_state(STATE_READY)


def handle_key(key):
    global state, menu_selected_index, char_select_cursor, roster
    global active, active_form, move_cooldown_remaining
    global battle_phase, battle_fighter, battle_enemy_hp, battle_log, battle_enemy_ref
    global princess_trail, princess_trail_index, princess_shield_ready
    global pending_game_over

    if key == 'escape':
        application.quit()
        return

    if state == STATE_MENU:
        if key in ('up arrow', 'w'):
            menu_selected_index = (menu_selected_index - 1) % len(menu_options)
            show_menu_screen()
        elif key in ('down arrow', 's'):
            menu_selected_index = (menu_selected_index + 1) % len(menu_options)
            show_menu_screen()
        elif key in ('enter', 'space'):
            if menu_options[menu_selected_index] == "Start":
                set_state(STATE_CHARACTER_SELECT)
            else:
                application.quit()

    elif state == STATE_CHARACTER_SELECT:
        num_rows = len(CHARACTER_ORDER) + 1
        if key == 'up arrow':
            char_select_cursor = (char_select_cursor - 1) % num_rows
            show_character_select_screen()
        elif key == 'down arrow':
            char_select_cursor = (char_select_cursor + 1) % num_rows
            show_character_select_screen()
        elif key in ('enter', 'space'):
            if char_select_cursor < len(CHARACTER_ORDER):
                picked = CHARACTER_ORDER[char_select_cursor]
                char_selected[picked] = not char_selected[picked]
                show_character_select_screen()
            elif any(char_selected.values()):
                roster = [c for c in CHARACTER_ORDER if char_selected[c]]
                full_reset()
                set_state(STATE_READY)

    elif state == STATE_READY:
        if key in ('enter', 'space'):
            set_state(STATE_OVERWORLD)

    elif state == STATE_OVERWORLD:
        if key == 'd':
            toggle_form("dragon")
        elif key == 'w':
            toggle_form("whale")
        elif key == 'b':
            toggle_form("bird")
        elif key == 'r':
            toggle_form("werewolf")
        elif key == 'i':
            d_col, d_row = FACING_OFFSET[facing[active]]
            col, row = pos[active]
            struck = enemy_at(col + d_col, row + d_row)
            if struck is not None:
                remove_enemy(struck)
                scores[active] += SCORE_PER_KILL
        elif key in ('left arrow', 'right arrow', 'up arrow', 'down arrow'):
            if move_cooldown_remaining <= 0:
                d_col, d_row = {
                    'left arrow': (-1, 0), 'right arrow': (1, 0),
                    'up arrow': (0, -1), 'down arrow': (0, 1),
                }[key]
                cooldown = FORM_MOVE_COOLDOWN_MS.get(active_form, BASE_MOVE_COOLDOWN_MS)
                move_cooldown_remaining = cooldown
                facing[active] = direction_from_delta(d_col, d_row)
                cur_col, cur_row = pos[active]
                new_col, new_row = cur_col + d_col, cur_row + d_row

                blocker = enemy_at(new_col, new_row)
                if blocker is not None:
                    battle_fighter = active
                    battle_enemy_ref = blocker
                    battle_enemy_hp = ENEMY_MAX_HP
                    battle_phase = "choose"
                    battle_log = []
                    set_state(STATE_BATTLE)
                elif is_walkable(new_col, new_row, ignore_trees=active_form in FORM_IGNORES_TREES):
                    pos[active] = (new_col, new_row)
                    player_rig["root"].position = grid_to_world(new_col, new_row)

                    princess_trail.append((new_col, new_row))
                    if len(princess_trail) > 20:
                        princess_trail = princess_trail[-20:]
                    if princess_trail_index > 1:
                        princess_trail_index -= 1
                        if princess_trail_index <= 1:
                            princess_shield_ready = True

                    if (new_col, new_row) == current_finish:
                        wins[active] += 1
                        scores[active] += SCORE_PER_WIN
                        set_state(STATE_FINISH)
                    else:
                        show_overworld_hud()

    elif state == STATE_BATTLE:
        if battle_phase == "choose" and key in ('enter', 'space'):
            fighter_name = DISPLAY_NAME[battle_fighter]
            player_dmg = rng.randint(*PLAYER_ATK_RANGE)
            dealt_multiplier = FORM_DAMAGE_DEALT_MULTIPLIER.get(active_form, 1.0)
            player_dmg = max(1, round(player_dmg * dealt_multiplier))
            battle_enemy_hp -= player_dmg
            battle_log = [f"{fighter_name} hits the Dark Knight for {player_dmg}!"]

            if battle_enemy_hp <= 0:
                battle_enemy_hp = 0
                battle_phase = "victory"
                scores[battle_fighter] += SCORE_PER_KILL
            elif princess_shield_ready:
                princess_shield_ready = False
                princess_trail_index = SHIELD_CATCHUP_DISTANCE
                battle_log.append("The princess steps in and blocks the blow!")
            else:
                enemy_dmg = rng.randint(*ENEMY_ATK_RANGE)
                damage_multiplier = FORM_DAMAGE_TAKEN_MULTIPLIER.get(active_form)
                if damage_multiplier is not None:
                    enemy_dmg = max(1, round(enemy_dmg * damage_multiplier))
                hp[battle_fighter] = max(0, hp[battle_fighter] - enemy_dmg)
                battle_log.append(f"The Dark Knight hits {fighter_name} for {enemy_dmg}!")
                if hp[battle_fighter] <= 0:
                    battle_phase = "defeat"
                    alive[battle_fighter] = False
                    pending_game_over = not any(alive[c] for c in roster if c != battle_fighter)
            show_battle_screen()

        elif battle_phase == "victory" and key in ('enter', 'space'):
            remove_enemy(battle_enemy_ref)
            set_state(STATE_OVERWORLD)

        elif battle_phase == "defeat" and key in ('enter', 'space'):
            advance_after_turn()

    elif state == STATE_FINISH:
        if key in ('enter', 'space'):
            advance_after_turn()

    elif state == STATE_TIMEOUT:
        if key in ('enter', 'space'):
            advance_after_turn()

    elif state == STATE_GAME_OVER:
        if key in ('enter', 'space'):
            full_reset()
            set_state(STATE_READY)

# =====================================================================
# ---- Per-frame update ----
# =====================================================================
RESPAWN_DELAY_MS = 5000


def wander_enemy(e):
    col, row = e["col"], e["row"]
    candidates = []
    for d_col, d_row in FACING_OFFSET.values():
        nc, nr = col + d_col, row + d_row
        if is_walkable(nc, nr) and enemy_at(nc, nr) is None and (nc, nr) != pos.get(active):
            candidates.append((nc, nr))
    if candidates:
        nc, nr = rng.choice(candidates)
        e["col"], e["row"] = nc, nr
        e["rig"]["root"].position = grid_to_world(nc, nr)
        e["ship"]["root"].position = grid_to_world(nc, nr)


def game_update(dt):
    global move_cooldown_remaining, enemy_wander_remaining, respawn_remaining
    global intro_elapsed_ms, run_elapsed_ms, drain_ticks_applied
    global pending_game_over

    dt_ms = dt * 1000

    if state == STATE_INTRO:
        globals()["intro_elapsed_ms"] += dt_ms
        if intro_elapsed_ms >= INTRO_DURATION_MS:
            set_state(STATE_MENU)
        return

    if move_cooldown_remaining > 0:
        move_cooldown_remaining = max(0.0, move_cooldown_remaining - dt_ms)

    if state != STATE_OVERWORLD:
        return

    # ---- camera follow ----
    update_camera(player_rig["root"].position, facing[active])

    # ---- princess follow visual ----
    idx = max(0, len(princess_trail) - 1 - princess_trail_index)
    p_col, p_row = princess_trail[idx]
    princess_rig["root"].position = grid_to_world(p_col, p_row)

    # ---- enemy wandering ----
    if enemies:
        enemy_wander_remaining -= dt_ms
        if enemy_wander_remaining <= 0:
            enemy_wander_remaining = enemy_wander_speed_ms()
            for e in list(enemies):
                wander_enemy(e)
    else:
        if respawn_remaining is None:
            respawn_remaining = RESPAWN_DELAY_MS
        else:
            respawn_remaining -= dt_ms
            if respawn_remaining <= 0:
                spawn_enemies(current_run_enemy_count)
                respawn_remaining = None
        show_overworld_hud()

    # ---- run timer / HP drain ----
    run_elapsed_ms += dt_ms
    if run_elapsed_ms >= RUN_TIMER_GRACE_MS:
        elapsed_in_drain = run_elapsed_ms - RUN_TIMER_GRACE_MS
        ticks_due = int(elapsed_in_drain // HP_DRAIN_INTERVAL_MS) + 1
        while drain_ticks_applied < ticks_due:
            drain_ticks_applied += 1
            max_hp = effective_max_hp(active, active_form)
            drain_amount = max(1, round(max_hp * HP_DRAIN_PERCENT / 100))
            hp[active] = max(0, hp[active] - drain_amount)
            if hp[active] <= 0:
                alive[active] = False
                pending_game_over = not any(alive[c] for c in roster if c != active)
                set_state(STATE_TIMEOUT)
                return
    show_overworld_hud()


def input(key):
    handle_key(key)


def update():
    game_update(time.dt)


set_state(STATE_INTRO)
clear_ui()
ui_text("WONDERNIGHT 3D", (0, 0), scale=3, origin=(0, 0))

if __name__ == '__main__':
    app.run()

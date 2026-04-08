import pygame
import sys
import os
import random
from pygame.locals import *

# usage: python3 module1_candycrush.py

# ------------------ SET WORKING DIRECTORY ------------------ #
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("Running from:", os.getcwd())

# ------------------ PARAMETERS ------------------ #
WINDOWWIDTH = 1320
WINDOWHEIGHT = 800
GAMEWIDTH = 600
GAMEHEIGHT = 600
SPACESIZE = 100
FPS = 60
TEXTCOLOR1 = (129, 115, 92)
TEXTCOLOR2 = (255, 255, 255)

rows, cols = GAMEHEIGHT // SPACESIZE, GAMEWIDTH // SPACESIZE
pop_sprites = []

# ------------------ UI LAYOUT ------------------ #
BOARD_OFFSET_X = 400
BOARD_OFFSET_Y = 100
PREVIEW_PANEL = pygame.Rect(995, 60, 295, 410)
PREVIEW_IMAGE_BOX = pygame.Rect(1020, 130, 245, 245)
PREVIEW_TEXT_Y = 395

# ------------------ UI: RESHUFFLE + LEVELS ------------------ #
RESHUFFLE_BTN_RECT = pygame.Rect(90, 640, 210, 55)
large_tile_cache = {}
LEVEL_MATCH_TARGET = 10

# ------------------ IMAGE TILE LOADING ------------------ #
IMAGE_TILE_FOLDER = "game_images_lipids"

LIPID_CLASSES = [
    "Fatty Acid",
    "Glycerolipid",
    "Glycerophospholipid",
    "Polyketide",
    "Prenol",
    "Saccharolipid",
    "Sphingolipid",
    "Sterol",
]

CLASS_FOLDER_MAP = {
    "Fatty Acid": "fattyacyls",
    "Glycerolipid": "glycerolipids",
    "Glycerophospholipid": "glycerophospholipids",
    "Polyketide": "polyketides",
    "Prenol": "prenols",
    "Saccharolipid": "sachharolipids",  # keep if your folder is actually spelled this way
    "Sphingolipid": "sphingolipids",
    "Sterol": "sterols",
}

COLORS = [
    (251, 180, 174),
    (179, 205, 227),
    (204, 235, 197),
    (222, 203, 228),
    (254, 217, 166),
    (255, 255, 204),
    (229, 216, 189),
    (253, 218, 236),
]
PLAIN_TILE_COLOR = (245, 245, 245)

POWER_NONE = None
POWER_ROW = "ROW"
POWER_COL = "COL"
POWER_BOMB = "BOMB"

# ------------------ INITIALIZE PYGAME ------------------ #
pygame.init()
mainClock = pygame.time.Clock()
windowSurface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), 0, 32)
pygame.display.set_caption("Lipid Crush")

font = pygame.font.Font("fonts/GravitasOne.ttf", 36)
stepfont = pygame.font.Font("fonts/GravitasOne.ttf", 66)
scorefont = pygame.font.Font("fonts/GravitasOne.ttf", 50)
resultfont = pygame.font.Font("fonts/GravitasOne.ttf", 60)
tinyfont = pygame.font.Font("fonts/GravitasOne.ttf", 18)

# ------------------ LOAD UI IMAGES ------------------ #
background_img = pygame.image.load("image/background.png").convert()
background_img = pygame.transform.scale(background_img, (WINDOWWIDTH, WINDOWHEIGHT))

gameboard_img = pygame.image.load("image/gameboard.png").convert_alpha()
gameboard_img = pygame.transform.scale(gameboard_img, (620, 620))

scorebar_img = pygame.image.load("image/scorebar.png").convert_alpha()
scorebar_img = pygame.transform.scale(scorebar_img, (210, 620))

gameover_img = pygame.image.load("image/gameover.png").convert_alpha()
gameover_img = pygame.transform.scale(gameover_img, (WINDOWWIDTH, WINDOWHEIGHT))

# ------------------ POWER ICONS ------------------ #
POWER_IMAGES = {}

def _placeholder_icon(kind, size=(72, 72)):
    s = pygame.Surface(size, pygame.SRCALPHA)
    cx, cy = size[0] // 2, size[1] // 2
    pygame.draw.circle(s, (255, 255, 255), (cx, cy), min(cx, cy) - 3)
    pygame.draw.circle(s, (90, 70, 50), (cx, cy), min(cx, cy) - 5, 4)

    if kind == POWER_ROW:
        pygame.draw.line(s, (90, 70, 50), (12, cy), (size[0] - 12, cy), 8)
    elif kind == POWER_COL:
        pygame.draw.line(s, (90, 70, 50), (cx, 12), (cx, size[1] - 12), 8)
    elif kind == POWER_BOMB:
        pygame.draw.circle(s, (90, 70, 50), (cx, cy), 10)

    return s

def load_power_icons(tile_icon_size=(72, 72)):
    paths = {
        POWER_ROW: "image/enzyme_row.png",
        POWER_COL: "image/enzyme_col.png",
        POWER_BOMB: "image/micelle.png",
    }

    for pwr, path in paths.items():
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, tile_icon_size)
            POWER_IMAGES[pwr] = img
        except Exception:
            POWER_IMAGES[pwr] = _placeholder_icon(pwr, tile_icon_size)

load_power_icons()

# ------------------ TILE IMAGE LOADING ------------------ #
def crop_center_molecule_area(img):
    """
    These card images contain title text at the top and lots of whitespace.
    We crop into the main center/lower-center area where the molecule usually is.
    """
    w, h = img.get_size()

    # Tuned crop box for your screenshot/card layout:
    # remove most top text, keep central molecule area
    left = int(w * 0.12)
    top = int(h * 0.22)
    right = int(w * 0.88)
    bottom = int(h * 0.86)

    crop_w = max(1, right - left)
    crop_h = max(1, bottom - top)

    cropped = img.subsurface((left, top, crop_w, crop_h)).copy()
    return cropped

def make_board_tile_from_crop(img, size=(96, 96)):
    ow, oh = img.get_size()
    tw, th = size

    # fill tile
    scale_ratio = max(tw / ow, th / oh)
    nw = max(1, int(ow * scale_ratio))
    nh = max(1, int(oh * scale_ratio))

    if nw < ow or nh < oh:
        scaled = pygame.transform.smoothscale(img, (nw, nh))
    else:
        scaled = pygame.transform.scale(img, (nw, nh))

    x = max(0, (nw - tw) // 2)
    y = max(0, (nh - th) // 2)
    tile = scaled.subsurface((x, y, tw, th)).copy()
    return tile

def load_tile_image(filepath, size=(96, 96)):
    try:
        full_img = pygame.image.load(filepath).convert_alpha()

        bbox = full_img.get_bounding_rect()
        if bbox.width > 0 and bbox.height > 0:
            full_img = full_img.subsurface(bbox).copy()

        cropped_focus = crop_center_molecule_area(full_img)
        board_tile = make_board_tile_from_crop(cropped_focus, size=size)

        return board_tile, full_img

    except Exception as e:
        print(f"Could not load image: {filepath} -> {e}")
        fallback = pygame.Surface(size, pygame.SRCALPHA)
        fallback.fill((200, 200, 200))
        return fallback, fallback.copy()

def load_lipid_tiles_from_folders():
    lipids = []
    tile_to_class = {}
    tile_to_full = {}

    for idx, lipid_class in enumerate(LIPID_CLASSES):
        folder_name = CLASS_FOLDER_MAP[lipid_class]
        folder_path = os.path.join(IMAGE_TILE_FOLDER, folder_name)

        if not os.path.exists(folder_path):
            print(f"Folder not found: {folder_path}")
            continue

        png_files = sorted(
            f for f in os.listdir(folder_path)
            if f.lower().endswith(".png")
        )

        print(f"Loading {len(png_files)} images from {folder_path}")

        for fname in png_files:
            full_path = os.path.join(folder_path, fname)
            tile_img, original_img = load_tile_image(full_path, size=(96, 96))
            lipids.append(tile_img)
            tile_to_class[tile_img] = idx
            tile_to_full[tile_img] = original_img

    if len(lipids) == 0:
        raise RuntimeError(
            "No PNG images were loaded from game_images_lipids. "
            "Check that the folder names and file paths are correct."
        )

    return lipids, tile_to_class, tile_to_full

# ------------------ LIPID TILES ------------------ #
lipids, tile_to_class, tile_to_full = load_lipid_tiles_from_folders()

lipid_none = pygame.Surface((96, 96), pygame.SRCALPHA)
lipid_none.fill((200, 200, 200))
tile_to_class[lipid_none] = None
tile_to_full[lipid_none] = lipid_none.copy()

# ------------------ BASIC HELPERS ------------------ #
def terminate():
    pygame.quit()
    sys.exit()

def draw_text(text, font_obj, surface, x, y, color):
    textobj = font_obj.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)

def draw_text_wrapped(text, font_obj, surface, rect, color):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + (" " if current else "") + word
        if font_obj.size(test)[0] <= rect.width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    y = rect.top
    for line in lines:
        textobj = font_obj.render(line, True, color)
        textrect = textobj.get_rect(centerx=rect.centerx, top=y)
        surface.blit(textobj, textrect)
        y += font_obj.get_linesize()

def draw_image(img, surface, x, y):
    if img is not None:
        img_rect = img.get_rect(center=(x, y))
        surface.blit(img, img_rect)

def cell_center(row, col):
    x = col * SPACESIZE + SPACESIZE / 2 + BOARD_OFFSET_X
    y = row * SPACESIZE + SPACESIZE / 2 + BOARD_OFFSET_Y
    return x, y

def get_cell_from_mouse(pos):
    x, y = pos
    row = (y - BOARD_OFFSET_Y) // SPACESIZE
    col = (x - BOARD_OFFSET_X) // SPACESIZE
    return int(row), int(col)

def in_bounds(r, c):
    return 0 <= r < rows and 0 <= c < cols

def are_nextdoor(a, b):
    r1, c1 = a
    r2, c2 = b
    return abs(r1 - r2) + abs(c1 - c2) == 1

# ------------------ UI: RESHUFFLE ------------------ #
def draw_reshuffle_button(surface, enabled=True):
    bg = (255, 255, 255) if enabled else (235, 235, 235)
    border = (120, 100, 80) if enabled else (170, 170, 170)
    textc = TEXTCOLOR1 if enabled else (170, 170, 170)
    pygame.draw.rect(surface, bg, RESHUFFLE_BTN_RECT, border_radius=14)
    pygame.draw.rect(surface, border, RESHUFFLE_BTN_RECT, 3, border_radius=14)
    draw_text("Reshuffle", tinyfont, surface, RESHUFFLE_BTN_RECT.centerx, RESHUFFLE_BTN_RECT.centery, textc)

def make_cell(tile):
    cidx = tile_to_class.get(tile)
    return {"tile": tile, "class": cidx, "power": POWER_NONE}

def random_cell():
    return make_cell(random.choice(lipids))

def initiate_gameboard():
    board = [[None for _ in range(cols)] for _ in range(rows)]

    for i in range(rows):
        for j in range(cols):
            tries = 0
            while True:
                tries += 1
                cell = random_cell()
                c = cell["class"]

                if j >= 2 and board[i][j - 1] and board[i][j - 2]:
                    if board[i][j - 1]["class"] == board[i][j - 2]["class"] == c:
                        if tries < 50:
                            continue

                if i >= 2 and board[i - 1][j] and board[i - 2][j]:
                    if board[i - 1][j]["class"] == board[i - 2][j]["class"] == c:
                        if tries < 50:
                            continue

                board[i][j] = cell
                break

    return board

def find_match_runs(board):
    runs = []

    for r in range(rows):
        start = 0
        while start < cols:
            if board[r][start] is None or board[r][start]["class"] is None:
                start += 1
                continue

            cidx = board[r][start]["class"]
            end = start + 1
            while end < cols and board[r][end] is not None and board[r][end]["class"] == cidx:
                end += 1

            if end - start >= 3:
                runs.append({
                    "cells": [(r, c) for c in range(start, end)],
                    "dir": "H",
                    "class": cidx
                })
            start = end

    for c in range(cols):
        start = 0
        while start < rows:
            if board[start][c] is None or board[start][c]["class"] is None:
                start += 1
                continue

            cidx = board[start][c]["class"]
            end = start + 1
            while end < rows and board[end][c] is not None and board[end][c]["class"] == cidx:
                end += 1

            if end - start >= 3:
                runs.append({
                    "cells": [(r, c) for r in range(start, end)],
                    "dir": "V",
                    "class": cidx
                })
            start = end

    return runs

def shuffle_board(board, max_tries=120):
    for r in range(rows):
        for c in range(cols):
            if board[r][c] is None:
                board[r][c] = random_cell()

    cells = [board[r][c] for r in range(rows) for c in range(cols)]

    for _ in range(max_tries):
        random.shuffle(cells)
        k = 0
        for r in range(rows):
            for c in range(cols):
                board[r][c] = cells[k]
                k += 1

        if not find_match_runs(board):
            return True

    return False

# ------------------ DRAW TILE / BOARD ------------------ #
def draw_tile(cell, surface, x, y, color_enabled=True):
    if cell is None:
        tile = lipid_none
        cidx = None
        power = None
    else:
        tile = cell["tile"]
        cidx = cell["class"]
        power = cell["power"]

    rect = pygame.Rect(x - SPACESIZE // 2, y - SPACESIZE // 2, SPACESIZE, SPACESIZE)

    if color_enabled and cidx is not None:
        color = COLORS[cidx % len(COLORS)]
        pygame.draw.rect(surface, color, rect, border_radius=12)
    else:
        pygame.draw.rect(surface, PLAIN_TILE_COLOR, rect, border_radius=12)

    if power is None:
        img_rect = tile.get_rect(center=(x, y))
        surface.blit(tile, img_rect)
    else:
        icon = POWER_IMAGES.get(power)
        if icon is None:
            icon = _placeholder_icon(power, (72, 72))
        icon_rect = icon.get_rect(center=(x, y))
        surface.blit(icon, icon_rect)

def draw_gameboard(board, color_enabled=True):
    for i in range(rows):
        for j in range(cols):
            x, y = cell_center(i, j)
            draw_tile(board[i][j], windowSurface, x, y, color_enabled=color_enabled)

    for (row, col, t) in pop_sprites:
        x, y = cell_center(row, col)
        rr = int(10 + 40 * (1 - t))
        pygame.draw.circle(windowSurface, (255, 255, 255), (int(x), int(y)), rr, 3)

def draw_board_with_offsets(board, moving_tiles=None, color_enabled=True):
    moved_positions = set()

    if moving_tiles:
        for item in moving_tiles:
            moved_positions.add(item["from"])
            moved_positions.add(item["to"])

    for r in range(rows):
        for c in range(cols):
            if (r, c) in moved_positions:
                continue
            x, y = cell_center(r, c)
            draw_tile(board[r][c], windowSurface, x, y, color_enabled=color_enabled)

    if moving_tiles:
        for item in moving_tiles:
            draw_tile(item["cell"], windowSurface, item["x"], item["y"], color_enabled=color_enabled)

    for (row, col, t) in pop_sprites:
        x, y = cell_center(row, col)
        rr = int(10 + 40 * (1 - t))
        pygame.draw.circle(windowSurface, (255, 255, 255), (int(x), int(y)), rr, 3)

# ------------------ HOVER INFO + SIDE PREVIEW ------------------ #
def get_hovered_preview_cell(board, enabled=True):
    if not enabled:
        return None

    mx, my = pygame.mouse.get_pos()
    r, c = get_cell_from_mouse((mx, my))

    if not in_bounds(r, c):
        return None

    cell = board[r][c]
    if cell is None or cell["class"] is None:
        return None
    if cell.get("power") is not None:
        return None

    return cell

def draw_side_preview(cell):
    pygame.draw.rect(windowSurface, (255, 255, 255), PREVIEW_PANEL, border_radius=18)
    pygame.draw.rect(windowSurface, (120, 100, 80), PREVIEW_PANEL, 2, border_radius=18)

    draw_text("Preview", tinyfont, windowSurface, PREVIEW_PANEL.centerx, PREVIEW_PANEL.top + 22, TEXTCOLOR1)

    inner = PREVIEW_IMAGE_BOX
    pygame.draw.rect(windowSurface, (248, 248, 248), inner, border_radius=14)
    pygame.draw.rect(windowSurface, (220, 220, 220), inner, 1, border_radius=14)

    if cell is None:
        draw_text("Hover a tile", tinyfont, windowSurface, inner.centerx, inner.centery, TEXTCOLOR1)
        return

    tile = cell["tile"]
    full_img = tile_to_full.get(tile, tile)

    preview_key = (id(full_img), inner.width - 10, inner.height - 10)
    if preview_key not in large_tile_cache:
        ow, oh = full_img.get_size()
        max_w = inner.width - 10
        max_h = inner.height - 10

        scale_ratio = min(max_w / ow, max_h / oh)
        new_w = max(1, int(ow * scale_ratio))
        new_h = max(1, int(oh * scale_ratio))

        big = pygame.transform.smoothscale(full_img, (new_w, new_h))
        large_tile_cache[preview_key] = big

    big = large_tile_cache[preview_key]

    bx = inner.left + (inner.width - big.get_width()) // 2
    by = inner.top + (inner.height - big.get_height()) // 2
    windowSurface.blit(big, (bx, by))

    lipid_name = LIPID_CLASSES[cell["class"]]
    name_rect = pygame.Rect(PREVIEW_PANEL.left + 10, PREVIEW_TEXT_Y, PREVIEW_PANEL.width - 20, 60)
    draw_text_wrapped(lipid_name, tinyfont, windowSurface, name_rect, TEXTCOLOR1)

# ------------------ HUD ------------------ #
def draw_hud(level, matches_in_level, moves_left, score, combo, hover_hint=""):
    draw_image(background_img, windowSurface, WINDOWWIDTH // 2, WINDOWHEIGHT // 2)
    draw_image(gameboard_img, windowSurface, 700, 400)
    draw_image(scorebar_img, windowSurface, 195, 400)

    draw_text(f"Level {level}", tinyfont, windowSurface, 195, 35, TEXTCOLOR1)
    draw_text(f"Matches: {matches_in_level}/{LEVEL_MATCH_TARGET}", tinyfont, windowSurface, 195, 65, TEXTCOLOR1)

    if hover_hint:
        draw_text(hover_hint, tinyfont, windowSurface, 195, 95, TEXTCOLOR1)

    draw_text("Moves", font, windowSurface, 195, 120, TEXTCOLOR1)
    draw_text("Score", font, windowSurface, 195, 355, TEXTCOLOR1)

    draw_text(str(moves_left), stepfont, windowSurface, 195, 180, TEXTCOLOR1)
    draw_text(str(score), scorefont, windowSurface, 195, 415, TEXTCOLOR1)

    draw_text(f"Combo x{combo}", tinyfont, windowSurface, 195, 510, TEXTCOLOR1)

# ------------------ START + END SCREENS ------------------ #
def start_screen():
    draw_image(background_img, windowSurface, WINDOWWIDTH // 2, WINDOWHEIGHT // 2)
    draw_text("Welcome to Lipid Crush!", font, windowSurface,
              windowSurface.get_rect().centerx,
              windowSurface.get_rect().centery - 50, TEXTCOLOR1)
    draw_text("Press ENTER to start.", font, windowSurface,
              windowSurface.get_rect().centerx,
              windowSurface.get_rect().centery, TEXTCOLOR1)
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                elif event.key == K_RETURN:
                    return

def wait_for_enter():
    while True:
        for e in pygame.event.get():
            if e.type == QUIT:
                terminate()
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    terminate()
                elif e.key == K_RETURN:
                    return

# ------------------ POP EFFECTS ------------------ #
def update_pop_effects():
    for i in range(len(pop_sprites) - 1, -1, -1):
        r, c, t = pop_sprites[i]
        t -= 0.08
        if t <= 0:
            pop_sprites.pop(i)
        else:
            pop_sprites[i] = (r, c, t)

# ------------------ SIMPLE GRAVITY/REFILL ------------------ #
def gravity_simple(board):
    moved = True
    while moved:
        moved = False
        for c in range(cols):
            for r in range(rows - 2, -1, -1):
                if board[r][c] is not None and board[r + 1][c] is None:
                    board[r + 1][c] = board[r][c]
                    board[r][c] = None
                    moved = True

def refill_simple(board):
    for c in range(cols):
        for r in range(rows):
            if board[r][c] is None:
                board[r][c] = random_cell()

# ------------------ POWER ACTIVATION ------------------ #
def _bomb_area(center):
    r0, c0 = center
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r0 + dr, c0 + dc
            if in_bounds(rr, cc):
                out.append((rr, cc))
    return out

def _expand_with_powers(board, initial_cells):
    to_process = list(initial_cells)
    cleared = set(initial_cells)
    processed_power = set()

    while to_process:
        r, c = to_process.pop()
        cell = board[r][c]
        if cell is None:
            continue

        power = cell.get("power")
        if power is None:
            continue

        if (r, c) in processed_power:
            continue
        processed_power.add((r, c))

        if power == POWER_ROW:
            for cc in range(cols):
                if (r, cc) not in cleared:
                    cleared.add((r, cc))
                    to_process.append((r, cc))
        elif power == POWER_COL:
            for rr in range(rows):
                if (rr, c) not in cleared:
                    cleared.add((rr, c))
                    to_process.append((rr, c))
        elif power == POWER_BOMB:
            for (rr, cc) in _bomb_area((r, c)):
                if (rr, cc) not in cleared:
                    cleared.add((rr, cc))
                    to_process.append((rr, cc))

    return cleared

def clear_runs_with_powers(board, runs, keep_positions=None):
    if keep_positions is None:
        keep_positions = set()

    base_cleared = set()
    for run in runs:
        for (r, c) in run["cells"]:
            if (r, c) not in keep_positions:
                base_cleared.add((r, c))

    all_cleared = _expand_with_powers(board, base_cleared)

    for (r, c) in all_cleared:
        pop_sprites.append((r, c, 1.0))
        board[r][c] = None

    return len(all_cleared)

# ------------------ STREAK-BASED SPECIAL CREATION ------------------ #
def _run_contains(run, pos):
    return pos in run["cells"]

def _pick_run_for_special(runs, prefer_a, prefer_b, required_class=None):
    preferred = []
    for run in runs:
        if required_class is not None and run["class"] != required_class:
            continue
        if prefer_a is not None and _run_contains(run, prefer_a):
            preferred.append(run)
        elif prefer_b is not None and _run_contains(run, prefer_b):
            preferred.append(run)

    if preferred:
        preferred.sort(key=lambda r: len(r["cells"]), reverse=True)
        return preferred[0]

    candidates = [r for r in runs if required_class is None or r["class"] == required_class]
    if not candidates:
        return None

    candidates.sort(key=lambda r: len(r["cells"]), reverse=True)
    return candidates[0]

def _choose_pos_in_run(run, prefer_a, prefer_b):
    cells = run["cells"]
    s = set(cells)
    if prefer_a in s:
        return prefer_a
    if prefer_b in s:
        return prefer_b
    return cells[len(cells) // 2]

def _make_special_from_sameclass_streak(board, runs, prefer_a, prefer_b, streak_value, required_class):
    if not runs:
        return set()

    run = _pick_run_for_special(runs, prefer_a, prefer_b, required_class=required_class)
    if run is None:
        return set()

    r, c = _choose_pos_in_run(run, prefer_a, prefer_b)
    if not in_bounds(r, c) or board[r][c] is None:
        return set()

    if streak_value == 3:
        board[r][c]["power"] = POWER_ROW if run["dir"] == "H" else POWER_COL
        return {(r, c)}

    if streak_value == 4:
        board[r][c]["power"] = POWER_BOMB
        return {(r, c)}

    return set()

def class_for_streak(runs, start_cell, end_cell):
    candidates = []
    for run in runs:
        s = set(run["cells"])
        if start_cell in s or end_cell in s:
            candidates.append(run)

    if not candidates:
        candidates = runs[:]

    candidates.sort(key=lambda r: len(r["cells"]), reverse=True)
    return candidates[0]["class"] if candidates else None

# ------------------ LEVEL FLAGS ------------------ #
def level_flags(level):
    if level == 1:
        return True, "ON"
    if level == 2:
        return False, "OPTIONAL"
    return False, "OFF"

# ------------------ ANIMATION ------------------ #
def draw_full_scene(board, level, matches_in_level, moves_left, score, combo, hover_hint,
                    color_enabled, hover_enabled, moving_tiles=None):
    draw_hud(level, matches_in_level, moves_left, score, combo, hover_hint=hover_hint)
    draw_board_with_offsets(board, moving_tiles=moving_tiles, color_enabled=color_enabled)
    draw_reshuffle_button(windowSurface, enabled=True)
    hovered = get_hovered_preview_cell(board, enabled=hover_enabled)
    draw_side_preview(hovered)
    pygame.display.flip()

def animate_swap(board, pos1, pos2, cell1, cell2,
                 level, matches_in_level, moves_left, score, combo, hover_hint,
                 color_enabled=True, hover_enabled=True, bounce=False):
    x1_start, y1_start = cell_center(*pos1)
    x2_start, y2_start = cell_center(*pos2)
    x1_end, y1_end = cell_center(*pos2)
    x2_end, y2_end = cell_center(*pos1)

    frames = 9

    for frame in range(1, frames + 1):
        t = frame / frames
        ease = t * t * (3 - 2 * t)

        x1 = x1_start + (x1_end - x1_start) * ease
        y1 = y1_start + (y1_end - y1_start) * ease
        x2 = x2_start + (x2_end - x2_start) * ease
        y2 = y2_start + (y2_end - y2_start) * ease

        if bounce:
            extra = 8 * (1 - abs(2 * t - 1))
            if pos1[0] == pos2[0]:
                x1 += extra if pos2[1] > pos1[1] else -extra
                x2 += extra if pos1[1] > pos2[1] else -extra
            else:
                y1 += extra if pos2[0] > pos1[0] else -extra
                y2 += extra if pos1[0] > pos2[0] else -extra

        draw_full_scene(
            board, level, matches_in_level, moves_left, score, combo, hover_hint,
            color_enabled, hover_enabled,
            moving_tiles=[
                {"cell": cell1, "from": pos1, "to": pos2, "x": x1, "y": y1},
                {"cell": cell2, "from": pos2, "to": pos1, "x": x2, "y": y2},
            ]
        )
        mainClock.tick(FPS)

# ------------------ RUN ------------------ #
start_screen()

while True:
    board = initiate_gameboard()

    moves_left = 45
    score = 0
    combo = 1

    level = 1
    matches_in_level = 0
    hover_enabled = True

    start_cell = None
    gameover = False

    same_class_streak = 0
    last_matched_class = None

    while not gameover:
        color_enabled, hover_mode = level_flags(level)

        hover_hint = ""
        if hover_mode == "ON":
            hover_enabled = True
        elif hover_mode == "OFF":
            hover_enabled = False
        else:
            hover_hint = f"Hover: {'ON' if hover_enabled else 'OFF'} (press H)"

        draw_hud(level, matches_in_level, moves_left, score, combo, hover_hint=hover_hint)
        draw_gameboard(board, color_enabled=color_enabled)
        draw_reshuffle_button(windowSurface, enabled=True)
        hovered = get_hovered_preview_cell(board, enabled=hover_enabled)
        draw_side_preview(hovered)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                if event.key == K_h and hover_mode == "OPTIONAL":
                    hover_enabled = not hover_enabled

            elif event.type == MOUSEBUTTONDOWN:
                if RESHUFFLE_BTN_RECT.collidepoint(event.pos):
                    shuffle_board(board)
                    start_cell = None
                    same_class_streak = 0
                    last_matched_class = None
                    continue
                start_cell = get_cell_from_mouse(event.pos)

            elif event.type == MOUSEBUTTONUP:
                if not start_cell:
                    continue

                end_cell = get_cell_from_mouse(event.pos)

                if in_bounds(*start_cell) and in_bounds(*end_cell) and are_nextdoor(start_cell, end_cell):
                    r1, c1 = start_cell
                    r2, c2 = end_cell

                    cell1 = board[r1][c1]
                    cell2 = board[r2][c2]

                    animate_swap(
                        board, (r1, c1), (r2, c2), cell1, cell2,
                        level, matches_in_level, moves_left, score, combo, hover_hint,
                        color_enabled=color_enabled, hover_enabled=hover_enabled, bounce=False
                    )

                    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]

                    runs_after_swap = find_match_runs(board)
                    if runs_after_swap:
                        moves_left -= 1
                        matches_in_level += 1

                        this_class = class_for_streak(runs_after_swap, start_cell, end_cell)

                        if this_class is not None and this_class == last_matched_class:
                            same_class_streak += 1
                        else:
                            same_class_streak = 1
                            last_matched_class = this_class

                        streak_special = None
                        if same_class_streak == 3:
                            streak_special = 3
                        elif same_class_streak == 4:
                            streak_special = 4

                        keep_positions = set()
                        if streak_special is not None and last_matched_class is not None:
                            keep_positions = _make_special_from_sameclass_streak(
                                board,
                                runs=runs_after_swap,
                                prefer_a=start_cell,
                                prefer_b=end_cell,
                                streak_value=streak_special,
                                required_class=last_matched_class
                            )

                        combo = 1
                        first_clear = True

                        while True:
                            runs = find_match_runs(board)
                            if not runs:
                                break

                            kp = keep_positions if first_clear else set()
                            first_clear = False

                            cleared = clear_runs_with_powers(board, runs, keep_positions=kp)
                            score += cleared * combo

                            gravity_simple(board)
                            refill_simple(board)
                            combo = min(combo + 1, 6)

                        if same_class_streak >= 4:
                            same_class_streak = 0
                            last_matched_class = None

                        if matches_in_level >= LEVEL_MATCH_TARGET:
                            level += 1
                            matches_in_level = 0

                            if level > 3:
                                draw_image(gameover_img, windowSurface, WINDOWWIDTH // 2, WINDOWHEIGHT // 2)
                                draw_text("YOU WIN!", resultfont, windowSurface,
                                          windowSurface.get_rect().centerx,
                                          windowSurface.get_rect().centery - 40, TEXTCOLOR1)
                                draw_text("Press ENTER to play again", font, windowSurface,
                                          windowSurface.get_rect().centerx,
                                          windowSurface.get_rect().centery + 110, TEXTCOLOR2)
                                pygame.display.flip()
                                wait_for_enter()
                                gameover = True
                                break

                            board = initiate_gameboard()
                            _, hm = level_flags(level)
                            hover_enabled = (hm != "OFF")

                            same_class_streak = 0
                            last_matched_class = None

                    else:
                        animate_swap(
                            board, (r2, c2), (r1, c1), board[r2][c2], board[r1][c1],
                            level, matches_in_level, moves_left, score, combo, hover_hint,
                            color_enabled=color_enabled, hover_enabled=hover_enabled, bounce=True
                        )

                        board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
                        same_class_streak = 0
                        last_matched_class = None

                start_cell = None

        update_pop_effects()

        if moves_left <= 0 and not gameover:
            draw_image(gameover_img, windowSurface, WINDOWWIDTH // 2, WINDOWHEIGHT // 2)
            draw_text("YOU LOSE!", resultfont, windowSurface,
                      windowSurface.get_rect().centerx,
                      windowSurface.get_rect().centery - 40, TEXTCOLOR1)
            draw_text("Press ENTER to play again", font, windowSurface,
                      windowSurface.get_rect().centerx,
                      windowSurface.get_rect().centery + 110, TEXTCOLOR2)
            pygame.display.flip()
            wait_for_enter()
            gameover = True

        mainClock.tick(FPS)
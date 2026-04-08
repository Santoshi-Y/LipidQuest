import math
import random
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pygame


# ============================================================
# LipidQuest Mini Game #2: Build the Plate
# Standalone pygame implementation
# ============================================================
# Controls:
# - Click a food on the conveyor to break it into lipid tiles
# - Drag lipid tiles into one of three bins:
#       Energy Storage
#       Essential & Structural
#       Limit Intake
# - Build 3 balanced meals to win
#
# Educational goals built into mechanics:
# - Different foods generate different lipid compositions
# - Saturated, unsaturated, trans fats, cholesterol, omega-3, omega-6
# - Membrane Fluidity, Inflammation, and Energy Reserve change live
# - Balance matters more than simply removing all fats
# ============================================================

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1400, 900
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LipidQuest - Mini Game #2: Build the Plate")
CLOCK = pygame.time.Clock()
FPS = 60

# ------------------------------------------------------------
# Colors
# ------------------------------------------------------------
BG = (14, 18, 28)
PANEL = (24, 30, 44)
PANEL_2 = (32, 40, 58)
WHITE = (245, 247, 252)
SOFT = (200, 210, 230)
MUTED = (145, 160, 185)
BLACK = (12, 12, 12)
GREEN = (94, 201, 117)
RED = (224, 86, 86)
YELLOW = (244, 201, 94)
BLUE = (86, 164, 236)
CYAN = (82, 218, 214)
PURPLE = (177, 111, 255)
ORANGE = (245, 153, 66)
PINK = (244, 113, 161)
TEAL = (64, 195, 158)
GOLD = (236, 198, 74)
GRAY = (95, 105, 125)
DANGER = (255, 80, 80)
SUCCESS = (120, 230, 160)

# ------------------------------------------------------------
# Fonts
# ------------------------------------------------------------
TITLE_FONT = pygame.font.SysFont("arial", 34, bold=True)
HEADER_FONT = pygame.font.SysFont("arial", 26, bold=True)
BODY_FONT = pygame.font.SysFont("arial", 20)
SMALL_FONT = pygame.font.SysFont("arial", 16)
TINY_FONT = pygame.font.SysFont("arial", 14)
BIG_FONT = pygame.font.SysFont("arial", 48, bold=True)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def draw_text(
    surf: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Tuple[int, int, int],
    pos: Tuple[int, int],
    center: bool = False,
) -> pygame.Rect:
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surf.blit(img, rect)
    return rect


def draw_rounded_panel(surf: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], border: Tuple[int, int, int] = (60, 70, 95), radius: int = 18, border_width: int = 2) -> None:
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    pygame.draw.rect(surf, border, rect, width=border_width, border_radius=radius)


def lerp_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = clamp(t, 0.0, 1.0)
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# ------------------------------------------------------------
# Data models
# ------------------------------------------------------------
@dataclass
class LipidInfo:
    name: str
    short: str
    color: Tuple[int, int, int]
    ideal_zone: str
    fluidity: float
    inflammation: float
    energy: float
    description: str


LIPID_DATA: Dict[str, LipidInfo] = {
    "saturated": LipidInfo(
        name="Saturated Fat",
        short="SAT",
        color=(242, 153, 74),
        ideal_zone="energy",
        fluidity=-4,
        inflammation=2,
        energy=8,
        description="Useful for energy, but too much can make membranes more rigid.",
    ),
    "unsaturated": LipidInfo(
        name="Unsaturated Fat",
        short="UNSAT",
        color=(82, 196, 179),
        ideal_zone="essential",
        fluidity=6,
        inflammation=-1,
        energy=5,
        description="Supports more flexible membranes and helps maintain balance.",
    ),
    "trans": LipidInfo(
        name="Trans Fat",
        short="TRANS",
        color=(230, 87, 87),
        ideal_zone="limit",
        fluidity=-8,
        inflammation=8,
        energy=6,
        description="Raises inflammation and reduces membrane fluidity.",
    ),
    "omega3": LipidInfo(
        name="Omega-3",
        short="O3",
        color=(92, 157, 255),
        ideal_zone="essential",
        fluidity=9,
        inflammation=-6,
        energy=4,
        description="Improves membrane fluidity and lowers inflammation.",
    ),
    "omega6": LipidInfo(
        name="Omega-6",
        short="O6",
        color=(166, 119, 255),
        ideal_zone="essential",
        fluidity=4,
        inflammation=1,
        energy=4,
        description="Important structurally, but balance with omega-3 matters.",
    ),
    "cholesterol": LipidInfo(
        name="Cholesterol",
        short="CHOL",
        color=(240, 215, 92),
        ideal_zone="essential",
        fluidity=0,
        inflammation=0,
        energy=0,
        description="Structurally important in moderation, but excess can be harmful.",
    ),
}


FOOD_COMPOSITION: Dict[str, Dict[str, int]] = {
    "Olive Oil": {"unsaturated": 3, "omega6": 1},
    "Butter": {"saturated": 3, "cholesterol": 1},
    "Salmon": {"omega3": 3, "unsaturated": 1, "cholesterol": 1},
    "Avocado": {"unsaturated": 3, "omega6": 1},
    "Nuts": {"unsaturated": 2, "omega6": 2},
    "Cheese": {"saturated": 2, "cholesterol": 1},
    "Bacon": {"saturated": 2, "unsaturated": 1, "cholesterol": 1},
    "Processed Snack": {"trans": 2, "saturated": 1, "omega6": 1},
    "Fried Dessert": {"trans": 2, "saturated": 2},
    "Plant Oil": {"unsaturated": 2, "omega6": 2},
}


FOOD_COLORS: Dict[str, Tuple[int, int, int]] = {
    "Olive Oil": (115, 180, 70),
    "Butter": (248, 219, 97),
    "Salmon": (244, 132, 116),
    "Avocado": (97, 188, 101),
    "Nuts": (181, 123, 78),
    "Cheese": (255, 201, 82),
    "Bacon": (210, 98, 104),
    "Processed Snack": (161, 106, 255),
    "Fried Dessert": (214, 151, 75),
    "Plant Oil": (90, 179, 95),
}


ZONE_LABELS = {
    "energy": "Energy Storage",
    "essential": "Essential & Structural",
    "limit": "Limit Intake",
}


# ------------------------------------------------------------
# Entities
# ------------------------------------------------------------
class Particle:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1.6, 1.6)
        self.vy = random.uniform(-2.8, -0.4)
        self.life = random.randint(18, 34)
        self.max_life = self.life
        self.radius = random.randint(3, 6)
        self.color = color

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12
        self.life -= 1

    def draw(self, surf: pygame.Surface) -> None:
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        temp = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(temp, (*self.color, alpha), (self.radius * 2, self.radius * 2), self.radius)
        surf.blit(temp, (self.x - self.radius * 2, self.y - self.radius * 2))


class FloatingText:
    def __init__(self, text: str, x: int, y: int, color: Tuple[int, int, int]):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = 45
        self.max_life = 45

    def update(self) -> None:
        self.y -= 0.75
        self.life -= 1

    def draw(self, surf: pygame.Surface) -> None:
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        img = BODY_FONT.render(self.text, True, self.color)
        temp = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        temp.blit(img, (0, 0))
        temp.set_alpha(alpha)
        surf.blit(temp, (self.x, self.y))


class FoodCard:
    W = 180
    H = 88

    def __init__(self, food_name: str, x: int, y: int, speed: float):
        self.food_name = food_name
        self.rect = pygame.Rect(x, y, self.W, self.H)
        self.speed = speed
        self.selected = False
        self.flash_timer = 0

    @property
    def color(self) -> Tuple[int, int, int]:
        return FOOD_COLORS[self.food_name]

    def update(self, sluggish_factor: float) -> None:
        self.rect.x -= int(self.speed * sluggish_factor)
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surf: pygame.Surface, hovered: bool = False) -> None:
        color = self.color
        border = WHITE if hovered else (80, 94, 124)
        draw_rounded_panel(surf, self.rect, color, border=border, radius=16, border_width=3)
        inner = self.rect.inflate(-12, -12)
        pygame.draw.rect(surf, (255, 255, 255, 28), inner, border_radius=14)
        draw_text(surf, self.food_name, BODY_FONT, BLACK if hovered else BLACK, (self.rect.x + 14, self.rect.y + 15))

        composition = FOOD_COMPOSITION[self.food_name]
        summary = ", ".join(LIPID_DATA[k].short for k in composition.keys())
        draw_text(surf, summary, TINY_FONT, BLACK, (self.rect.x + 14, self.rect.y + 50))

        if self.flash_timer > 0:
            alpha = int(120 * (self.flash_timer / 12))
            temp = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            pygame.draw.rect(temp, (255, 255, 255, alpha), temp.get_rect(), border_radius=16)
            surf.blit(temp, self.rect.topleft)


class LipidTile:
    SIZE = 66

    def __init__(self, lipid_key: str, x: int, y: int):
        self.lipid_key = lipid_key
        self.info = LIPID_DATA[lipid_key]
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.home_pos = (x, y)
        self.placed_zone: Optional[str] = None
        self.hovered = False

    def start_drag(self, mouse_pos: Tuple[int, int]) -> None:
        self.dragging = True
        self.offset_x = self.rect.x - mouse_pos[0]
        self.offset_y = self.rect.y - mouse_pos[1]

    def drag(self, mouse_pos: Tuple[int, int]) -> None:
        if self.dragging:
            self.rect.x = mouse_pos[0] + self.offset_x
            self.rect.y = mouse_pos[1] + self.offset_y

    def stop_drag(self) -> None:
        self.dragging = False

    def snap_to(self, pos: Tuple[int, int]) -> None:
        self.rect.topleft = pos
        self.home_pos = pos

    def draw(self, surf: pygame.Surface, large_preview: bool = False) -> None:
        border = WHITE if self.hovered or self.dragging else (75, 88, 110)
        draw_rounded_panel(surf, self.rect, self.info.color, border=border, radius=16, border_width=3)
        pygame.draw.rect(surf, (255, 255, 255), self.rect, width=1, border_radius=16)

        draw_text(surf, self.info.short, BODY_FONT, BLACK, (self.rect.centerx, self.rect.y + 12), center=True)
        draw_text(surf, self.info.name, TINY_FONT, BLACK, (self.rect.centerx, self.rect.y + 38), center=True)

        if large_preview and self.hovered:
            preview = pygame.Rect(1090, 520, 255, 180)
            draw_rounded_panel(surf, preview, PANEL_2, border=(95, 110, 142), radius=20)
            draw_text(surf, self.info.name, HEADER_FONT, WHITE, (preview.x + 18, preview.y + 18))
            bubble = pygame.Rect(preview.x + 18, preview.y + 58, 92, 92)
            draw_rounded_panel(surf, bubble, self.info.color, border=WHITE, radius=18, border_width=3)
            draw_text(surf, self.info.short, HEADER_FONT, BLACK, (bubble.centerx, bubble.y + 18), center=True)
            draw_text(surf, self.info.ideal_zone.replace("essential", "essential"), SMALL_FONT, BLACK, (bubble.centerx, bubble.y + 56), center=True)
            wrapped = wrap_text(self.info.description, BODY_FONT, 125)
            y = preview.y + 58
            for line in wrapped:
                draw_text(surf, line, SMALL_FONT, SOFT, (preview.x + 128, y))
                y += 22
            zone_text = f"Best fit: {ZONE_LABELS[self.info.ideal_zone]}"
            draw_text(surf, zone_text, SMALL_FONT, CYAN, (preview.x + 18, preview.y + 148))


class DropZone:
    def __init__(self, key: str, rect: pygame.Rect, accent: Tuple[int, int, int]):
        self.key = key
        self.rect = rect
        self.accent = accent

    def draw(self, surf: pygame.Surface, active: bool = False) -> None:
        fill = lerp_color(PANEL, self.accent, 0.20 if active else 0.08)
        border = self.accent if active else (82, 96, 124)
        draw_rounded_panel(surf, self.rect, fill, border=border, radius=20, border_width=3)
        draw_text(surf, ZONE_LABELS[self.key], HEADER_FONT, WHITE, (self.rect.centerx, self.rect.y + 16), center=True)

        subtitle = {
            "energy": "Store useful energy, but do not overload",
            "essential": "Supports structure and membrane function",
            "limit": "Keep harmful lipids low",
        }[self.key]
        lines = wrap_text(subtitle, SMALL_FONT, 28)
        y = self.rect.y + 52
        for line in lines:
            draw_text(surf, line, SMALL_FONT, SOFT, (self.rect.centerx, y), center=True)
            y += 19


def wrap_text(text: str, font: pygame.font.Font, max_chars: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ------------------------------------------------------------
# Main game class
# ------------------------------------------------------------
class BuildThePlateGame:
    def __init__(self):
        self.state = "intro"
        self.running = True

        self.intro_stage = 0
        self.intro_timer = 0

        self.food_cards: List[FoodCard] = []
        self.lipid_tiles: List[LipidTile] = []
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []

        self.meals_completed = 0
        self.tiles_sorted_this_meal = 0
        self.correct_this_meal = 0
        self.incorrect_this_meal = 0
        self.current_food_selected: Optional[str] = None

        self.score = 0
        self.combo_multiplier = 1.0

        self.membrane_fluidity = 60.0
        self.inflammation = 28.0
        self.energy_reserve = 35.0

        self.processed_choice_count = 0
        self.total_cholesterol_this_meal = 0

        self.base_conveyor_speed = 2.0
        self.conveyor_spawn_timer = 0
        self.round_time = 80
        self.max_round_time = 80

        self.dragging_tile: Optional[LipidTile] = None
        self.hovered_food: Optional[FoodCard] = None
        self.hovered_tile: Optional[LipidTile] = None

        self.drop_zones = {
            "energy": DropZone("energy", pygame.Rect(720, 260, 210, 260), ORANGE),
            "essential": DropZone("essential", pygame.Rect(950, 260, 210, 260), CYAN),
            "limit": DropZone("limit", pygame.Rect(1180, 260, 180, 260), RED),
        }

        self.tile_spawn_positions = [
            (735, 590), (810, 590), (885, 590),
            (735, 665), (810, 665), (885, 665),
            (735, 740), (810, 740), (885, 740),
            (960, 590), (1035, 590), (1110, 590),
        ]

        self.food_pool_whole = ["Olive Oil", "Salmon", "Avocado", "Nuts", "Plant Oil"]
        self.food_pool_mixed = ["Olive Oil", "Butter", "Salmon", "Avocado", "Nuts", "Cheese", "Bacon", "Plant Oil"]
        self.food_pool_hard = list(FOOD_COMPOSITION.keys())

        self.reset_for_new_meal(full_reset=True)

    # --------------------------------------------------------
    # Setup / reset
    # --------------------------------------------------------
    def reset_for_new_meal(self, full_reset: bool = False) -> None:
        self.food_cards.clear()
        self.lipid_tiles.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.dragging_tile = None
        self.hovered_tile = None
        self.hovered_food = None

        self.tiles_sorted_this_meal = 0
        self.correct_this_meal = 0
        self.incorrect_this_meal = 0
        self.current_food_selected = None
        self.total_cholesterol_this_meal = 0
        self.round_time = self.max_round_time if full_reset else max(42, self.max_round_time - self.meals_completed * 8)
        self.conveyor_spawn_timer = 0

        if full_reset:
            self.score = 0
            self.meals_completed = 0
            self.combo_multiplier = 1.0
            self.membrane_fluidity = 60.0
            self.inflammation = 28.0
            self.energy_reserve = 35.0
            self.processed_choice_count = 0

    # --------------------------------------------------------
    # Game rules
    # --------------------------------------------------------
    def current_level(self) -> int:
        return min(3, self.meals_completed + 1)

    def get_food_pool(self) -> List[str]:
        level = self.current_level()
        if level == 1:
            return self.food_pool_whole
        if level == 2:
            return self.food_pool_mixed
        return self.food_pool_hard

    def conveyor_speed_factor(self) -> float:
        # If fluidity is low, metabolism is sluggish and the conveyor visually slows.
        if self.membrane_fluidity < 25:
            return 0.45
        if self.membrane_fluidity < 40:
            return 0.7
        return 1.0

    def current_multiplier(self) -> float:
        # Inflammation above threshold disables multipliers.
        if self.inflammation >= 75:
            return 1.0
        in_optimal = (
            45 <= self.membrane_fluidity <= 75 and
            self.inflammation <= 40 and
            self.energy_reserve >= 35
        )
        return 2.0 if in_optimal else 1.25

    def spawn_food_card(self) -> None:
        pool = self.get_food_pool()
        chosen = random.choice(pool)
        y = 128
        x = WIDTH + random.randint(40, 120)
        speed = self.base_conveyor_speed + self.current_level() * 0.6
        self.food_cards.append(FoodCard(chosen, x, y, speed))

    def select_food(self, card: FoodCard) -> None:
        if self.lipid_tiles:
            return

        self.current_food_selected = card.food_name
        card.flash_timer = 12
        comp = FOOD_COMPOSITION[card.food_name]
        self.lipid_tiles.clear()

        spawn_positions = self.tile_spawn_positions[:]
        random.shuffle(spawn_positions)

        idx = 0
        for lipid_key, count in comp.items():
            for _ in range(count):
                if idx >= len(spawn_positions):
                    break
                x, y = spawn_positions[idx]
                idx += 1
                self.lipid_tiles.append(LipidTile(lipid_key, x, y))
                for _ in range(6):
                    self.particles.append(Particle(x + 33, y + 33, LIPID_DATA[lipid_key].color))

        if card.food_name in {"Processed Snack", "Fried Dessert"}:
            self.processed_choice_count += 1

        self.floating_texts.append(FloatingText(f"{card.food_name} broken into lipid tiles", 720, 548, CYAN))

    def score_tile(self, tile: LipidTile, zone_key: str) -> None:
        lipid = tile.lipid_key
        info = tile.info

        correct = zone_key == info.ideal_zone
        base_points = 120 if correct else 40
        bonus_mult = self.current_multiplier()
        gained = int(base_points * bonus_mult)

        # Apply educational effects to indicators.
        fluidity_delta = info.fluidity
        inflammation_delta = info.inflammation
        energy_delta = info.energy

        # Zone-specific interpretation.
        if lipid == "cholesterol":
            self.total_cholesterol_this_meal += 1
            if zone_key == "essential":
                if self.total_cholesterol_this_meal <= 2:
                    fluidity_delta += 4
                    inflammation_delta -= 1
                else:
                    inflammation_delta += 7
                    fluidity_delta -= 3
            elif zone_key == "limit":
                inflammation_delta += 1
            elif zone_key == "energy":
                inflammation_delta += 4
                fluidity_delta -= 2

        if zone_key == "limit":
            if lipid == "trans":
                inflammation_delta -= 5
                energy_delta -= 2
                gained += 70
            elif lipid in {"saturated", "cholesterol"}:
                inflammation_delta -= 1
                energy_delta -= 1
            else:
                # Limiting beneficial lipids is not ideal.
                fluidity_delta -= 2
                energy_delta -= 2

        elif zone_key == "energy":
            if lipid in {"saturated", "unsaturated", "omega6"}:
                energy_delta += 3
            if lipid == "trans":
                inflammation_delta += 4
            if lipid == "omega3":
                energy_delta += 1
                fluidity_delta -= 1

        elif zone_key == "essential":
            if lipid in {"omega3", "unsaturated", "omega6"}:
                fluidity_delta += 2
            if lipid == "saturated":
                fluidity_delta -= 2

        self.membrane_fluidity = clamp(self.membrane_fluidity + fluidity_delta, 0, 100)
        self.inflammation = clamp(self.inflammation + inflammation_delta, 0, 100)
        self.energy_reserve = clamp(self.energy_reserve + energy_delta, 0, 100)

        self.score += gained
        self.tiles_sorted_this_meal += 1
        if correct:
            self.correct_this_meal += 1
        else:
            self.incorrect_this_meal += 1

        msg = f"+{gained}"
        msg_color = SUCCESS if correct else YELLOW
        self.floating_texts.append(FloatingText(msg, tile.rect.x, tile.rect.y - 10, msg_color))

        for _ in range(10):
            self.particles.append(Particle(tile.rect.centerx, tile.rect.centery, info.color))

    def evaluate_meal(self) -> None:
        fluidity_ok = 45 <= self.membrane_fluidity <= 78
        inflammation_ok = self.inflammation < 65
        energy_ok = self.energy_reserve >= 35
        accuracy_ok = self.correct_this_meal >= max(2, self.tiles_sorted_this_meal - 1)

        if fluidity_ok and inflammation_ok and energy_ok and accuracy_ok:
            self.meals_completed += 1
            self.score += 500
            self.membrane_fluidity = clamp(self.membrane_fluidity + 5, 0, 100)
            self.floating_texts.append(FloatingText("Balanced meal bonus +500", 880, 210, SUCCESS))

            if self.meals_completed >= 3:
                self.state = "win"
            else:
                self.reset_for_new_meal(full_reset=False)
        else:
            # Penalties encourage balance and connect choices to the next round.
            if self.processed_choice_count >= 2:
                self.membrane_fluidity = clamp(self.membrane_fluidity - 8, 0, 100)
            self.state = "lose"

    def can_finish_current_meal(self) -> bool:
        return self.tiles_sorted_this_meal > 0 and not self.lipid_tiles

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------
    def update(self) -> None:
        if self.state == "intro":
            self.update_intro()
            return

        if self.state in {"win", "lose"}:
            self.update_effects_only()
            return

        sluggish = self.conveyor_speed_factor()

        self.conveyor_spawn_timer += 1
        spawn_gap = max(75, 135 - self.current_level() * 16)
        if self.conveyor_spawn_timer >= spawn_gap:
            self.conveyor_spawn_timer = 0
            if len(self.food_cards) < 6:
                self.spawn_food_card()

        for card in self.food_cards:
            card.update(sluggish)
        self.food_cards = [c for c in self.food_cards if c.rect.right > -40]

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if ft.life > 0]

        self.round_time -= 1 / FPS
        if self.round_time <= 0:
            self.state = "lose"

        if self.inflammation >= 90:
            self.state = "lose"

        if self.energy_reserve <= 5 and self.tiles_sorted_this_meal >= 3:
            self.state = "lose"

        if self.can_finish_current_meal():
            self.evaluate_meal()

    def update_intro(self) -> None:
        self.intro_timer += 1
        if self.intro_stage == 0 and self.intro_timer > 210:
            self.intro_stage = 1
            self.intro_timer = 0
        elif self.intro_stage == 1 and self.intro_timer > 210:
            self.intro_stage = 2
            self.intro_timer = 0
        elif self.intro_stage == 2 and self.intro_timer > 240:
            self.state = "play"

        self.update_effects_only()

    def update_effects_only(self) -> None:
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if ft.life > 0]

    # --------------------------------------------------------
    # Input
    # --------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return

        if self.state == "intro":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = "play"
            return

        if self.state in {"win", "lose"}:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.state = "intro"
                self.intro_stage = 0
                self.intro_timer = 0
                self.reset_for_new_meal(full_reset=True)
            return

        if event.type == pygame.MOUSEMOTION:
            self.handle_mouse_motion(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_mouse_down(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.handle_mouse_up(event.pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.reset_for_new_meal(full_reset=False)

    def handle_mouse_motion(self, pos: Tuple[int, int]) -> None:
        self.hovered_food = None
        for card in reversed(self.food_cards):
            if card.rect.collidepoint(pos):
                self.hovered_food = card
                break

        self.hovered_tile = None
        for tile in reversed(self.lipid_tiles):
            tile.hovered = tile.rect.collidepoint(pos)
            if tile.hovered and self.hovered_tile is None:
                self.hovered_tile = tile

        if self.dragging_tile:
            self.dragging_tile.drag(pos)

    def handle_mouse_down(self, pos: Tuple[int, int]) -> None:
        # Start dragging topmost tile first.
        for tile in reversed(self.lipid_tiles):
            if tile.rect.collidepoint(pos):
                self.dragging_tile = tile
                tile.start_drag(pos)
                self.lipid_tiles.remove(tile)
                self.lipid_tiles.append(tile)
                return

        # Otherwise select a food if no tile set is active.
        if not self.lipid_tiles:
            for card in reversed(self.food_cards):
                if card.rect.collidepoint(pos):
                    self.select_food(card)
                    return

    def handle_mouse_up(self, pos: Tuple[int, int]) -> None:
        if not self.dragging_tile:
            return

        tile = self.dragging_tile
        tile.stop_drag()

        placed = False
        for zone_key, zone in self.drop_zones.items():
            if zone.rect.collidepoint(pos):
                self.score_tile(tile, zone_key)
                self.lipid_tiles.remove(tile)
                placed = True
                break

        if not placed:
            tile.snap_to(tile.home_pos)

        self.dragging_tile = None

    # --------------------------------------------------------
    # Drawing
    # --------------------------------------------------------
    def draw(self) -> None:
        SCREEN.fill(BG)
        self.draw_background()

        if self.state == "intro":
            self.draw_intro()
        else:
            self.draw_ui()
            self.draw_gameplay()

            if self.state == "win":
                self.draw_overlay("Balanced Meals Complete", "You kept the cell stable, responsive, and efficient.", SUCCESS)
            elif self.state == "lose":
                self.draw_overlay("Meal Balance Failed", "The cell lost balance. Press R to restart.", DANGER)

        for p in self.particles:
            p.draw(SCREEN)
        for ft in self.floating_texts:
            ft.draw(SCREEN)

        pygame.display.flip()

    def draw_background(self) -> None:
        for i in range(0, HEIGHT, 40):
            color = lerp_color((16, 20, 32), (28, 34, 52), i / HEIGHT)
            pygame.draw.rect(SCREEN, color, (0, i, WIDTH, 40))

        # Large soft membrane/cell shapes
        pygame.draw.circle(SCREEN, (28, 48, 76), (220, 620), 290)
        pygame.draw.circle(SCREEN, (36, 60, 94), (220, 620), 250, width=16)
        pygame.draw.circle(SCREEN, (55, 92, 140), (220, 620), 155, width=8)

        pygame.draw.circle(SCREEN, (42, 52, 75), (1160, 120), 120)
        pygame.draw.circle(SCREEN, (66, 80, 110), (1160, 120), 96, width=12)

        # Conveyor belt
        belt = pygame.Rect(30, 110, 620, 106)
        draw_rounded_panel(SCREEN, belt, (46, 50, 62), border=(84, 88, 102), radius=24)
        pygame.draw.rect(SCREEN, (66, 72, 88), (46, 150, 588, 26), border_radius=12)
        for x in range(50, 620, 48):
            pygame.draw.line(SCREEN, (88, 93, 110), (x, 150), (x + 24, 176), 4)

        # Bloodstream particles
        for i in range(18):
            x = 25 + (i * 85) % (WIDTH + 120)
            y = 82 + int(10 * math.sin((pygame.time.get_ticks() / 350) + i))
            pygame.draw.circle(SCREEN, (176, 70, 88), (x % WIDTH, y), 7)
            pygame.draw.circle(SCREEN, (226, 100, 120), (x % WIDTH, y), 7, width=2)

    def draw_intro(self) -> None:
        title = "Mini Game #2: Build the Plate"
        draw_text(SCREEN, title, BIG_FONT, WHITE, (WIDTH // 2, 120), center=True)

        box = pygame.Rect(180, 210, 1040, 430)
        draw_rounded_panel(SCREEN, box, PANEL, border=(86, 100, 130), radius=26)

        if self.intro_stage == 0:
            draw_text(SCREEN, "What you eat becomes part of your cells.", HEADER_FONT, CYAN, (WIDTH // 2, 265), center=True)
            draw_text(SCREEN, "A meal rich in fish, nuts, and plant oils keeps membranes flexible.", BODY_FONT, WHITE, (WIDTH // 2, 330), center=True)
            draw_text(SCREEN, "Proteins move smoothly. Signaling stays efficient.", BODY_FONT, SOFT, (WIDTH // 2, 365), center=True)

            self.draw_intro_plate((400, 485), healthy=True)
            self.draw_intro_plate((1000, 485), healthy=False, ghost=True)

        elif self.intro_stage == 1:
            draw_text(SCREEN, "A diet heavy in processed snacks and fried foods can stiffen the membrane.", HEADER_FONT, ORANGE, (WIDTH // 2, 265), center=True)
            draw_text(SCREEN, "Fluidity drops. Inflammation rises. Signaling slows.", BODY_FONT, WHITE, (WIDTH // 2, 330), center=True)

            self.draw_intro_plate((400, 485), healthy=True, ghost=True)
            self.draw_intro_plate((1000, 485), healthy=False)

        else:
            draw_text(SCREEN, "Design meals that keep the cell stable, responsive, and efficient.", HEADER_FONT, SUCCESS, (WIDTH // 2, 265), center=True)
            bullet_lines = [
                "Click foods on the conveyor to reveal their lipid composition.",
                "Drag each lipid tile into the best category.",
                "Keep membrane fluidity in range, inflammation low, and energy reserve high enough.",
                "Complete 3 balanced meals to win.",
                "Press SPACE to start now.",
            ]
            y = 330
            for line in bullet_lines:
                draw_text(SCREEN, line, BODY_FONT, WHITE, (WIDTH // 2, y), center=True)
                y += 44

        draw_text(SCREEN, "Press SPACE or ENTER to skip intro", SMALL_FONT, MUTED, (WIDTH // 2, 700), center=True)

    def draw_intro_plate(self, center: Tuple[int, int], healthy: bool, ghost: bool = False) -> None:
        alpha = 90 if ghost else 255
        temp = pygame.Surface((320, 220), pygame.SRCALPHA)
        cx, cy = 160, 110
        plate_color = (235, 237, 245, alpha)
        ring_color = (200, 205, 220, alpha)
        pygame.draw.circle(temp, plate_color, (cx, cy), 90)
        pygame.draw.circle(temp, ring_color, (cx, cy), 90, width=10)

        if healthy:
            pygame.draw.circle(temp, (110, 190, 120, alpha), (124, 110), 22)
            pygame.draw.circle(temp, (245, 135, 110, alpha), (160, 88), 20)
            pygame.draw.circle(temp, (210, 160, 80, alpha), (197, 118), 18)
            pygame.draw.circle(temp, (90, 165, 85, alpha), (178, 145), 16)
            label = "Flexible membrane"
            color = SUCCESS
        else:
            pygame.draw.circle(temp, (182, 125, 78, alpha), (124, 110), 22)
            pygame.draw.circle(temp, (208, 105, 105, alpha), (160, 88), 20)
            pygame.draw.circle(temp, (170, 95, 150, alpha), (197, 118), 18)
            pygame.draw.circle(temp, (220, 165, 75, alpha), (178, 145), 16)
            label = "Rigid membrane"
            color = ORANGE

        SCREEN.blit(temp, (center[0] - 160, center[1] - 110))
        draw_text(SCREEN, label, BODY_FONT, color, (center[0], center[1] + 115), center=True)

    def draw_ui(self) -> None:
        # Top metrics panel
        panel = pygame.Rect(26, 18, 1348, 82)
        draw_rounded_panel(SCREEN, panel, PANEL, border=(86, 101, 132), radius=24)

        draw_text(SCREEN, f"Score: {self.score}", HEADER_FONT, WHITE, (46, 28))
        draw_text(SCREEN, f"Level {self.current_level()} / 3", BODY_FONT, SOFT, (50, 62))
        draw_text(SCREEN, f"Meals Completed: {self.meals_completed} / 3", BODY_FONT, SOFT, (220, 62))

        self.draw_meter(440, 26, 250, "Membrane Fluidity", self.membrane_fluidity, BLUE, ideal=(45, 75))
        self.draw_meter(720, 26, 250, "Inflammation", self.inflammation, RED, ideal=(0, 40), reverse_good=True)
        self.draw_meter(1000, 26, 250, "Energy Reserve", self.energy_reserve, YELLOW, ideal=(35, 80))

        # Instructions / live rules
        left = pygame.Rect(26, 238, 660, 610)
        draw_rounded_panel(SCREEN, left, PANEL, border=(84, 100, 128), radius=22)
        draw_text(SCREEN, "Incoming Nutrients", HEADER_FONT, WHITE, (50, 250))
        draw_text(SCREEN, "Click a food to break it into lipid tiles.", BODY_FONT, SOFT, (50, 282))
        draw_text(SCREEN, f"Time left: {max(0, int(self.round_time))}s", BODY_FONT, CYAN if self.round_time > 15 else ORANGE, (500, 250))
        draw_text(SCREEN, "Press R to reset the current meal.", SMALL_FONT, MUTED, (500, 282))

        rule_panel = pygame.Rect(40, 710, 632, 122)
        draw_rounded_panel(SCREEN, rule_panel, PANEL_2, border=(95, 110, 140), radius=18)
        draw_text(SCREEN, "Sorting guide", HEADER_FONT, WHITE, (58, 724))
        guide_lines = [
            "Energy Storage: useful fuel, but too much can reduce flexibility.",
            "Essential & Structural: omega-3, unsaturated fats, moderate cholesterol.",
            "Limit Intake: trans fats and excess harmful lipids.",
        ]
        y = 756
        for line in guide_lines:
            draw_text(SCREEN, line, SMALL_FONT, SOFT, (58, y))
            y += 22

        # Tray panel
        tray = pygame.Rect(710, 530, 650, 318)
        draw_rounded_panel(SCREEN, tray, PANEL, border=(84, 100, 128), radius=22)
        draw_text(SCREEN, "Lipid Tile Tray", HEADER_FONT, WHITE, (730, 542))
        if self.current_food_selected:
            draw_text(SCREEN, f"Selected food: {self.current_food_selected}", BODY_FONT, CYAN, (930, 544))
        else:
            draw_text(SCREEN, "No food selected yet", BODY_FONT, MUTED, (980, 544))

        # Zone panels
        for key, zone in self.drop_zones.items():
            active = bool(self.dragging_tile and zone.rect.colliderect(self.dragging_tile.rect))
            zone.draw(SCREEN, active=active)

        # Hover/help area
        info = pygame.Rect(950, 710, 390, 122)
        draw_rounded_panel(SCREEN, info, PANEL_2, border=(95, 110, 140), radius=18)
        draw_text(SCREEN, "Hover Info", HEADER_FONT, WHITE, (970, 724))

        if self.hovered_food:
            draw_text(SCREEN, self.hovered_food.food_name, BODY_FONT, CYAN, (970, 760))
            summary = ", ".join(LIPID_DATA[k].name for k in FOOD_COMPOSITION[self.hovered_food.food_name].keys())
            wrapped = wrap_text(summary, SMALL_FONT, 35)
            y = 788
            for line in wrapped:
                draw_text(SCREEN, line, SMALL_FONT, SOFT, (970, y))
                y += 18
        elif self.hovered_tile:
            draw_text(SCREEN, self.hovered_tile.info.name, BODY_FONT, CYAN, (970, 760))
            wrapped = wrap_text(self.hovered_tile.info.description, SMALL_FONT, 38)
            y = 788
            for line in wrapped:
                draw_text(SCREEN, line, SMALL_FONT, SOFT, (970, y))
                y += 18
        else:
            draw_text(SCREEN, "Hover over a food or lipid tile to learn more.", SMALL_FONT, SOFT, (970, 764))

    def draw_meter(self, x: int, y: int, w: int, label: str, value: float, color: Tuple[int, int, int], ideal: Tuple[int, int], reverse_good: bool = False) -> None:
        draw_text(SCREEN, label, SMALL_FONT, SOFT, (x, y))
        bar = pygame.Rect(x, y + 24, w, 24)
        pygame.draw.rect(SCREEN, (55, 62, 84), bar, border_radius=12)
        fill = pygame.Rect(x, y + 24, int(w * (value / 100)), 24)
        pygame.draw.rect(SCREEN, color, fill, border_radius=12)
        pygame.draw.rect(SCREEN, (120, 132, 160), bar, width=2, border_radius=12)

        ideal_lo, ideal_hi = ideal
        ix = x + int((ideal_lo / 100) * w)
        iw = int(((ideal_hi - ideal_lo) / 100) * w)
        ideal_rect = pygame.Rect(ix, y + 24, iw, 24)
        pygame.draw.rect(SCREEN, (255, 255, 255), ideal_rect, width=2, border_radius=12)

        status = self.metric_status(value, ideal_lo, ideal_hi, reverse_good)
        draw_text(SCREEN, f"{int(value)}", SMALL_FONT, WHITE, (x + w + 12, y + 25))
        draw_text(SCREEN, status, SMALL_FONT, color if status == "Optimal" else SOFT, (x, y + 52))

    def metric_status(self, value: float, lo: int, hi: int, reverse_good: bool) -> str:
        if reverse_good:
            return "Optimal" if value <= hi else "High"
        return "Optimal" if lo <= value <= hi else ("Low" if value < lo else "High")

    def draw_gameplay(self) -> None:
        # Food cards
        for card in self.food_cards:
            card.draw(SCREEN, hovered=(card is self.hovered_food))

        # Live belt labels
        draw_text(SCREEN, "Bloodstream nutrient conveyor", SMALL_FONT, MUTED, (42, 118))
        draw_text(SCREEN, "Whole foods dominate early levels. Processed foods increase later.", SMALL_FONT, MUTED, (42, 196))

        # Lipid tiles
        large_preview_allowed = self.current_level() < 3
        for tile in self.lipid_tiles:
            tile.draw(SCREEN, large_preview=large_preview_allowed)

        # Level-specific hinting
        if self.current_level() == 1:
            draw_text(SCREEN, "Level 1: full color and hover guidance enabled", SMALL_FONT, SUCCESS, (730, 574))
        elif self.current_level() == 2:
            draw_text(SCREEN, "Level 2: hover help is still available, but choices get more complex", SMALL_FONT, YELLOW, (730, 574))
        else:
            draw_text(SCREEN, "Level 3: no large hover preview, faster and less forgiving", SMALL_FONT, RED, (730, 574))

        # Selected food composition view
        if self.current_food_selected:
            comp_rect = pygame.Rect(40, 320, 632, 370)
            draw_rounded_panel(SCREEN, comp_rect, PANEL_2, border=(95, 110, 140), radius=18)
            draw_text(SCREEN, f"{self.current_food_selected} composition", HEADER_FONT, WHITE, (58, 336))

            comp = FOOD_COMPOSITION[self.current_food_selected]
            start_x = 65
            start_y = 386
            col = 0
            row = 0
            for lipid_key, count in comp.items():
                info = LIPID_DATA[lipid_key]
                item_rect = pygame.Rect(start_x + col * 180, start_y + row * 105, 160, 88)
                draw_rounded_panel(SCREEN, item_rect, info.color, border=WHITE, radius=16, border_width=2)
                draw_text(SCREEN, info.name, SMALL_FONT, BLACK, (item_rect.centerx, item_rect.y + 16), center=True)
                draw_text(SCREEN, f"x{count}", BODY_FONT, BLACK, (item_rect.centerx, item_rect.y + 46), center=True)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1

            if not self.lipid_tiles:
                draw_text(SCREEN, "All tiles from this food have been sorted. Choose another food when the next meal begins.", SMALL_FONT, SOFT, (58, 650))
        else:
            prompt_rect = pygame.Rect(40, 320, 632, 370)
            draw_rounded_panel(SCREEN, prompt_rect, PANEL_2, border=(95, 110, 140), radius=18)
            draw_text(SCREEN, "Meal design prompt", HEADER_FONT, WHITE, (58, 336))
            prompt_lines = [
                "Choose foods that help the membrane stay flexible while keeping inflammation under control.",
                "You still need enough energy reserve to complete the meal.",
                "Trans fats are harmful. Omega-3 is especially helpful. Cholesterol can help in moderation.",
            ]
            y = 392
            for line in prompt_lines:
                wrapped = wrap_text(line, BODY_FONT, 56)
                for sub in wrapped:
                    draw_text(SCREEN, sub, BODY_FONT, SOFT, (58, y))
                    y += 30
                y += 10

    def draw_overlay(self, title: str, subtitle: str, color: Tuple[int, int, int]) -> None:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 140))
        SCREEN.blit(shade, (0, 0))

        box = pygame.Rect(300, 250, 800, 300)
        draw_rounded_panel(SCREEN, box, PANEL, border=color, radius=26, border_width=4)
        draw_text(SCREEN, title, BIG_FONT, color, (box.centerx, box.y + 60), center=True)
        draw_text(SCREEN, subtitle, BODY_FONT, WHITE, (box.centerx, box.y + 140), center=True)

        if self.state == "win":
            details = f"Final Score: {self.score}   |   Final Fluidity: {int(self.membrane_fluidity)}   |   Final Inflammation: {int(self.inflammation)}"
            draw_text(SCREEN, details, BODY_FONT, SOFT, (box.centerx, box.y + 184), center=True)
        else:
            fail_reasons = []
            if self.inflammation >= 65:
                fail_reasons.append("inflammation got too high")
            if self.energy_reserve < 35:
                fail_reasons.append("energy reserve was too low")
            if not (45 <= self.membrane_fluidity <= 78):
                fail_reasons.append("fluidity moved out of range")
            if not fail_reasons:
                fail_reasons.append("time ran out")
            draw_text(SCREEN, "Why it failed: " + ", ".join(fail_reasons), SMALL_FONT, SOFT, (box.centerx, box.y + 184), center=True)

        draw_text(SCREEN, "Press R to restart", HEADER_FONT, WHITE, (box.centerx, box.y + 240), center=True)


# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------
def main() -> None:
    game = BuildThePlateGame()

    while game.running:
        for event in pygame.event.get():
            game.handle_event(event)

        game.update()
        game.draw()
        CLOCK.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
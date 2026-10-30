"""FIREFLY MARSH - a 2D night-marsh arcade game for Multimedia Systems Lab Test 2.

You are a firefly in a pitch-dark marsh. Only a small circle around you is lit.
Collect dew drops, glow berries and dawn petals, and avoid spiders and frog tongues.

Customization: FLARE. Collecting items fills the Flare meter. At 100% press SPACE:
for 5 seconds the whole marsh is lit and every hazard moves at half speed.

Run with:  python main.py
"""
import json
import math
import os
import random
import sys

import pygame

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR = os.path.join(BASE_DIR, "assets", "sounds")
HIGH_SCORE_FILE = os.path.join(BASE_DIR, "highscore.json")

WIDTH, HEIGHT = 960, 640
HUD_HEIGHT = 60
ARENA = pygame.Rect(0, HUD_HEIGHT, WIDTH, HEIGHT - HUD_HEIGHT)
FPS = 60
MAX_FRAME_TIME = 0.05          # longest frame we simulate (seconds)

# Colour palette: indigo night, soft yellow light, teal water
INDIGO = (14, 17, 40)
INDIGO_DARK = (9, 11, 28)
INDIGO_LIGHT = (30, 36, 78)
TEAL = (64, 214, 200)
TEAL_DARK = (22, 70, 82)
YELLOW = (255, 226, 120)
YELLOW_PALE = (255, 246, 200)
LAVENDER = (226, 214, 255)
PINK = (226, 104, 140)
RED_EYE = (255, 70, 80)
MOSS = (30, 74, 70)
TEXT = (226, 232, 250)
TEXT_DIM = (140, 150, 190)
DARKNESS = (3, 4, 14)
DARKNESS_ALPHA = 238

# Player
PLAYER_SPEED = 270             # pixels per second
PLAYER_MARGIN = 14             # keeps the firefly inside the arena
PLAYER_HITBOX = 16
HIT_INVULNERABLE_TIME = 1.5    # seconds of grace after being hurt

# Rules
START_LIVES = 3
START_TIME = 90.0
MAX_TIME = 120.0
PETAL_TIME_BONUS = 5.0
HIT_SCORE_PENALTY = 5
FLARE_DURATION = 5.0
FLARE_HAZARD_SLOWDOWN = 0.5    # hazards move at half speed during a flare
FLARE_FADE_TIME = 0.4
ENERGY_MAX = 100

# Items: score / energy / time / drawing size / collision size
ITEM_INFO = {
    "dew":    {"hazard": False, "score": 10, "energy": 20, "radius": 11, "box": (26, 26)},
    "berry":  {"hazard": False, "score": 30, "energy": 40, "radius": 13, "box": (30, 30)},
    "petal":  {"hazard": False, "score": 0,  "energy": 0,  "radius": 13, "box": (30, 30)},
    "spider": {"hazard": True,  "radius": 14, "box": (24, 24)},
    "tongue": {"hazard": True,  "radius": 10, "box": (84, 12)},
}
COLLECTIBLE_WEIGHTS = (("dew", 68), ("berry", 17), ("petal", 15))
MAX_COLLECTIBLES = 7
COLLECTIBLE_INTERVAL = 1.0
COLLECTIBLE_LIFETIME = 10.0
COLLECTIBLE_DRIFT = (18, 38)   # min / max drift speed
START_COLLECTIBLES = 4
SPAWN_MIN_DISTANCE = 100       # collectibles never appear on top of the player
FIRST_HAZARD_DELAY = 2.5
SPIDER_SWAY = 34
TONGUE_SPEED_FACTOR = 1.5

# Difficulty: index 0 is level 1 ... index 3 is level 4
LEVEL_THRESHOLDS = (50, 100, 150)           # score needed for level 2, 3, 4
LANTERN_RADIUS = (200, 172, 146, 122)       # lit circle shrinks
HAZARD_SPEED = (150, 185, 220, 255)         # pixels per second
HAZARD_INTERVAL = (2.4, 1.9, 1.5, 1.2)      # seconds between hazard spawns
MAX_HAZARDS = (2, 3, 4, 5)
LANTERN_SHRINK_SPEED = 60                   # pixels per second
SAFE_LANE = 90                              # hazards never spawn in the player's lane


# ----------------------------------------------------------------------------
# Small helper functions
# ----------------------------------------------------------------------------
def level_for_score(score):
    """Returns the difficulty level (1-4) for a given score."""
    level = 1
    for threshold in LEVEL_THRESHOLDS:
        if score >= threshold:
            level += 1
    return level


def load_high_score(path=HIGH_SCORE_FILE):
    """Reads the saved high score. Missing, empty or broken files give 0."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return max(0, int(json.load(file)["high_score"]))
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def save_high_score(score, path=HIGH_SCORE_FILE):
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump({"high_score": int(score)}, file)
    except OSError:
        pass  # a read-only folder must not crash the game


def make_font(size, serif=False):
    if serif:
        path = pygame.font.match_font("georgia,palatinolinotype,bookantiqua,dejavuserif,liberationserif")
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def draw_text(surface, text, font, color, pos, anchor="center"):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(**{anchor: (int(pos[0]), int(pos[1]))}))


def wrap_text(text, font, max_width):
    lines, current = [], ""
    for word in text.split():
        trial = (current + " " + word).strip()
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def rect_centered_at(size, pos):
    rect = pygame.Rect(0, 0, size[0], size[1])
    rect.center = (int(pos[0]), int(pos[1]))
    return rect


_glow_cache = {}


def glow_sprite(radius, color, strength=1.0):
    """A soft round glow made of concentric circles, cached so it is built once."""
    key = (radius, color, strength)
    if key not in _glow_cache:
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            fade = 1 - r / radius
            pygame.draw.circle(surface, (*color, int(255 * strength * fade * fade)), (radius, radius), r)
        _glow_cache[key] = surface
    return _glow_cache[key]


def blit_glow(surface, pos, radius, color, strength=1.0):
    sprite = glow_sprite(radius, color, strength)
    surface.blit(sprite, sprite.get_rect(center=(int(pos[0]), int(pos[1]))))


_light_cache = {}


def light_sprite(radius):
    """The lantern: clear in the middle, fading to full darkness at the edge."""
    if radius not in _light_cache:
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        surface.fill((*DARKNESS, DARKNESS_ALPHA))
        for r in range(radius, 0, -2):
            alpha = int(DARKNESS_ALPHA * (r / radius) ** 3.0)
            pygame.draw.circle(surface, (*DARKNESS, alpha), (radius, radius), r)
        _light_cache[radius] = surface
    return _light_cache[radius]


# ----------------------------------------------------------------------------
# Sound
# ----------------------------------------------------------------------------
class SoundManager:
    """Loads .wav files if they exist. Missing files or no audio device never crash the game."""
    NAMES = ("dew", "berry", "petal", "hit", "flare", "gameover", "ambient")

    def __init__(self, sound_dir=SOUND_DIR):
        self.sounds = {}
        try:
            pygame.mixer.init()
        except pygame.error:
            return
        for name in self.NAMES:
            path = os.path.join(sound_dir, name + ".wav")
            if os.path.isfile(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except pygame.error:
                    pass
        if "ambient" in self.sounds:
            self.sounds["ambient"].set_volume(0.35)

    def play(self, name, loops=0):
        sound = self.sounds.get(name)
        if sound:
            sound.play(loops)


# ----------------------------------------------------------------------------
# Game objects
# ----------------------------------------------------------------------------
class Player:
    """The firefly. Two pre-drawn wing frames are swapped quickly to animate the wings."""

    def __init__(self):
        self.pos = pygame.Vector2(ARENA.center)
        self.frames = [self._make_frame(wings_up=True), self._make_frame(wings_up=False)]

    @staticmethod
    def _make_frame(wings_up):
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        wing_color = (205, 232, 255, 150)
        if wings_up:
            pygame.draw.ellipse(surface, wing_color, (10, 6, 20, 26))
            pygame.draw.ellipse(surface, wing_color, (34, 6, 20, 26))
        else:
            pygame.draw.ellipse(surface, wing_color, (4, 22, 26, 14))
            pygame.draw.ellipse(surface, wing_color, (34, 22, 26, 14))
        pygame.draw.ellipse(surface, (62, 52, 74), (26, 22, 12, 22))        # body
        pygame.draw.circle(surface, (62, 52, 74), (32, 21), 5)              # head
        pygame.draw.line(surface, (62, 52, 74), (30, 17), (26, 10), 1)      # antennae
        pygame.draw.line(surface, (62, 52, 74), (34, 17), (38, 10), 1)
        pygame.draw.circle(surface, YELLOW, (32, 40), 7)                    # glowing tail
        pygame.draw.circle(surface, YELLOW_PALE, (32, 40), 4)
        return surface

    @property
    def rect(self):
        return rect_centered_at((PLAYER_HITBOX, PLAYER_HITBOX), self.pos)

    def move(self, direction, dt):
        """direction is a Vector2 such as (1, 0). Distance = speed * dt (frame-rate independent)."""
        if direction.length_squared() > 0:
            self.pos += direction.normalize() * PLAYER_SPEED * dt
        self.pos.x = max(ARENA.left + PLAYER_MARGIN, min(ARENA.right - PLAYER_MARGIN, self.pos.x))
        self.pos.y = max(ARENA.top + PLAYER_MARGIN, min(ARENA.bottom - PLAYER_MARGIN, self.pos.y))

    def draw(self, surface, t, flare_active, blink_off):
        blit_glow(surface, self.pos, 58 if flare_active else 40, YELLOW, 0.55 if flare_active else 0.4)
        if blink_off:
            return
        frame = self.frames[int(t * 18) % 2]
        surface.blit(frame, frame.get_rect(center=(int(self.pos.x), int(self.pos.y))))


class Item:
    """Collectibles and hazards share one class; ITEM_INFO says which is which."""

    def __init__(self, kind, pos, velocity):
        self.kind = kind
        self.info = ITEM_INFO[kind]
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.base_x = self.pos.x
        self.age = 0.0
        self.phase = random.uniform(0, math.tau)

    @property
    def is_hazard(self):
        return self.info["hazard"]

    @property
    def rect(self):
        return rect_centered_at(self.info["box"], self.pos)

    def update(self, dt, speed_scale=1.0):
        self.age += dt
        if self.kind == "spider":
            self.pos.y += self.velocity.y * speed_scale * dt
            self.pos.x = self.base_x + math.sin(self.age * 2.2 + self.phase) * SPIDER_SWAY
        elif self.kind == "tongue":
            self.pos += self.velocity * speed_scale * dt
        else:
            self.pos += self.velocity * dt
            if self.pos.x < ARENA.left + 20 or self.pos.x > ARENA.right - 20:
                self.velocity.x *= -1
            if self.pos.y < ARENA.top + 20 or self.pos.y > ARENA.bottom - 20:
                self.velocity.y *= -1

    def is_gone(self):
        if self.kind == "spider":
            return self.pos.y > ARENA.bottom + 40
        if self.kind == "tongue":
            return self.pos.x < -120 or self.pos.x > WIDTH + 120
        return self.age > COLLECTIBLE_LIFETIME


class Particle:
    def __init__(self, pos, velocity, color, life, size):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.color = color
        self.life = self.max_life = life
        self.size = size

    def update(self, dt):
        self.pos += self.velocity * dt
        self.velocity *= max(0.0, 1 - 2.2 * dt)
        self.life -= dt

    def draw(self, surface):
        radius = max(1, int(self.size * self.life / self.max_life))
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), radius)


class AmbientFirefly:
    """Tiny background firefly that wobbles around and pulses. Pure decoration."""

    def __init__(self):
        self.pos = pygame.Vector2(random.uniform(0, WIDTH), random.uniform(HUD_HEIGHT, HEIGHT))
        angle = random.uniform(0, math.tau)
        self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(8, 22)
        self.phase = random.uniform(0, math.tau)

    def update(self, dt, t):
        self.pos += self.velocity * dt
        self.pos.x += math.sin(t * 1.3 + self.phase) * 12 * dt
        if self.pos.x < -10 or self.pos.x > WIDTH + 10:
            self.velocity.x *= -1
        if self.pos.y < HUD_HEIGHT or self.pos.y > HEIGHT:
            self.velocity.y *= -1

    def draw(self, surface, t, small=False):
        pulse = 0.5 + 0.5 * math.sin(t * 2.2 + self.phase)
        radius = 6 + int(4 * pulse) if small else 10 + int(8 * pulse)
        blit_glow(surface, self.pos, radius, (200, 235, 140), 0.85)
        pygame.draw.circle(surface, YELLOW_PALE, (int(self.pos.x), int(self.pos.y)), 2)


class Button:
    def __init__(self, text, center, action, size=(250, 52)):
        self.text = text
        self.action = action
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center

    def draw(self, surface, font, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        fill = (52, 60, 118) if hovered else INDIGO_LIGHT
        border = YELLOW if hovered else TEAL_DARK
        pygame.draw.rect(surface, fill, self.rect, border_radius=10)
        pygame.draw.rect(surface, border, self.rect, 3 if hovered else 2, border_radius=10)
        draw_text(surface, self.text, font, YELLOW if hovered else TEXT, self.rect.center)


# ----------------------------------------------------------------------------
# Item drawing
# ----------------------------------------------------------------------------
def draw_item(surface, item, t, center=None, size_scale=1.0):
    """Draws any item. 'center' lets the instructions screen draw samples anywhere."""
    pos = center if center is not None else item.pos
    x, y = int(pos[0]), int(pos[1])
    pulse = 1 + 0.08 * math.sin(t * 5 + item.phase)
    radius = int(item.info["radius"] * pulse * size_scale)
    if item.kind == "dew":
        pygame.draw.circle(surface, TEAL, (x, y), radius)
        pygame.draw.circle(surface, (150, 250, 235), (x, y), radius, 2)
        pygame.draw.circle(surface, (235, 255, 252), (x - radius // 3, y - radius // 3), max(2, radius // 4))
    elif item.kind == "berry":
        for dx, dy in ((-6, 3), (6, 3), (0, -5)):
            pygame.draw.circle(surface, (255, 200, 80), (x + int(dx * size_scale), y + int(dy * size_scale)), int(radius * 0.62))
        pygame.draw.circle(surface, YELLOW_PALE, (x - 2, y - 7), max(2, radius // 5))
        pygame.draw.line(surface, (110, 190, 110), (x, y - radius), (x + 5, y - radius - 5), 2)
    elif item.kind == "petal":
        for i in range(6):
            angle = i * math.tau / 6 + t * 0.8
            pygame.draw.circle(surface, LAVENDER,
                               (x + int(math.cos(angle) * radius * 0.62), y + int(math.sin(angle) * radius * 0.62)),
                               int(radius * 0.45))
        pygame.draw.circle(surface, YELLOW, (x, y), max(3, radius // 3))
    elif item.kind == "spider":
        if center is None:
            pygame.draw.line(surface, (120, 120, 160), (int(item.pos.x), ARENA.top), (x, y), 1)
        for i in range(4):
            lift = -6 + i * 5
            pygame.draw.line(surface, (36, 28, 50), (x, y), (x - 20, y + lift), 2)
            pygame.draw.line(surface, (36, 28, 50), (x, y), (x + 20, y + lift), 2)
        pygame.draw.circle(surface, (46, 34, 62), (x, y), 12)
        pygame.draw.circle(surface, (80, 62, 104), (x, y), 12, 2)
        pygame.draw.circle(surface, RED_EYE, (x - 4, y - 3), 2)
        pygame.draw.circle(surface, RED_EYE, (x + 4, y - 3), 2)
    elif item.kind == "tongue":
        direction = 1 if item.velocity.x >= 0 else -1
        body = rect_centered_at((84, 12), (x, y))
        pygame.draw.rect(surface, PINK, body, border_radius=6)
        pygame.draw.rect(surface, (170, 70, 104), (body.x, body.centery - 1, body.w, 3))
        pygame.draw.circle(surface, (244, 140, 168), (x + direction * 40, y), 9)
        pygame.draw.circle(surface, (255, 190, 205), (x + direction * 38, y - 3), 3)


def draw_hazard_glints(surface, item):
    """Hazards keep tiny glowing eyes so they stay visible (and fair) in the dark."""
    x, y = int(item.pos.x), int(item.pos.y)
    if item.kind == "spider":
        for dx in (-4, 4):
            blit_glow(surface, (x + dx, y - 3), 9, RED_EYE, 0.9)
    else:
        direction = 1 if item.velocity.x >= 0 else -1
        blit_glow(surface, (x + direction * 40, y), 14, PINK, 0.9)


# ----------------------------------------------------------------------------
# The game
# ----------------------------------------------------------------------------
class Game:
    def __init__(self, high_score_path=HIGH_SCORE_FILE, sound_dir=SOUND_DIR):
        pygame.init()
        pygame.display.set_caption("FIREFLY MARSH")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = {
            "title": make_font(92, serif=True),
            "heading": make_font(54, serif=True),
            "body": make_font(28),
            "small": make_font(22),
            "hud": make_font(30),
        }
        self.high_score_path = high_score_path
        self.high_score = load_high_score(high_score_path)
        self.sounds = SoundManager(sound_dir)
        self.sounds.play("ambient", loops=-1)
        self.background = self.build_background()
        self.dark_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.ambient_flies = [AmbientFirefly() for _ in range(26)]
        self.buttons = self.build_buttons()
        self.t = 0.0
        self.running = True
        self.state = "menu"
        self.reset_round()

    # ---------------- setup ----------------
    def build_buttons(self):
        cx = WIDTH // 2
        return {
            "menu": [Button("Start Game", (cx, 360), "start"),
                     Button("Instructions", (cx, 428), "instructions"),
                     Button("Quit", (cx, 496), "quit")],
            "instructions": [Button("Back", (cx, 588), "menu", size=(200, 46))],
            "paused": [Button("Resume", (cx, 330), "resume"),
                       Button("Main Menu", (cx, 398), "menu")],
            "gameover": [Button("Play Again", (cx, 468), "start"),
                         Button("Main Menu", (cx, 536), "menu")],
        }

    @staticmethod
    def build_background():
        """The marsh is drawn once into a surface and reused every frame."""
        rng = random.Random(11)
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill(INDIGO)
        for _ in range(80):
            star = (rng.randint(0, WIDTH), rng.randint(HUD_HEIGHT, 330))
            pygame.draw.circle(surface, rng.choice([(90, 100, 150), (150, 160, 200)]), star, rng.choice([1, 1, 2]))
        pygame.draw.circle(surface, (236, 232, 205), (885, 175), 36)
        pygame.draw.circle(surface, INDIGO, (901, 165), 31)           # crescent cut-out
        water_top = HEIGHT - 150
        pygame.draw.rect(surface, (16, 30, 60), (0, water_top, WIDTH, 150))
        for i in range(7):                                             # moon reflection
            pygame.draw.line(surface, (60, 84, 120), (800 + i * 8, water_top + 14 + i * 16),
                             (830 + i * 8, water_top + 14 + i * 16), 2)
        for _ in range(7):                                             # lily pads
            pad = (rng.randint(30, WIDTH - 60), rng.randint(water_top + 20, HEIGHT - 20), 46, 18)
            pygame.draw.ellipse(surface, (26, 66, 64), pad)
            pygame.draw.line(surface, (16, 30, 60), (pad[0] + 23, pad[1] + 9), (pad[0] + 46, pad[1] + 4), 2)
        for x in range(-10, WIDTH + 10, 11):                           # reeds
            top = water_top - rng.randint(30, 120)
            lean = rng.randint(-8, 8)
            pygame.draw.line(surface, MOSS, (x, water_top + 10), (x + lean, top), 2)
            if rng.random() < 0.22:
                pygame.draw.ellipse(surface, (58, 40, 52), (x + lean - 3, top - 4, 7, 24))
        return surface

    def reset_round(self):
        """Everything a new round needs. Called on Start and Play Again (high score is kept)."""
        self.player = Player()
        self.items = []
        self.particles = []
        self.popups = []
        self.score = 0
        self.lives = START_LIVES
        self.time_left = START_TIME
        self.energy = 0
        self.flare_time_left = 0.0
        self.hit_cooldown = 0.0
        self.flash_time = 0.0
        self.level = 1
        self.best_level = 1
        self.lantern_radius = float(LANTERN_RADIUS[0])
        self.collectible_timer = COLLECTIBLE_INTERVAL
        self.hazard_timer = FIRST_HAZARD_DELAY
        self.trail_timer = 0.0
        self.game_over_reason = ""
        self.new_best = False
        for _ in range(START_COLLECTIBLES):
            self.spawn_collectible()

    # ---------------- state changes ----------------
    def start_round(self):
        self.reset_round()
        self.state = "playing"

    def end_round(self, reason):
        self.state = "gameover"
        self.game_over_reason = reason
        self.new_best = self.score > self.high_score
        if self.new_best:
            self.high_score = self.score
            save_high_score(self.high_score, self.high_score_path)
        self.sounds.play("gameover")

    def toggle_pause(self):
        if self.state == "playing":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "playing"

    def run_action(self, action):
        if action == "start":
            self.start_round()
        elif action == "instructions":
            self.state = "instructions"
        elif action == "menu":
            self.state = "menu"
        elif action == "resume":
            self.state = "playing"
        elif action == "quit":
            self.running = False

    # ---------------- input ----------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            self.handle_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons.get(self.state, []):
                if button.rect.collidepoint(event.pos):
                    self.run_action(button.action)
                    break

    def handle_key(self, key):
        if self.state == "menu" and key == pygame.K_RETURN:
            self.start_round()
        elif self.state == "instructions" and key == pygame.K_ESCAPE:
            self.state = "menu"
        elif self.state in ("playing", "paused") and key in (pygame.K_p, pygame.K_ESCAPE):
            self.toggle_pause()
        elif self.state == "playing" and key == pygame.K_SPACE:
            self.try_activate_flare()
        elif self.state == "gameover":
            if key == pygame.K_RETURN:
                self.start_round()
            elif key == pygame.K_ESCAPE:
                self.state = "menu"

    @staticmethod
    def read_direction():
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        return pygame.Vector2(dx, dy)

    # ---------------- rules ----------------
    def add_score(self, points):
        self.score = max(0, self.score + points)
        self.level = level_for_score(self.score)
        self.best_level = max(self.best_level, self.level)

    def add_energy(self, amount):
        self.energy = min(ENERGY_MAX, self.energy + amount)

    def flare_active(self):
        return self.flare_time_left > 0

    def try_activate_flare(self):
        """SPACE: works only with a full meter and only if no flare is running."""
        if self.energy >= ENERGY_MAX and not self.flare_active():
            self.flare_time_left = FLARE_DURATION
            self.energy = 0
            self.sounds.play("flare")
            self.burst(self.player.pos, YELLOW, 26, 240)
            return True
        return False

    def collect(self, item):
        info = item.info
        self.add_score(info["score"])
        self.add_energy(info["energy"])
        if item.kind == "petal":
            self.time_left = min(MAX_TIME, self.time_left + PETAL_TIME_BONUS)
            label, color = "+5s", LAVENDER
        else:
            label = "+%d" % info["score"]
            color = TEAL if item.kind == "dew" else YELLOW
        self.sounds.play(item.kind)
        self.burst(item.pos, color, 14 if item.kind == "dew" else 24, 150)
        self.popups.append({"text": label, "pos": pygame.Vector2(item.pos), "life": 0.9, "color": color})
        self.items.remove(item)

    def hit_by(self, hazard):
        """A hazard that touches the player is removed, so one touch can only hurt once."""
        if self.hit_cooldown > 0:
            return
        self.lives -= 1
        self.add_score(-HIT_SCORE_PENALTY)
        self.hit_cooldown = HIT_INVULNERABLE_TIME
        self.flash_time = 0.3
        self.sounds.play("hit")
        self.burst(self.player.pos, RED_EYE, 22, 220)
        self.popups.append({"text": "-1 life", "pos": pygame.Vector2(self.player.pos), "life": 1.0, "color": RED_EYE})
        self.items.remove(hazard)

    def check_collisions(self):
        player_rect = self.player.rect
        for item in self.items[:]:
            if item.rect.colliderect(player_rect):
                if item.is_hazard:
                    self.hit_by(item)
                else:
                    self.collect(item)

    # ---------------- spawning ----------------
    def spawn_collectible(self):
        kind = random.choices([k for k, _ in COLLECTIBLE_WEIGHTS], [w for _, w in COLLECTIBLE_WEIGHTS])[0]
        for _ in range(30):
            pos = (random.randint(ARENA.left + 40, ARENA.right - 40), random.randint(ARENA.top + 40, ARENA.bottom - 40))
            if pygame.Vector2(pos).distance_to(self.player.pos) >= SPAWN_MIN_DISTANCE:
                break
        angle = random.uniform(0, math.tau)
        speed = random.uniform(*COLLECTIBLE_DRIFT)
        self.items.append(Item(kind, pos, (math.cos(angle) * speed, math.sin(angle) * speed)))

    def spawn_hazard(self):
        speed = HAZARD_SPEED[self.level - 1] * random.uniform(0.85, 1.15)
        if random.random() < 0.5:
            x = self.pick_away_from(self.player.pos.x, ARENA.left + 30, ARENA.right - 30)
            self.items.append(Item("spider", (x, ARENA.top - 30), (0, speed)))
        else:
            y = self.pick_away_from(self.player.pos.y, ARENA.top + 30, ARENA.bottom - 30)
            from_left = random.random() < 0.5
            x = -70 if from_left else WIDTH + 70
            direction = 1 if from_left else -1
            self.items.append(Item("tongue", (x, y), (direction * speed * TONGUE_SPEED_FACTOR, 0)))

    @staticmethod
    def pick_away_from(player_coordinate, low, high):
        """A random lane that is not right next to the player (fair spawning)."""
        value = random.randint(low, high)
        for _ in range(20):
            if abs(value - player_coordinate) >= SAFE_LANE:
                break
            value = random.randint(low, high)
        return value

    def hazard_count(self):
        return sum(1 for item in self.items if item.is_hazard)

    def collectible_count(self):
        return len(self.items) - self.hazard_count()

    def update_spawning(self, dt):
        self.collectible_timer -= dt
        if self.collectible_timer <= 0:
            if self.collectible_count() < MAX_COLLECTIBLES:
                self.spawn_collectible()
            self.collectible_timer = COLLECTIBLE_INTERVAL
        self.hazard_timer -= dt
        if self.hazard_timer <= 0:
            if self.hazard_count() < MAX_HAZARDS[self.level - 1]:
                self.spawn_hazard()
            self.hazard_timer = HAZARD_INTERVAL[self.level - 1]

    # ---------------- effects ----------------
    def burst(self, pos, color, count, speed):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            velocity = (math.cos(angle), math.sin(angle))
            self.particles.append(Particle(pos, pygame.Vector2(velocity) * random.uniform(0.3, 1.0) * speed,
                                           color, random.uniform(0.3, 0.7), random.randint(2, 4)))

    def update_effects(self, dt):
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.life <= 0:
                self.particles.remove(particle)
        for popup in self.popups[:]:
            popup["life"] -= dt
            popup["pos"].y -= 40 * dt
            if popup["life"] <= 0:
                self.popups.remove(popup)

    # ---------------- update ----------------
    def update(self, dt):
        self.t += dt
        if self.state == "paused":
            return                           # frozen: nothing moves, the timer does not run
        for fly in self.ambient_flies:
            fly.update(dt, self.t)
        if self.state == "playing":
            self.update_playing(dt, self.read_direction())

    def update_playing(self, dt, direction):
        self.time_left = max(0.0, self.time_left - dt)
        self.flare_time_left = max(0.0, self.flare_time_left - dt)
        self.hit_cooldown = max(0.0, self.hit_cooldown - dt)
        self.flash_time = max(0.0, self.flash_time - dt)

        self.player.move(direction, dt)
        if direction.length_squared() > 0:
            self.trail_timer -= dt
            if self.trail_timer <= 0:
                self.trail_timer = 0.05
                self.particles.append(Particle(self.player.pos + (0, 8), (0, 0), YELLOW, 0.5, 3))

        speed_scale = FLARE_HAZARD_SLOWDOWN if self.flare_active() else 1.0
        for item in self.items[:]:
            item.update(dt, speed_scale if item.is_hazard else 1.0)
            if item.is_gone():
                self.items.remove(item)

        target_radius = LANTERN_RADIUS[self.level - 1]
        step = LANTERN_SHRINK_SPEED * dt
        self.lantern_radius += max(-step, min(step, target_radius - self.lantern_radius))

        self.update_spawning(dt)
        self.check_collisions()
        self.update_effects(dt)

        if self.lives <= 0:
            self.end_round("The marsh got you.")
        elif self.time_left <= 0:
            self.end_round("Dawn broke over the marsh.")

    # ---------------- drawing ----------------
    def darkness_strength(self):
        """1 = full darkness, 0 = fully lit. Fades out/in around a flare."""
        if not self.flare_active():
            return 1.0
        elapsed = FLARE_DURATION - self.flare_time_left
        lit = min(elapsed / FLARE_FADE_TIME, self.flare_time_left / FLARE_FADE_TIME, 1.0)
        return 1.0 - lit

    def draw_water_ripples(self):
        for i in range(6):
            x = 90 + i * 160
            y = HEIGHT - 70 + (i % 3) * 22
            grow = 18 + 10 * math.sin(self.t * 1.2 + i)
            pygame.draw.ellipse(self.screen, (34, 56, 98), (x - grow, y - grow / 4, grow * 2, grow / 2), 1)

    def draw_darkness(self):
        strength = self.darkness_strength()
        if strength <= 0:
            return
        flicker = 3 * math.sin(self.t * 9) + 2 * math.sin(self.t * 23)
        radius = max(40, int((self.lantern_radius + flicker) / 4) * 4)
        self.dark_layer.fill((*DARKNESS, DARKNESS_ALPHA))
        sprite = light_sprite(radius)
        self.dark_layer.blit(sprite, sprite.get_rect(center=(int(self.player.pos.x), int(self.player.pos.y))),
                             special_flags=pygame.BLEND_RGBA_MIN)
        self.dark_layer.set_alpha(int(255 * strength))
        self.screen.blit(self.dark_layer, (0, 0))

    def draw_game(self):
        self.screen.blit(self.background, (0, 0))
        self.draw_water_ripples()
        for fly in self.ambient_flies:
            fly.draw(self.screen, self.t, small=True)
        for item in self.items:
            if item.is_hazard or item.age < COLLECTIBLE_LIFETIME - 2 or int(item.age * 8) % 2 == 0:
                draw_item(self.screen, item, self.t)
        for particle in self.particles:
            particle.draw(self.screen)

        self.draw_darkness()

        for item in self.items:                         # glows that show through the dark
            if item.is_hazard:
                draw_hazard_glints(self.screen, item)
            else:
                color = {"dew": TEAL, "berry": YELLOW, "petal": LAVENDER}[item.kind]
                blit_glow(self.screen, item.pos, 30, color, 0.55)
        blink_off = self.hit_cooldown > 0 and int(self.t * 12) % 2 == 0
        self.player.draw(self.screen, self.t, self.flare_active(), blink_off)
        for popup in self.popups:
            draw_text(self.screen, popup["text"], self.fonts["body"], popup["color"], popup["pos"])

        if self.flash_time > 0:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((200, 40, 60, int(110 * self.flash_time / 0.3)))
            self.screen.blit(flash, (0, 0))
        self.draw_hud()

    def draw_hud(self):
        pygame.draw.rect(self.screen, INDIGO_DARK, (0, 0, WIDTH, HUD_HEIGHT))
        pygame.draw.line(self.screen, TEAL_DARK, (0, HUD_HEIGHT - 1), (WIDTH, HUD_HEIGHT - 1), 2)
        small, hud = self.fonts["small"], self.fonts["hud"]

        draw_text(self.screen, "SCORE", small, TEXT_DIM, (24, 8), "topleft")
        draw_text(self.screen, str(self.score), hud, YELLOW, (24, 28), "topleft")

        draw_text(self.screen, "LIVES", small, TEXT_DIM, (170, 8), "topleft")
        for i in range(START_LIVES):
            center = (180 + i * 28, 42)
            if i < self.lives:
                blit_glow(self.screen, center, 14, YELLOW, 0.6)
                pygame.draw.circle(self.screen, YELLOW, center, 7)
            else:
                pygame.draw.circle(self.screen, TEXT_DIM, center, 7, 2)

        self.draw_flare_meter(pygame.Rect(300, 32, 270, 16))

        low_time = self.time_left <= 10 and int(self.t * 3) % 2 == 0
        draw_text(self.screen, "TIME", small, TEXT_DIM, (640, 8), "topleft")
        draw_text(self.screen, "%d:%02d" % divmod(int(math.ceil(self.time_left)), 60), hud,
                  RED_EYE if low_time else TEXT, (640, 28), "topleft")

        draw_text(self.screen, "LEVEL", small, TEXT_DIM, (780, 8), "topleft")
        draw_text(self.screen, "%d / 4" % self.level, hud, TEAL, (780, 28), "topleft")

    def draw_flare_meter(self, bar):
        small = self.fonts["small"]
        if self.flare_active():
            label, fraction, color = "FLARE ACTIVE  %.1fs" % self.flare_time_left, self.flare_time_left / FLARE_DURATION, YELLOW
        elif self.energy >= ENERGY_MAX:
            label, fraction, color = "FLARE READY - PRESS SPACE", 1.0, YELLOW
        else:
            label, fraction, color = "FLARE  %d%%" % self.energy, self.energy / ENERGY_MAX, TEAL
        if self.energy >= ENERGY_MAX and not self.flare_active() and int(self.t * 4) % 2 == 0:
            color = YELLOW_PALE
        draw_text(self.screen, label, small, YELLOW if fraction >= 1 or self.flare_active() else TEXT_DIM, (bar.x, 8), "topleft")
        pygame.draw.rect(self.screen, INDIGO_LIGHT, bar, border_radius=8)
        fill = bar.copy()
        fill.width = int(bar.width * fraction)
        if fill.width > 0:
            pygame.draw.rect(self.screen, color, fill, border_radius=8)
        pygame.draw.rect(self.screen, TEAL_DARK, bar, 2, border_radius=8)

    def draw_backdrop(self):
        self.screen.blit(self.background, (0, 0))
        self.draw_water_ripples()
        for fly in self.ambient_flies:
            fly.draw(self.screen, self.t)

    def draw_dim_panel(self, rect):
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 10, 26, 225), panel.get_rect(), border_radius=16)
        self.screen.blit(panel, rect.topleft)
        pygame.draw.rect(self.screen, TEAL_DARK, rect, 2, border_radius=16)

    def draw_menu(self):
        self.draw_backdrop()
        draw_text(self.screen, "FIREFLY MARSH", self.fonts["title"], YELLOW, (WIDTH // 2, 120))
        draw_text(self.screen, "a night-marsh blackout game", self.fonts["body"], TEAL, (WIDTH // 2, 190))
        blurb = "You are a firefly in a pitch-dark marsh. Only your lantern lights the way. " \
                "Collect the glowing treasures, dodge spiders and frog tongues, and light up the night with your Flare."
        for i, line in enumerate(wrap_text(blurb, self.fonts["small"], 620)):
            draw_text(self.screen, line, self.fonts["small"], TEXT, (WIDTH // 2, 238 + i * 26))
        self.draw_buttons()
        draw_text(self.screen, "Move: WASD / Arrows     Flare: SPACE     Pause: P / ESC     Start: ENTER",
                  self.fonts["small"], TEXT_DIM, (WIDTH // 2, 580))
        draw_text(self.screen, "Best score: %d" % self.high_score, self.fonts["body"], YELLOW, (WIDTH // 2, 612))

    def draw_buttons(self):
        mouse = pygame.mouse.get_pos()
        for button in self.buttons[self.state]:
            button.draw(self.screen, self.fonts["body"], mouse)

    def draw_instructions(self):
        self.draw_backdrop()
        self.draw_dim_panel(pygame.Rect(40, 24, WIDTH - 80, 530))
        small, body = self.fonts["small"], self.fonts["body"]
        draw_text(self.screen, "How to play", self.fonts["heading"], YELLOW, (WIDTH // 2, 68))
        goal = "Survive the night. Collect as much as you can before your lives or the night timer run out. " \
               "You can only see inside your lantern, but treasures and hazard eyes glow faintly in the dark."
        for i, line in enumerate(wrap_text(goal, small, 840)):
            draw_text(self.screen, line, small, TEXT, (WIDTH // 2, 116 + i * 24))

        rows = [("dew", "Dew Drop: +10 points, +20% Flare"),
                ("berry", "Glow Berry (rare): +30 points, +40% Flare"),
                ("petal", "Dawn Petal: +5 seconds (max 2:00)"),
                ("spider", "Spider: -1 life and -5 points"),
                ("tongue", "Frog Tongue: -1 life and -5 points")]
        for i, (kind, text) in enumerate(rows):
            y = 196 + i * 54
            sample = Item(kind, (0, 0), (1, 0))
            draw_item(self.screen, sample, self.t, center=(110 if kind != "tongue" else 100, y), size_scale=1.2)
            draw_text(self.screen, text, small, TEXT, (170, y), "midleft")

        draw_text(self.screen, "CONTROLS", body, TEAL, (560, 180), "topleft")
        controls = ["WASD / Arrow keys: move", "SPACE: use Flare (meter at 100%)",
                    "P or ESC: pause / resume", "ENTER: start / play again"]
        for i, line in enumerate(controls):
            draw_text(self.screen, line, small, TEXT, (560, 214 + i * 28), "topleft")
        draw_text(self.screen, "THE FLARE", body, YELLOW, (560, 340), "topleft")
        flare = "Fill the meter with treasures, then press SPACE. For 5 seconds the whole marsh is lit " \
                "and every hazard moves at half speed."
        for i, line in enumerate(wrap_text(flare, small, 360)):
            draw_text(self.screen, line, small, TEXT, (560, 372 + i * 26), "topleft")
        over = "GAME OVER: you lose all 3 lives, or the 90 second night ends. The longer you play, " \
               "the smaller your lantern and the faster the hazards (4 levels)."
        for i, line in enumerate(wrap_text(over, small, 840)):
            draw_text(self.screen, line, small, TEXT_DIM, (WIDTH // 2, 486 + i * 24))
        self.draw_buttons()

    def draw_pause(self):
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 10, 170))
        self.screen.blit(dim, (0, 0))
        draw_text(self.screen, "PAUSED", self.fonts["heading"], YELLOW, (WIDTH // 2, 230))
        draw_text(self.screen, "Press P or ESC to resume", self.fonts["small"], TEXT_DIM, (WIDTH // 2, 280))
        self.draw_buttons()

    def draw_game_over(self):
        self.draw_backdrop()
        panel = pygame.Rect(0, 0, 560, 480)
        panel.center = (WIDTH // 2, 330)
        self.draw_dim_panel(panel)
        draw_text(self.screen, "GAME OVER", self.fonts["heading"], YELLOW, (WIDTH // 2, 130))
        draw_text(self.screen, self.game_over_reason, self.fonts["small"], TEXT_DIM, (WIDTH // 2, 176))
        draw_text(self.screen, "Final score: %d" % self.score, self.fonts["heading"], TEXT, (WIDTH // 2, 240))
        high_text = "NEW BEST SCORE!" if self.new_best else "Best score: %d" % self.high_score
        draw_text(self.screen, high_text, self.fonts["body"], YELLOW if self.new_best else TEAL, (WIDTH // 2, 296))
        draw_text(self.screen, "Highest level reached: %d / 4" % self.best_level, self.fonts["body"], TEXT, (WIDTH // 2, 340))
        draw_text(self.screen, "Press ENTER to play again", self.fonts["small"], TEXT_DIM, (WIDTH // 2, 392))
        self.draw_buttons()

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "instructions":
            self.draw_instructions()
        elif self.state in ("playing", "paused"):
            self.draw_game()
            if self.state == "paused":
                self.draw_pause()
        elif self.state == "gameover":
            self.draw_game_over()

    # ---------------- main loop ----------------
    def run(self, max_frames=None):
        frames = 0
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, MAX_FRAME_TIME)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            pygame.display.flip()
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
        pygame.quit()


if __name__ == "__main__":
    # Optional:  python main.py --frames 120   (runs 120 frames then exits; used for automated checks)
    frame_limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--frames" else None
    Game().run(max_frames=frame_limit)

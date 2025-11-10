import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import pygame

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

SCREEN_WIDTH = 640  # Primary display width.
SCREEN_HEIGHT = 800  # Primary display height.
FPS = 60  # Target frames per second for the main loop.

PLAYER_SPEED = 5  # Horizontal pixels per frame when the player moves.
PLAYER_COOLDOWN = 250  # Milliseconds the player must wait between shots.

BULLET_SPEED = -8  # Upward velocity for player bullets.
ENEMY_SPEED = 1  # Baseline enemy speed used for movement calculations.
ENEMY_DROP = 24  # Vertical drop when enemies advance (unused but retained for clarity).
ENEMY_COOLDOWN = 1000  # Milliseconds between enemy shots before randomisation.
ENEMY_BULLET_SPEED = 3  # Downward velocity for enemy bullets.

STAR_COUNT = 64  # Total number of background stars.
STAR_SPEED = 1  # Pixels per frame that each star moves vertically.

ASSET_DIR = Path(__file__).with_name("assets")  # Directory holding image/font assets.
FONT_NAME = "Arial"  # Fallback system font if the custom one is missing.

PLAYER_SIZE = (48, 48)  # Expected sprite size for the player ship.
ENEMY_SIZE = (44, 44)  # Expected sprite size for enemy ships.
PLAYER_BULLET_SIZE = (6, 20)  # Expected sprite size for player bullets.
ENEMY_BULLET_SIZE = (8, 24)  # Expected sprite size for enemy bullets.


# -----------------------------------------------------------------------------
# Resource helpers
# -----------------------------------------------------------------------------

FallbackFactory = Callable[[pygame.Surface], None]


def create_surface(size: Tuple[int, int], factory: FallbackFactory) -> pygame.Surface:
    """Create a transparent surface of `size` and draw a fallback sprite using `factory`."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    factory(surface)
    return surface


def load_or_create_sprite(filename: str, size: Tuple[int, int], factory: FallbackFactory) -> pygame.Surface:
    """Load a sprite from disk if present, otherwise build it procedurally via `factory`."""
    path = ASSET_DIR / filename
    if path.exists():
        sprite = pygame.image.load(str(path)).convert_alpha()
        if sprite.get_size() != size:
            sprite = pygame.transform.smoothscale(sprite, size)
        return sprite
    return create_surface(size, factory)


def get_font(size: int) -> pygame.font.Font:
    """Retrieve the custom Galaga font, falling back to a system font when missing."""
    try:
        return pygame.font.Font(str(ASSET_DIR / "galaga.ttf"), size)
    except FileNotFoundError:
        return pygame.font.SysFont(FONT_NAME, size)


# -----------------------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------------------


@dataclass
class Entity:
    sprite: pygame.Surface
    rect: pygame.Rect

    def draw(self, surface: pygame.Surface):
        """Blit the entity's sprite onto `surface` at the stored rectangle position."""
        surface.blit(self.sprite, self.rect.topleft)


@dataclass
class Bullet(Entity):
    velocity: pygame.Vector2

    def update(self):
        """Move the bullet in-place according to its velocity vector."""
        self.rect.move_ip(self.velocity)


@dataclass
class Enemy(Entity):
    offset: float
    base_pos: pygame.Vector2
    direction: int = 1
    cooldown: int = ENEMY_COOLDOWN

    def update(self, dt: int, bullets: List["Bullet"], bullet_sprite: pygame.Surface):
        """Animate the enemy along a sine wave and fire bullets when the cooldown elapses."""
        self.offset += dt * 0.002 * self.direction
        self.rect.x = int(self.base_pos.x + math.sin(self.offset) * 80)
        self.rect.y = int(self.base_pos.y + (math.cos(self.offset) * 10))

        self.cooldown -= dt
        if self.cooldown <= 0:
            self.cooldown = ENEMY_COOLDOWN + random.randint(-200, 200)
            bullet = Bullet(
                sprite=bullet_sprite,
                rect=bullet_sprite.get_rect(midtop=self.rect.midbottom),
                velocity=pygame.Vector2(0, ENEMY_BULLET_SPEED),
            )
            bullets.append(bullet)


# -----------------------------------------------------------------------------
# Starfield
# -----------------------------------------------------------------------------


class StarField:
    def __init__(self, width: int, height: int, count: int):
        """Populate a simple scrolling star field used as the game's background."""
        self.stars = [
            pygame.Vector2(random.randrange(width), random.randrange(height))
            for _ in range(count)
        ]
        self.speed = STAR_SPEED
        self.width = width
        self.height = height

    def update(self):
        """Advance all stars vertically, wrapping them to the top once off-screen."""
        for star in self.stars:
            star.y += self.speed
            if star.y >= self.height:
                star.y = 0
                star.x = random.randrange(self.width)

    def draw(self, surface: pygame.Surface):
        """Render the star field as individual white pixels onto `surface`."""
        for star in self.stars:
            surface.fill((255, 255, 255), (int(star.x), int(star.y), 2, 2))

# -----------------------------------------------------------------------------
# Sprite factories
# -----------------------------------------------------------------------------


def build_sprite_factories() -> Dict[str, Tuple[Tuple[int, int], FallbackFactory]]:
    """Create fallback drawing factories for each sprite used by the game."""
    def player_factory(surface: pygame.Surface) -> None:
        """Draw a minimalist player ship using polygons and highlights."""
        w, h = surface.get_size()
        pygame.draw.polygon(
            surface,
            (90, 190, 255),
            [(w // 2, 4), (4, h - 4), (w - 4, h - 4)],
        )
        pygame.draw.polygon(
            surface,
            (255, 255, 255, 120),
            [(w // 2, 8), (w // 2 - 6, h - 8), (w // 2 + 6, h - 8)],
        )
        pygame.draw.circle(surface, (255, 120, 120), (w // 2, h // 2 + 4), 6)

    def enemy_factory(surface: pygame.Surface) -> None:
        """Draw a circular enemy with contrasting cockpit and body details."""
        w, h = surface.get_size()
        pygame.draw.circle(surface, (255, 60, 90), (w // 2, h // 2), w // 2 - 4)
        pygame.draw.circle(surface, (255, 190, 70), (w // 2, h // 2 - 6), 10)
        pygame.draw.rect(surface, (40, 0, 90), (w // 2 - 6, h // 2 + 4, 12, 12), border_radius=4)
        pygame.draw.line(surface, (255, 220, 220), (8, h // 2), (w - 8, h // 2), 3)

    def player_bullet_factory(surface: pygame.Surface) -> None:
        """Draw a bright rectangular projectile for the player."""
        w, h = surface.get_size()
        pygame.draw.rect(surface, (120, 255, 120), (0, 0, w, h), border_radius=2)
        pygame.draw.rect(surface, (255, 255, 255), (1, 1, w - 2, h - 2), border_radius=2)

    def enemy_bullet_factory(surface: pygame.Surface) -> None:
        """Draw a heavier-looking projectile to distinguish enemy fire."""
        w, h = surface.get_size()
        pygame.draw.rect(surface, (255, 210, 80), (0, 0, w, h), border_radius=3)
        pygame.draw.rect(surface, (200, 80, 0), (1, h // 3, w - 2, h // 3), border_radius=2)

    return {
        "player.png": (PLAYER_SIZE, player_factory),
        "enemy.png": (ENEMY_SIZE, enemy_factory),
        "player_bullet.png": (PLAYER_BULLET_SIZE, player_bullet_factory),
        "enemy_bullet.png": (ENEMY_BULLET_SIZE, enemy_bullet_factory),
    }


# -----------------------------------------------------------------------------
# Game
# -----------------------------------------------------------------------------


class GalagaGame:
    def __init__(self):
        """Initialise pygame, load resources, and prepare the first gameplay state."""
        pygame.init()
        pygame.display.set_caption("Mini Galaga")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.background = StarField(SCREEN_WIDTH, SCREEN_HEIGHT, STAR_COUNT)
        self.font_small = get_font(24)
        self.font_large = get_font(48)

        factories = build_sprite_factories()
        self.player_sprite = load_or_create_sprite("player.png", *factories["player.png"])
        self.enemy_sprite = load_or_create_sprite("enemy.png", *factories["enemy.png"])
        self.bullet_sprite = load_or_create_sprite("player_bullet.png", *factories["player_bullet.png"])
        self.enemy_bullet_sprite = load_or_create_sprite("enemy_bullet.png", *factories["enemy_bullet.png"])

        self.reset()

    def reset(self):
        """Restore the game to its initial values and spawn a fresh enemy wave."""
        self.running = True
        self.player = Entity(
            sprite=self.player_sprite,
            rect=self.player_sprite.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)),
        )
        self.player_bullets: List[Bullet] = []
        self.enemy_bullets: List[Bullet] = []
        self.enemies: List[Enemy] = []
        self.score = 0
        self.lives = 3
        self.player_timer = 0
        self.wave = 1
        self.spawn_wave()

    def spawn_wave(self):
        """Populate the playfield with a formation of enemies based on the current wave."""
        cols = 6
        rows = 3 + min(self.wave, 3)
        gap_x = SCREEN_WIDTH // (cols + 1)
        gap_y = 60

        for row in range(rows):
            for col in range(cols):
                x = gap_x * (col + 1)
                y = 80 + row * gap_y
                enemy = Enemy(
                    sprite=self.enemy_sprite,
                    rect=self.enemy_sprite.get_rect(center=(x, y)),
                    offset=random.uniform(0, math.tau),
                    base_pos=pygame.Vector2(x, y),
                )
                self.enemies.append(enemy)

    def run(self):
        """Main loop that keeps the game running until the user quits or loses."""
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()

    # -------------------------------------------------------------------------
    # Loop stages
    # -------------------------------------------------------------------------

    def handle_events(self):
        """Process pygame events and stop the loop if the window is closed."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt: int):
        """Advance all game actors, manage waves, and check for end conditions."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.running = False

        self.background.update()
        self.update_player(dt, keys)
        self.update_bullets()
        self.update_enemies(dt)
        self.handle_collisions()

        if not self.enemies:
            self.wave += 1
            self.spawn_wave()

        if self.lives <= 0:
            self.running = False

    def draw(self):
        """Render the entire scene, including the HUD and optional game-over screen."""
        self.screen.fill((0, 0, 16))
        self.background.draw(self.screen)

        for bullet in self.player_bullets:
            bullet.draw(self.screen)
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)

        self.player.draw(self.screen)

        hud = self.font_small.render(f"Score: {self.score}   Lives: {self.lives}", True, (255, 255, 255))
        self.screen.blit(hud, (20, 20))

        if self.lives <= 0:
            text = self.font_large.render("Game Over", True, (255, 64, 64))
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)

        pygame.display.flip()

    # -------------------------------------------------------------------------
    # Update helpers
    # -------------------------------------------------------------------------

    def update_player(self, dt: int, keys):
        """Handle player input, apply movement bounds, and spawn bullets on fire."""
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * PLAYER_SPEED
        new_x = self.player.rect.x + dx
        self.player.rect.x = max(0, min(SCREEN_WIDTH - self.player.rect.width, new_x))

        self.player_timer += dt
        if keys[pygame.K_SPACE] and self.player_timer >= PLAYER_COOLDOWN:
            self.player_timer = 0
            bullet = Bullet(
                sprite=self.bullet_sprite,
                rect=self.bullet_sprite.get_rect(midbottom=self.player.rect.midtop),
                velocity=pygame.Vector2(0, BULLET_SPEED),
            )
            self.player_bullets.append(bullet)

    def update_bullets(self):
        """Advance all bullets and cull those that leave the play area."""
        for bullet_list in (self.player_bullets, self.enemy_bullets):
            for bullet in bullet_list[:]:
                bullet.update()
                if bullet.rect.bottom < 0 or bullet.rect.top > SCREEN_HEIGHT:
                    bullet_list.remove(bullet)

    def update_enemies(self, dt: int):
        """Update enemy movement patterns and occasionally flip their direction."""
        for enemy in self.enemies:
            enemy.update(dt, self.enemy_bullets, self.enemy_bullet_sprite)
            if random.random() < 0.005:
                enemy.direction *= -1

    def handle_collisions(self):
        """Resolve bullet collisions, update score and lives, and reset positions."""
        # Player bullets vs enemies
        for bullet in self.player_bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    self.player_bullets.remove(bullet)
                    self.enemies.remove(enemy)
                    self.score += 100
                    break

        # Enemy bullets vs player
        for bullet in self.enemy_bullets[:]:
            if bullet.rect.colliderect(self.player.rect):
                self.enemy_bullets.remove(bullet)
                self.lives -= 1
                self.player.rect.midbottom = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)
                break

        # Enemies reaching bottom
        for enemy in self.enemies[:]:
            if enemy.rect.bottom >= SCREEN_HEIGHT - 40:
                self.enemies.remove(enemy)
                self.lives -= 1


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    # Launch the arcade loop when executed as a script.
    GalagaGame().run()


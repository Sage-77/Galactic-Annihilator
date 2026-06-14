import pygame
import random
import sys
import math
import array
import json
import os

# --- Constants & Configuration ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

# Cyberpunk-inspired Palette
BLACK = (5, 5, 12)
DARK_BLUE = (10, 15, 30)
WHITE = (245, 245, 255)
CYAN = (0, 255, 240)
MAGENTA = (255, 0, 128)
YELLOW = (255, 230, 0)
RED = (255, 30, 70)
GREEN = (10, 255, 120)
PURPLE = (150, 0, 255)
ORANGE = (255, 100, 0)

# --- Procedural Audio Synth Engine ---
class SoundEngine:
    """Generates and plays retro sci-fi sounds procedurally without using external audio files."""
    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.shoot_sound = self._synth_sound(880, 220, 0.12, "sine", 0.15)
            self.laser_heavy_sound = self._synth_sound(400, 80, 0.25, "saw", 0.2)
            self.hit_sound = self._synth_sound(350, 100, 0.08, "noise", 0.25)
            self.explosion_sound = self._synth_sound(200, 30, 0.4, "noise", 0.45)
            self.powerup_sound = self._synth_sound(300, 900, 0.3, "sine", 0.2)
            self.boss_spawn_sound = self._synth_sound(90, 45, 0.9, "saw", 0.4)
            self.shield_down_sound = self._synth_sound(600, 100, 0.25, "square", 0.15)
            self.missile_launch = self._synth_sound(200, 600, 0.2, "saw", 0.15)
        except Exception:
            self.enabled = False

    def _synth_sound(self, f_start, f_end, duration, wave_type="sine", volume=0.5):
        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * num_samples)
        for i in range(num_samples):
            t = i / sample_rate
            freq = f_start + (f_end - f_start) * (t / duration)
            val = 0.0
            if wave_type == "sine":
                val = math.sin(2 * math.pi * freq * t)
            elif wave_type == "square":
                val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
            elif wave_type == "saw":
                val = 2.0 * (t * freq - math.floor(0.5 + t * freq))
            elif wave_type == "noise":
                val = random.uniform(-1, 1)

            # Smooth exponential decay
            env = math.exp(-3 * (t / duration)) * (1.0 - (t / duration))
            sample = int(val * env * volume * 32767)
            buf[i] = max(-32768, min(32767, sample))
        return pygame.mixer.Sound(buffer=buf)

    def play(self, sound_name):
        if not self.enabled:
            return
        sound = getattr(self, f"{sound_name}_sound", None)
        if sound:
            sound.play()


# --- Vector Art Pre-render Engine ---
class AssetCache:
    """Pre-renders procedural vector artwork onto cached alpha surfaces for optimum rendering performance."""
    def __init__(self):
        self.cache = {}
        self._build_assets()

    def _build_assets(self):
        # 1. Player Ship
        surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        self._draw_glow_poly(surf, CYAN, [(24, 2), (2, 42), (18, 32), (24, 44), (30, 32), (46, 42)])
        pygame.draw.line(surf, WHITE, (24, 8), (24, 28), 2)
        self.cache["player_ship"] = surf

        # 2. Enemy Scout
        surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        self._draw_glow_poly(surf, RED, [(18, 34), (4, 10), (14, 2), (22, 2), (32, 10)])
        pygame.draw.circle(surf, WHITE, (18, 14), 4)
        self.cache["enemy_scout"] = surf

        # 3. Enemy Interceptor
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        self._draw_glow_poly(surf, PURPLE, [(20, 38), (2, 16), (10, 2), (30, 2), (38, 16)])
        pygame.draw.line(surf, CYAN, (10, 10), (30, 10), 3)
        self.cache["enemy_interceptor"] = surf

        # 4. Enemy Bomber
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        self._draw_glow_poly(surf, ORANGE, [(25, 46), (4, 15), (12, 4), (38, 4), (46, 15)])
        pygame.draw.rect(surf, YELLOW, (18, 16, 14, 14), 2)
        self.cache["enemy_bomber"] = surf

        # 5. Alien Overlord Boss
        surf = pygame.Surface((180, 120), pygame.SRCALPHA)
        self._draw_glow_poly(surf, MAGENTA, [(90, 115), (20, 40), (45, 10), (135, 10), (160, 40)])
        self._draw_glow_poly(surf, RED, [(90, 80), (60, 40), (120, 40)], 3)
        pygame.draw.circle(surf, GREEN, (90, 45), 12)
        self.cache["enemy_boss"] = surf

        # 6. Shield Power-up Indicator
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(surf, CYAN, (16, 16), 14, 3)
        pygame.draw.polygon(surf, WHITE, [(16, 8), (10, 14), (13, 22), (16, 25), (19, 22), (22, 14)])
        self.cache["powerup_shield"] = surf

        # 7. Spread-shot Power-up Indicator
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(surf, YELLOW, (16, 16), 14, 3)
        pygame.draw.polygon(surf, WHITE, [(16, 6), (10, 16), (22, 16)])
        pygame.draw.polygon(surf, WHITE, [(10, 16), (4, 24), (16, 24)])
        pygame.draw.polygon(surf, WHITE, [(22, 16), (16, 24), (28, 24)])
        self.cache["powerup_spread"] = surf

        # 8. Plasma Power-up Indicator
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(surf, GREEN, (16, 16), 14, 3)
        pygame.draw.circle(surf, WHITE, (16, 16), 7)
        self.cache["powerup_plasma"] = surf

        # 9. Missile Power-up Indicator
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(surf, PURPLE, (16, 16), 14, 3)
        pygame.draw.rect(surf, WHITE, (13, 8, 6, 16))
        pygame.draw.polygon(surf, RED, [(16, 4), (11, 8), (21, 8)])
        self.cache["powerup_missile"] = surf

    def _draw_glow_poly(self, surface, color, points, glow_radius=4):
        for r in range(glow_radius, 0, -1):
            alpha_color = (*color[:3], int(150 / (r * 1.8)))
            pygame.draw.polygon(surface, alpha_color, points, r * 2)
        pygame.draw.polygon(surface, color, points, 0)
        pygame.draw.polygon(surface, WHITE, points, 2)

    def get(self, name):
        return self.cache.get(name)


# --- Visual Polish: Particle Systems ---
class Particle(pygame.sprite.Sprite):
    """Individually calculated dynamic particle for highly explosive and engine thruster effects."""
    def __init__(self, x, y, dx, dy, color, size, decay, gravity=0.0):
        super().__init__()
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.color = color
        self.rect = self.image.get_rect(center=(x, y))
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.dx = dx
        self.dy = dy
        self.alpha = 255
        self.decay = decay
        self.size = size
        self.gravity = gravity
        self._render()

    def _render(self):
        self.image.fill((0, 0, 0, 0))
        cur_color = (*self.color[:3], int(self.alpha))
        pygame.draw.circle(self.image, cur_color, (self.size // 2, self.size // 2), self.size // 2)

    def update(self):
        self.pos_x += self.dx
        self.pos_y += self.dy
        self.dy += self.gravity
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        self.alpha -= self.decay
        if self.alpha <= 0:
            self.kill()
        else:
            self._render()


class Shockwave(pygame.sprite.Sprite):
    """Expanding vector circle wave triggered by dynamic impacts or massive explosions."""
    def __init__(self, x, y, max_radius, color, thickness=3):
        super().__init__()
        self.x = x
        self.y = y
        self.radius = 5.0
        self.max_radius = max_radius
        self.color = color
        self.thickness = thickness
        self.image = pygame.Surface((max_radius * 2, max_radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.radius += 4.5
        if self.radius >= self.max_radius:
            self.kill()
            return

        self.image.fill((0, 0, 0, 0))
        alpha = int(255 * (1.0 - (self.radius / self.max_radius)))
        draw_color = (*self.color[:3], max(0, min(255, alpha)))
        pygame.draw.circle(self.image, draw_color, (self.max_radius, self.max_radius), int(self.radius), self.thickness)


class FloatingText(pygame.sprite.Sprite):
    """Dynamic indicators presenting score increases and system warnings."""
    def __init__(self, x, y, text, color, size=24, speed_y=-2.0):
        super().__init__()
        font = pygame.font.SysFont("Trebuchet MS", size, bold=True)
        self.image = font.render(text, True, color)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos_y = float(y)
        self.speed_y = speed_y
        self.alpha = 255

    def update(self):
        self.pos_y += self.speed_y
        self.rect.centery = int(self.pos_y)
        self.alpha -= 6
        if self.alpha <= 0:
            self.kill()
        else:
            # Re-render text with alpha modulation
            temp = self.image.copy()
            alpha_surf = pygame.Surface(temp.get_size(), pygame.SRCALPHA)
            alpha_surf.fill((255, 255, 255, self.alpha))
            temp.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.image = temp


# --- Entities: Projectiles ---
class Bullet(pygame.sprite.Sprite):
    """Custom standard, plasma, and high-velocity physical projectiles."""
    def __init__(self, x, y, speed_y, color, width=4, height=14, damage=1, penetrative=False):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.color = color
        self.damage = damage
        self.penetrative = penetrative

        # Core bullet graphic + outer glow
        pygame.draw.rect(self.image, (*color[:3], 100), (0, 0, width, height), border_radius=2)
        pygame.draw.rect(self.image, WHITE, (width // 4, 1, width // 2, height - 2), border_radius=2)

        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = speed_y

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.bottom < -20 or self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


class HomingMissile(pygame.sprite.Sprite):
    """A self-guided missile locking on target with cinematic flame trails."""
    def __init__(self, x, y, target_group, particle_group):
        super().__init__()
        self.image = pygame.Surface((12, 24), pygame.SRCALPHA)
        # Structural design
        pygame.draw.rect(self.image, WHITE, (4, 4, 4, 16))
        pygame.draw.polygon(self.image, PURPLE, [(6, 0), (3, 5), (9, 5)])
        pygame.draw.polygon(self.image, RED, [(2, 16), (4, 20), (2, 22)])
        pygame.draw.polygon(self.image, RED, [(10, 16), (8, 20), (10, 22)])

        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, -5)
        self.target_group = target_group
        self.particle_group = particle_group
        self.damage = 3
        self.target = None

    def _find_target(self):
        if self.target_group:
            # Target the enemy closest to missile origin
            closest_enemy = None
            min_dist = 99999
            for enemy in self.target_group:
                dist = self.pos.distance_to(enemy.rect.center)
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
            self.target = closest_enemy

    def update(self):
        if not self.target or not self.target.alive():
            self._find_target()

        if self.target:
            target_vector = pygame.math.Vector2(self.target.rect.center) - self.pos
            if target_vector.length() > 0:
                target_vector = target_vector.normalize() * 8.0
                # Smooth steering calculation
                self.velocity = self.velocity * 0.90 + target_vector * 0.10
        else:
            # Continue drifting upwards
            self.velocity = self.velocity * 0.98 + pygame.math.Vector2(0, -8.0) * 0.02

        self.pos += self.velocity
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Trail combustion generation
        if random.random() < 0.6:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, 1.5)
            dx = math.sin(angle) * speed - self.velocity.x * 0.2
            dy = -self.velocity.y * 0.3 + random.uniform(0, 1)
            p = Particle(self.rect.centerx, self.rect.bottom, dx, dy, ORANGE, 6, 12)
            self.particle_group.add(p)

        if self.rect.bottom < -20 or self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


# --- Entities: Power-ups ---
class PowerUp(pygame.sprite.Sprite):
    """Procedural drop items granting major defensive or offensive buffs."""
    def __init__(self, x, y, asset_cache):
        super().__init__()
        self.types = ["shield", "spread", "plasma", "missile"]
        self.type = random.choice(self.types)
        self.image = asset_cache.get(f"powerup_{self.type}")
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = 2.5
        self.float_offset = random.uniform(0, 100)

    def update(self):
        self.rect.y += self.speed_y
        # Subtle levitating wiggle
        self.rect.x += math.sin(pygame.time.get_ticks() * 0.01 + self.float_offset) * 0.6
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


# --- Entities: Enemies ---
class Enemy(pygame.sprite.Sprite):
    """Base class hosting physical characteristics, attack behavior, and score structures."""
    def __init__(self, x, y, tier, asset_cache):
        super().__init__()
        self.tier = tier
        self.anim_offset = random.uniform(0, 100)

        if self.tier == "scout":
            self.image_base = asset_cache.get("enemy_scout")
            self.max_hp = 1
            self.score_value = 100
            self.shoot_cooldown = random.randint(2000, 4000)
        elif self.tier == "interceptor":
            self.image_base = asset_cache.get("enemy_interceptor")
            self.max_hp = 2
            self.score_value = 250
            self.shoot_cooldown = random.randint(1500, 3000)
        elif self.tier == "bomber":
            self.image_base = asset_cache.get("enemy_bomber")
            self.max_hp = 4
            self.score_value = 500
            self.shoot_cooldown = random.randint(2500, 4500)

        self.image = self.image_base.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = self.max_hp
        self.last_shot = pygame.time.get_ticks() + random.randint(0, 1000)
        self.hit_timer = 0

    def update(self):
        self._apply_hover_effect()
        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer == 0:
                self.image = self.image_base.copy()

    def _apply_hover_effect(self):
        # Micro-scaling animation
        scale = 1.0 + math.sin(pygame.time.get_ticks() * 0.01 + self.anim_offset) * 0.04
        w = int(self.image_base.get_width() * scale)
        h = int(self.image_base.get_height() * scale)
        center = self.rect.center
        self.image = pygame.transform.scale(self.image_base, (w, h))
        self.rect = self.image.get_rect(center=center)

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_timer = 4
        # Turn white to indicate hit state
        white_mask = pygame.Surface(self.image_base.get_size(), pygame.SRCALPHA)
        white_mask.fill((255, 255, 255, 180))
        self.image.blit(white_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return self.hp <= 0


class EnemyBoss(pygame.sprite.Sprite):
    """The formidable Alien Overlord with automated phase management and massive structural shields."""
    def __init__(self, asset_cache):
        super().__init__()
        self.image_base = asset_cache.get("enemy_boss")
        self.image = self.image_base.copy()
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, -150))
        self.target_y = 150
        self.max_hp = 80
        self.hp = self.max_hp
        self.score_value = 10000
        self.last_attack_time = pygame.time.get_ticks()
        self.attack_cooldown = 2000
        self.phase = 1
        self.hit_timer = 0
        self.speed_x = 2.5
        self.shield_up = True
        self.shield_hp = 30
        self.max_shield_hp = 30

    def update(self):
        # Introductory descent logic
        if self.rect.centery < self.target_y:
            self.rect.centery += 2
        else:
            # Strafe movement back and forth
            self.rect.x += self.speed_x
            if self.rect.right > SCREEN_WIDTH - 20 or self.rect.left < 20:
                self.speed_x *= -1

        # Phase transition based on HP
        if self.hp < self.max_hp * 0.4:
            self.phase = 3
            self.attack_cooldown = 900
        elif self.hp < self.max_hp * 0.7:
            self.phase = 2
            self.attack_cooldown = 1400

        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer == 0:
                self.image = self.image_base.copy()

    def take_damage(self, amount):
        if self.shield_up:
            self.shield_hp -= amount
            if self.shield_hp <= 0:
                self.shield_up = False
                return -1 # Shield destroyed indicator
            return 0 # Damaged but shield held
        else:
            self.hp -= amount
            self.hit_timer = 3
            white_mask = pygame.Surface(self.image_base.get_size(), pygame.SRCALPHA)
            white_mask.fill((255, 255, 255, 150))
            self.image.blit(white_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            return self.hp <= 0


# --- Entities: Player Ship ---
class Player(pygame.sprite.Sprite):
    """Primary operational fighter with full status, weapons, and thruster dynamics."""
    def __init__(self, all_sprites, bullets, enemy_group, particles, asset_cache):
        super().__init__()
        self.all_sprites = all_sprites
        self.bullets = bullets
        self.enemy_group = enemy_group
        self.particles = particles
        self.asset_cache = asset_cache

        self.image_base = asset_cache.get("player_ship")
        self.image = self.image_base.copy()
        self.rect = self.image.get_rect(centerx=SCREEN_WIDTH // 2, bottom=SCREEN_HEIGHT - 30)

        # Smooth positional physics
        self.pos_x = float(self.rect.centerx)
        self.vel_x = 0.0
        self.speed = 1.0
        self.friction = 0.88
        self.max_speed = 9.0

        # Operational status meters
        self.lives = 3
        self.score = 0
        self.max_shield = 100
        self.shield = 100
        self.shoot_cooldown = 180
        self.last_shot = 0

        # Dynamic weapon statuses
        self.active_powerup = None
        self.powerup_timer = 0
        self.roll_angle = 0.0

    def update(self):
        self._handle_movement()
        self._emit_thruster_particles()
        self._update_powerup_states()

    def _handle_movement(self):
        keys = pygame.key.get_pressed()
        move_dir = 0
        if keys[pygame.K_LEFT]:
            move_dir -= 1
        if keys[pygame.K_RIGHT]:
            move_dir += 1

        # Smooth acceleration
        self.vel_x += move_dir * self.speed
        self.vel_x *= self.friction

        # Bound check velocities
        if self.vel_x > self.max_speed:
            self.vel_x = self.max_speed
        elif self.vel_x < -self.max_speed:
            self.vel_x = -self.max_speed

        self.pos_x += self.vel_x
        self.rect.centerx = int(self.pos_x)

        # Dynamic screen border lock
        if self.rect.left < 10:
            self.rect.left = 10
            self.pos_x = float(self.rect.centerx)
            self.vel_x = 0
        if self.rect.right > SCREEN_WIDTH - 10:
            self.rect.right = SCREEN_WIDTH - 10
            self.pos_x = float(self.rect.centerx)
            self.vel_x = 0

        # Rotate graphic slightly based on lateral velocity
        self.roll_angle = -self.vel_x * 2.5
        self.image = pygame.transform.rotate(self.image_base, self.roll_angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def _emit_thruster_particles(self):
        # Flickering rocket emissions at base of the engine
        if random.random() < 0.72:
            colors = [CYAN, WHITE, DARK_BLUE]
            color = random.choice(colors)
            dx = random.uniform(-1.0, 1.0) - self.vel_x * 0.1
            dy = random.uniform(2.5, 4.5)
            # Spawn slightly behind the central vector point
            p = Particle(self.rect.centerx + random.randint(-4, 4), self.rect.bottom - 4, dx, dy, color, 8, 14)
            self.particles.add(p)

    def _update_powerup_states(self):
        if self.active_powerup:
            if pygame.time.get_ticks() > self.powerup_timer:
                self.active_powerup = None

    def shoot(self, sound_engine):
        now = pygame.time.get_ticks()
        # Rapid weapon systems firing modifier
        cooldown = self.shoot_cooldown
        if self.active_powerup == "spread" or self.active_powerup == "plasma":
            cooldown = self.shoot_cooldown * 0.75

        if now - self.last_shot > cooldown:
            self.last_shot = now
            if self.active_powerup == "spread":
                sound_engine.play("shoot")
                b1 = Bullet(self.rect.centerx, self.rect.top, -12, YELLOW, damage=1)
                b2 = Bullet(self.rect.left + 5, self.rect.top + 8, -11, YELLOW, damage=1)
                b3 = Bullet(self.rect.right - 5, self.rect.top + 8, -11, YELLOW, damage=1)
                # Apply trajectory offsets to lateral shots
                b2.update = lambda self=b2: (setattr(self.rect, 'x', self.rect.x - 2), setattr(self.rect, 'y', self.rect.y + self.speed_y))
                b3.update = lambda self=b3: (setattr(self.rect, 'x', self.rect.x + 2), setattr(self.rect, 'y', self.rect.y + self.speed_y))
                self.all_sprites.add(b1, b2, b3)
                self.bullets.add(b1, b2, b3)

            elif self.active_powerup == "plasma":
                sound_engine.play("laser_heavy")
                # Massive penetrating projectile
                b = Bullet(self.rect.centerx, self.rect.top, -8, GREEN, width=12, height=22, damage=2, penetrative=True)
                self.all_sprites.add(b)
                self.bullets.add(b)

            elif self.active_powerup == "missile":
                sound_engine.play("missile_launch")
                m1 = HomingMissile(self.rect.left, self.rect.centery, self.enemy_group, self.particles)
                m2 = HomingMissile(self.rect.right, self.rect.centery, self.enemy_group, self.particles)
                self.all_sprites.add(m1, m2)
                self.bullets.add(m1, m2)

            else:
                sound_engine.play("shoot")
                b = Bullet(self.rect.centerx, self.rect.top, -12, CYAN, damage=1)
                self.all_sprites.add(b)
                self.bullets.add(b)

    def apply_powerup(self, p_type, sound_engine):
        sound_engine.play("powerup")
        if p_type == "shield":
            self.shield = min(self.max_shield, self.shield + 40)
        else:
            self.active_powerup = p_type
            self.powerup_timer = pygame.time.get_ticks() + 8000 # 8 Seconds operation window


# --- Leaderboard Persistent Manager ---
class Leaderboard:
    """Saves and aggregates local high score achievements using highly accessible JSON files."""
    def __init__(self, filename="highscores.json"):
        self.filename = filename
        self.scores = self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return sorted(json.load(f), reverse=True)[:5]
            except Exception:
                return [0, 0, 0, 0, 0]
        return [0, 0, 0, 0, 0]

    def check_high_score(self, score):
        if score > self.scores[-1]:
            self.scores.append(score)
            self.scores = sorted(self.scores, reverse=True)[:5]
            self.save()
            return True
        return False

    def save(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.scores, f)
        except Exception:
            pass


# --- Main Game Manager Loop ---
class Game:
    """The central loop driving mechanics, UI overlays, visual effects, and game state transitions."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Galactic Annihilator: Re-Engineered")
        self.clock = pygame.time.Clock()
        self.sound_engine = SoundEngine()
        self.assets = AssetCache()
        self.leaderboard = Leaderboard()

        self.game_state = "MENU"
        self.running = True

        # Configurable environment assets
        self.stars_layer1 = [{'x': random.randint(0, SCREEN_WIDTH), 'y': random.randint(0, SCREEN_HEIGHT)} for _ in range(120)]
        self.stars_layer2 = [{'x': random.randint(0, SCREEN_WIDTH), 'y': random.randint(0, SCREEN_HEIGHT)} for _ in range(60)]
        self.stars_layer3 = [{'x': random.randint(0, SCREEN_WIDTH), 'y': random.randint(0, SCREEN_HEIGHT)} for _ in range(25)]

        self.screen_shake = 0
        self.combo_counter = 0
        self.combo_timer = 0
        self.highest_combo = 0

    def init_level(self, level=1):
        self.level = level
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()

        # Build user craft
        self.player = Player(self.all_sprites, self.bullets, self.enemies, self.particles, self.assets)
        if hasattr(self, 'saved_score'):
            self.player.score = self.saved_score
            self.player.lives = self.saved_lives
            self.player.shield = self.saved_shield
        self.all_sprites.add(self.player)

        # Spawning wave generation
        if level % 5 == 0:
            # Dynamic Mega Boss Combat Arena
            self.boss = EnemyBoss(self.assets)
            self.all_sprites.add(self.boss)
            self.enemies.add(self.boss)
            self.sound_engine.play("boss_spawn")
        else:
            self._generate_wave()

        self.wave_transition_ticks = pygame.time.get_ticks() + 1500

    def _generate_wave(self):
        # Programmatically scales structure distribution as standard level counts rise
        rows = min(5, 2 + (self.level // 3))
        cols = min(12, 6 + (self.level // 2))
        spacing_x = 65
        spacing_y = 50
        offset_x = (SCREEN_WIDTH - (cols * spacing_x)) // 2
        offset_y = 70

        for r in range(rows):
            for c in range(cols):
                grid_x = offset_x + c * spacing_x + random.randint(-4, 4)
                grid_y = offset_y + r * spacing_y + random.randint(-4, 4)

                # Tier probability distribution logic
                weight = random.random() + (self.level * 0.05)
                if weight > 1.25:
                    tier = "bomber"
                elif weight > 0.85:
                    tier = "interceptor"
                else:
                    tier = "scout"

                enemy = Enemy(grid_x, grid_y, tier, self.assets)
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)

    def trigger_explosion(self, x, y, size=30, color=ORANGE):
        self.screen_shake = max(self.screen_shake, int(size * 0.4))
        # Emit shockwave
        s = Shockwave(x, y, size * 2, color, thickness=2)
        self.particles.add(s)

        # Build structural combustion core
        for _ in range(size):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 7.0)
            dx = math.sin(angle) * speed
            dy = math.cos(angle) * speed
            decay = random.randint(6, 15)
            p = Particle(x, y, dx, dy, color, random.randint(4, 10), decay)
            self.particles.add(p)

    def trigger_sparks(self, x, y, dx, dy, color):
        for _ in range(5):
            angle = random.uniform(-0.5, 0.5)
            speed = random.uniform(2.0, 5.0)
            p_dx = math.sin(angle) * speed + dx * 0.3
            p_dy = -math.cos(angle) * speed + dy * 0.3
            p = Particle(x, y, p_dx, p_dy, color, random.randint(3, 5), 18)
            self.particles.add(p)

    def draw_background(self):
        self.screen.fill(BLACK)

        # Starfield Parallax calculations
        for star in self.stars_layer1:
            star['y'] += 0.5
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, SCREEN_WIDTH)
            pygame.draw.circle(self.screen, (100, 100, 150), (int(star['x']), int(star['y'])), 1)

        for star in self.stars_layer2:
            star['y'] += 1.2
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, SCREEN_WIDTH)
            pygame.draw.circle(self.screen, (180, 180, 220), (int(star['x']), int(star['y'])), 1)

        for star in self.stars_layer3:
            star['y'] += 3.0
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, SCREEN_WIDTH)
            pygame.draw.circle(self.screen, CYAN, (int(star['x']), int(star['y'])), 2)

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.draw_background()

            if self.game_state == "MENU":
                self._handle_menu_events()
                self._draw_menu()
            elif self.game_state == "PLAYING":
                self._handle_playing_events()
                self._update_playing()
                self._draw_playing()
            elif self.game_state == "GAMEOVER":
                self._handle_gameover_events()
                self._draw_gameover()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # --- Start Menu Routines ---
    def _handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Clean operational initialization
                    self.saved_score = 0
                    self.saved_lives = 3
                    self.saved_shield = 100
                    self.init_level(1)
                    self.game_state = "PLAYING"

    def _draw_menu(self):
        # Cosmic aesthetic glow panels
        now_ms = pygame.time.get_ticks()
        pulse = int(180 + 75 * math.sin(now_ms * 0.005))

        # Title Block
        font_title = pygame.font.SysFont("Lucida Console", 56, bold=True)
        title_surf = font_title.render("GALACTIC ANNIHILATOR", True, CYAN)
        # Offset drop shadow
        title_shadow = font_title.render("GALACTIC ANNIHILATOR", True, (0, int(pulse * 0.5), int(pulse * 0.6)))
        self.screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title_shadow.get_width() // 2 + 3, SCREEN_HEIGHT // 4 + 3))
        self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, SCREEN_HEIGHT // 4))

        # Subtitle Action Info
        font_sub = pygame.font.SysFont("Trebuchet MS", 22, bold=False)
        sub_text = font_sub.render("UPGRADED TO ULTIMATE MASTERPIECE EDITION", True, MAGENTA)
        self.screen.blit(sub_text, (SCREEN_WIDTH // 2 - sub_text.get_width() // 2, SCREEN_HEIGHT // 4 + 75))

        # Interactive Enter to Start message
        font_action = pygame.font.SysFont("Lucida Console", 24, bold=True)
        act_color = (pulse, pulse, pulse)
        action_surf = font_action.render("PRESS ENTER TO LAUNCH FIGHTER", True, act_color)
        self.screen.blit(action_surf, (SCREEN_WIDTH // 2 - action_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        # Controls panel
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 + 100, 440, 120)
        pygame.draw.rect(self.screen, DARK_BLUE, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, CYAN, panel_rect, 2, border_radius=8)

        ctrl_font = pygame.font.SysFont("Courier New", 18, bold=True)
        ctrls = [
            "[LEFT / RIGHT ARROWS] - Shift Ship Lateral Thrust",
            "[SPACEBAR]          - Primary Fire Cannons",
            "[S/R/M/P ORBS]       - Weapon Overcharges",
            "Developed by: Sage"
        ]
        for idx, line in enumerate(ctrls):
            text_color = WHITE if idx < 3 else YELLOW
            c_surf = ctrl_font.render(line, True, text_color)
            self.screen.blit(c_surf, (panel_rect.x + 20, panel_rect.y + 15 + idx * 24))

        # Top High Scores list
        score_font = pygame.font.SysFont("Lucida Console", 16)
        lbl = score_font.render("--- SYSTEM TOP RECORDFILE ---", True, GREEN)
        self.screen.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, SCREEN_HEIGHT - 90))
        for idx, score in enumerate(self.leaderboard.scores):
            entry = score_font.render(f"TOP #{idx+1}: {score:06d} PTS", True, CYAN if idx == 0 else WHITE)
            self.screen.blit(entry, (SCREEN_WIDTH // 2 - entry.get_width() // 2, SCREEN_HEIGHT - 70 + idx * 16))

    # --- Core Gameplay Loop Routines ---
    def _handle_playing_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = "MENU"

        # Continuous fire tracking
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.player.shoot(self.sound_engine)

    def _update_playing(self):
        # Update high-performance sprites and systems
        self.all_sprites.update()
        self.particles.update()

        # Update scoring combos
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo_counter = 0

        # --- Dynamic Collision Processing ---

        # 1. Player shots impacting Standard Enemies
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, False, False)
        for enemy, bullet_list in hits.items():
            if isinstance(enemy, EnemyBoss):
                continue  # Bosses are handled separately below

            for bullet in bullet_list:
                if bullet.penetrative:
                    if bullet not in getattr(enemy, 'hit_by', []):
                        if not hasattr(enemy, 'hit_by'):
                            enemy.hit_by = []
                        enemy.hit_by.append(bullet)
                        is_dead = enemy.take_damage(bullet.damage)
                        self._handle_enemy_impact(enemy, bullet.rect.center, is_dead)
                else:
                    is_dead = enemy.take_damage(bullet.damage)
                    bullet.kill()
                    self._handle_enemy_impact(enemy, bullet.rect.center, is_dead)

        # 2. Player shots impacting Mega Bosses
        for bullet in self.bullets:
            if hasattr(self, 'boss') and self.boss.alive():
                if self.boss.rect.colliderect(bullet.rect):
                    result = self.boss.take_damage(bullet.damage)
                    if not bullet.penetrative:
                        bullet.kill()

                    if result == -1: # Shield collapsed notification
                        self.sound_engine.play("shield_down")
                        self.trigger_explosion(bullet.rect.centerx, bullet.rect.centery, 40, RED)
                        ft = FloatingText(self.boss.rect.centerx, self.boss.rect.bottom + 10, "BOSS SHIELDS BURNT", RED, size=24)
                        self.particles.add(ft)
                    elif result == 0: # Standard impact, shield held
                        self.sound_engine.play("hit")
                        self.trigger_sparks(bullet.rect.centerx, bullet.rect.centery, 0, 5, CYAN)
                    elif result is True: # Boss destroyed completely
                        self.sound_engine.play("explosion")
                        self.trigger_explosion(self.boss.rect.centerx, self.boss.rect.centery, 100, MAGENTA)
                        self.player.score += self.boss.score_value
                        self.boss.kill()
                        ft = FloatingText(self.boss.rect.centerx, self.boss.rect.centery, f"+{self.boss.score_value} BOSS SLAYER!", CYAN, size=32)
                        self.particles.add(ft)
                        self.combo_counter += 10
                        self.combo_timer = 180

        # 3. Enemy shots impacting Player
        player_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for hit in player_hits:
            damage = 15
            self.player.shield -= damage
            self.sound_engine.play("hit")
            self.trigger_sparks(self.player.rect.centerx, self.player.rect.top, 0, -5, CYAN)
            self.screen_shake = max(self.screen_shake, 12)

            if self.player.shield <= 0:
                self.player.lives -= 1
                self.sound_engine.play("explosion")
                self.trigger_explosion(self.player.rect.centerx, self.player.rect.centery, 55, RED)
                if self.player.lives <= 0:
                    self.leaderboard.check_high_score(self.player.score)
                    self.game_state = "GAMEOVER"
                else:
                    self.player.shield = self.player.max_shield

        # 4. Colliding Items triggering Power-ups
        collected = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for item in collected:
            self.player.apply_powerup(item.type, self.sound_engine)
            ft = FloatingText(self.player.rect.centerx, self.player.rect.top - 15, f"{item.type.upper()} SYSTEM ACTIVE!", GREEN, size=24)
            self.particles.add(ft)

        # --- AI Strategy Combat & Wave Mechanics ---

        # Reverse wave direction at boundary edges
        shift_down = False
        for enemy in self.enemies:
            if not isinstance(enemy, EnemyBoss):
                # Lateral dynamic check
                if enemy.rect.right > SCREEN_WIDTH - 20 or enemy.rect.left < 20:
                    shift_down = True
                    break

        if shift_down:
            for enemy in self.enemies:
                if not isinstance(enemy, EnemyBoss):
                    if hasattr(enemy, 'x_speed'):
                        enemy.x_speed *= -1
                    else:
                        enemy.x_speed = -2.0 if enemy.rect.right > SCREEN_WIDTH - 20 else 2.0
                    enemy.rect.y += 20

        # Run automated AI fire calculations
        self._handle_enemy_attacks()

        # Progression check when all Hostiles are vaporized
        if not self.enemies:
            self.saved_score = self.player.score
            self.saved_lives = self.player.lives
            self.saved_shield = self.player.shield
            self.init_level(self.level + 1)

    def _handle_enemy_impact(self, enemy, pos, is_dead):
        if is_dead:
            self.sound_engine.play("explosion")
            self.trigger_explosion(pos[0], pos[1], 25 + enemy.max_hp * 8, ORANGE if enemy.tier == "bomber" else CYAN)
            enemy.kill()

            # Dynamic combat combo accumulation
            self.combo_counter += 1
            self.combo_timer = 180  # 3 seconds combo reset window
            if self.combo_counter > self.highest_combo:
                self.highest_combo = self.combo_counter

            multiplier = 1.0 + (self.combo_counter * 0.1)
            added_score = int(enemy.score_value * multiplier)
            self.player.score += added_score

            # Render combat text display
            col = YELLOW if self.combo_counter > 5 else WHITE
            ft = FloatingText(pos[0], pos[1], f"+{added_score} x{multiplier:.1f}", col, size=20)
            self.particles.add(ft)

            # High-tier loot drops
            drop_chance = 0.18 + (self.level * 0.01)
            if random.random() < min(0.40, drop_chance):
                p = PowerUp(pos[0], pos[1], self.assets)
                self.all_sprites.add(p)
                self.powerups.add(p)
        else:
            self.sound_engine.play("hit")
            self.trigger_sparks(pos[0], pos[1], 0, 4, RED)

    def _handle_enemy_attacks(self):
        now = pygame.time.get_ticks()

        # 1. Standard Fleet attack pattern
        for enemy in self.enemies:
            if isinstance(enemy, EnemyBoss):
                continue

            if now - enemy.last_shot > enemy.shoot_cooldown:
                enemy.last_shot = now + random.randint(0, 500)
                bullet_color = RED if enemy.tier == "scout" else MAGENTA
                speed = 4.5 + (self.level * 0.2)

                if enemy.tier == "bomber":
                    # Double threat spread bullet pattern
                    b1 = Bullet(enemy.rect.left + 5, enemy.rect.bottom, speed, bullet_color, width=6, height=14)
                    b2 = Bullet(enemy.rect.right - 5, enemy.rect.bottom, speed, bullet_color, width=6, height=14)
                    self.all_sprites.add(b1, b2)
                    self.enemy_bullets.add(b1, b2)
                else:
                    b = Bullet(enemy.rect.centerx, enemy.rect.bottom, speed, bullet_color, width=5, height=12)
                    self.all_sprites.add(b)
                    self.enemy_bullets.add(b)

        # 2. Overlord Mega Boss specialized patterns
        if hasattr(self, 'boss') and self.boss.alive() and self.boss.rect.centery >= self.boss.target_y:
            if now - self.boss.last_attack_time > self.boss.attack_cooldown:
                self.boss.last_attack_time = now

                if self.boss.phase == 1:
                    # Circular bullet hell blast
                    self.sound_engine.play("shoot")
                    num_shots = 12
                    for i in range(num_shots):
                        angle = (i * (2 * math.pi / num_shots))
                        dx = math.sin(angle) * 4.0
                        dy = math.cos(angle) * 4.0
                        b = Bullet(self.boss.rect.centerx, self.boss.rect.bottom, dy, MAGENTA, width=6, height=12)
                        # Inject horizontal movement calculations into update loop
                        b.update = lambda self=b, dx=dx: (setattr(self.rect, 'x', self.rect.x + dx), setattr(self.rect, 'y', self.rect.y + self.speed_y))
                        self.all_sprites.add(b)
                        self.enemy_bullets.add(b)

                elif self.boss.phase == 2:
                    # Alternating direct spray
                    self.sound_engine.play("laser_heavy")
                    for offset_x in [-50, -20, 20, 50]:
                        b = Bullet(self.boss.rect.centerx + offset_x, self.boss.rect.bottom, 6.0, YELLOW, width=8, height=16)
                        self.all_sprites.add(b)
                        self.enemy_bullets.add(b)

                elif self.boss.phase == 3:
                    # Aggressive multi-targeting chaos sweep
                    self.sound_engine.play("shoot")
                    for angle_offset in [-0.4, -0.2, 0, 0.2, 0.4]:
                        dx = math.sin(angle_offset) * 5.0
                        dy = math.cos(angle_offset) * 6.0
                        b = Bullet(self.boss.rect.centerx, self.boss.rect.bottom, dy, RED, width=8, height=16)
                        b.update = lambda self=b, dx=dx: (setattr(self.rect, 'x', self.rect.x + dx), setattr(self.rect, 'y', self.rect.y + self.speed_y))
                        self.all_sprites.add(b)
                        self.enemy_bullets.add(b)

    def _draw_playing(self):
        # Dynamic Camera Screen Shake offset calculations
        render_offset = [0, 0]
        if self.screen_shake > 0:
            render_offset[0] = random.randint(-self.screen_shake, self.screen_shake)
            render_offset[1] = random.randint(-self.screen_shake, self.screen_shake)
            self.screen_shake = int(self.screen_shake * 0.85)

        # Draw main gameplay elements using active shake offsets
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, sprite.rect.move(render_offset))

        # Render active screen particles
        for p in self.particles:
            self.screen.blit(p.image, p.rect.move(render_offset))

        # 1. Overlay Player Shield barrier ring
        if self.player.shield > 0:
            alpha = int(80 + 40 * math.sin(pygame.time.get_ticks() * 0.01))
            shield_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (*CYAN[:3], alpha), (35, 35), 32, 3)
            self.screen.blit(shield_surf, (self.player.rect.centerx - 35, self.player.rect.centery - 35))

        # 2. Overlay Boss Shield indicator
        if hasattr(self, 'boss') and self.boss.alive() and self.boss.shield_up:
            alpha = int(100 + 50 * math.sin(pygame.time.get_ticks() * 0.015))
            shield_surf = pygame.Surface((220, 150), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surf, (*CYAN[:3], alpha), (10, 10, 200, 130), 4)
            self.screen.blit(shield_surf, (self.boss.rect.centerx - 110, self.boss.rect.centery - 75))

        # UI Overlay Panels
        self._draw_hud()

    def _draw_hud(self):
        # Top Header Bar panel
        pygame.draw.rect(self.screen, DARK_BLUE, (0, 0, SCREEN_WIDTH, 50))
        pygame.draw.line(self.screen, CYAN, (0, 50), (SCREEN_WIDTH, 50), 2)

        font = pygame.font.SysFont("Lucida Console", 18, bold=True)

        # Score & Level info
        score_lbl = font.render(f"SCORE: {self.player.score:06d}", True, WHITE)
        self.screen.blit(score_lbl, (20, 15))

        level_lbl = font.render(f"SECTOR: {self.level:02d}", True, YELLOW)
        self.screen.blit(level_lbl, (SCREEN_WIDTH // 2 - level_lbl.get_width() // 2, 15))

        # Structural Health shield indicator bar
        hud_right_edge = SCREEN_WIDTH - 250
        sh_lbl = font.render("SHIELD:", True, CYAN)
        self.screen.blit(sh_lbl, (hud_right_edge - 90, 15))

        pygame.draw.rect(self.screen, (30, 30, 60), (hud_right_edge, 16, 120, 16), border_radius=4)
        sh_percentage = max(0, min(1.0, self.player.shield / self.player.max_shield))
        bar_color = GREEN if sh_percentage > 0.5 else (YELLOW if sh_percentage > 0.25 else RED)
        pygame.draw.rect(self.screen, bar_color, (hud_right_edge + 2, 18, int(116 * sh_percentage), 12), border_radius=2)

        # Hull/Lives indicator
        for l_idx in range(self.player.lives):
            heart_x = SCREEN_WIDTH - 40 - l_idx * 28
            heart_rect = pygame.Rect(heart_x, 15, 18, 18)
            pygame.draw.polygon(self.screen, RED, [
                (heart_rect.centerx, heart_rect.y + 4),
                (heart_rect.x + 4, heart_rect.y),
                (heart_rect.x, heart_rect.y + 5),
                (heart_rect.centerx, heart_rect.bottom),
                (heart_rect.right, heart_rect.y + 5),
                (heart_rect.right - 4, heart_rect.y)
            ])

        # Overlord Boss Health Bar overlay
        if hasattr(self, 'boss') and self.boss.alive() and self.boss.rect.centery >= self.boss.target_y:
            panel_x = SCREEN_WIDTH // 2 - 250
            panel_y = SCREEN_HEIGHT - 45
            pygame.draw.rect(self.screen, DARK_BLUE, (panel_x - 10, panel_y - 10, 520, 40), border_radius=6)
            pygame.draw.rect(self.screen, MAGENTA, (panel_x - 10, panel_y - 10, 520, 40), 1, border_radius=6)

            boss_lbl = font.render("OVERLORD HP:", True, MAGENTA)
            self.screen.blit(boss_lbl, (panel_x, panel_y))

            pygame.draw.rect(self.screen, (40, 10, 20), (panel_x + 140, panel_y + 2, 350, 14), border_radius=4)
            hp_percentage = max(0.0, self.boss.hp / self.boss.max_hp)
            pygame.draw.rect(self.screen, RED, (panel_x + 142, panel_y + 4, int(346 * hp_percentage), 10), border_radius=2)

        # Combo Tracking Meter overlay
        if self.combo_counter > 0:
            combo_font = pygame.font.SysFont("Trebuchet MS", 20, bold=True)
            scale = 1.0 + (self.combo_counter * 0.05)
            # Cap limits to avoid sizing glitches
            scale = min(2.5, scale)

            c_str = f"COMBO x{self.combo_counter}!"
            color = GREEN if self.combo_counter > 8 else YELLOW
            rendered = combo_font.render(c_str, True, color)
            w, h = rendered.get_size()
            scaled_surf = pygame.transform.scale(rendered, (int(w * scale), int(h * scale)))
            self.screen.blit(scaled_surf, (20, 70))

        # Active weapon countdown meters
        if self.player.active_powerup:
            remaining_time = max(0, self.player.powerup_timer - pygame.time.get_ticks())
            p_percent = remaining_time / 8000.0
            p_font = pygame.font.SysFont("Lucida Console", 14, bold=True)
            p_text = p_font.render(f"OVERCHARGE: {self.player.active_powerup.upper()}", True, WHITE)
            self.screen.blit(p_text, (20, SCREEN_HEIGHT - 60))
            pygame.draw.rect(self.screen, (40, 40, 80), (20, SCREEN_HEIGHT - 40, 180, 10), border_radius=3)
            pygame.draw.rect(self.screen, YELLOW, (22, SCREEN_HEIGHT - 38, int(176 * p_percent), 6), border_radius=2)

    # --- Game Over Screen Routines ---
    def _handle_gameover_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Clean operational reset
                    self.saved_score = 0
                    self.saved_lives = 3
                    self.saved_shield = 100
                    self.init_level(1)
                    self.game_state = "PLAYING"
                elif event.key == pygame.K_ESCAPE:
                    self.game_state = "MENU"

    def _draw_gameover(self):
        # Masterpiece Game Over panel layout
        font_title = pygame.font.SysFont("Lucida Console", 64, bold=True)
        t_surf = font_title.render("MISSION TERMINATED", True, RED)
        self.screen.blit(t_surf, (SCREEN_WIDTH // 2 - t_surf.get_width() // 2, SCREEN_HEIGHT // 4))

        font_score = pygame.font.SysFont("Trebuchet MS", 28, bold=True)
        sc_surf = font_score.render(f"FINAL RECORDED SCORE: {self.player.score:06d}", True, WHITE)
        self.screen.blit(sc_surf, (SCREEN_WIDTH // 2 - sc_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 40))

        combo_surf = font_score.render(f"MAX COMBAT COMBO: {self.highest_combo}", True, GREEN)
        self.screen.blit(combo_surf, (SCREEN_WIDTH // 2 - combo_surf.get_width() // 2, SCREEN_HEIGHT // 2))

        # Local Top Scores records presentation panel
        panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 50, 400, 140)
        pygame.draw.rect(self.screen, DARK_BLUE, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, RED, panel_rect, 1, border_radius=8)

        lbl_font = pygame.font.SysFont("Lucida Console", 14)
        lbl = lbl_font.render("--- SYSTEM RECORD FILE ---", True, MAGENTA)
        self.screen.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, panel_rect.y + 10))

        for idx, score in enumerate(self.leaderboard.scores):
            col = CYAN if score == self.player.score and score > 0 else WHITE
            score_line = lbl_font.render(f"RANK #{idx+1}: {score:06d} PTS", True, col)
            self.screen.blit(score_line, (SCREEN_WIDTH // 2 - score_line.get_width() // 2, panel_rect.y + 35 + idx * 18))

        # Operational Instructions info block
        font_inst = pygame.font.SysFont("Lucida Console", 18, bold=True)
        inst_surf = font_inst.render("PRESS [ENTER] TO RE-DEPLOY / [ESC] FOR HQ MENU", True, WHITE)
        self.screen.blit(inst_surf, (SCREEN_WIDTH // 2 - inst_surf.get_width() // 2, SCREEN_HEIGHT - 80))


# --- Main Execution Entry Point ---
if __name__ == "__main__":
    game = Game()
    game.run()

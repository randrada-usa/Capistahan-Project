import pygame
import random
from enum import Enum


class Rarity(Enum):
    COMMON = "common"
    RARE = "rare"
    ULTRA_RARE = "ultra_rare"


class FallingItem:
    """Single falling item with rarity system and theme integration."""
    
    SCORE_TABLE = {
        Rarity.COMMON: 10,
        Rarity.RARE: 25,
        Rarity.ULTRA_RARE: 50
    }
    
    RARITY_COLORS = {
        Rarity.COMMON: (255, 200, 100),
        Rarity.RARE: (255, 215, 0),
        Rarity.ULTRA_RARE: (255, 100, 255)
    }
    
    def __init__(self, x, item_type, rarity, speed, 
                 asset_manager=None, theme_manager=None):
        
        self.x = x
        self.y = -50
        self.type = item_type
        self.rarity = rarity  # ✅ ALWAYS Enum now
        self.speed = speed
        self.assets = asset_manager
        
        # Theme
        if theme_manager:
            self.category = theme_manager.get_theme()
            self.theme_manager = theme_manager
        else:
            self.category = 'food'
            self.theme_manager = None
        
        # Visuals
        self.radius = 30
        self.size = 60
        self.rotation = 0
        self.rotation_speed = random.uniform(-2, 2)
        
        # Glow effect
        self.glow_color = None
        if self.rarity == Rarity.ULTRA_RARE:
            self.glow_color = (255, 215, 0)
        elif self.rarity == Rarity.RARE:
            self.glow_color = (100, 200, 255)
        
        self.glow_pulse = 0.0
    
    def get_score_value(self):
        base = self.SCORE_TABLE.get(self.rarity, 10)
        return base if self.type == 'good' else 0
    
    def update(self, dt, speed_multiplier):
        self.y += self.speed * speed_multiplier * dt * 60
        self.rotation += self.rotation_speed
        
        if self.rarity in (Rarity.RARE, Rarity.ULTRA_RARE):
            self.glow_pulse = (self.glow_pulse + dt * 3) % (2 * 3.14159)
    
    def render(self, screen):
        if self.assets:
            sprite_key = f'{self.category}_{self.type}_{self.rarity.value}'
            sprite = self.assets.get(sprite_key)
            
            if not sprite:
                sprite_key = 'good_item' if self.type == 'good' else 'bad_item'
                sprite = self.assets.get(sprite_key)
            
            if sprite:
                rotated = pygame.transform.rotate(sprite, self.rotation)
                rect = rotated.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(rotated, rect)
                return
        
        base_color = self.RARITY_COLORS.get(self.rarity, (255, 200, 100))
        
        if self.type == 'bad':
            base_color = tuple(max(0, c - 100) for c in base_color)
        
        pygame.draw.circle(screen, base_color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 255),
                           (int(self.x), int(self.y)), self.radius, 2)
        
        # Indicators
        if self.rarity == Rarity.RARE:
            pygame.draw.circle(screen, (255, 255, 0),
                               (int(self.x - 15), int(self.y - 15)), 5)
        elif self.rarity == Rarity.ULTRA_RARE:
            pygame.draw.circle(screen, (255, 0, 255),
                               (int(self.x - 15), int(self.y - 15)), 5)
            pygame.draw.circle(screen, (0, 255, 255),
                               (int(self.x + 15), int(self.y - 15)), 5)
    
    def is_off_screen(self, screen_height):
        return self.y > screen_height + 50
    
    def get_hitbox(self):
        hit_radius = self.radius * 0.8
        return pygame.Rect(
            self.x - hit_radius,
            self.y - hit_radius,
            hit_radius * 2,
            hit_radius * 2
        )


class ObjectManager:
    """Spawns and manages falling items with weighted rarity."""
    
    RARITY_WEIGHTS = {
        Rarity.COMMON: 0.75,
        Rarity.RARE: 0.20,
        Rarity.ULTRA_RARE: 0.05
    }
    
    MAX_COMMON_STREAK = 3
    
    def __init__(self, screen_width, asset_manager=None, theme_manager=None):
        self.screen_width = screen_width
        self.assets = asset_manager
        self.theme_manager = theme_manager
        self.category = theme_manager.get_theme() if theme_manager else 'food'
        
        self.items = []
        self.game_time = 0
        
        self.spawn_timer = 0
        self.base_spawn_interval = 1.5
        self.min_spawn_interval = 0.4
        self.current_spawn_interval = self.base_spawn_interval
        
        self.speed_multiplier = 1.0
        
        self.initial_spawn_count = 4
        self.has_spawned_initial = False
        
        self._missed_good_count = 0
        
        self._consecutive_commons = 0
    
    def _roll_rarity(self):
        if self._consecutive_commons >= self.MAX_COMMON_STREAK:
            self._consecutive_commons = 0
            return Rarity.RARE if random.random() > 0.05 else Rarity.ULTRA_RARE
        
        rarities = list(self.RARITY_WEIGHTS.keys())
        weights = list(self.RARITY_WEIGHTS.values())
        
        result = random.choices(rarities, weights=weights, k=1)[0]
        
        if result == Rarity.COMMON:
            self._consecutive_commons += 1
        else:
            self._consecutive_commons = 0
        
        return result
    
    def spawn_item(self):
        BORDER_WIDTH = 200
        margin = BORDER_WIDTH + 30
        x = random.randint(margin, self.screen_width - margin)
        
        rarity = self._roll_rarity()
        item_type = 'good' if random.random() < 0.7 else 'bad'
        base_speed = random.uniform(4, 7)
        
        item = FallingItem(
            x, item_type, rarity, base_speed,
            self.assets, self.theme_manager
        )
        self.items.append(item)
    
    def spawn_initial_burst(self):
        for i in range(self.initial_spawn_count):
            x = random.randint(210, self.screen_width - 210)
            rarity = self._roll_rarity()
            item_type = 'good' if random.random() < 0.7 else 'bad'
            base_speed = random.uniform(4, 7)

            item = FallingItem(x, item_type, rarity, base_speed,
                               self.assets, self.theme_manager)
            item.y = -50 - (i * 80)
            self.items.append(item)

        self.has_spawned_initial = True
    
    def update(self, dt, score):
        if not self.has_spawned_initial:
            self.spawn_initial_burst()

        self.game_time += dt
        
        self.spawn_timer += dt
        if self.spawn_timer >= self.current_spawn_interval:
            self.spawn_item()
            self.spawn_timer = 0
        
        for item in self.items:
            item.update(dt, self.speed_multiplier)

        self._missed_good_count = 0
        for item in self.items[:]:
            if item.is_off_screen(1080):
                if item.type == 'good':
                    self._missed_good_count += 1
        
        self.items = [
            item for item in self.items 
            if not item.is_off_screen(1080)
        ]
    
    def render(self, screen):
        for item in self.items:
            item.render(screen)
    
    def check_collisions(self, player_hitbox):
        caught = []
        
        for item in self.items[:]:
            if item.get_hitbox().colliderect(player_hitbox):
                caught.append(item)
                self.items.remove(item)

        missed_good = self._missed_good_count
        self._missed_good_count = 0
        
        return caught, missed_good
import pygame
import random
from enum import Enum


class Rarity(Enum):
    VERY_COMMON = "very_common"  # 5 pts
    COMMON = "common"            # 10 pts
    RARE = "rare"                # 25 pts
    ULTRA_RARE = "ultra_rare"    # 50 pts
    WISH = "wish"


class FallingItem:
    """Falling item with category-specific PNG assets for Capiztahan."""
    
    SCORE_TABLE = {
        Rarity.VERY_COMMON: 5,
        Rarity.COMMON: 10,
        Rarity.RARE: 25,
        Rarity.ULTRA_RARE: 50,
        Rarity.WISH:100
    }
    
    # Map rarities to glow sprite keys (from assets/effects/)
    GLOW_SPRITES = {
        Rarity.COMMON: 'common_glow',
        Rarity.RARE: 'rare_glow',
        Rarity.ULTRA_RARE: 'ultra_rare_glow',
        Rarity.WISH: 'wish_glow'
        # VERY_COMMON has no glow
    }
    
    # Map rarities to asset key prefixes
    RARITY_PREFIXES = {
        Rarity.VERY_COMMON: 'ultracommon',
        Rarity.COMMON: 'common',
        Rarity.RARE: 'rare',
        Rarity.ULTRA_RARE: 'ultrarare',
        Rarity.WISH: 'wish'
    }
    
    def __init__(self, x, item_type, rarity, speed, asset_manager=None, theme_manager=None):
        self.x = x
        self.y = -50
        self.type = item_type  # 'good' or 'bad'
        self.rarity = rarity
        self.speed = speed
        self.assets = asset_manager

        # Get theme category
        if theme_manager:
            self.category = theme_manager.get_theme()
        else:
            self.category = 'food'
        
        # Generate asset key based on category and rarity
        if self.type == 'bad':
            # bad_item_food, bad_item_culture, bad_item_people
            self.item_key = f'bad_item_{self.category}'
        else:
            # Determine suffix: 'item' for food/culture, 'book' for people
            suffix = 'book' if self.category == 'people' else 'item'
            prefix = self.RARITY_PREFIXES[rarity]
            self.item_key = f'{prefix}_{suffix}'
        
        # Visual properties
        self.radius = 30
        self.size = 60
        self.rotation = 0
        self.glow_rotation = 0
        self.rotation_speed = random.uniform(-2, 2)
        self.glow_rotation_speed = random.uniform(-1, 1)
        self.glow_scale = 1.2
    
    def get_score_value(self):
        base = self.SCORE_TABLE.get(self.rarity, 10)
        return base if self.type == 'good' else 0
    
    def update(self, dt, speed_multiplier):
        self.y += self.speed * speed_multiplier * dt * 60
        self.rotation += self.rotation_speed
        self.glow_rotation += self.glow_rotation_speed
    
    def render(self, screen):
        """Draw glow behind, then item on top using PNG assets."""
        
        # 1. Draw glow first (behind item) for common/rare/ultra-rare good items
        # VERY_COMMON (ultracommon) has no glow
        if self.type == 'good' and self.rarity != Rarity.VERY_COMMON:
            glow_key = self.GLOW_SPRITES.get(self.rarity)
            if glow_key and self.assets:
                glow_sprite = self.assets.get(glow_key)
                if glow_sprite:
                    # Rotate glow independently
                    rotated_glow = pygame.transform.rotate(glow_sprite, self.glow_rotation)
                    # Scale up slightly
                    scaled_size = (
                        int(rotated_glow.get_width() * self.glow_scale),
                        int(rotated_glow.get_height() * self.glow_scale)
                    )
                    scaled_glow = pygame.transform.scale(rotated_glow, scaled_size)
                    # Center on item
                    glow_rect = scaled_glow.get_rect(center=(int(self.x), int(self.y)))
                    screen.blit(scaled_glow, glow_rect)

                    
        
        # 2. Draw the actual item using the generated asset key
        if self.assets:
            sprite = self.assets.get(self.item_key)
            
            if sprite:
                # Rotate item independently
                rotated = pygame.transform.rotate(sprite, self.rotation)
                rect = rotated.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(rotated, rect)
            else:
                # Debug: show pink circle if asset missing
                pygame.draw.circle(screen, (255, 0, 255), (int(self.x), int(self.y)), 10)
                font = pygame.font.Font(None, 24)
                text = font.render(self.item_key[:6], True, (255, 255, 255))
                screen.blit(text, (int(self.x) - 15, int(self.y) - 10))
    
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
    """Spawns and manages falling items."""
    
    RARITY_WEIGHTS = {
        Rarity.VERY_COMMON: 0.35,  # 35%
        Rarity.COMMON: 0.40,       # 40%
        Rarity.RARE: 0.20,         # 20%
        Rarity.ULTRA_RARE: 0.05,
        Rarity.WISH: 0.01   # 5%
    }
    
    MAX_VERY_COMMON_STREAK = 4
    
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
        self._consecutive_very_common = 0
    
    def _roll_rarity(self):
        """Weighted random with anti-streak for very common."""
        if self._consecutive_very_common >= self.MAX_VERY_COMMON_STREAK:
            self._consecutive_very_common = 0
            return Rarity.RARE if random.random() > 0.05 else Rarity.ULTRA_RARE
        
        rarities = list(self.RARITY_WEIGHTS.keys())
        weights = list(self.RARITY_WEIGHTS.values())
        
        result = random.choices(rarities, weights=weights, k=1)[0]
        
        if result == Rarity.VERY_COMMON:
            self._consecutive_very_common += 1
        else:
            self._consecutive_very_common = 0
        
        return result
    
    def spawn_item(self):
        """Create new item with proper margins."""
        BORDER_WIDTH = 200
        margin = BORDER_WIDTH + 30
        x = random.randint(margin, self.screen_width - margin)
        
        # Roll rarity
        rarity = self._roll_rarity()
        
        # 70% good, 30% bad
        if rarity == Rarity.WISH:
            item_type = 'good'
        elif random.random() < 0.3:
            item_type = 'bad'
            rarity = Rarity.VERY_COMMON
        else:
            item_type = 'good'
        
        base_speed = random.uniform(4, 7)
        
        item = FallingItem(
            x, item_type, rarity, base_speed,
            self.assets, self.theme_manager
        )
        self.items.append(item)
    
    def spawn_initial_burst(self):
        """Spawn initial items."""
        for i in range(self.initial_spawn_count):
            x = random.randint(210, self.screen_width - 210)
            
            if random.random() < 0.3:
                item_type = 'bad'
                rarity = Rarity.VERY_COMMON
            else:
                item_type = 'good'
                rarity = self._roll_rarity()

                rarities = [Rarity.VERY_COMMON, Rarity.COMMON, Rarity.RARE, Rarity.ULTRA_RARE]
                weights = [0.35, 0.40, 0.20, 0.05]
                rarity = random.choices(rarities, weights=weights, k=1)[0]
            
            base_speed = random.uniform(4, 7)

            item = FallingItem(x, item_type, rarity, base_speed,
                               self.assets, self.theme_manager)
            item.y = -50 - (i * 80)  # Stagger heights
            self.items.append(item)

        self.has_spawned_initial = True
    
    def update(self, dt, score):
        """Update all items."""
        if not self.has_spawned_initial:
            self.spawn_initial_burst()

        self.game_time += dt
        
        # Difficulty scaling
        time_level = int(self.game_time // 20)
        score_level = score // 50
        difficulty_level = (time_level // 2) + score_level
        
        self.speed_multiplier = 0.50 + difficulty_level * 0.25
        
        spawn_reduction = difficulty_level * 0.10
        self.current_spawn_interval = max(
            self.min_spawn_interval,
            self.base_spawn_interval - spawn_reduction
        )
        
        # Spawn logic
        self.spawn_timer += dt
        if self.spawn_timer >= self.current_spawn_interval:
            self.spawn_item()
            self.spawn_timer = 0
        
        # Update existing items
        for item in self.items:
            item.update(dt, self.speed_multiplier)

        # Check for missed good items
        self._missed_good_count = 0
        for item in self.items[:]:
            if item.is_off_screen(1080):
                if item.type == 'good':
                    self._missed_good_count += 1
        
        # Remove off-screen items
        self.items = [
            item for item in self.items 
            if not item.is_off_screen(1080)
        ]
    
    def render(self, screen):
        """Draw all items."""
        for item in self.items:
            item.render(screen)
    
    def check_collisions(self, player_hitbox):
        """Check collisions with player."""
        caught = []
        
        for item in self.items[:]:
            if item.get_hitbox().colliderect(player_hitbox):
                caught.append(item)
                self.items.remove(item)

                caught.append(item)
                # Play glow SFX when catching glowing items
                if item.type == 'good' and item.rarity != Rarity.VERY_COMMON and self.assets:
                    glow_sfx = None
                    if item.rarity == Rarity.COMMON:
                        glow_sfx = self.assets.get('blue')
                    elif item.rarity == Rarity.RARE:
                        glow_sfx = self.assets.get('red')
                    elif item.rarity == Rarity.ULTRA_RARE:
                        glow_sfx = self.assets.get('gold')
                    elif item.rarity == Rarity.WISH:
                        glow_sfx = self.assets.get('uber_rare')
                    if glow_sfx:
                        glow_sfx.play()

        # REMOVED: No penalty for missed items in timer mode
        # Just reset the counter for next frame
        self._missed_good_count = 0
        
        return caught, 0
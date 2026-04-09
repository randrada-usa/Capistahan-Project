import pygame
import random


class FallingItem:
    """Single falling item with rarity system and theme integration."""
    
    # Score values by rarity
    SCORE_TABLE = {
        'common': 10,
        'rare': 25,
        'ultra_rare': 50
    }
    
    # Rarity colors for debug/fallback rendering
    RARITY_COLORS = {
        'common': (255, 200, 100),     # Normal gold
        'rare': (255, 215, 0),         # Bright gold
        'ultra_rare': (255, 100, 255)  # Magenta/rainbow
    }
    
    def __init__(self, x, item_type, rarity, speed, 
                 asset_manager=None, theme_manager=None):
        self.x = x
        self.y = -50
        self.type = item_type  # 'good' or 'bad'
        self.rarity = rarity   # 'common', 'rare', 'ultra_rare'
        self.speed = speed
        self.assets = asset_manager
        
        # Get category from Rey's ThemeManager
        if theme_manager:
            self.category = theme_manager.get_theme()
            self.theme_manager = theme_manager
        else:
            self.category = 'food'
            self.theme_manager = None
        
        # Visual properties
        self.radius = 30
        self.size = 60
        self.rotation = 0
        self.rotation_speed = random.uniform(-2, 2)

                # NEW: Add rarity (Gio sets this based on weights)
        self.rarity = rarity  # Rarity enum or None for legacy
        
        # Visual indicator based on rarity
        self.glow_color = None
        if rarity:
            if rarity.value == "ultra_rare":
                self.glow_color = (255, 215, 0)  # Gold glow
            elif rarity.value == "rare":
                self.glow_color = (100, 200, 255)  # Blue glow

        
        # Effect timer for Jen's visual hooks
        self.glow_pulse = 0.0
    
    def get_score_value(self):
        """Return points based on rarity."""
        base = self.SCORE_TABLE.get(self.rarity, 10)
        # Bad items score 0 regardless of rarity
        return base if self.type == 'good' else 0
    
    def update(self, dt, speed_multiplier):
        """Fall down with difficulty scaling."""
        self.y += self.speed * speed_multiplier * dt * 60
        self.rotation += self.rotation_speed
        
        # Pulse glow for rare/ultra-rare (for Jen's renderer to use)
        if self.rarity in ('rare', 'ultra_rare'):
            self.glow_pulse = (self.glow_pulse + dt * 3) % (2 * 3.14159)
    
    def render(self, screen):
        """Draw item with rarity-based visual treatment."""
        if self.assets:
            # Build sprite key: '{category}_{type}_{rarity}'
            # e.g., 'food_good_common', 'culture_good_ultra_rare'
            sprite_key = f'{self.category}_{self.type}_{self.rarity}'
            sprite = self.assets.get(sprite_key)
            
            # Fallback to generic good/bad if specific not found
            if not sprite:
                sprite_key = 'good_item' if self.type == 'good' else 'bad_item'
                sprite = self.assets.get(sprite_key)
            
            if sprite:
                rotated = pygame.transform.rotate(sprite, self.rotation)
                rect = rotated.get_rect(center=(int(self.x), int(self.y)))
                
                # Jen can check self.rarity to add glow overlay here
                screen.blit(rotated, rect)
                return
        
        # Fallback: rarity-colored circle
        base_color = self.RARITY_COLORS.get(self.rarity, (255, 200, 100))
        if self.type == 'bad':
            # Darken for bad items
            base_color = tuple(max(0, c - 100) for c in base_color)
        
        pygame.draw.circle(screen, base_color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 
                          self.radius, 2)
        
        # Rarity indicator dots
        if self.rarity == 'rare':
            pygame.draw.circle(screen, (255, 255, 0), 
                             (int(self.x - 15), int(self.y - 15)), 5)
        elif self.rarity == 'ultra_rare':
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
    
    # Rarity probability distribution (must sum to 1.0)
    RARITY_WEIGHTS = {
        'common': 0.75,
        'rare': 0.20,
        'ultra_rare': 0.05
    }
    
    # Anti-streak protection: max consecutive commons before forcing rare
    MAX_COMMON_STREAK = 3
    
    def __init__(self, screen_width, asset_manager=None, theme_manager=None):
        self.screen_width = screen_width
        self.assets = asset_manager
        self.theme_manager = theme_manager
        self.category = theme_manager.get_theme() if theme_manager else 'food'
        
        self.items = []
        self.game_time = 0
        
        # Spawn timing
        self.spawn_timer = 0
        self.base_spawn_interval = 1.5
        self.min_spawn_interval = 0.4
        self.current_spawn_interval = self.base_spawn_interval
        
        # Difficulty
        self.speed_multiplier = 1.0
        
        # Initial burst
        self.initial_spawn_count = 4
        self.has_spawned_initial = False
        
        # Missed tracking
        self._missed_good_count = 0
        
        # Streak prevention
        self._spawn_history = []
        self._consecutive_commons = 0
    
    def _roll_rarity(self):
        """
        Weighted random selection with anti-streak protection.
        Returns: 'common', 'rare', or 'ultra_rare'
        """
        # Force rare if too many commons in a row
        if self._consecutive_commons >= self.MAX_COMMON_STREAK:
            self._consecutive_commons = 0
            return 'rare' if random.random() > 0.05 else 'ultra_rare'
        
        # Standard weighted roll
        rarities = list(self.RARITY_WEIGHTS.keys())
        weights = list(self.RARITY_WEIGHTS.values())
        
        result = random.choices(rarities, weights=weights, k=1)[0]
        
        # Track streak
        if result == 'common':
            self._consecutive_commons += 1
        else:
            self._consecutive_commons = 0
        
        self._spawn_history.append(result)
        if len(self._spawn_history) > 10:
            self._spawn_history.pop(0)
        
        return result
    
    def spawn_item(self):
        """Create new item with rolled rarity."""
        # Proper margin to keep on screen
        BORDER_WIDTH = 200
        margin = BORDER_WIDTH + 30
        x = random.randint(margin, self.screen_width - margin)
        
        # Roll rarity first
        rarity = self._roll_rarity()
        
        # 70% good, 30% bad (independent of rarity)
        item_type = 'good' if random.random() < 0.7 else 'bad'
        
        base_speed = random.uniform(4, 7)
        
        item = FallingItem(
            x=x,
            item_type=item_type,
            rarity=rarity,
            speed=base_speed,
            asset_manager=self.assets,
            theme_manager=self.theme_manager
        )
        self.items.append(item)
    
    def spawn_initial_burst(self):
        """Spawn multiple items at game start."""
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
    
    def update_difficulty(self, score):
        """Increase speed and spawn rate based on time and score."""
        time_level = int(self.game_time // 5)
        score_level = score // 4
        difficulty_level = time_level + score_level
        
        self.speed_multiplier = 1.0 + difficulty_level * 0.14
        
        spawn_reduction = difficulty_level * 0.20
        self.current_spawn_interval = max(
            self.min_spawn_interval,
            self.base_spawn_interval - spawn_reduction
        )
    
    def update(self, dt, score):
        """Update all items and spawn new ones."""
        if not self.has_spawned_initial:
            self.spawn_initial_burst()

        self.game_time += dt
        self.update_difficulty(score)
        
        # Spawn logic
        self.spawn_timer += dt
        if self.spawn_timer >= self.current_spawn_interval:
            self.spawn_item()
            self.spawn_timer = 0
        
        # Update items
        for item in self.items:
            item.update(dt, self.speed_multiplier)

        # Check missed good items
        self._missed_good_count = 0
        for item in self.items[:]:
            if item.is_off_screen(1080):
                if item.type == 'good':
                    self._missed_good_count += 1
        
        # Remove off-screen
        self.items = [
            item for item in self.items 
            if not item.is_off_screen(1080)
        ]
    
    def render(self, screen):
        for item in self.items:
            item.render(screen)
    
    def check_collisions(self, player_hitbox):
        """Check collisions, return caught items and missed count."""
        caught = []
        
        for item in self.items[:]:
            if item.get_hitbox().colliderect(player_hitbox):
                caught.append(item)
                self.items.remove(item)

        missed_good = self._missed_good_count
        self._missed_good_count = 0
        
        return caught, missed_good
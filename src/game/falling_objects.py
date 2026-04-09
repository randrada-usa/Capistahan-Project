import pygame
import random


class FallingItem:
    """Single falling item (good or bad)."""
    
    def __init__(self, x, item_type, speed, asset_manager=None):
        self.x = x
        self.y = -50  # Start above screen
        self.type = item_type  # 'good' or 'bad'
        self.speed = speed
        self.assets = asset_manager
        
        # Visual size (60x60 scaled sprites)
        self.radius = 30  # For collision circle
        self.size = 60    # For sprite rendering
        
        # Rotation for visual flair
        self.rotation = 0
        self.rotation_speed = random.uniform(-2, 2)
    
    def update(self, dt, speed_multiplier):
        """Fall down with difficulty scaling."""
        self.y += self.speed * speed_multiplier * dt * 60
        self.rotation += self.rotation_speed
    
    def render(self, screen):
        """Draw item sprite with rotation."""
        if self.assets:
            sprite_key = 'good_item' if self.type == 'good' else 'bad_item'
            sprite = self.assets.get(sprite_key)
            
            if sprite:
                # Rotate sprite
                rotated = pygame.transform.rotate(sprite, self.rotation)
                rect = rotated.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(rotated, rect)
                return
        
        # Fallback circle
        color = (255, 200, 100) if self.type == 'good' else (255, 80, 80)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 
                          self.radius, 2)
    
    def is_off_screen(self, screen_height):
        """Check if fallen past bottom."""
        return self.y > screen_height + 50
    
    def get_hitbox(self):
        """Circular hitbox for collision."""
        # Use slightly smaller hitbox than visual for fair gameplay
        hit_radius = self.radius * 0.8
        return pygame.Rect(
            self.x - hit_radius,
            self.y - hit_radius,
            hit_radius * 2,
            hit_radius * 2
        )


class ObjectManager:
    """Spawns and manages all falling items."""
    
    def __init__(self, screen_width, asset_manager=None):
        self.screen_width = screen_width
        self.assets = asset_manager
        self.items = []
        
        # Time tracking
        self.game_time = 0
        
        # Spawn timing
        self.spawn_timer = 0
        self.base_spawn_interval = 1.5
        self.min_spawn_interval = 0.4
        self.current_spawn_interval = self.base_spawn_interval
        
        # Difficulty scaling
        self.speed_multiplier = 1.0

        # INITIAL BURST: Spawn multiple items at game start
        self.initial_spawn_count = 4
        self.has_spawned_initial = False

        # Missed good items tracking (for life deduction)
        self._missed_good_count = 0
    
    def update_difficulty(self, score):
        """Increase speed based on time and score."""
        # Time-based difficulty (every 5 seconds)
        time_level = int(self.game_time // 5)
        
        # Score-based difficulty
        score_level = score // 4
        
        difficulty_level = time_level + score_level
        
        # Falling speed increases
        self.speed_multiplier = 1.0 + difficulty_level * 0.14
        
        # Spawn rate increases
        spawn_reduction = difficulty_level * 0.20
        self.current_spawn_interval = max(
            self.min_spawn_interval,
            self.base_spawn_interval - spawn_reduction
        )
    
    def spawn_item(self):
        """Create new falling item - kept on screen with proper margin."""
        # Proper margin calculation to keep items fully on screen
        BORDER_WIDTH = 200  # Keep in sync with player.py
        margin = BORDER_WIDTH + self.items[0].radius if self.items else BORDER_WIDTH + 30
        x = random.randint(margin, self.screen_width - margin)

        item_type = 'good' if random.random() < 0.7 else 'bad'
        base_speed = random.uniform(4, 7)
        
        item = FallingItem(x, item_type, base_speed, self.assets)
        self.items.append(item)

    def spawn_initial_burst(self):
        """Spawn multiple items at game start with staggered heights."""
        for i in range(self.initial_spawn_count):
            x = random.randint(210, self.screen_width - 210)
            item_type = 'good' if random.random() < 0.7 else 'bad'
            base_speed = random.uniform(4, 7)

            item = FallingItem(x, item_type, base_speed, self.assets)
            # Stagger starting positions above screen
            item.y = -50 - (i * 80)  # Each item 80px higher
            self.items.append(item)

        self.has_spawned_initial = True
    
    def update(self, dt, score):
        """Update all items and spawn new ones."""
        # INITIAL BURST on first update
        if not self.has_spawned_initial:
            self.spawn_initial_burst()

        # Track game time
        self.game_time += dt
        
        # Update difficulty
        self.update_difficulty(score)
        
        # Spawn logic
        self.spawn_timer += dt
        if self.spawn_timer >= self.current_spawn_interval:
            self.spawn_item()
            self.spawn_timer = 0
        
        # Update existing items
        for item in self.items:
            item.update(dt, self.speed_multiplier)

        # Check for missed good items before removing them
        self._missed_good_count = 0
        for item in self.items[:]:
            if item.is_off_screen(1080):
                if item.type == 'good':
                    self._missed_good_count += 1                    
        
        # Now remove off-screen items
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

        # Return missed good items count from update()
        missed_good = self._missed_good_count
        self._missed_good_count = 0  # Reset for next frame
        
        return caught, missed_good
"""
player.py - MODIFIED FOR CAPIZTAHAN
Removed: Expression system (moved to Perla HUD)
Added: 2-frame walk animation (switches every 5px)
"""

import pygame
import math


class Player:
    def __init__(self, screen_width, screen_height, asset_manager=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.assets = asset_manager
        
        # Position
        self.x = screen_width // 2
        self.y = 970
        self.lerp_speed = 0.15
        self.target_x = self.x
        self.frozen = False
        
        # Sprite dimensions
        self.width = 380
        self.height = 260
        self.facing = 'idle'
        self.move_threshold = 40  # Changed from 40 to 10 as requested
        self.sprite_offset_y = 30
        
        # Basket hitbox
        self.basket_width = 70
        self.basket_height = 40
        self.basket_offset_y = 175
        
        # NEW: 2-frame animation variables
        self.walk_frame = 0  # 0 or 1
        self.distance_accumulator = 0.0
        
    def set_target_x(self, x):
        """Set target position."""
        if x is None:
            self.freeze()
        else:
            self.unfreeze()
            BORDER_WIDTH = 200
            margin = BORDER_WIDTH + self.width // 2
            self.target_x = max(margin, min(x, self.screen_width - margin))
    
    def freeze(self):
        self.frozen = True
    
    def unfreeze(self):
        self.frozen = False
    
    def set_expression(self, expression, duration=0.5):
        """DEPRECATED: Expressions moved to Perla HUD."""
        pass
    
    def update(self, dt):
        """Update movement and animation frame."""
        if not self.frozen:
            diff = self.target_x - self.x
            
            # Determine facing direction (threshold: 10px)
            if diff < -self.move_threshold:
                new_facing = 'left'
            elif diff > self.move_threshold:
                new_facing = 'right'
            else:
                new_facing = 'idle'
            
            # Reset animation when stopping or changing direction
            if new_facing == 'idle' or new_facing != self.facing:
                self.walk_frame = 0
                self.distance_accumulator = 0
            
            self.facing = new_facing
            
            # Move player
            movement = diff * self.lerp_speed
            self.x += movement
            
            # NEW: Track distance for frame animation (toggle every 20px)
            if self.facing != 'idle':
                self.distance_accumulator += abs(movement)
                if self.distance_accumulator >= 20:
                    self.walk_frame = 1 - self.walk_frame  # Toggle 0 <-> 1
                    self.distance_accumulator = 0
    
    def render(self, screen):
        """Draw player sprite with 2-frame animation."""
        # NEW: Select sprite based on facing and animation frame
        if self.facing == 'left':
            sprite_key = 'new_sprite_left' if self.walk_frame == 0 else 'new_sprite_left_extend'
        elif self.facing == 'right':
            sprite_key = 'new_sprite_right' if self.walk_frame == 0 else 'new_sprite_right_extend'
        else:
            sprite_key = 'new_sprite_default'
        
        sprite = self.assets.get(sprite_key) if self.assets else None
        
        if sprite:
            rect = sprite.get_rect()
            rect.centerx = int(self.x)
            rect.bottom = int(self.y + self.height // 2 - 10)
            screen.blit(sprite, rect)
        else:
            # Fallback rectangle
            color = (100, 200, 255)
            rect = pygame.Rect(
                self.x - self.width // 2,
                self.y - self.height // 2,
                self.width,
                self.height
            )
            pygame.draw.rect(screen, color, rect, border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), rect, width=2, border_radius=10)
        
        # Hand lost indicator
        if self.frozen:
            pulse = abs(math.sin(pygame.time.get_ticks() / 200)) * 10
            pygame.draw.circle(screen, (255, 50, 50),
                             (int(self.x), int(self.y)),
                             self.width // 2 + 15 + int(pulse), 3)
            
            font = pygame.font.Font(None, 36)
            text = font.render("HAND LOST", True, (255, 50, 50))
            text_rect = text.get_rect(center=(int(self.x), int(self.y) - 100))
            screen.blit(text, text_rect)
    
    def get_hitbox(self):
        """Return basket hitbox."""
        basket_y = self.y - self.basket_offset_y
        return pygame.Rect(
            self.x - self.basket_width // 2,
            basket_y - self.basket_height // 2,
            self.basket_width,
            self.basket_height
        )
    
    def reset(self):
        """Reset position."""
        self.x = self.screen_width // 2
        self.target_x = self.x
        self.frozen = False
        self.facing = 'idle'
        # NEW: Reset animation
        self.walk_frame = 0
        self.distance_accumulator = 0
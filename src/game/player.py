import pygame
import math


class Player:
    def __init__(self, screen_width, screen_height, asset_manager=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.assets = asset_manager
        
        # Position (fixed Y per Gio's spec)
        self.x = screen_width // 2
        self.y = 970
        
        # Lerp smoothing
        self.lerp_speed = 0.15
        self.target_x = self.x
        
        # Freeze state for hand loss
        self.frozen = False
        
        # Sprite dimensions
        self.width = 140
        self.height = 150
        
        # Direction tracking: idle, left, right
        self.facing = 'idle'
        self.move_threshold = 40  # px difference before sprite switches direction
        
        # Visual offset
        self.sprite_offset_y = 30

        # Basket hitbox 
        self.basket_width = 70   
        self.basket_height = 40  
        self.basket_offset_y = 175
        
    def set_target_x(self, x):
        """Called by GestureController - x is screen coordinate or None"""
        if x is None:
            self.freeze()
        else:
            self.unfreeze()
            BORDER_WIDTH = 200
            margin = BORDER_WIDTH + self.width // 2
            self.target_x = max(margin, min(x, self.screen_width - margin))
    
    def freeze(self):
        """Hand lost - stop lerping, hold position"""
        self.frozen = True
    
    def unfreeze(self):
        """Hand found - resume normal movement"""
        self.frozen = False
    
    def update(self, dt):
        """Update position with lerp smoothing."""
        if not self.frozen:
            diff = self.target_x - self.x

            # Only switch sprite if movement exceeds threshold
            if diff < -self.move_threshold:
                self.facing = 'left'
            elif diff > self.move_threshold:
                self.facing = 'right'
            else:
                self.facing = 'idle'  # Within threshold = show normal sprite

            self.x += diff * self.lerp_speed
    
    def render(self, screen):
        """Draw player sprite based on movement direction."""
        if self.facing == 'left':
            sprite_key = 'sprite_left'
        elif self.facing == 'right':
            sprite_key = 'sprite_right'
        else:
            sprite_key = 'sprite_idle'

        sprite = self.assets.get(sprite_key) if self.assets else None

        if sprite:
            rect = sprite.get_rect()
            rect.centerx = int(self.x)
            rect.bottom = int(self.y + self.height // 2 - 10)
            screen.blit(sprite, rect)
        else:
            # Fallback rectangle
            rect = pygame.Rect(
                self.x - self.width // 2,
                self.y - self.height // 2,
                self.width,
                self.height
            )
            pygame.draw.rect(screen, (100, 200, 255), rect, border_radius=10)
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
        """Hitbox positioned at the basket (top of sprite)."""
        basket_y = self.y - self.basket_offset_y
        return pygame.Rect(
            self.x - self.basket_width // 2,
            basket_y - self.basket_height // 2,
            self.basket_width,
            self.basket_height
        )
    
    def get_hitbox_visual(self):
        """Optional: draw hitbox for debugging."""
        return self.get_hitbox()
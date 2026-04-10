"""
player.py - MODIFIED FOR CAPIZTAHAN
Added: Expression system for Billy mascot (Jen)
Keeps: Original movement system (Gio/Rey)
"""

import pygame
import math
import random
from enum import Enum


class Expression(Enum):
    NEUTRAL = "neutral"
    EXCITED = "excited"
    SUPER_EXCITED = "super_excited"
    SAD = "sad"


class Player:
    def __init__(self, screen_width, screen_height, asset_manager=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.assets = asset_manager
        
        # Position (keep original)
        self.x = screen_width // 2
        self.y = 970
        self.lerp_speed = 0.15
        self.target_x = self.x
        self.frozen = False
        
        # Original sprite dimensions
        self.width = 140
        self.height = 150
        self.facing = 'idle'
        self.move_threshold = 40
        self.sprite_offset_y = 30
        
        # Basket hitbox (original)
        self.basket_width = 70
        self.basket_height = 40
        self.basket_offset_y = 175
        
        # Expression System (Jen)
        self.current_expression = Expression.NEUTRAL
        self.expression_timer = 0
        self.expression_duration = 0
        
        # Particle effects for catches
        self.particles = []
        
        # Expression colors (for placeholder sprites)
        self.expression_tints = {
            Expression.NEUTRAL: (255, 255, 255),
            Expression.EXCITED: (255, 255, 150),
            Expression.SUPER_EXCITED: (255, 150, 255),
            Expression.SAD: (150, 150, 200)
        }
        
        # Blinking
        self.blink_timer = 0
        self.is_blinking = False
        self.next_blink = random.uniform(2.0, 4.0)
        
        # FIXED: Store initial Y for reset
        self._initial_y = 970
    
    def set_target_x(self, x):
        """Original method - unchanged"""
        if x is None:
            self.freeze()
        else:
            self.unfreeze()
            BORDER_WIDTH = 200
            margin = BORDER_WIDTH + self.width // 2
            self.target_x = max(margin, min(x, self.screen_width - margin))
    
    def freeze(self):
        """Original method"""
        self.frozen = True
    
    def unfreeze(self):
        """Original method"""
        self.frozen = False
    
    def set_expression(self, expression_input, duration=0.5):
        """
        Set Billy's expression. Auto-reverts to neutral after duration.
        Called by game loop when catches happen.
        """
        # Convert string to enum if needed
        if isinstance(expression_input, str):
            expression_map = {
                'neutral': Expression.NEUTRAL,
                'excited': Expression.EXCITED,
                'super_excited': Expression.SUPER_EXCITED,
                'sad': Expression.SAD
            }
            expression = expression_map.get(expression_input, Expression.NEUTRAL)
        elif isinstance(expression_input, Expression):
            expression = expression_input
        else:
            expression = Expression.NEUTRAL
        
        # Don't interrupt super excited with just excited
        if (self.current_expression == Expression.SUPER_EXCITED and 
            expression == Expression.EXCITED and 
            self.expression_timer > 0):
            return
        
        self.current_expression = expression
        self.expression_duration = duration
        self.expression_timer = duration
        
        # Effects based on expression
        if expression == Expression.SUPER_EXCITED:
            self._spawn_particles(15, (255, 215, 0))  # Gold
        elif expression == Expression.EXCITED:
            self._spawn_particles(8, (100, 255, 100))  # Green
    
    def _spawn_particles(self, count, color):
        """Spawn celebration particles"""
        for _ in range(count):
            self.particles.append({
                'x': self.x + random.randint(-50, 50),
                'y': self.y - 80,
                'vx': random.uniform(-4, 4),
                'vy': random.uniform(-6, -3),
                'life': 1.0,
                'color': color,
                'size': random.randint(5, 10)
            })
    
    def update(self, dt):
        """Modified: Added expression and particle updates"""
        # Movement code (unchanged)
        if not self.frozen:
            diff = self.target_x - self.x
            
            if diff < -self.move_threshold:
                self.facing = 'left'
            elif diff > self.move_threshold:
                self.facing = 'right'
            else:
                self.facing = 'idle'
            
            self.x += diff * self.lerp_speed
        
        # Expression timer
        if self.expression_timer > 0:
            self.expression_timer -= dt
            if self.expression_timer <= 0:
                self.current_expression = Expression.NEUTRAL
        
        # Particle physics
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 200 * dt  # Gravity
            p['life'] -= 1.5 * dt
            if p['life'] <= 0:
                self.particles.remove(p)
        
        # Blinking
        self.blink_timer += dt
        if self.blink_timer >= self.next_blink:
            self.is_blinking = True
            if self.blink_timer >= self.next_blink + 0.15:
                self.is_blinking = False
                self.blink_timer = 0
                self.next_blink = random.uniform(2.0, 4.0)
    
    def render(self, screen):
        """Modified: Added particles and expression visualization"""
        # Draw particles behind player
        for p in self.particles:
            alpha = int(255 * p['life'])
            particle_surf = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            color_with_alpha = (*p['color'][:3], alpha)
            pygame.draw.circle(particle_surf, color_with_alpha, 
                             (p['size'], p['size']), int(p['size'] * p['life']))
            screen.blit(particle_surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
        
        # Sprite selection
        if self.facing == 'left':
            sprite_key = 'sprite_left'
        elif self.facing == 'right':
            sprite_key = 'sprite_right'
        else:
            sprite_key = 'sprite_idle'
        
        sprite = self.assets.get(sprite_key) if self.assets else None
        
        if sprite:
            # Apply expression tint
            tinted = sprite.copy()
            if self.current_expression != Expression.NEUTRAL:
                tint = self.expression_tints[self.current_expression]
                tinted.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
            
            rect = tinted.get_rect()
            rect.centerx = int(self.x)
            rect.bottom = int(self.y + self.height // 2 - 10)
            screen.blit(tinted, rect)
            
            # FIXED: Draw blinking overlay when blinking
            if self.is_blinking:
                blink_surf = pygame.Surface((rect.width, rect.height // 5), pygame.SRCALPHA)
                blink_surf.fill((0, 0, 0, 200))
                # Position over eyes (approximate)
                blink_rect = blink_surf.get_rect(center=(rect.centerx, rect.top + rect.height // 4))
                screen.blit(blink_surf, blink_rect)
            
            # Draw expression indicator above head
            if self.current_expression != Expression.NEUTRAL:
                self._draw_expression_indicator(screen)
        else:
            # Fallback with expression color
            color = (100, 200, 255)
            if self.current_expression == Expression.EXCITED:
                color = (255, 200, 100)
            elif self.current_expression == Expression.SUPER_EXCITED:
                color = (255, 100, 255)
            elif self.current_expression == Expression.SAD:
                color = (100, 100, 150)
            
            rect = pygame.Rect(
                self.x - self.width // 2,
                self.y - self.height // 2,
                self.width,
                self.height
            )
            pygame.draw.rect(screen, color, rect, border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), rect, width=2, border_radius=10)
            
            # FIXED: Draw blinking for fallback too
            if self.is_blinking:
                pygame.draw.rect(screen, (0, 0, 0), 
                               (rect.centerx - 20, rect.top + 20, 40, 10), border_radius=5)
        
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
    
    def _draw_expression_indicator(self, screen):
        """Draw icon above head showing current expression"""
        indicators = {
            Expression.EXCITED: "★",
            Expression.SUPER_EXCITED: "★★",
            Expression.SAD: "..."
        }
        
        if self.current_expression in indicators:
            font = pygame.font.Font(None, 48)
            text = font.render(indicators[self.current_expression], True, (255, 215, 0))
            text_rect = text.get_rect(center=(self.x, self.y - 120))
            screen.blit(text, text_rect)
    
    def get_hitbox(self):
        """Original method - unchanged"""
        basket_y = self.y - self.basket_offset_y
        return pygame.Rect(
            self.x - self.basket_width // 2,
            basket_y - self.basket_height // 2,
            self.basket_width,
            self.basket_height
        )
    
    def get_hitbox_visual(self):
        """Original method"""
        return self.get_hitbox()
    
    def reset(self):
        """FIXED: Fully reset all state for new game"""
        self.x = self.screen_width // 2
        self.target_x = self.x
        self.y = self._initial_y
        self.current_expression = Expression.NEUTRAL
        self.expression_timer = 0
        self.expression_duration = 0
        self.particles = []
        self.frozen = False
        self.facing = 'idle'
        self.blink_timer = 0
        self.is_blinking = False
        self.next_blink = random.uniform(2.0, 4.0)
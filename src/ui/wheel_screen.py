"""
wheel_screen.py
Capiztahan Gacha Game - Category Selection Wheel
Author: Jen (UI/UX Engineer)
"""

import pygame
import math
import random
from enum import Enum


class Category(Enum):
    FOOD = "food"
    CULTURE = "culture"
    PEOPLE = "people"


class WheelScreen:
    def __init__(self, screen_width=1920, screen_height=1080, assets=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.assets = assets
        
        # Wheel config
        self.center_x = screen_width // 2
        self.center_y = screen_height // 2 + 50
        self.wheel_radius = 250
        
        # Categories with Capiztahan colors
        self.categories = [
            (Category.FOOD, (255, 107, 107)),      # Coral red
            (Category.CULTURE, (78, 205, 196)),    # Turquoise  
            (Category.PEOPLE, (255, 230, 109))     # Golden yellow
        ]
        self.segment_angle = 360 / len(self.categories)
        
        # Animation states
        self.SPINNING = "spinning"
        self.SELECTED = "selected"
        self.TRANSITIONING = "transitioning"
        self.state = self.SPINNING
        
        # Spin parameters (5 seconds smooth spin)
        self.spin_duration = 5000
        self.current_rotation = 0
        self.target_rotation = 0
        self.spin_start_time = 0
        
        # Selection
        self.selected_category = None
        self.selection_time = 0
        self.transition_delay = 2000  # 2s auto-advance
        
        # Pointer animation
        self.pointer_bounce = 0
        self.pointer_direction = 1
        
        # Fonts
        self.font_large = pygame.font.Font(None, 100)
        self.font_medium = pygame.font.Font(None, 60)
        self.font_small = pygame.font.Font(None, 40)
        
        # Callback
        self.on_category_selected = None
        
        self._calculate_spin()
    
    def _calculate_spin(self):
        """Calculate target rotation for random selection"""
        full_rotations = random.randint(3, 5) * 360
        random_offset = random.randint(0, 359)
        self.target_rotation = full_rotations + random_offset
        
        # Determine selected category (pointer at top = 270 degrees)
        final_angle = (self.target_rotation + 270) % 360
        segment_index = int(final_angle / self.segment_angle) % len(self.categories)
        self.selected_category = self.categories[segment_index][0]
    
    def start(self):
        """Start spinning"""
        self.state = self.SPINNING
        self.spin_start_time = pygame.time.get_ticks()
        self.current_rotation = 0
        self._calculate_spin()
        print(f"[Wheel] Will select: {self.selected_category.value}")
    
    def update(self, dt):
        """Update animation"""
        current_time = pygame.time.get_ticks()
        
        if self.state == self.SPINNING:
            elapsed = current_time - self.spin_start_time
            
            if elapsed < self.spin_duration:
                # Smooth ease-out
                progress = elapsed / self.spin_duration
                ease_progress = 1 - (1 - progress) ** 3
                self.current_rotation = self.target_rotation * ease_progress
            else:
                self.current_rotation = self.target_rotation
                self.state = self.SELECTED
                self.selection_time = current_time
                
                if self.on_category_selected:
                    self.on_category_selected(self.selected_category)
        
        elif self.state == self.SELECTED:
            if current_time - self.selection_time >= self.transition_delay:
                self.state = self.TRANSITIONING
        
        # Pointer bounce
        self.pointer_bounce += 0.3 * self.pointer_direction
        if abs(self.pointer_bounce) > 8:
            self.pointer_direction *= -1
    
    def draw(self, screen):
        """Render wheel"""
        # Dark gradient background
        for y in range(self.screen_height):
            color_val = int(15 + (y / self.screen_height) * 30)
            pygame.draw.line(screen, (color_val // 2, color_val // 3, color_val), 
                           (0, y), (self.screen_width, y))
        
        # Title
        title = self.font_large.render("SPIN THE WHEEL!", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.center_x, 100))
        screen.blit(title, title_rect)
        
        subtitle = self.font_small.render("Discover Capiztahan's treasures...", True, (200, 200, 200))
        sub_rect = subtitle.get_rect(center=(self.center_x, 170))
        screen.blit(subtitle, sub_rect)
        
        # Draw wheel
        self._draw_wheel(screen)
        
        # Draw pointer at top
        self._draw_pointer(screen)
        
        # Center hub
        pygame.draw.circle(screen, (40, 40, 60), (self.center_x, self.center_y), 40)
        pygame.draw.circle(screen, (255, 255, 255), (self.center_x, self.center_y), 25)
        
        # Result overlay
        if self.state in [self.SELECTED, self.TRANSITIONING]:
            self._draw_result(screen)
        
        # Countdown
        if self.state == self.SELECTED:
            elapsed = pygame.time.get_ticks() - self.selection_time
            remaining = max(0, (self.transition_delay - elapsed) // 1000 + 1)
            countdown = self.font_small.render(f"Starting in {remaining}...", True, (255, 255, 255))
            count_rect = countdown.get_rect(center=(self.center_x, self.screen_height - 100))
            screen.blit(countdown, count_rect)
    
    def _draw_wheel(self, screen):
        """Draw wheel segments"""
        for i, (category, color) in enumerate(self.categories):
            start_angle = math.radians(self.current_rotation + i * self.segment_angle)
            end_angle = math.radians(self.current_rotation + (i + 1) * self.segment_angle)
            
            # Draw segment
            points = [(self.center_x, self.center_y)]
            steps = 30
            for step in range(steps + 1):
                angle = start_angle + (end_angle - start_angle) * step / steps
                x = self.center_x + math.cos(angle) * self.wheel_radius
                y = self.center_y + math.sin(angle) * self.wheel_radius
                points.append((x, y))
            
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 4)
            
            # Label
            mid_angle = start_angle + (end_angle - start_angle) / 2
            label_x = self.center_x + math.cos(mid_angle) * (self.wheel_radius * 0.6)
            label_y = self.center_y + math.sin(mid_angle) * (self.wheel_radius * 0.6)
            
            label = category.value.upper()
            text = self.font_medium.render(label, True, (30, 30, 30))
            text_rect = text.get_rect(center=(label_x, label_y))
            screen.blit(text, text_rect)
        
        # Outer ring
        pygame.draw.circle(screen, (255, 255, 255), (self.center_x, self.center_y), 
                          self.wheel_radius, 6)
    
    def _draw_pointer(self, screen):
        """Draw pointer at top"""
        pointer_y = self.center_y - self.wheel_radius - 30 + self.pointer_bounce
        
        # Triangle pointer
        points = [
            (self.center_x, pointer_y),
            (self.center_x - 25, pointer_y - 40),
            (self.center_x + 25, pointer_y - 40)
        ]
        pygame.draw.polygon(screen, (255, 215, 0), points)
        pygame.draw.polygon(screen, (180, 140, 0), points, 3)
        pygame.draw.circle(screen, (255, 50, 50), (self.center_x, pointer_y - 20), 10)
    
    def _draw_result(self, screen):
        """Draw selection result modal"""
        # Overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Box
        box_w, box_h = 600, 250
        box_x = (self.screen_width - box_w) // 2
        box_y = (self.screen_height - box_h) // 2
        
        pygame.draw.rect(screen, (255, 215, 0), (box_x - 5, box_y - 5, box_w + 10, box_h + 10), border_radius=25)
        pygame.draw.rect(screen, (40, 40, 60), (box_x, box_y, box_w, box_h), border_radius=20)
        
        # Result text
        result_text = f"{self.selected_category.value.upper()}!"
        text = self.font_large.render(result_text, True, (255, 215, 0))
        text_rect = text.get_rect(center=(self.center_x, box_y + 90))
        screen.blit(text, text_rect)
        
        # Description
        descriptions = {
            Category.FOOD: "Discover Capiz delicacies!",
            Category.CULTURE: "Explore rich traditions!",
            Category.PEOPLE: "Meet the local heroes!"
        }
        desc = self.font_small.render(descriptions[self.selected_category], True, (255, 255, 255))
        desc_rect = desc.get_rect(center=(self.center_x, box_y + 160))
        screen.blit(desc, desc_rect)
    
    def is_transitioning(self):
        """Check if ready to go to game"""
        return self.state == self.TRANSITIONING
    
    def get_selected_category(self):
        return self.selected_category
    
    def reset(self):
        """Reset for next time"""
        self.state = self.SPINNING
        self.current_rotation = 0
        self.spin_start_time = pygame.time.get_ticks()
        self._calculate_spin()
    
    def handle_event(self, event):
        """Handle input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.state == self.SPINNING:
                # Skip to end
                self.current_rotation = self.target_rotation
                self.state = self.SELECTED
                self.selection_time = pygame.time.get_ticks()
                if self.on_category_selected:
                    self.on_category_selected(self.selected_category)
            elif event.key == pygame.K_RETURN and self.state == self.SELECTED:
                self.state = self.TRANSITIONING


def show_wheel_screen(screen, screen_width=1920, screen_height=1080, 
                     gesture_controller=None, assets=None):
    """
    Main wheel screen loop.
    Returns selected category string or None if quit.
    """
    clock = pygame.time.Clock()
    wheel = WheelScreen(screen_width, screen_height, assets)
    wheel.start()
    
    selected_category = None
    
    while True:
        dt = clock.tick(60) / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            
            wheel.handle_event(event)
        
        # Update camera feed (keep it live)
        if gesture_controller:
            gesture_controller.update()
            debug_frame = gesture_controller.get_debug_frame()
            if debug_frame is not None:
                import cv2
                cv2.imshow("GAMEFRICKS PROTOTYPE01 - Camera Feed", debug_frame)
                cv2.waitKey(1)
        
        wheel.update(dt)
        wheel.draw(screen)
        pygame.display.flip()
        
        if wheel.is_transitioning():
            return wheel.get_selected_category().value
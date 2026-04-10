"""
wheel_screen.py - CAPIZTAHAN GACHA WHEEL (CLEANED - No Duplicates)
"""

import pygame
import math
import random
from enum import Enum


class Category(Enum):
    FOOD = "food"
    CULTURE = "culture"
    PEOPLE = "people"


def rot_center(image, angle, x, y):
    """Rotates an image and keeps its center at (x, y)"""
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=(x, y))
    return rotated_image, new_rect


class WheelScreen:
    def __init__(self, screen_width=1920, screen_height=1080, assets=None, background=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.assets = assets
        self.background = background
        
        # === ADJUST THESE FOR BIGGER/OUTER ICONS ===
        self.wheel_radius = 220          
        self.icon_size = 280             # INCREASED from 240 for bigger icons
        self.icon_distance = 1.3        # INCREASED from 0.85 for outer position (try 1.0 or 1.1)
        self.wheel_scale = 0.6
        
        self.icon_angles = {
            Category.FOOD: -15,        
            Category.CULTURE: 105,   
            Category.PEOPLE: 225    
        }
        
        self.center_x = screen_width // 2
        self.center_y = screen_height // 2 + 50
        
        self.categories = [Category.FOOD, Category.CULTURE, Category.PEOPLE]
        self.segment_angle = 120
        
        self.STATE_POPPING = "popping"
        self.STATE_SPINNING = "spinning"
        self.STATE_SELECTED = "selected"
        self.STATE_TRANSITIONING = "transitioning"
        self.state = self.STATE_POPPING
        
        self.pop_duration = 800
        self.pop_progress = 0.0
        self.current_scale = 0.0
        self.current_alpha = 0
        
        self.spin_duration = 5000
        self.current_rotation = 0
        self.target_rotation = 0
        self.spin_start_time = 0
        
        self.selected_category = None
        self.selection_time = 0
        self.transition_delay = 2000
        
        self.pointer_bounce = 0
        self.pointer_direction = 1
        
        self.font_large = pygame.font.Font(None, 100)
        self.font_medium = pygame.font.Font(None, 60)
        self.font_small = pygame.font.Font(None, 40)
        
        self.on_category_selected = None
        
        self._load_assets()
        self._calculate_spin()
    
    def _load_assets(self):
        if self.assets:
            wheel_img = self.assets.get('wheel_base')
            self.icons_orig = {
                Category.FOOD: self.assets.get('perla_food'),
                Category.CULTURE: self.assets.get('perla_culture'),
                Category.PEOPLE: self.assets.get('perla_people')
            }
        else:
            wheel_img = None
            self.icons_orig = {}
        
        if not wheel_img:
            wheel_img = self._create_wheel_placeholder()
        
        for cat in Category:
            if not self.icons_orig.get(cat):
                self.icons_orig[cat] = self._create_icon_placeholder(cat)
        
        self.wheel_orig = self._make_square(wheel_img)
    
    def _make_square(self, surface):
        w, h = surface.get_size()
        if w != h:
            size = max(w, h)
            square = pygame.Surface((size, size), pygame.SRCALPHA)
            x_off = (size - w) // 2
            y_off = (size - h) // 2
            square.blit(surface, (x_off, y_off))
            return square
        return surface.copy()
    
    def _create_wheel_placeholder(self):
        size = self.wheel_radius * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = self.wheel_radius
        
        colors = [(255, 107, 107), (78, 205, 196), (255, 230, 109)]
        for i, color in enumerate(colors):
            start_angle = math.radians(i * 120 - 90)
            end_angle = math.radians((i + 1) * 120 - 90)
            points = [(center, center)]
            for step in range(31):
                angle = start_angle + (end_angle - start_angle) * step / 30
                x = center + math.cos(angle) * self.wheel_radius
                y = center + math.sin(angle) * self.wheel_radius
                points.append((x, y))
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, (255, 255, 255), points, 4)
        return surf
    
    def _create_icon_placeholder(self, category):
        size = self.icon_size
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        colors = {
            Category.FOOD: (255, 107, 107),
            Category.CULTURE: (78, 205, 196),
            Category.PEOPLE: (255, 230, 109)
        }
        color = colors.get(category, (200, 200, 200))
        center = size // 2
        pygame.draw.circle(surf, color, (center, center), center - 5)
        pygame.draw.circle(surf, (255, 255, 255), (center, center), center - 5, 3)
        font = pygame.font.Font(None, 36)
        text = font.render(category.value[:4].upper(), True, (0, 0, 0))
        text_rect = text.get_rect(center=(center, center))
        surf.blit(text, text_rect)
        return surf
    
    def _ease_out_back(self, x):
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(x - 1, 3) + c1 * pow(x - 1, 2)
    
    def start(self):
        self.state = self.STATE_POPPING
        self.pop_progress = 0.0
        self.current_scale = 0.0
        self.current_alpha = 0
        self.current_rotation = 0
        self._calculate_spin()
        print(f"[Wheel] Will select: {self.selected_category.value}")
    
    def _calculate_spin(self):
        full_rotations = random.randint(3, 5) * 360
        random_offset = random.randint(0, 359)
        self.target_rotation = full_rotations + random_offset
        
        # Changed from 270 to 15 to align with FOOD icon at -15°
        # When wheel rotates +15°, FOOD (-15°) reaches top (0°)
        final_angle = (self.target_rotation + 15) % 360
        segment_index = int(final_angle / self.segment_angle) % 3
        
        # Reordered: FOOD (0-120°), PEOPLE (120-240°), CULTURE (240-360°)
        # This matches the physical positions when each icon reaches the top
        self.categories = [Category.FOOD, Category.PEOPLE, Category.CULTURE]
        self.selected_category = self.categories[segment_index]
        
        print(f"[Wheel] Target rotation: {self.target_rotation}°, Final angle: {final_angle}°, Segment: {segment_index}, Selected: {self.selected_category.value}")
    
    def update(self, dt):
        current_time = pygame.time.get_ticks()
        
        if self.state == self.STATE_POPPING:
            self.pop_progress += (dt * 1000) / self.pop_duration
            if self.pop_progress >= 1.0:
                self.pop_progress = 1.0
                self.state = self.STATE_SPINNING
                self.spin_start_time = current_time
            
            eased = self._ease_out_back(self.pop_progress)
            self.current_scale = max(0.0, eased)
            self.current_alpha = int(255 * min(1.0, self.pop_progress))
        
        elif self.state == self.STATE_SPINNING:
            elapsed = current_time - self.spin_start_time
            if elapsed < self.spin_duration:
                progress = elapsed / self.spin_duration
                ease_progress = 1 - pow(1 - progress, 3)
                self.current_rotation = self.target_rotation * ease_progress
            else:
                self.current_rotation = self.target_rotation
                self.state = self.STATE_SELECTED
                self.selection_time = current_time
                if self.on_category_selected:
                    self.on_category_selected(self.selected_category)
        
        elif self.state == self.STATE_SELECTED:
            if current_time - self.selection_time >= self.transition_delay:
                self.state = self.STATE_TRANSITIONING
        
        self.pointer_bounce += 0.3 * self.pointer_direction
        if abs(self.pointer_bounce) > 8:
            self.pointer_direction *= -1
    
    def draw(self, screen):
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((20, 20, 30))
        
        overlay_alpha = int(180 * self.pop_progress) if self.state == self.STATE_POPPING else 180
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0))
        overlay.set_alpha(overlay_alpha)
        screen.blit(overlay, (0, 0))
        
        title = self.font_large.render("SPIN THE WHEEL!", True, (255, 215, 0))
        screen.blit(title, title.get_rect(center=(self.center_x, 100)))
        
        subtitle = self.font_small.render("Discover Capiztahan's treasures...", True, (220, 220, 200))
        screen.blit(subtitle, subtitle.get_rect(center=(self.center_x, 170)))
        
        self._draw_wheel(screen)
        self._draw_pointer(screen)
        
        if self.state in [self.STATE_SELECTED, self.STATE_TRANSITIONING]:
            self._draw_result(screen)
        
        if self.state == self.STATE_SELECTED:
            elapsed = pygame.time.get_ticks() - self.selection_time
            remaining = max(0, (self.transition_delay - elapsed) // 1000 + 1)
            countdown = self.font_small.render(f"Starting in {remaining}...", True, (255, 255, 255))
            screen.blit(countdown, countdown.get_rect(center=(self.center_x, self.screen_height - 100)))
    
    def _draw_wheel(self, screen):
        """Draw wheel with upright icons - CLEAN VERSION (no duplicates)"""
        if self.current_scale <= 0.01:
            return
        
        # === DRAW WHEEL ===
        base_size = self.wheel_orig.get_width()
        new_size = int(base_size * self.current_scale * self.wheel_scale)
        
        scaled_wheel = pygame.transform.smoothscale(self.wheel_orig, (new_size, new_size))
        wheel_img, wheel_rect = rot_center(scaled_wheel, -self.current_rotation, self.center_x, self.center_y)
        
        if self.state == self.STATE_POPPING and self.current_alpha < 255:
            wheel_img.set_alpha(self.current_alpha)
        
        screen.blit(wheel_img, wheel_rect)
        
        # === DRAW ICONS (UPRIGHT - NO ROTATION) ===
        for category in self.categories:
            base_angle = self.icon_angles[category]
            current_angle = base_angle + self.current_rotation
            rad = math.radians(current_angle - 90)
            
            # IMPORTANT: Include wheel_scale so icons scale with wheel!
            distance = self.wheel_radius * self.icon_distance * self.current_scale * self.wheel_scale
            x = self.center_x + math.cos(rad) * distance
            y = self.center_y + math.sin(rad) * distance
            
            icon_orig = self.icons_orig[category]
            if icon_orig:
                # Scale icon with wheel_scale too
                new_icon_size = int(self.icon_size * self.current_scale * self.wheel_scale)
                scaled_icon = pygame.transform.smoothscale(icon_orig, (new_icon_size, new_icon_size))
                
                # UPRIGHT: Just center, don't rotate
                icon_rect = scaled_icon.get_rect(center=(int(x), int(y)))
                
                if self.state == self.STATE_POPPING and self.current_alpha < 255:
                    scaled_icon.set_alpha(self.current_alpha)
                
                screen.blit(scaled_icon, icon_rect)
    
    def _draw_pointer(self, screen):
        # 1 o'clock position: 330 degrees (30 degrees clockwise from top)
        # 0=right, 90=down, 180=left, 270=up, 330=1 o'clock
        angle = math.radians(300)
        
        # Distance from center: wheel radius + margin to sit outside
        distance = self.wheel_radius * self.current_scale * self.wheel_scale + 200
        
        # Base position at 1 o'clock
        base_x = self.center_x + math.cos(angle) * distance
        base_y = self.center_y + math.sin(angle) * distance
        
        # Bounce effect (radial - toward/away from center)
        bounce = self.pointer_bounce * self.current_scale
        pointer_x = base_x + math.cos(angle) * bounce
        pointer_y = base_y + math.sin(angle) * bounce
        scale = self.current_scale
        
        # Triangle points toward center (down-left from 1 o'clock)
        # Tip is closer to center, base is at pointer position
        tip_dist = 35 * scale
        half_base = 20 * scale
        
        # Vector pointing toward center
        dx = -math.cos(angle)  # negative because we want inward
        dy = -math.sin(angle)
        
        # Perpendicular vector for base width
        perp_x = -dy
        perp_y = dx
        
        # Calculate triangle points
        tip_x = pointer_x + dx * tip_dist
        tip_y = pointer_y + dy * tip_dist
        
        base1_x = pointer_x + perp_x * half_base
        base1_y = pointer_y + perp_y * half_base
        base2_x = pointer_x - perp_x * half_base
        base2_y = pointer_y - perp_y * half_base
        
        points = [(tip_x, tip_y), (base1_x, base1_y), (base2_x, base2_y)]
        
        pygame.draw.polygon(screen, (255, 50, 50), points)
        pygame.draw.polygon(screen, (255, 215, 0), points, max(1, int(3 * scale)))
        pygame.draw.circle(screen, (255, 215, 0), (int(pointer_x), int(pointer_y)), int(8 * scale))
    
    def _draw_result(self, screen):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        box_w, box_h = 600, 300
        box_x = (self.screen_width - box_w) // 2
        box_y = (self.screen_height - box_h) // 2
        
        pygame.draw.rect(screen, (255, 215, 0), (box_x - 5, box_y - 5, box_w + 10, box_h + 10), border_radius=25)
        pygame.draw.rect(screen, (40, 40, 60), (box_x, box_y, box_w, box_h), border_radius=20)
        
        result_text = f"{self.selected_category.value.upper()}!"
        text = self.font_large.render(result_text, True, (255, 215, 0))
        screen.blit(text, text.get_rect(center=(self.center_x, box_y + 80)))
        
        icon = self.icons_orig.get(self.selected_category)
        if icon:
            icon_large = pygame.transform.smoothscale(icon, (120, 120))
            screen.blit(icon_large, icon_large.get_rect(center=(self.center_x, box_y + 170)))
        
        descriptions = {
            Category.FOOD: "Discover Capiz delicacies!",
            Category.CULTURE: "Explore rich traditions!",
            Category.PEOPLE: "Meet the local heroes!"
        }
        desc = self.font_small.render(descriptions[self.selected_category], True, (255, 255, 255))
        screen.blit(desc, desc.get_rect(center=(self.center_x, box_y + 250)))
    
    def is_transitioning(self):
        return self.state == self.STATE_TRANSITIONING
    
    def get_selected_category(self):
        return self.selected_category
    
    def reset(self):
        self.state = self.STATE_POPPING
        self.pop_progress = 0.0
        self.current_scale = 0.0
        self.current_alpha = 0
        self.current_rotation = 0
        self._calculate_spin()
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.state == self.STATE_SPINNING:
                self.current_rotation = self.target_rotation
                self.state = self.STATE_SELECTED
                self.selection_time = pygame.time.get_ticks()
                if self.on_category_selected:
                    self.on_category_selected(self.selected_category)
            elif event.key == pygame.K_RETURN and self.state == self.STATE_SELECTED:
                self.state = self.STATE_TRANSITIONING
            elif event.key == pygame.K_ESCAPE:
                return "quit"
        return None


def show_wheel_screen(screen, screen_width=1920, screen_height=1080, 
                     gesture_controller=None, assets=None, background=None):
    clock = pygame.time.Clock()
    wheel = WheelScreen(screen_width, screen_height, assets, background)
    wheel.start()
    
    while True:
        dt = clock.tick(60) / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            result = wheel.handle_event(event)
            if result == "quit":
                return None
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
        
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
import pygame
import sys
import cv2
from src.game.player import Player
from src.game.falling_objects import ObjectManager
from src.game.game_state import GameState

# Try to import CV controller, fallback to mouse if unavailable
try:
    from src.cv.gesture_controller import GestureController
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False
    print("[WARNING] CV modules not available, using mouse fallback")


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60


class GameLoop:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gesture Cafe - GameFrick")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game components
        self.player = Player(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.object_manager = ObjectManager(SCREEN_WIDTH)
        self.game_state = GameState()
        
        # CV Integration
        self.gesture_controller = None
        self.use_cv = False
        self.debug_window = False
        
        # Fonts for HUD
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)
        
        # Hand loss indicator timer
        self.hand_lost_timer = 0
    
    def init_cv(self):
        """Initialize hand tracking."""
        if CV_AVAILABLE:
            try:
                self.gesture_controller = GestureController().start()
                self.use_cv = True
                print("[GameLoop] CV mode active — use your hand!")
            except Exception as e:
                print(f"[GameLoop] CV init failed: {e}")
                print("[GameLoop] Falling back to mouse control")
                self.use_cv = False
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                if event.key == pygame.K_r and self.game_state.game_over:
                    self.game_state.reset()
                    self.object_manager = ObjectManager(SCREEN_WIDTH)
                    if self.gesture_controller:
                        self.gesture_controller.reset()
                    self.hand_lost_timer = 0
                
                # Toggle debug window
                if event.key == pygame.K_d:
                    self.debug_window = not self.debug_window
                    if not self.debug_window:
                        cv2.destroyAllWindows()
            
            # Mouse fallback
            if not self.use_cv and event.type == pygame.MOUSEMOTION:
                mouse_x, _ = pygame.mouse.get_pos()
                self.player.set_target_x(mouse_x)
    
    def update(self, dt):
        if self.game_state.game_over:
            return
        
        # === CV INPUT ===
        if self.use_cv and self.gesture_controller:
            screen_x = self.gesture_controller.update()
            self.player.set_target_x(screen_x)
            
            # Track hand loss for HUD
            if screen_x is None:
                self.hand_lost_timer += dt
            else:
                self.hand_lost_timer = max(0, self.hand_lost_timer - dt * 2)
        
        # === GAME LOGIC ===
        self.player.update(dt)
        
        # Objects
        self.object_manager.update(dt, self.game_state.score)
        
        # Collisions
        caught, missed_good = self.object_manager.check_collisions(
            self.player.get_hitbox()
        )
        
        # Apply rules
        self.game_state.handle_caught(caught)
        self.game_state.handle_missed_good(len(missed_good))
        self.game_state.check_game_over()
    
    def render(self):
        # Clear
        self.screen.fill((30, 30, 40))
        
        if not self.game_state.game_over:
            # Game objects
            self.object_manager.render(self.screen)
            self.player.render(self.screen)
            
            # HUD with hearts and high score
            self._draw_hud()
        else:
            self._draw_game_over()
        
        pygame.display.flip()
        
        # Debug window
        if self.debug_window and self.use_cv and self.gesture_controller:
            debug_frame = self.gesture_controller.get_debug_frame()
            if debug_frame is not None:
                cv2.imshow("CV Debug (D to toggle, Q in window to close)", debug_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.debug_window = False
    
    def _draw_hud(self):
        """Draw score, lives as hearts, high score, speed, hand status."""
        
        # === SCORE (Top Left) ===
        score_text = self.font.render(f"Score: {self.game_state.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))
        
        # === HIGH SCORE (Below Score, Gold color) ===
        high_text = self.small_font.render(f"Best: {self.game_state.high_score}", True, (255, 215, 0))
        self.screen.blit(high_text, (20, 85))
        
        # === LIVES (Visual Hearts) ===
        self._draw_hearts(20, 130)
        
        # === SPEED MULTIPLIER ===
        speed_text = self.small_font.render(
            f"Speed: {self.object_manager.speed_multiplier:.1f}x", 
            True, (200, 200, 200))
        self.screen.blit(speed_text, (20, 195))
        
        # === INPUT MODE (Top Right) ===
        mode_color = (100, 255, 100) if self.use_cv else (255, 255, 100)
        mode_text = "HAND TRACKING" if self.use_cv else "MOUSE MODE"
        mode_surf = self.small_font.render(mode_text, True, mode_color)
        self.screen.blit(mode_surf, (SCREEN_WIDTH - mode_surf.get_width() - 20, 20))
        
        # === HAND LOST WARNING (Center Top, Flashing) ===
        if self.hand_lost_timer > 0.1:
            # Flash effect: show/hide every 200ms
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                warning = self.font.render("! HAND LOST !", True, (255, 50, 50))
                rect = warning.get_rect(center=(SCREEN_WIDTH // 2, 100))
                self.screen.blit(warning, rect)
    
    def _draw_hearts(self, x, y):
        """Draw 3 hearts - red for remaining lives, gray for lost."""
        heart_size = 40
        spacing = 15
        
        for i in range(3):
            heart_x = x + i * (heart_size + spacing)
            
            # Red if alive, dark gray if lost
            if i < self.game_state.lives:
                color = (255, 50, 50)  # Bright red
            else:
                color = (60, 60, 60)   # Dark gray (empty)
            
            self._draw_heart_shape(heart_x, y, heart_size, color)
    
    def _draw_heart_shape(self, x, y, size, color):
        """Draw a single heart using pygame.draw."""
        import pygame.draw as draw
        
        # Heart is two circles + triangle
        radius = size // 3
        center_y = y + radius
        
        # Left circle
        draw.circle(self.screen, color, (x + radius, center_y), radius)
        # Right circle  
        draw.circle(self.screen, color, (x + size - radius, center_y), radius)
        # Bottom point
        points = [
            (x, center_y),
            (x + size, center_y),
            (x + size // 2, y + size)
        ]
        draw.polygon(self.screen, color, points)
    
    def _draw_game_over(self):
        """Game over screen with final score and high score."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        over_text = self.font.render("GAME OVER", True, (255, 80, 80))
        over_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
        self.screen.blit(over_text, over_rect)
        
        # Final score
        score_text = self.font.render(f"Final Score: {self.game_state.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(score_text, score_rect)
        
        # High score (gold)
        high_text = self.font.render(f"Best Score: {self.game_state.high_score}", True, (255, 215, 0))
        high_rect = high_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(high_text, high_rect)
        
        # New high score celebration!
        if self.game_state.score >= self.game_state.high_score and self.game_state.score > 0:
            new_record = self.small_font.render("★ NEW RECORD! ★", True, (255, 215, 0))
            rec_rect = new_record.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            self.screen.blit(new_record, rec_rect)
        
        # Restart instruction
        restart_text = self.small_font.render("Press R to Restart", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self.screen.blit(restart_text, restart_rect)
    
    def run(self):
        # Initialize CV before starting loop
        self.init_cv()
        
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0
                self.handle_events()
                self.update(dt)
                self.render()
        finally:
            # Cleanup
            if self.gesture_controller:
                self.gesture_controller.stop()
            pygame.quit()
            cv2.destroyAllWindows()
            sys.exit()


if __name__ == "__main__":
    game = GameLoop()
    game.run()
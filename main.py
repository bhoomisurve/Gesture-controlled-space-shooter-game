import cv2
import pygame
import mediapipe as mp
import numpy as np
import random
import math
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# Colors - Cute pastel theme
SPACE_DARK = (15, 15, 30)
CUTE_PINK = (255, 182, 193)
SOFT_BLUE = (173, 216, 230)
MINT_GREEN = (152, 251, 152)
LAVENDER = (230, 230, 250)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
RED = (255, 100, 100)
GREEN = (100, 255, 100)

class Particle:
    def __init__(self, x, y, color, size=2):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.color = color
        self.size = size
        self.life = 60
        self.max_life = 60
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(0, self.size * (self.life / self.max_life))
        
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            color = (*self.color[:3], alpha)
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), max(1, int(self.size)))
    
    def is_alive(self):
        return self.life > 0

class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(0.5, 2)
        self.size = random.randint(1, 3)
        self.twinkle = random.randint(0, 60)
        
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = -10
            self.x = random.randint(0, SCREEN_WIDTH)
        self.twinkle = (self.twinkle + 1) % 120
        
    def draw(self, screen):
        alpha = 100 + int(100 * math.sin(self.twinkle * 0.1))
        brightness = max(50, min(255, alpha))
        color = (brightness, brightness, brightness)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)

class Spaceship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.width = 60
        self.height = 50
        self.speed = 8
        self.bob_offset = 0
        self.trail_particles = []
        
    def update(self, hand_x):
        if hand_x is not None:
            self.target_x = int(hand_x * SCREEN_WIDTH)
            self.target_x = max(self.width // 2, min(SCREEN_WIDTH - self.width // 2, self.target_x))
        
        # Smooth movement
        self.x += (self.target_x - self.x) * 0.15
        self.bob_offset += 0.2
        
        # Add cute trail particles
        if random.random() < 0.7:
            self.trail_particles.append(Particle(
                self.x + random.randint(-15, 15), 
                self.y + 20, 
                SOFT_BLUE, 
                random.randint(2, 4)
            ))
        
        # Update trail particles
        self.trail_particles = [p for p in self.trail_particles if p.is_alive()]
        for particle in self.trail_particles:
            particle.update()
    
    def draw(self, screen):
        # Draw trail particles
        for particle in self.trail_particles:
            particle.draw(screen)
            
        current_y = self.y + math.sin(self.bob_offset) * 3
        
        # Draw spaceship body (cute rounded shape)
        pygame.draw.ellipse(screen, MINT_GREEN, 
                          (self.x - self.width//2, current_y - self.height//2, 
                           self.width, self.height))
        pygame.draw.ellipse(screen, WHITE, 
                          (self.x - self.width//2, current_y - self.height//2, 
                           self.width, self.height), 3)
        
        # Draw cute cockpit
        pygame.draw.ellipse(screen, SOFT_BLUE, 
                          (self.x - 15, current_y - 10, 30, 20))
        pygame.draw.ellipse(screen, WHITE, 
                          (self.x - 15, current_y - 10, 30, 20), 2)
        
        # Draw cute eyes
        pygame.draw.circle(screen, WHITE, (int(self.x - 8), int(current_y - 5)), 4)
        pygame.draw.circle(screen, WHITE, (int(self.x + 8), int(current_y - 5)), 4)
        pygame.draw.circle(screen, SPACE_DARK, (int(self.x - 8), int(current_y - 5)), 2)
        pygame.draw.circle(screen, SPACE_DARK, (int(self.x + 8), int(current_y - 5)), 2)

class Laser:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 6
        self.height = 20
        self.speed = 12
        self.glow = 0
        
    def update(self):
        self.y -= self.speed
        self.glow += 0.3
        
    def draw(self, screen):
        # Draw glowing laser effect
        glow_size = 3 + int(2 * math.sin(self.glow))
        
        # Outer glow
        pygame.draw.ellipse(screen, GOLD, 
                          (self.x - glow_size, self.y - self.height//2, 
                           glow_size * 2, self.height))
        # Inner core
        pygame.draw.ellipse(screen, WHITE, 
                          (self.x - self.width//2, self.y - self.height//2, 
                           self.width, self.height))
        
    def is_off_screen(self):
        return self.y < -self.height

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.speed = 1.5 + random.uniform(0, 1)
        self.rotation = 0
        self.hit_particles = []
        
    def update(self):
        self.y += self.speed
        self.rotation += 2
        
        # Update hit particles
        self.hit_particles = [p for p in self.hit_particles if p.is_alive()]
        for particle in self.hit_particles:
            particle.update()
        
    def draw(self, screen):
        # Draw hit particles
        for particle in self.hit_particles:
            particle.draw(screen)
            
        # Draw rotating enemy (cute alien)
        center_x, center_y = int(self.x), int(self.y)
        
        # Main body
        pygame.draw.circle(screen, CUTE_PINK, (center_x, center_y), self.width//2)
        pygame.draw.circle(screen, WHITE, (center_x, center_y), self.width//2, 2)
        
        # Cute antennae
        antenna_offset = 5 * math.sin(math.radians(self.rotation))
        pygame.draw.circle(screen, LAVENDER, 
                         (center_x - 10 + int(antenna_offset), center_y - 15), 3)
        pygame.draw.circle(screen, LAVENDER, 
                         (center_x + 10 - int(antenna_offset), center_y - 15), 3)
        
        # Eyes
        pygame.draw.circle(screen, WHITE, (center_x - 8, center_y - 5), 5)
        pygame.draw.circle(screen, WHITE, (center_x + 8, center_y - 5), 5)
        pygame.draw.circle(screen, SPACE_DARK, (center_x - 8, center_y - 5), 3)
        pygame.draw.circle(screen, SPACE_DARK, (center_x + 8, center_y - 5), 3)
        
    def explode(self):
        for _ in range(15):
            self.hit_particles.append(Particle(
                self.x + random.randint(-20, 20),
                self.y + random.randint(-20, 20),
                random.choice([CUTE_PINK, GOLD, WHITE]),
                random.randint(2, 5)
            ))
        
    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + self.height

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.hand_detected = False
        self.confidence = 0
        
    def find_hands(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        self.hand_detected = bool(self.results.multi_hand_landmarks)
        return img
    
    def find_position(self, img):
        lm_list = []
        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                for id, lm in enumerate(hand_lms.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
                    
                # Calculate confidence based on landmark visibility
                self.confidence = min([lm.visibility for lm in hand_lms.landmark if hasattr(lm, 'visibility')] + [1.0])
        return lm_list
    
    def is_fist(self, lm_list):
        if len(lm_list) == 21:
            fingers = []
            
            # Thumb
            if lm_list[4][1] < lm_list[3][1]:
                fingers.append(1)
            else:
                fingers.append(0)
                
            # Other fingers
            for finger_id in range(1, 5):
                if lm_list[4 + finger_id * 4][2] < lm_list[2 + finger_id * 4][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)
            
            return sum(fingers) <= 1
        return False
    
    def get_hand_center(self, lm_list):
        if len(lm_list) >= 9:
            return lm_list[9][1] / 640, lm_list[9][2] / 480
        return None, None

class UI:
    def __init__(self):
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 48)
        self.font_huge = pygame.font.Font(None, 72)
        self.pulse = 0
        
    def draw_rounded_rect(self, screen, color, rect, radius=10, border=0, border_color=WHITE):
        pygame.draw.rect(screen, color, rect, border_radius=radius)
        if border > 0:
            pygame.draw.rect(screen, border_color, rect, border, border_radius=radius)
    
    def draw_hand_status(self, screen, hand_detected, confidence, is_fist):
        # Hand detection panel
        panel_rect = pygame.Rect(10, 10, 280, 120)
        self.draw_rounded_rect(screen, (0, 0, 0, 150), panel_rect, 15, 2, LAVENDER)
        
        # Title
        title = self.font_medium.render("🖐️ Hand Tracking", True, WHITE)
        screen.blit(title, (20, 20))
        
        # Detection status
        if hand_detected:
            status_color = GREEN
            status_text = "✅ Hand Detected"
            confidence_text = f"Confidence: {confidence:.1%}"
        else:
            status_color = RED
            status_text = "❌ No Hand Detected"
            confidence_text = "Move hand in front of camera"
            
        status = self.font_small.render(status_text, True, status_color)
        screen.blit(status, (20, 50))
        
        conf = self.font_small.render(confidence_text, True, LIGHT_GRAY)
        screen.blit(conf, (20, 70))
        
        # Gesture status
        if hand_detected:
            if is_fist:
                gesture_text = "👊 Fist - FIRING!"
                gesture_color = GOLD
            else:
                gesture_text = "✋ Open Hand - Moving"
                gesture_color = SOFT_BLUE
        else:
            gesture_text = "🤷 No Gesture"
            gesture_color = DARK_GRAY
            
        gesture = self.font_small.render(gesture_text, True, gesture_color)
        screen.blit(gesture, (20, 95))
    
    def draw_score_panel(self, screen, score, lives=3):
        # Score panel
        panel_rect = pygame.Rect(SCREEN_WIDTH - 200, 10, 180, 80)
        self.draw_rounded_rect(screen, (0, 0, 0, 150), panel_rect, 15, 2, GOLD)
        
        score_text = self.font_medium.render("⭐ Score", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH - 190, 20))
        
        score_value = self.font_large.render(str(score), True, GOLD)
        screen.blit(score_value, (SCREEN_WIDTH - 190, 45))
    
    def draw_instructions(self, screen):
        instructions = [
            "🎮 Controls:",
            "✋ Move hand left/right to steer",
            "👊 Make fist to shoot lasers",
            "🎯 Destroy cute aliens to score!"
        ]
        
        panel_height = len(instructions) * 25 + 20
        panel_rect = pygame.Rect(10, SCREEN_HEIGHT - panel_height - 10, 350, panel_height)
        self.draw_rounded_rect(screen, (0, 0, 0, 120), panel_rect, 15, 2, SOFT_BLUE)
        
        for i, instruction in enumerate(instructions):
            color = WHITE if i == 0 else LIGHT_GRAY
            text = self.font_small.render(instruction, True, color)
            screen.blit(text, (20, SCREEN_HEIGHT - panel_height + i * 25))
    
    def draw_game_over(self, screen, score):
        self.pulse += 0.1
        pulse_scale = 1 + 0.1 * math.sin(self.pulse)
        
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(SPACE_DARK)
        screen.blit(overlay, (0, 0))
        
        # Game over panel
        panel_rect = pygame.Rect(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 150, 500, 300)
        self.draw_rounded_rect(screen, (20, 20, 40), panel_rect, 20, 3, CUTE_PINK)
        
        # Game over text
        game_over = self.font_huge.render("💥 GAME OVER", True, CUTE_PINK)
        go_rect = game_over.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
        screen.blit(game_over, go_rect)
        
        # Final score
        final_score = self.font_large.render(f"Final Score: {score}", True, GOLD)
        fs_rect = final_score.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
        screen.blit(final_score, fs_rect)
        
        # Restart instructions with pulse effect
        restart_font = pygame.font.Font(None, int(36 * pulse_scale))
        restart_text = restart_font.render("Press R to Restart • Q to Quit", True, WHITE)
        r_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
        screen.blit(restart_text, r_rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🚀 Cute Space Shooter - Gesture Controlled! 🚀")
        self.clock = pygame.time.Clock()
        
        # Game objects
        self.spaceship = Spaceship(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
        self.lasers = []
        self.enemies = []
        self.stars = [Star() for _ in range(100)]
        self.explosion_particles = []
        
        # Game state
        self.score = 0
        self.game_over = False
        self.enemy_spawn_timer = 0
        self.laser_cooldown = 0
        
        # Hand tracking
        self.hand_tracker = HandTracker()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # UI
        self.ui = UI()
        
    def handle_collision(self):
        # Laser-Enemy collisions
        for laser in self.lasers[:]:
            for enemy in self.enemies[:]:
                if (abs(laser.x - enemy.x) < (laser.width + enemy.width) // 2 and
                    abs(laser.y - enemy.y) < (laser.height + enemy.height) // 2):
                    self.lasers.remove(laser)
                    enemy.explode()
                    self.enemies.remove(enemy)
                    self.score += 10
                    break
        
        # Enemy-Spaceship collisions
        for enemy in self.enemies:
            if (abs(self.spaceship.x - enemy.x) < (self.spaceship.width + enemy.width) // 2 and
                abs(self.spaceship.y - enemy.y) < (self.spaceship.height + enemy.height) // 2):
                self.game_over = True
    
    def spawn_enemies(self):
        if self.enemy_spawn_timer <= 0:
            enemy_x = random.randint(50, SCREEN_WIDTH - 50)
            self.enemies.append(Enemy(enemy_x, -50))
            self.enemy_spawn_timer = random.randint(90, 150)  # Slower spawn rate
        else:
            self.enemy_spawn_timer -= 1
    
    def update_game_objects(self):
        # Update stars
        for star in self.stars:
            star.update()
            
        # Update lasers
        for laser in self.lasers[:]:
            laser.update()
            if laser.is_off_screen():
                self.lasers.remove(laser)
        
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.update()
            if enemy.is_off_screen():
                self.enemies.remove(enemy)
        
        # Update explosion particles
        self.explosion_particles = [p for p in self.explosion_particles if p.is_alive()]
        for particle in self.explosion_particles:
            particle.update()
    
    def draw_everything(self, hand_detected, confidence, is_fist):
        # Gradient background
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(SPACE_DARK[0] * (1 - color_ratio) + (SPACE_DARK[0] + 20) * color_ratio)
            g = int(SPACE_DARK[1] * (1 - color_ratio) + (SPACE_DARK[1] + 30) * color_ratio)
            b = int(SPACE_DARK[2] * (1 - color_ratio) + (SPACE_DARK[2] + 50) * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # Draw stars
        for star in self.stars:
            star.draw(self.screen)
        
        # Draw explosion particles
        for particle in self.explosion_particles:
            particle.draw(self.screen)
        
        # Draw game objects
        self.spaceship.draw(self.screen)
        for laser in self.lasers:
            laser.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Draw UI
        self.ui.draw_hand_status(self.screen, hand_detected, confidence, is_fist)
        self.ui.draw_score_panel(self.screen, self.score)
        self.ui.draw_instructions(self.screen)
        
        if self.game_over:
            self.ui.draw_game_over(self.screen, self.score)
    
    def process_hand_tracking(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, False, False, 0
        
        frame = cv2.flip(frame, 1)
        frame = self.hand_tracker.find_hands(frame)
        lm_list = self.hand_tracker.find_position(frame)
        
        hand_x, hand_y = self.hand_tracker.get_hand_center(lm_list)
        is_fist = self.hand_tracker.is_fist(lm_list)
        
        return hand_x, is_fist, self.hand_tracker.hand_detected, self.hand_tracker.confidence
    
    def restart_game(self):
        self.spaceship = Spaceship(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
        self.lasers = []
        self.enemies = []
        self.explosion_particles = []
        self.score = 0
        self.game_over = False
        self.enemy_spawn_timer = 0
        self.laser_cooldown = 0
    
    def run(self):
        print("🚀 Starting Cute Space Shooter!")
        print("📷 Make sure your webcam is connected and working")
        print("✋ Show your hand to the camera to start playing!")
        
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_r and self.game_over:
                        self.restart_game()
            
            if not self.game_over:
                # Process hand tracking
                hand_x, is_fist, hand_detected, confidence = self.process_hand_tracking()
                
                # Update spaceship position based on hand
                self.spaceship.update(hand_x)
                
                # Handle shooting
                if is_fist and hand_detected and self.laser_cooldown <= 0:
                    self.lasers.append(Laser(self.spaceship.x, self.spaceship.y - self.spaceship.height // 2))
                    self.laser_cooldown = 30  # Cooldown
                
                if self.laser_cooldown > 0:
                    self.laser_cooldown -= 1
                
                # Spawn enemies
                self.spawn_enemies()
                
                # Update game objects
                self.update_game_objects()
                
                # Handle collisions
                self.handle_collision()
                
                # Draw everything
                self.draw_everything(hand_detected, confidence, is_fist)
            else:
                # Game over state - still show hand tracking
                hand_x, is_fist, hand_detected, confidence = self.process_hand_tracking()
                self.update_game_objects()  # Keep particles moving
                self.draw_everything(hand_detected, confidence, is_fist)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
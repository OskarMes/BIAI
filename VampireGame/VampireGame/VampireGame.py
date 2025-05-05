
import os
import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 900, 900
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Vampire Survivors")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)

# --- Load Background Tile ---
tile_filename = "Ground_Tile_02_C.png"
background_tile = None  # Zainicjuj jako None
tile_width, tile_height = 0, 0

try:
    # Skonstruuj pełną ścieżkę do pliku obrazka
    local_dir = os.path.dirname(__file__)
    tile_path = os.path.join(local_dir, "Static", "Img", "Ground_Tile_02_C.png")

    if not os.path.exists(tile_path):
        print(f"Ostrzeżenie: Plik tła 'Static/Img/Ground_Tile_02_C.png' nie znaleziony w '{tile_path}'. Używam czarnego tła.")
    else:
       # Załaduj i skonwertuj obrazek
        background_tile = pygame.image.load(tile_path).convert()
        tile_width, tile_height = background_tile.get_size()
        print(f"Załadowano tło: Static/Img/Ground_Tile_02_C.png ({tile_width}x{tile_height})")

except pygame.error as e:
    print(f"Błąd ładowania tła '{tile_filename}': {e}")
    background_tile = None # Upewnij się, że jest None jeśli ładowanie zawiodło

# --- Sprawdzenie czy ładowanie się powiodło ---
if background_tile is None or tile_width == 0 or tile_height == 0:
    # Jeśli ładowanie zawiodło lub wymiary są niepoprawne, nie próbuj kafelkować
    use_tiling = False
    print("Kafelkowanie tła wyłączone z powodu błędu ładowania lub nieprawidłowych wymiarów.")
else:
    use_tiling = True


# Game settings
#DOSTOSOWAC USTAWIENIA TAK BY GRA BYLA TRUDNA ALE WYKONYWALNA
# czas gry powinien byc 3 lub 5 min tak zeby byl czas na prezentacje
enemy_spawn_interval = 1300  # milliseconds
enemy_speed = 1.8
bullet_speed = 7
player_speed = 3
shoot_interval = 1000  # milliseconds
#win_time = 5 * 60 * 1000  # 5 minutes in milliseconds
win_time = 50 * 1000

# Fonts
font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 72)

# Game states
MENU = 'menu'
PLAYING = 'playing'
VICTORY = 'victory'
DEFEAT = 'defeat'

class Player:
    def __init__(self, x, y, radius=15):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = GREEN
        self.last_shot = pygame.time.get_ticks()

    def draw(self):
        pygame.draw.circle(SCREEN, self.color, (int(self.x), int(self.y)), self.radius)

    def move(self, keys):
        if keys[pygame.K_w] and self.y - self.radius > 0:
            self.y -= player_speed
        if keys[pygame.K_s] and self.y + self.radius < HEIGHT:
            self.y += player_speed
        if keys[pygame.K_a] and self.x - self.radius > 0:
            self.x -= player_speed
        if keys[pygame.K_d] and self.x + self.radius < WIDTH:
            self.x += player_speed

    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= shoot_interval

    def shoot(self, target_pos):
        self.last_shot = pygame.time.get_ticks()
        dx, dy = target_pos[0] - self.x, target_pos[1] - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1
        dx, dy = dx / dist, dy / dist
        return Bullet(self.x, self.y, dx * bullet_speed, dy * bullet_speed)

class Bullet:
    def __init__(self, x, y, vx, vy, radius=5):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.color = WHITE

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        pygame.draw.circle(SCREEN, self.color, (int(self.x), int(self.y)), self.radius)

    def off_screen(self):
        return not (0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT)

class Enemy:
    def __init__(self):
        # Spawn at random edge
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            self.x = random.uniform(0, WIDTH)
            self.y = 0
        elif edge == 'bottom':
            self.x = random.uniform(0, WIDTH)
            self.y = HEIGHT
        elif edge == 'left':
            self.x = 0
            self.y = random.uniform(0, HEIGHT)
        else:
            self.x = WIDTH
            self.y = random.uniform(0, HEIGHT)
        self.width = 20
        self.height = 20
        self.color = RED
        self.speed = enemy_speed

    def update(self, player):
        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx, dy = dx / dist, dy / dist
        self.x += dx * self.speed
        self.y += dy * self.speed

    def draw(self):
        pygame.draw.rect(SCREEN, self.color, pygame.Rect(int(self.x - self.width/2), int(self.y - self.height/2), self.width, self.height))

    def collides_with_player(self, player):
        # Circle-rectangle collision
        closest_x = max(self.x - self.width/2, min(player.x, self.x + self.width/2))
        closest_y = max(self.y - self.height/2, min(player.y, self.y + self.height/2))
        dx, dy = player.x - closest_x, player.y - closest_y
        return dx*dx + dy*dy < player.radius**2

    def collides_with_bullet(self, bullet):
        dx = abs(bullet.x - self.x)
        dy = abs(bullet.y - self.y)
        if dx > (self.width/2 + bullet.radius) or dy > (self.height/2 + bullet.radius):
            return False
        return True


def draw_text(text, font, color, surface, x, y):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))


def main():
    state = MENU
    player = Player(WIDTH // 2, HEIGHT // 2)
    bullets = []
    enemies = []
    kill_count = 0
    start_time = 0
    last_enemy_spawn = pygame.time.get_ticks()

    while True:
        dt = pygame.time.Clock().tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if state == MENU and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # Start game
                state = PLAYING
                player = Player(WIDTH // 2, HEIGHT // 2)
                bullets = []
                enemies = []
                kill_count = 0
                start_time = pygame.time.get_ticks()
                last_enemy_spawn = start_time
            if state in (VICTORY, DEFEAT) and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                state = MENU

        SCREEN.fill(BLACK)
        keys = pygame.key.get_pressed()

        if state == MENU:
            draw_text("SIMPLE VAMPIRE SURVIVORS", large_font, WHITE, SCREEN, WIDTH//2 - 350, HEIGHT//2 - 50)
            draw_text("Press ENTER to Start", font, WHITE, SCREEN, WIDTH//2 - 110, HEIGHT//2 + 20)

        elif state == PLAYING:
            if use_tiling:
                # Rysuj kafelki
                for x in range(0, WIDTH, tile_width):
                    for y in range(0, HEIGHT, tile_height):
                        SCREEN.blit(background_tile, (x, y))
            else:
                # Jeśli kafelki nie działają, wypełnij czarnym
                SCREEN.fill(BLACK)
            now = pygame.time.get_ticks()
            elapsed = now - start_time

            # Spawn enemies
            if now - last_enemy_spawn >= enemy_spawn_interval:
                enemies.append(Enemy())
                last_enemy_spawn = now

            # Player movement and shooting
            player.move(keys)
            if player.can_shoot():
                mx, my = pygame.mouse.get_pos()
                bullets.append(player.shoot((mx, my)))

            # Update bullets
            for bullet in bullets[:]:
                bullet.update()
                if bullet.off_screen():
                    bullets.remove(bullet)

            # Update enemies
            for enemy in enemies[:]:
                enemy.update(player)
                # Check collision with player
                if enemy.collides_with_player(player):
                    state = DEFEAT
                # Check collision with bullets
                for bullet in bullets[:]:
                    if enemy.collides_with_bullet(bullet):
                        enemies.remove(enemy)
                        bullets.remove(bullet)
                        kill_count += 1
                        break

            # Draw everything
            player.draw()
            for bullet in bullets:
                bullet.draw()
            for enemy in enemies:
                enemy.draw()

            # Draw HUD
            draw_text(f"Kills: {kill_count}", font, WHITE, SCREEN, 10, 10)
            draw_text(f"Time: {elapsed//1000}s", font, WHITE, SCREEN, WIDTH - 150, 10)

            # Check win condition
            if elapsed >= win_time:
                state = VICTORY

        elif state == VICTORY:
            draw_text("VICTORY! You Survived!", large_font, GREEN, SCREEN, WIDTH//2 - 250, HEIGHT//2 - 50)
            draw_text("Press R to Return to Menu", font, WHITE, SCREEN, WIDTH//2 - 140, HEIGHT//2 + 20)
            draw_text(f"Total Kills: {kill_count}", font, WHITE, SCREEN, WIDTH//2 - 80, HEIGHT//2 + 70)

        elif state == DEFEAT:
            draw_text("DEFEAT! You Died!", large_font, RED, SCREEN, WIDTH//2 - 200, HEIGHT//2 - 50)
            draw_text("Press R to Return to Menu", font, WHITE, SCREEN, WIDTH//2 - 140, HEIGHT//2 + 20)
            draw_text(f"Total Kills: {kill_count}", font, WHITE, SCREEN, WIDTH//2 - 80, HEIGHT//2 + 70)
            draw_text(f"Time Survived: {(now - start_time)//1000}s", font, WHITE, SCREEN, WIDTH//2 - 100, HEIGHT//2 + 110)

        pygame.display.update()

if __name__ == "__main__":
    main()

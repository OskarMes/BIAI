
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


# --- Load Assets ---
local_dir = os.path.dirname(__file__)
assets_dir = os.path.join(local_dir, "Static", "Img")

# --- Load Background Tile ---
tile_filename = "Ground_Tile_02_C.png"
background_tile = None
tile_width, tile_height = 0, 0
try:
    tile_path = os.path.join(assets_dir, tile_filename)
    if not os.path.exists(tile_path):
        print(f"Ostrzeżenie: Plik tła '{tile_filename}' nie znaleziony w '{tile_path}'. Używam czarnego tła.")
    else:
        background_tile = pygame.image.load(tile_path).convert()
        tile_width, tile_height = background_tile.get_size()
        print(f"Załadowano tło: {tile_filename} ({tile_width}x{tile_height})")
except pygame.error as e:
    print(f"Błąd ładowania tła '{tile_filename}': {e}")
    background_tile = None

use_tiling = background_tile is not None and tile_width > 0 and tile_height > 0
if not use_tiling:
     print("Kafelkowanie tła wyłączone z powodu błędu ładowania lub nieprawidłowych wymiarów.")

# --- Load Player Image ---
player_filename = "Player.png"
player_image_original = None
try:
    player_path = os.path.join(assets_dir, player_filename)
    if not os.path.exists(player_path):
        print(f"Błąd: Plik gracza '{player_filename}' nie znaleziony w '{player_path}'.")
    else:
        player_image_original = pygame.image.load(player_path).convert_alpha()
        print(f"Załadowano gracza: {player_filename} ({player_image_original.get_width()}x{player_image_original.get_height()})")
        # ===  SKALOWANIE  === 
        original_width = player_image_original.get_width()
        original_height = player_image_original.get_height()
        scale_factor = 0.4 # Przykładowy współczynnik skalowania (70%)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        player_image_original = pygame.transform.smoothscale(player_image_original, (new_width, new_height))
        print(f"Przeskalowano gracza do: {new_width}x{new_height}")

except pygame.error as e:
    print(f"Błąd ładowania obrazka gracza '{player_filename}': {e}")
    player_image_original = None

# Game settings
#DOSTOSOWAC USTAWIENIA TAK BY GRA BYLA TRUDNA ALE WYKONYWALNA
# czas gry powinien byc 3 lub 5 min tak zeby byl czas na prezentacje
enemy_spawn_interval = 1300  # milliseconds
enemy_speed = 1.8
bullet_speed = 7
player_speed = 2
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
    def __init__(self, x, y, image):
        self.original_image = image # Przechowaj oryginalny obrazek
        if self.original_image:
            self.image = self.original_image.copy() # Aktualnie wyświetlany obrazek (na początku kopia oryginału)
            # Pobierz wymiary z ORYGINALNEGO obrazka dla stałego collidera
            self.width = self.original_image.get_width()
            self.height = self.original_image.get_height()
            self.x = x # Środek logiczny gracza
            self.y = y
            # Rect używany do RYSOWANIA (jego pozycja topleft będzie aktualizowana)
            # Jego środek zawsze będzie (self.x, self.y)
            self.rect = self.image.get_rect(center=(self.x, self.y))
        else:
            # Fallback (jeśli chcesz zachować możliwość gry bez obrazka)
            print("OSTRZEŻENIE: Obrazek gracza nie załadowany, używam wartości domyślnych.")
            self.original_image = None
            self.image = None
            self.width = 30
            self.height = 30
            self.x = x
            self.y = y
            # Tworzymy prosty rect dla fallbacku
            self.rect = pygame.Rect(0, 0, self.width, self.height)
            self.rect.center = (self.x, self.y)

        self.last_shot = pygame.time.get_ticks()

    def move(self, keys):
        # Ta metoda tylko aktualizuje logiczne koordynaty środka x, y
        half_w = self.width // 2 # Używamy stałych wymiarów collidera do granic
        half_h = self.height // 2
        delta_x, delta_y = 0, 0
        if keys[pygame.K_w] and self.y - half_h > 0:
            delta_y = -player_speed
        if keys[pygame.K_s] and self.y + half_h < HEIGHT:
            delta_y = player_speed
        if keys[pygame.K_a] and self.x - half_w > 0:
            delta_x = -player_speed
        if keys[pygame.K_d] and self.x + half_w < WIDTH:
            delta_x = player_speed

        # Aktualizuj pozycję
        self.x += delta_x
        self.y += delta_y

    # --- TO JEST METODA, KTÓREJ PRAWDOPODOBNIE BRAKUJE LUB JEST ŹLE UMIESZCZONA ---
    def rotate(self):
         if not self.original_image: return # Nic nie rób jeśli nie ma obrazka

         # 1. Pobierz pozycję myszki
         mx, my = pygame.mouse.get_pos()

         # 2. Oblicz wektor od gracza do myszki
         dx = mx - self.x
         dy = my - self.y

         # 3. Oblicz kąt używając atan2(y, x)
         #    Używamy -dy, ponieważ oś Y w pygame rośnie w dół
         angle_rad = math.atan2(-dy, dx)

         # 4. Konwertuj na stopnie
         angle_deg = math.degrees(angle_rad)

         # 5. Obróć ORYGINALNY obrazek
         #    Pamiętaj o dostosowaniu "- 90" jeśli Twój obrazek domyślnie nie patrzy w górę!
         self.image = pygame.transform.rotate(self.original_image, angle_deg - 90)

         # 6. Zaktualizuj rect dla RYSOWANIA, aby był wyśrodkowany w (self.x, self.y)
         self.rect = self.image.get_rect(center=(self.x, self.y))
    # --- KONIEC METODY ROTATE ---

    def update(self, keys):
        self.move(keys) # Najpierw zaktualizuj pozycję (self.x, self.y)
        self.rotate()   # Następnie obróć obrazek i zaktualizuj self.rect do rysowania

    def draw(self):
        if self.image:
            # Rysuj aktualny (potencjalnie obrócony) obrazek
            # używając zaktualizowanego self.rect (który ma poprawny topleft)
            SCREEN.blit(self.image, self.rect.topleft)
        else:
            # Fallback rysowania
            pygame.draw.rect(SCREEN, (0, 255, 0), (self.x - self.width//2, self.y - self.height//2, self.width, self.height))

    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= shoot_interval

    def shoot(self, target_pos):
        self.last_shot = pygame.time.get_ticks()
        dx, dy = target_pos[0] - self.x, target_pos[1] - self.y
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 1
        dx, dy = dx / dist, dy / dist
        return Bullet(self.x, self.y, dx * bullet_speed, dy * bullet_speed)

    def get_rect(self):
        # Zwraca prostokąt collidera o STAŁYCH wymiarach (z oryginalnego obrazka)
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)
    
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
        self.rect = pygame.Rect(int(self.x - self.width/2), int(self.y - self.height/2), self.width, self.height)

    def update(self, player):
        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx, dy = dx / dist, dy / dist
        self.x += dx * self.speed
        self.y += dy * self.speed
        # Aktualizuj pozycję Rect
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    def draw(self):
        pygame.draw.rect(SCREEN, self.color, self.rect)

    def collides_with_player(self, player):
        # Używamy metody colliderect z Rect gracza i wroga
        player_rect = player.get_rect()
        return self.rect.colliderect(player_rect)

    def collides_with_bullet(self, bullet):
        bullet_rect = pygame.Rect(bullet.x - bullet.radius, bullet.y - bullet.radius, bullet.radius*2, bullet.radius*2)
        return self.rect.colliderect(bullet_rect)


def draw_text(text, font, color, surface, x, y):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))


def main():

    if player_image_original is None:
        print("Nie można uruchomić gry - błąd ładowania obrazka gracza.")
        pygame.quit()
        sys.exit()

    state = MENU
    player = Player(WIDTH // 2, HEIGHT // 2, player_image_original)
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
                player = Player(WIDTH // 2, HEIGHT // 2, player_image_original)
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
            player.update(keys)
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
            # ### DODANO: Rysowanie collidera gracza (jako niebieski prostokąt) ###
            player_rect = player.get_rect()
            pygame.draw.rect(SCREEN, (255,0,0), player_rect, 1) # Ostatni argument '1' oznacza grubość linii ramki
            # ### KONIEC DODANO ###
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

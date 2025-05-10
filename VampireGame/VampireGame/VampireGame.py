import os
import pygame
import sys
import random
import math
import neat 
import pickle

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 900, 900
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Vampire Survivors - NEAT AI")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 165, 0)
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
        # print(f"Załadowano tło: {tile_filename} ({tile_width}x{tile_height})")
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
        # print(f"Załadowano gracza: {player_filename} ({player_image_original.get_width()}x{player_image_original.get_height()})")
        original_width = player_image_original.get_width()
        original_height = player_image_original.get_height()
        scale_factor = 0.4
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        player_image_original = pygame.transform.smoothscale(player_image_original, (new_width, new_height))
        # print(f"Przeskalowano gracza do: {new_width}x{new_height}")
except pygame.error as e:
    print(f"Błąd ładowania obrazka gracza '{player_filename}': {e}")
    player_image_original = None

# --- Load Enemy Image ---
enemy_filename = "Enemy.png"
enemy_image_original = None
try:
    enemy_path = os.path.join(assets_dir, enemy_filename)
    if not os.path.exists(enemy_path):
        print(f"Błąd: Plik wroga '{enemy_filename}' nie znaleziony. Używam czerwonego kwadratu.")
        enemy_image_original = pygame.Surface((20, 20))
        enemy_image_original.fill(RED)
    else:
        enemy_image_original = pygame.image.load(enemy_path).convert_alpha()
        # print(f"Załadowano wroga: {enemy_filename} ({enemy_image_original.get_width()}x{enemy_image_original.get_height()})")
        scale_factor_enemy = 0.4
        new_width_enemy = int(enemy_image_original.get_width() * scale_factor_enemy)
        new_height_enemy = int(enemy_image_original.get_height() * scale_factor_enemy)
        enemy_image_original = pygame.transform.smoothscale(enemy_image_original, (new_width_enemy, new_height_enemy))
        # print(f"Przeskalowano wroga do: {new_width_enemy}x{new_height_enemy}")
except pygame.error as e:
    print(f"Błąd ładowania obrazka wroga '{enemy_filename}': {e}. Używam czerwonego kwadratu.")
    enemy_image_original = pygame.Surface((20, 20))
    enemy_image_original.fill(RED)


# Game settings
enemy_spawn_interval = 1300
enemy_speed = 1.8
bullet_speed = 7
player_speed = 2 
shoot_interval = 1000
win_time = 50 * 1000

# Fonts
font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 72)

# Game states (dla trybu ludzkiego)
MENU = 'menu'
PLAYING = 'playing'
VICTORY = 'victory'
DEFEAT = 'defeat'

# --- Zmienne globalne dla NEAT ---
GENERATION_COUNT = 0
DISPLAY_EVERY_N_GENERATIONS = 100

class Player:
    def __init__(self, x, y, image):
        self.boundary_violations = 0 # Licznik prób wyjścia poza ekran
        self.last_shot_timestamp = 0 # Czas ostatniego strzału
        self.original_image = image
        if self.original_image:
            self.image = self.original_image.copy()
            self.width = self.original_image.get_width()
            self.height = self.original_image.get_height()
            self.x = x
            self.y = y
            self.rect = self.image.get_rect(center=(self.x, self.y))
        else:
            self.original_image = None 
            self.image = pygame.Surface((30,30)); self.image.fill(GREEN) 
            self.width = 30
            self.height = 30
            self.x = x
            self.y = y
            self.rect = self.image.get_rect(center=(self.x, self.y))

        self.last_shot = pygame.time.get_ticks()

    # --- Metody dla ludzkiego gracza ---
    def move_human(self, keys):
        half_w = self.width // 2
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
        self.x += delta_x
        self.y += delta_y

    def rotate_human(self):
         if not self.original_image: return
         mx, my = pygame.mouse.get_pos()
         dx = mx - self.x
         dy = my - self.y
         angle_rad = math.atan2(-dy, dx)
         angle_deg = math.degrees(angle_rad)
         self.image = pygame.transform.rotate(self.original_image, angle_deg - 90)
         self.rect = self.image.get_rect(center=(self.x, self.y))

    def update_human(self, keys):
        self.move_human(keys)
        self.rotate_human()

    def shoot_human(self, target_pos):
        self.last_shot = pygame.time.get_ticks()
        dx, dy = target_pos[0] - self.x, target_pos[1] - self.y
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 1
        dx, dy = dx / dist, dy / dist
        return Bullet(self.x, self.y, dx * bullet_speed, dy * bullet_speed)
    

    # --- dla AI ---
    def reset_simulation_stats(self): # Wywoływane na początku każdej symulacji AI
        self.boundary_violations = 0
        self.last_shot_timestamp = 0

    def can_shoot_auto(self, current_game_time_ms):
        return current_game_time_ms - self.last_shot_timestamp >= shoot_interval # shoot_interval = 1000 ms
 
    def update_ai(self, net_outputs, target_enemy_for_shooting, current_game_time_ms):
        threshold = 0.5 
        delta_x_intended, delta_y_intended = 0, 0 # Zamierzone zmiany pozycji

        delta_x, delta_y = 0, 0

        if net_outputs[0] > threshold: delta_y_intended -= player_speed
        if net_outputs[1] > threshold: delta_y_intended += player_speed
        if net_outputs[2] > threshold: delta_x_intended -= player_speed
        if net_outputs[3] > threshold: delta_x_intended += player_speed

        if delta_x_intended != 0 and delta_y_intended != 0:
            factor = player_speed / math.sqrt(delta_x_intended**2 + delta_y_intended**2)
            delta_x_intended *= factor
            delta_y_intended *= factor
        elif delta_x_intended != 0:
             delta_x_intended = math.copysign(player_speed, delta_x_intended)
        elif delta_y_intended != 0:
             delta_y_intended = math.copysign(player_speed, delta_y_intended)


        predicted_x = self.x + delta_x_intended
        predicted_y = self.y + delta_y_intended
        half_w = self.width // 2
        half_h = self.height // 2

        violation_this_frame = False
        if predicted_x - half_w < 0:
            self.boundary_violations += 1
            violation_this_frame = True
        if predicted_x + half_w > WIDTH:
            self.boundary_violations += 1
            violation_this_frame = True
        if predicted_y - half_h < 0:
            self.boundary_violations += 1
            violation_this_frame = True
        if predicted_y + half_h > HEIGHT:
            self.boundary_violations += 1
            violation_this_frame = True

        if half_w <= predicted_x <= WIDTH - half_w:
            self.x = predicted_x
        elif predicted_x < half_w : # Jeśli wyszedł za lewą
            self.x = half_w
        elif predicted_x > WIDTH - half_w: # Jeśli wyszedł za prawą
            self.x = WIDTH - half_w

        if half_h <= predicted_y <= HEIGHT - half_h:
            self.y = predicted_y
        elif predicted_y < half_h: # Jeśli wyszedł za górną
            self.y = half_h
        elif predicted_y > HEIGHT - half_h: # Jeśli wyszedł za dolną
            self.y = HEIGHT - half_h

        bullet_to_add = None
        if target_enemy_for_shooting and self.can_shoot_auto(current_game_time_ms):
            self.last_shot_timestamp = current_game_time_ms # Zapisz czas tego strzału

            dx_aim = target_enemy_for_shooting.x - self.x
            dy_aim = target_enemy_for_shooting.y - self.y
            dist_aim = math.hypot(dx_aim, dy_aim)
            if dist_aim == 0: dist_aim = 1
            
            bullet_vx = (dx_aim / dist_aim) * bullet_speed
            bullet_vy = (dy_aim / dist_aim) * bullet_speed
            bullet_to_add = Bullet(self.x, self.y, bullet_vx, bullet_vy)
        
        if self.original_image and target_enemy_for_shooting:
            dx_aim_rot = target_enemy_for_shooting.x - self.x
            dy_aim_rot = target_enemy_for_shooting.y - self.y
            if not (dx_aim_rot == 0 and dy_aim_rot == 0):
                angle_rad = math.atan2(-dy_aim_rot, dx_aim_rot)
                angle_deg = math.degrees(angle_rad)
                self.image = pygame.transform.rotate(self.original_image, angle_deg - 90)
        elif self.original_image: # Brak celu, domyślna rotacja
            self.image = pygame.transform.rotate(self.original_image, 0)

       
        if self.image: 
             self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        else: 
             self.rect.center = (int(self.x), int(self.y))

        return bullet_to_add
   

    def draw(self):
        if self.image:
            SCREEN.blit(self.image, self.rect.topleft)
        else: 
            pygame.draw.rect(SCREEN, GREEN, (self.x - self.width//2, self.y - self.height//2, self.width, self.height))


    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= shoot_interval

    def get_rect(self): 
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class Bullet:
    def __init__(self, x, y, vx, vy, radius=5):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.color = YELLOW

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        pygame.draw.circle(SCREEN, self.color, (int(self.x), int(self.y)), self.radius)

    def off_screen(self):
        return not (0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT)

class Enemy:
    def __init__(self,image):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top': self.x, self.y = random.uniform(0, WIDTH), -10
        elif edge == 'bottom': self.x, self.y = random.uniform(0, WIDTH), HEIGHT + 10
        elif edge == 'left': self.x, self.y = -10, random.uniform(0, HEIGHT)
        else: self.x, self.y = WIDTH + 10, random.uniform(0, HEIGHT)

        self.original_image = image
        if self.original_image:
            self.image = self.original_image.copy()
            self.base_width = self.original_image.get_width()
            self.base_height = self.original_image.get_height()
        else:
            self.image = pygame.Surface((20, 20)); self.image.fill(RED)
            self.original_image = self.image 
            self.base_width = 20; self.base_height = 20

        self.speed = enemy_speed
        self.angle_deg = 0
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self, player): 
        dx_move, dy_move = player.x - self.x, player.y - self.y
        dist = math.hypot(dx_move, dy_move)
        if dist != 0:
            dx_norm, dy_norm = dx_move / dist, dy_move / dist
            self.x += dx_norm * self.speed
            self.y += dy_norm * self.speed

        if self.original_image:
            dx_angle = player.x - self.x
            dy_angle = player.y - self.y
            angle_rad = math.atan2(-dy_angle, dx_angle)
            angle_deg = math.degrees(angle_rad)
            rotation_angle = angle_deg - 90
            self.angle_deg = rotation_angle
            self.image = pygame.transform.rotate(self.original_image, self.angle_deg)
            self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        else: 
            self.rect.center = (int(self.x), int(self.y))


    def draw(self):
        if self.image:
            SCREEN.blit(self.image, self.rect.topleft)

    def collides_with_player(self, player):
        player_rect = player.get_rect()
       
        return self.rect.colliderect(player_rect)

    def collides_with_bullet(self, bullet):
        bullet_rect = pygame.Rect(bullet.x - bullet.radius, bullet.y - bullet.radius, bullet.radius*2, bullet.radius*2)
      
        return self.rect.colliderect(bullet_rect)


def draw_text(text, font, color, surface, x, y, center=False):
    img = font.render(text, True, color)
    if center:
        rect = img.get_rect(center=(x,y))
        surface.blit(img, rect)
    else:
        surface.blit(img, (x, y))

# --- Funkcje  NEAT ---

def get_inputs_for_nn(player, enemies, num_visible_enemies=3):
    inputs = []
    # 1. Pozycja gracza (znormalizowana)
    inputs.append(player.x / WIDTH)
    inputs.append(player.y / HEIGHT)

    sorted_enemies = sorted(enemies, key=lambda e: math.hypot(e.x - player.x, e.y - player.y))

    # 2. Pozycja "targetu" (najbliższego wroga)
    target_for_shooting = None
    if sorted_enemies:
        target_enemy = sorted_enemies[0]
        inputs.append(target_enemy.x / WIDTH)
        inputs.append(target_enemy.y / HEIGHT)
        target_for_shooting = target_enemy
    else:
        inputs.append(player.x / WIDTH) # Brak celu, podaj pozycję gracza
        inputs.append(player.y / HEIGHT)

    # 3. Pozycje `num_visible_enemies` najbliższych wrogów
    for i in range(num_visible_enemies):
        if i < len(sorted_enemies):
            enemy = sorted_enemies[i]
            inputs.append(enemy.x / WIDTH)
            inputs.append(enemy.y / HEIGHT)
        else:
            # Wypełnij wartościami neutralnymi, np. pozycja gracza
            # lub wartości poza ekranem np. -1.0 (jeśli sieć ma się tego nauczyć)
            # Użycie pozycji gracza może być bezpieczniejsze na początek.
            inputs.append(player.x / WIDTH)
            inputs.append(player.y / HEIGHT)
            # Alternatywnie:
            # inputs.append(-1.0)
            # inputs.append(-1.0)

    return inputs, target_for_shooting

def calculate_fitness(kill_count, time_survived_ms, game_won, boundary_violations):
    fitness = 0.0
    fitness += time_survived_ms / 1000.0  # Punkty za sekundy
    fitness += kill_count * 50.0          # Punkty za zabójstwa
    if game_won:
        fitness += 1000.0                 # Bonus za wygraną
    
    penalty_per_violation = 5.0
    fitness -= boundary_violations * penalty_per_violation

    if fitness < 0: fitness = 0.0 

    return fitness

def run_game_for_ai(genome, config, display_game=False, genome_id=None, gen_num=None):
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    if player_image_original is None or enemy_image_original is None:
        print("Krytyczny błąd AI: Brak obrazków gracza lub wroga.")
        return 0 
    
    player = Player(WIDTH // 2, HEIGHT // 2, player_image_original)
    player.reset_simulation_stats()
    
    bullets = []
    enemies = []
    kill_count = 0
    start_time_sim = pygame.time.get_ticks()
    last_enemy_spawn = start_time_sim

    clock = pygame.time.Clock()
    running = True
    game_won = False

    frames_stuck = 0
    last_player_pos = (player.x, player.y)

    while running:
        current_game_time_ms_loop = pygame.time.get_ticks() 
        if display_game:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

        elapsed_time_ms_sim = current_game_time_ms_loop - start_time_sim # Czas trwania tej symulacji

        # --- Logika AI ---
        game_inputs, current_target_for_shooting = get_inputs_for_nn(player, enemies)
        outputs_from_net = net.activate(game_inputs)
        new_bullet = player.update_ai(outputs_from_net, current_target_for_shooting, current_game_time_ms_loop)
        if new_bullet:
            bullets.append(new_bullet)
        # -----------------

        # Spawn enemies
        if current_game_time_ms_loop - last_enemy_spawn >= enemy_spawn_interval:
            enemies.append(Enemy(enemy_image_original))
            last_enemy_spawn = current_game_time_ms_loop

        # Update bullets
        for bullet in bullets[:]:
            bullet.update()
            if bullet.off_screen():
                bullets.remove(bullet)

        # Update enemies
        player_died = False
        for enemy in enemies[:]:
            enemy.update(player)
            if enemy.collides_with_player(player):
                player_died = True
                break
            for bullet in bullets[:]:
                if enemy.collides_with_bullet(bullet):
                    if enemy in enemies: enemies.remove(enemy)
                    if bullet in bullets: bullets.remove(bullet)
                    kill_count += 1
                    # genome.fitness += 10 # Mały bonus od razu, jeśli chcesz
                    break
        if player_died:
            running = False

        # Check win condition
        if elapsed_time_ms_sim >= win_time:
            running = False
            game_won = True

        # Opcjonalna kara za stagnację
        if (player.x, player.y) == last_player_pos:
            frames_stuck += 1
        else:
            frames_stuck = 0
            last_player_pos = (player.x, player.y)
        if frames_stuck > 180: # Np. 3 sekundy bez ruchu
            running = False # Zakończ grę, jeśli AI utknęło

        # zakończ, jeśli gra trwa za długo
        if elapsed_time_ms_sim > win_time + 10000: # 10 sekund po czasie wygranej
            running = False
            

        if display_game:
            SCREEN.fill(BLACK)
            if use_tiling:
                for x_tile in range(0, WIDTH, tile_width):
                    for y_tile in range(0, HEIGHT, tile_height):
                        SCREEN.blit(background_tile, (x_tile, y_tile))
            else:
                SCREEN.fill(BLACK)

            player.draw()
            for bullet in bullets:
                bullet.draw()
            for enemy in enemies:
                enemy.draw()

            draw_text(f"Kills: {kill_count}", font, WHITE, SCREEN, 10, 10)
            draw_text(f"Time: {elapsed_time_ms_sim//1000}s", font, WHITE, SCREEN, WIDTH - 150, 10)
            if genome_id is not None and gen_num is not None:
                draw_text(f"Gen: {gen_num} Genome: {genome_id}", font, WHITE, SCREEN, 10, 40)
                draw_text(f"Fitness: {genome.fitness:.2f}", font, WHITE, SCREEN, 10, 70)


            pygame.display.update()
            clock.tick(60) # Ogranicz FPS podczas wyświetlania
        else: # Jeśli nie wyświetlamy, możemy próbować iść szybciej
            clock.tick(0) # Bez limitu FPS, jeśli nie rysujemy

    
    fitness = calculate_fitness(kill_count, elapsed_time_ms_sim, game_won, player.boundary_violations)
    return fitness

def eval_genomes(genomes, config):
    global GENERATION_COUNT
    GENERATION_COUNT += 1
    display_this_generation = (GENERATION_COUNT % DISPLAY_EVERY_N_GENERATIONS == 0)

  

    for i, (genome_id, genome) in enumerate(genomes):
        genome.fitness = 0.0 # Resetuj fitness przed każdą ewaluacją

       
        display_run = display_this_generation and (i == 0) 

        if display_run:
            print(f"  Wyświetlanie genomu {genome_id} (pierwszy z generacji {GENERATION_COUNT})...")

      
        num_simulation_runs = 1 
        total_fitness_for_genome = 0.0
        for run_idx in range(num_simulation_runs):
            
            current_fitness = run_game_for_ai(genome, config, display_game=display_run, genome_id=genome_id, gen_num=GENERATION_COUNT)
            total_fitness_for_genome += current_fitness
        
        genome.fitness = total_fitness_for_genome / num_simulation_runs

        if display_run:
            print(f"  Genom {genome_id} zakończył z uśrednionym fitness: {genome.fitness:.2f}")


def run_neat(config):
    global GENERATION_COUNT 
    p = neat.Population(config)
    GENERATION_COUNT = 0 # Resetuj, jeśli zaczynasz od nowa

    p.add_reporter(neat.StdOutReporter(True)) # Wyświetla podstawowe info w konsoli
    stats = neat.StatisticsReporter() 
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(generation_interval=10, filename_prefix='neat-checkpoint-'))
    winner = p.run(eval_genomes, n=50)

    print('\nNajlepszy znaleziony genom:\n{!s}'.format(winner))

    with open('best_genome.pkl', 'wb') as output_file:
        pickle.dump(winner, output_file, 1)
    print("Zapisano najlepszy genom do 'best_genome.pkl'")

    print("\nUruchamianie najlepszego genomu w akcji...")
    run_game_for_ai(winner, config, display_game=True, genome_id="WINNER", gen_num="FINAL")


# Funkcja  dla ludzkiego gracza 
def main_human_player():
    if player_image_original is None:
        print("Nie można uruchomić gry - błąd ładowania obrazka gracza.")
        pygame.quit()
        sys.exit()
    if enemy_image_original is None:
         print("Krytyczny błąd: Nie udało się załadować obrazka wroga. Zamykanie.")
         pygame.quit(); sys.exit()

    state = MENU
    player = Player(WIDTH // 2, HEIGHT // 2, player_image_original)
    bullets = []
    enemies = []
    kill_count = 0
    start_time_game = 0 #
    last_enemy_spawn_game = pygame.time.get_ticks() 

    game_clock = pygame.time.Clock() 

    while True:
        
        game_clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if state == MENU and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                state = PLAYING
                player = Player(WIDTH // 2, HEIGHT // 2, player_image_original)
                bullets = []
                enemies = []
                kill_count = 0
                start_time_game = pygame.time.get_ticks()
                last_enemy_spawn_game = start_time_game
            if state in (VICTORY, DEFEAT) and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                state = MENU

        keys = pygame.key.get_pressed() 

        SCREEN.fill(BLACK) 

        if state == MENU:
            draw_text("SIMPLE VAMPIRE SURVIVORS", large_font, WHITE, SCREEN, WIDTH//2, HEIGHT//2 - 50, center=True)
            draw_text("Press ENTER to Start", font, WHITE, SCREEN, WIDTH//2, HEIGHT//2 + 20, center=True)
            draw_text("Press 'T' to Train AI", font, WHITE, SCREEN, WIDTH//2, HEIGHT//2 + 60, center=True)
            draw_text("Press 'L' to Load & Run Best AI", font, WHITE, SCREEN, WIDTH//2, HEIGHT//2 + 100, center=True)
            if keys[pygame.K_t]: # Jeśli T naciśnięte w menu, uruchom trening
                print("Rozpoczynanie treningu AI...")
                local_dir_neat = os.path.dirname(__file__)
                config_path_neat = os.path.join(local_dir_neat, 'Static','config.txt')
                try:
                    config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                        neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                        config_path_neat)
                    run_neat(config_neat)
                    
                    state = MENU # Wróć do menu
                except Exception as e:
                    print(f"Błąd podczas inicjalizacji lub uruchamiania NEAT: {e}")
                    state = MENU # Wróć do menu w razie błędu
                
            if keys[pygame.K_l]:
                print("Ładowanie najlepszego AI...")
                try:
                    with open('best_genome.pkl', 'rb') as f:
                        winner_genome = pickle.load(f)
                    local_dir_neat = os.path.dirname(__file__)
                    config_path_neat = os.path.join(local_dir_neat,  'Static','config.txt')
                    config_neat = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                        neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                        config_path_neat)
                    run_game_for_ai(winner_genome, config_neat, display_game=True, genome_id="LOADED_BEST", gen_num="N/A")
                    state = MENU # Wróć do menu po pokazie
                except FileNotFoundError:
                    print("Nie znaleziono pliku 'best_genome.pkl'. Najpierw przeprowadź trening.")
                    state = MENU
                except Exception as e:
                    print(f"Błąd podczas ładowania/uruchamiania najlepszego genomu: {e}")
                    state = MENU


        elif state == PLAYING:
            if use_tiling:
                for x in range(0, WIDTH, tile_width):
                    for y in range(0, HEIGHT, tile_height):
                        SCREEN.blit(background_tile, (x, y))
            else:
                SCREEN.fill(BLACK) 
            
            current_time_game = pygame.time.get_ticks()
            elapsed_game = current_time_game - start_time_game

            if current_time_game - last_enemy_spawn_game >= enemy_spawn_interval:
                enemies.append(Enemy(enemy_image_original))
                last_enemy_spawn_game = current_time_game

            player.update_human(keys)
            if player.can_shoot() and pygame.mouse.get_pressed()[0]: 
                mx, my = pygame.mouse.get_pos()
                bullets.append(player.shoot_human((mx, my))) 

            for bullet in bullets[:]:
                bullet.update()
                if bullet.off_screen():
                    bullets.remove(bullet)

            player_collided_human = False
            for enemy in enemies[:]:
                enemy.update(player)
                if enemy.collides_with_player(player):
                    player_collided_human = True
                    break
                for bullet in bullets[:]:
                    if enemy.collides_with_bullet(bullet):
                        if enemy in enemies: enemies.remove(enemy)
                        if bullet in bullets: bullets.remove(bullet)
                        kill_count += 1
                        break
            if player_collided_human:
                state = DEFEAT
              
                time_at_defeat = pygame.time.get_ticks()


            player.draw()
            
            for bullet in bullets:
                bullet.draw()
            for enemy in enemies:
                enemy.draw()

            draw_text(f"Kills: {kill_count}", font, WHITE, SCREEN, 10, 10)
            draw_text(f"Time: {elapsed_game//1000}s", font, WHITE, SCREEN, WIDTH - 150, 10)

            if elapsed_game >= win_time:
                state = VICTORY

        elif state == VICTORY:
            draw_text("VICTORY! You Survived!", large_font, GREEN, SCREEN, WIDTH//2, HEIGHT//2 - 50, center=True)
            draw_text("Press R to Return to Menu", font, WHITE, SCREEN, WIDTH//2, HEIGHT//2 + 20, center=True)
            draw_text(f"Total Kills: {kill_count}", font, WHITE, SCREEN, WIDTH//2, HEIGHT//2 + 70, center=True)

        elif state == DEFEAT:
            draw_text("DEFEAT! You Died!", large_font, RED, SCREEN, WIDTH//2, HEIGHT//2 - 50, center=True)
            draw_text("Press R to Return to Menu", font, WHITE, SCREEN, WIDTH//2, HEIGHT//2 + 20, center=True)
            draw_text(f"Total Kills: {kill_count}", font, WHITE, SCREEN, WIDTH//2, HEIGHT//2 + 70, center=True)
            
            time_survived_defeat = (time_at_defeat - start_time_game) // 1000 if 'time_at_defeat' in locals() else (current_time_game - start_time_game) // 1000
            draw_text(f"Time Survived: {time_survived_defeat}s", font, WHITE, SCREEN, WIDTH//2, HEIGHT//2 + 110, center=True)


        pygame.display.update()


if __name__ == "__main__":
    main_human_player()


import pygame
import random
import pygame.mixer
import os
import sys
import time

def resource_path(relative_path):
    """Renvoie le chemin absolu, compatible avec PyInstaller."""
    try:
        base_path = sys._MEIPASS  # quand c'est packagé
    except AttributeError:
        base_path = os.path.abspath(".")  # en mode normal
    return os.path.join(base_path, relative_path)

# Initialisation de Pygame
pygame.init()
pygame.mixer.init()
teleport_sound = pygame.mixer.Sound(resource_path("sons/teleport.wav"))
son_game_over = pygame.mixer.Sound(resource_path("sons/game_over.mp3"))
son_victoire = pygame.mixer.Sound(resource_path("sons/victory.mp3"))
son_pomme = pygame.mixer.Sound(resource_path("sons/apple_munch.mp3"))

# Définition des constantes
WIDTH, HEIGHT = 800, 600
GRID_SIZE=20
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)  # Pomme spéciale
BLACK = (0, 0, 0)
YELLOW=(255, 255, 0)
GRAY = (169, 169, 169)# Obstacles
DARK_RED = (200, 0, 0)
DARK_GREEN = (0, 200, 0)
DARK_YELLOW=(204, 204, 0)

# Création de la fenêtre
display = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Fichier du high score
HIGH_SCORE_FILE = "highscore.txt"

def get_high_score(difficulty, mode="chrono"):
    filename = resource_path(f"highscore/highscore_{mode}_{difficulty}.txt")
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return int(file.read().strip())
    return 0

def save_high_score(score, difficulty, mode="chrono"):
    high_score = get_high_score(difficulty, mode)
    filename = resource_path(f"highscore/highscore_{mode}_{difficulty}.txt")
    if score > high_score:
        with open(filename, "w") as file:
            file.write(str(score))


def draw_score(surface, score, high_score, difficulty):
    score_text = font.render(f"Score: {score}", True, WHITE)
    high_score_text = font.render(f"High Score ({difficulty}): {high_score}", True, WHITE)
    surface.blit(score_text, (WIDTH // 3 - score_text.get_width() // 2, 20))
    surface.blit(high_score_text, (WIDTH - high_score_text.get_width() - 20, 20))

def draw_scores(surface, score, high_score):
    score_text = font.render(f"Score: {score}", True, WHITE)
    high_score_text = font.render(f"High Score: {high_score}", True, WHITE)
    surface.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 20))
    surface.blit(high_score_text, (WIDTH - high_score_text.get_width() - 20, 20))



class Snake:
    def __init__(self):
        self.body = [[100, 100], [80, 100], [60, 100]]
        self.direction = "RIGHT"
        self.next_direction = "RIGHT"

    def move(self, easy_mode, score):
        if self.next_direction:
            opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
            if self.next_direction != opposite[self.direction]:
                self.direction = self.next_direction

        head = self.body[0][:]
        if self.direction == "UP":
            head[1] -= GRID_SIZE
        elif self.direction == "DOWN":
            head[1] += GRID_SIZE
        elif self.direction == "LEFT":
            head[0] -= GRID_SIZE
        elif self.direction == "RIGHT":
            head[0] += GRID_SIZE

        # Gestion de la téléportation et réduction du score
        teleported = False
        if easy_mode:
            if head[0] < 0:
                head[0] = WIDTH - GRID_SIZE
                teleported = True
            elif head[0] >= WIDTH:
                head[0] = 0
                teleported = True
            if head[1] < 0:
                head[1] = HEIGHT - GRID_SIZE
                teleported = True
            elif head[1] >= HEIGHT:
                head[1] = 0
                teleported = True
        else:  # Mode medium et hard -> Game over si on touche le bord
            if head[0] < 0 or head[0] >= WIDTH or head[1] < 0 or head[1] >= HEIGHT:
                game_state="game_over"
                return game_state, score
        if teleported:
            pygame.mixer.Sound.play(teleport_sound)  # Joue le son
            score -= 10  # Réduction du score
            if score < 0:
                score = 0
            if score <= 0:
                game_state = "game_over"
                return game_state, score  # Fin du jeu si le score atteint 0

        self.body.insert(0, head)
        self.body.pop()
        return "continue", score

    def grow(self):
        self.body.append(self.body[-1])

    def check_collision(self, obstacles):
        head = self.body[0]
        return head in self.body[1:] or head in obstacles

    def draw(self, surface):
        for segment in self.body:
            pygame.draw.rect(surface, GREEN, pygame.Rect(segment[0], segment[1], GRID_SIZE, GRID_SIZE))

def generate_obstacles(level, snake):
    obstacles = []

    # Ajouter des murs sur les bords du jeu
    if level in ["medium", "hard"]:
        for x in range(0, WIDTH, GRID_SIZE):
            obstacles.append([x, 0])
            obstacles.append([x, HEIGHT - GRID_SIZE])
        for y in range(0, HEIGHT, GRID_SIZE):
            obstacles.append([0, y])
            obstacles.append([WIDTH - GRID_SIZE, y])

    # Ajouter des obstacles aléatoires en plus des murs si niveau "hard"
    if level == "hard":
        for _ in range(10):
            while True:
                # Générer une position aléatoire
                new_obstacle = [random.randrange(1, (WIDTH // GRID_SIZE) - 1) * GRID_SIZE,
                                random.randrange(2, (HEIGHT // GRID_SIZE) - 1) * GRID_SIZE]

                # Vérifier si l'obstacle ne chevauche pas la tête du serpent ou d'autres obstacles
                if new_obstacle not in snake.body and new_obstacle not in obstacles:
                    obstacles.append(new_obstacle)
                    break  # Si l'obstacle est valide, on sort de la boucle while

    return obstacles

class Apple:
    def __init__(self, snake, obstacles, special=False):
        self.special = special
        self.color = ORANGE if special else RED
        self.position = self.get_valid_position(snake, obstacles)
        self.time_limit = 10  # Durée de vie de la pomme spéciale en secondes
        self.start_time = pygame.time.get_ticks()  # Temps initial de la pomme spéciale
        self.progress_bar_width = 100  # Largeur de la barre de progression
        self.progress_bar_height = 10  # Hauteur de la barre de progression

    def get_valid_position(self, snake, obstacles):
        available_positions = [
            [x, y]
            for x in range(0, WIDTH, GRID_SIZE)
            for y in range(0, HEIGHT, GRID_SIZE)
            if [x, y] not in snake.body and [x, y] not in obstacles  # Vérification des obstacles
        ]

        # Retourner une position valide ou None si aucune position n'est disponible
        return random.choice(available_positions) if available_positions else None

    def respawn(self, snake, obstacles):
        new_position = self.get_valid_position(snake, obstacles)
        if new_position:
            self.position = new_position

    def draw(self, surface):
        if self.special:
            pygame.draw.polygon(surface, self.color, [(self.position[0] + GRID_SIZE // 2, self.position[1]),
                                                       (self.position[0], self.position[1] + GRID_SIZE),
                                                       (self.position[0] + GRID_SIZE, self.position[1] + GRID_SIZE)])
        else:
            pygame.draw.circle(surface, self.color, (self.position[0] + GRID_SIZE // 2, self.position[1] + GRID_SIZE // 2), GRID_SIZE // 2)

def draw_button(text, x, y, width, height, color, hover_color):
    """ Dessine un bouton et détecte si la souris est dessus. """
    mouse_x, mouse_y = pygame.mouse.get_pos()
    button_color = hover_color if x <= mouse_x <= x + width and y <= mouse_y <= y + height else color

    pygame.draw.rect(display, button_color, (x, y, width, height))
    text_surf = font.render(text, True, BLACK)
    text_rect = text_surf.get_rect(center=(x + width // 2, y + height // 2))
    display.blit(text_surf, text_rect)

    return (x <= mouse_x <= x + width) and (y <= mouse_y <= y + height)


def main_menu():
    """ Affiche le menu principal """
    while True:
        # Fond dégradé amélioré
        for i in range(HEIGHT):
            color = (
                int(0 + (0 - 0) * i / HEIGHT),  # Bleu amélioré
                int(0 + (50 - 0) * i / HEIGHT),
                int(100 + (255 - 100) * i / HEIGHT)  # Bleu plus visible
            )
            pygame.draw.line(display, color, (0, i), (WIDTH, i))

        # Titre centré
        title_font = pygame.font.SysFont("Arial", 60, bold=True)
        title_surf = title_font.render("Jeu Snake", True, WHITE)
        title_shadow = title_font.render("Jeu Snake", True, (50, 50, 50))
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        display.blit(title_shadow, (title_rect.x + 5, title_rect.y + 5))  # Ombre du texte
        display.blit(title_surf, title_rect)

        # Boutons centrés dynamiquement
        button_width, button_height = 200, 60
        play_hover = draw_button("Démarrer", WIDTH // 2 - button_width // 2, HEIGHT // 2 - 40, button_width,
                                 button_height, GREEN, DARK_GREEN)
        quit_hover = draw_button("Quitter", WIDTH // 2 - button_width // 2, HEIGHT // 2 + 40, button_width,
                                 button_height, RED, DARK_RED)
        credits_hover = draw_button("Crédits", WIDTH // 2 - button_width // 2, HEIGHT // 2 + 120, button_width,
                                    button_height, YELLOW, DARK_YELLOW)
        pygame.display.update()

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_hover:
                    return mode_menu()  # Lancer le menu des difficultés
                if credits_hover:
                    return credits_page()
                if quit_hover:
                    pygame.quit()
                    sys.exit()

def difficulty_menu():
    """ Affiche le menu de sélection de difficulté """
    while True:
        display.fill(BLACK)

        # Fond dégradé amélioré
        for i in range(HEIGHT):
            color = (
                int(0 + (0 - 0) * i / HEIGHT),  # Bleu amélioré
                int(0 + (50 - 0) * i / HEIGHT),
                int(100 + (255 - 100) * i / HEIGHT)  # Bleu plus visible
            )
            pygame.draw.line(display, color, (0, i), (WIDTH, i))

        # Titre du menu
        title_font = pygame.font.SysFont("Arial", 60, bold=True)
        title_surf = title_font.render("Choisissez la difficulté", True, WHITE)
        title_shadow = title_font.render("Choisissez la difficulté", True, (50, 50, 50))
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 4-100))
        display.blit(title_shadow, (title_rect.x + 5, title_rect.y + 5))  # Ombre du texte
        display.blit(title_surf, title_rect)

        # Boutons de difficulté avec animation au survol
        easy_hover = draw_button("Facile", 300, 150, 200, 60, GREEN, (0, 200, 0))
        medium_hover = draw_button("Moyen", 300, 230, 200, 60, (255, 165, 0), (255, 140, 0))
        hard_hover = draw_button("Difficile", 300, 310, 200, 60, RED, (200, 0, 0))
        # Bouton Retour
        back_hover = draw_button("Retour", 300, 390, 200, 60, YELLOW, (200, 200, 0))
        # Gestion des événements (clic sur un bouton)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Clic gauche
                if easy_hover:
                    return main("easy")  # Lancer le jeu en mode facile
                if medium_hover:
                    return main("medium")  # Lancer le jeu en mode moyen
                if hard_hover:
                    return main("hard")  # Lancer le jeu en mode difficile
                if back_hover:
                    return mode_menu()  # Retour au menu principal

        pygame.display.flip()


# Fonction d'affichage du compte à rebours
def show_pause_screen():
    font = pygame.font.SysFont('Arial', 48)
    message = font.render("PAUSE", True, (255, 255, 255))
    (display.fill((0, 0, 0)))  # Fond noir
    display.blit(message, (WIDTH // 2 - message.get_width() // 2, HEIGHT // 2 - 50))
    pygame.display.update()


def game_over_screen(score, high_score, difficulty):
    """ Affiche l'écran de fin de jeu avec score, high score et difficulté """
    pygame.mixer.music.stop()  # Arrêter la musique de fond
    son_game_over.play(0)
    while True:
        display.fill(BLACK)

        # Fond dégradé amélioré
        for i in range(HEIGHT):
            color = (
                int(0 + (0 - 0) * i / HEIGHT),  # Bleu amélioré
                int(0 + (50 - 0) * i / HEIGHT),
                int(100 + (255 - 100) * i / HEIGHT)  # Bleu plus visible
            )
            pygame.draw.line(display, color, (0, i), (WIDTH, i))

        # Affichage du message de Game Over
        game_over_text = font.render("GAME OVER", True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        display.blit(game_over_text, game_over_rect)

        # Affichage du score et high score avec animation légère
        score_text = font.render(f"Score: {score}", True, WHITE)
        high_score_text = font.render(f"High Score: {high_score}", True, WHITE)

        # Positionnement centré
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        high_score_rect = high_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

        # Affichage des textes
        pygame.draw.rect(display, (50, 50, 50), score_rect.inflate(20, 20), border_radius=10)
        pygame.draw.rect(display, (50, 50, 50), high_score_rect.inflate(20, 20), border_radius=10)

        # Affichage des textes au-dessus des rectangles
        display.blit(score_text, score_rect)
        display.blit(high_score_text, high_score_rect)

        # Création des boutons avec un effet visuel
        replay_hover = draw_button("Rejouer", 300, 400, 200, 60, GREEN, (0, 200, 0))
        difficulty_hover = draw_button("Menu", 300, 480, 200, 60, RED, (200, 0, 0))

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Clic gauche
                if replay_hover:
                    return main(difficulty)  # Relancer la partie avec la même difficulté
                if difficulty_hover:
                    return difficulty_menu()  # Retour au menu de sélection de difficulté


        pygame.display.flip()

def game_over_screen2(score, high_score, difficulty):
    """ Affiche l'écran de fin de jeu avec score, high score et difficulté """
    pygame.mixer.music.stop()  # Arrêter la musique de fond
    son_game_over.play(0)
    while True:
        display.fill(BLACK)

        # Fond dégradé amélioré
        for i in range(HEIGHT):
            color = (
                int(0 + (0 - 0) * i / HEIGHT),  # Bleu amélioré
                int(0 + (50 - 0) * i / HEIGHT),
                int(100 + (255 - 100) * i / HEIGHT)  # Bleu plus visible
            )
            pygame.draw.line(display, color, (0, i), (WIDTH, i))

        # Affichage du message de Game Over
        game_over_text = font.render("GAME OVER", True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        display.blit(game_over_text, game_over_rect)

        # Affichage du score et high score avec animation légère
        score_text = font.render(f"Score: {score}", True, WHITE)
        high_score_text = font.render(f"High Score: {high_score}", True, WHITE)

        # Positionnement centré
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        high_score_rect = high_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

        # Affichage des textes
        pygame.draw.rect(display, (50, 50, 50), score_rect.inflate(20, 20), border_radius=10)
        pygame.draw.rect(display, (50, 50, 50), high_score_rect.inflate(20, 20), border_radius=10)

        # Affichage des textes au-dessus des rectangles
        display.blit(score_text, score_rect)
        display.blit(high_score_text, high_score_rect)

        # Création des boutons avec un effet visuel
        replay_hover = draw_button("Rejouer", 300, 400, 200, 60, GREEN, (0, 200, 0))
        difficulty_hover = draw_button("Menu", 300, 480, 200, 60, RED, (200, 0, 0))

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Clic gauche
                if replay_hover:
                    return classic_mode("easy")  # Relancer la partie avec la même difficulté
                if difficulty_hover:
                    return mode_menu()  # Retour au menu de sélection de difficulté


        pygame.display.flip()

def victory_screen(score, high_score, difficulty):
    pygame.mixer.music.stop()  # Arrêter la musique de fond
    son_victoire.play(0)
    """ Affiche l'écran de victoire avec score, high score et difficulté """
    while True:
        display.fill(BLACK)

        # Fond dégradé amélioré
        for i in range(HEIGHT):
            color = (
                int(0 + (0 - 0) * i / HEIGHT),  # Bleu amélioré
                int(0 + (50 - 0) * i / HEIGHT),
                int(100 + (255 - 100) * i / HEIGHT)  # Bleu plus visible
            )
            pygame.draw.line(display, color, (0, i), (WIDTH, i))

        # Affichage du message de victoire
        victory_text = font.render("Bravo ! Tu as mangé ton chemin jusqu'à la gloire !", True, WHITE)
        victory_rect = victory_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        display.blit(victory_text, victory_rect)

        # Affichage du score et high score avec animation légère
        score_text = font.render(f"Score: {score}", True, WHITE)
        high_score_text = font.render(f"High Score: {high_score}", True, WHITE)

        # Positionnement centré
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        high_score_rect = high_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

        # Affichage des textes avec fond
        pygame.draw.rect(display, (50, 50, 50), score_rect.inflate(20, 20), border_radius=10)
        pygame.draw.rect(display, (50, 50, 50), high_score_rect.inflate(20, 20), border_radius=10)
        display.blit(score_text, score_rect)
        display.blit(high_score_text, high_score_rect)

        # Création des boutons avec un effet visuel
        replay_hover = draw_button("Rejouer", 300, 400, 200, 60, GREEN, (0, 200, 0))
        difficulty_hover = draw_button("Menu", 300, 480, 200, 60, RED, (200, 0, 0))

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Clic gauche
                if replay_hover:
                    return main(difficulty)  # Relancer la partie avec la même difficulté
                if difficulty_hover:
                    return difficulty_menu()  # Retour au menu de sélection de difficulté

        pygame.display.flip()


# Fonction pour afficher les crédits
def credits_page():
    """ Affiche les informations universitaires avec un meilleur design """
    running = True
    while running:
        display.fill((0, 0, 0))  # Fond noir avant d'appliquer le dégradé

        # Dégradé de fond amélioré
        for i in range(HEIGHT):
            color = (
                int(0 + (30 - 0) * i / HEIGHT),
                int(0 + (80 - 0) * i / HEIGHT),
                int(120 + (255 - 120) * i / HEIGHT)
            )
            pygame.draw.line(display, color, (0, i), (WIDTH, i))

        # Titre stylisé avec ombre
        title_font = pygame.font.SysFont("Arial", 70, bold=True)
        title_surf = title_font.render("Crédits du Projet", True, WHITE)
        title_shadow = title_font.render("Crédits du Projet", True, (50, 50, 50))

        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 6))
        display.blit(title_shadow, (title_rect.x + 6, title_rect.y + 6))  # Ombre accentuée
        display.blit(title_surf, title_rect)

        # Informations Universitaires stylisées
        info_font = pygame.font.SysFont("Arial", 35)  # Texte plus grand
        info_texts = [
            "Université de Djibouti - Faculté de Science",
            "Filière: Informatique - Projet tutoré 2024/2025",
            "Groupe 33: Affi Hassan, Arafo Elmi, Souhaib Ahmed,",
            "Izoudine Bobekir, Med Moumine",
            "Prof encadreur: Issa Ali Isse"
        ]

        y_offset = 200
        for text in info_texts:
            info_surf = info_font.render(text, True, WHITE)
            info_shadow = info_font.render(text, True, (30, 30, 30))
            info_rect = info_surf.get_rect(center=(WIDTH // 2, y_offset))

            display.blit(info_shadow, (info_rect.x + 4, info_rect.y + 4))  # Ombre
            display.blit(info_surf, info_rect)
            y_offset += 50  # Plus d'espacement pour la lisibilité

        # Bouton stylisé pour "Retour"
        back_button_hover = draw_button("Retour", WIDTH // 2 - 120, HEIGHT - 100, 240, 70, (50, 200, 50), (20, 150, 20))

        pygame.display.update()

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button_hover:
                    return main_menu()  # Retour au menu principal


def mode_menu():
    """ Affiche le menu des modes de jeu """
    while True:
        # Fond dégradé amélioré
        for i in range(HEIGHT):
            color = (
                int(0 + (0 - 0) * i / HEIGHT),
                int(0 + (50 - 0) * i / HEIGHT),
                int(100 + (255 - 100) * i / HEIGHT)
            )
            pygame.draw.line(display, color, (0, i), (WIDTH, i))

        # Titre centré
        title_font = pygame.font.SysFont("Arial", 60, bold=True)
        title_surf = title_font.render("Choisissez le Mode de Jeu", True, WHITE)
        title_shadow = title_font.render("Choisissez le Mode de Jeu", True, (50, 50, 50))
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        display.blit(title_shadow, (title_rect.x + 5, title_rect.y + 5))  # Ombre du texte
        display.blit(title_surf, title_rect)

        # Boutons centrés pour les modes de jeu
        button_width, button_height = 250, 60
        classic_hover = draw_button("Mode Classic", WIDTH // 2 - button_width // 2, HEIGHT // 2 - 40, button_width, button_height, GREEN, DARK_GREEN)
        chrono_hover = draw_button("Mode Chrono", WIDTH // 2 - button_width // 2, HEIGHT // 2 + 40, button_width, button_height, RED, DARK_RED)
        back_hover = draw_button("Retour", WIDTH // 2 - button_width // 2, HEIGHT // 2 + 120, button_width, button_height, YELLOW, DARK_YELLOW)
        pygame.display.update()

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if classic_hover:
                    return classic_mode("easy") # Lancer le mode Classic
                if chrono_hover:
                    return difficulty_menu()  # Lancer le mode Chrono
                if back_hover:
                    return main_menu()


def classic_mode(difficulty="easy"):
    easy_mode = (difficulty == "easy")
    snake = Snake()
    obstacles = generate_obstacles(difficulty, snake)
    apple = Apple(snake, obstacles)
    special_apple = None
    score = 0
    speed = 10
    high_score = get_high_score(difficulty, mode="classic")
    pause = False
    game_running = True

    pygame.mixer.music.load(resource_path("sons/battleThemeA.mp3"))
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    while game_running:
        display.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pause = not pause
                if event.key == pygame.K_ESCAPE:
                    game_running = False
                directions = {
                    pygame.K_UP: "UP",
                    pygame.K_DOWN: "DOWN",
                    pygame.K_LEFT: "LEFT",
                    pygame.K_RIGHT: "RIGHT"
                }
                if event.key in directions:
                    snake.next_direction = directions[event.key]

        if pause:
            show_pause_screen()
            continue

        game_state, score = snake.move(easy_mode, score)
        if game_state == "game_over":
            save_high_score(score, difficulty, mode="classic")
            game_over_screen2(score, high_score, difficulty)
            break

        if special_apple:
            elapsed = (pygame.time.get_ticks() - special_apple.start_time) / 1000
            remaining = special_apple.time_limit - elapsed
            if remaining <= 0:
                special_apple = None
            else:
                progress_width = int(special_apple.progress_bar_width * (remaining / special_apple.time_limit))
                pygame.draw.rect(display, GRAY, (WIDTH//2 - 50, 50, 100, 10))
                pygame.draw.rect(display, ORANGE, (WIDTH//2 - 50, 50, progress_width, 10))

        if snake.body[0] == apple.position:
            son_pomme.play()
            snake.grow()
            score += 10
            apple.respawn(snake, obstacles)
            if score % 100 == 0 or (special_apple is None and random.random() < 0.1):
                special_apple = Apple(snake, obstacles, special=True)

        if special_apple and snake.body[0] == special_apple.position:
            son_pomme.play()
            snake.grow()
            snake.grow()
            score += 20
            special_apple = None

        if snake.check_collision(obstacles):
            save_high_score(score, difficulty, mode="classic")
            game_over_screen2(score, high_score, difficulty)
            pygame.mixer.music.stop()
            son_game_over.play()
            break

        snake.draw(display)
        apple.draw(display)
        draw_scores(display, score, high_score)

        if special_apple:
            special_apple.draw(display)

        for obs in obstacles:
            pygame.draw.rect(display, GRAY, pygame.Rect(obs[0], obs[1], GRID_SIZE, GRID_SIZE))

        pygame.draw.rect(display, WHITE, pygame.Rect(0, 0, WIDTH, HEIGHT), 2)

        pygame.display.flip()
        clock.tick(speed)



def main(level):
    easy_mode = (level == "easy")  # La téléportation est activée uniquement en mode easy
    snake = Snake()
    obstacles = generate_obstacles(level, snake)  # Générer les obstacles selon la difficulté
    apple = Apple(snake, obstacles)
    special_apple = None
    score = 0
    speed = 10
    high_score = get_high_score(level, mode="chrono")
    pause = False
    game_running = True  # Pour indiquer si le jeu est en cours

    pygame.mixer.music.load(resource_path("sons/battleThemeA.mp3"))  # Remplace par ton fichier
    pygame.mixer.music.set_volume(0.5)  # Ajuste le volume (0.0 à 1.0)
    pygame.mixer.music.play(-1)  # -1 pour répéter la musique en boucle


    # Paramètres en fonction du mode de jeu
    if level == "easy":
        time_limit = 180  # 3 minutes
        victory_score = 500  # Score requis pour gagner
    elif level == "medium":
        time_limit = 120  # 2 minutes
        victory_score = 300  # Score requis pour gagner
    else:
        time_limit = 60  # 1 minute
        victory_score = 200  # Score requis pour gagner

    start_time = time.time()
    game_state = "continue"

    if score % 100 == 0:
        speed = speed + 1

    while game_running:
        display.fill(BLACK)

        # Gérer les événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False  # Quitter le jeu
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # Appuie sur "Espace" pour mettre en pause/reprendre
                    pause = not pause  # Inverse l'état de pause (si c'est en pause, on reprend, sinon on met en pause)


                if event.type == pygame.KEYDOWN:
                    directions = {pygame.K_UP: "UP", pygame.K_DOWN: "DOWN", pygame.K_LEFT: "LEFT",
                                  pygame.K_RIGHT: "RIGHT"}
                    if event.key in directions:
                        snake.next_direction = directions[event.key]

        # Si le jeu est en pause, on affiche l'écran de pause
        if pause:
            show_pause_screen()  # Affiche "PAUSE"
            continue  # Ne pas exécuter le reste du code pour suspendre le jeu

        # Vérification du temps écoulé
        temps_ecoule = time.time() - start_time
        temps_restant = time_limit - int(temps_ecoule)

        # Afficher le score et le temps restant
        temps_font = pygame.font.SysFont("Arial", 24)
        temps_text = temps_font.render(f"Temps restant: {temps_restant}s", True, WHITE)
        display.blit(temps_text, (WIDTH // 2 - temps_text.get_width() // 2-300, 15))

        # Vérifier si le temps est écoulé
        if temps_restant <= 0:
            if score >= victory_score:
                save_high_score(score, level, mode="chrono")
                victory_screen(score, high_score, level)  # Afficher l'écran de victoire
                pygame.mixer.music.stop()  # Arrêter la musique de fond
                son_victoire.play()
            else:
                game_over_screen(score, high_score, level)  # Afficher l'écran de défaite
                pygame.mixer.music.stop()  # Arrêter la musique de fond
                son_game_over.play()
            break  # Quitter la boucle

        game_state, score = snake.move(easy_mode, score)
        if game_state == "game_over":
            save_high_score(score, level, mode="chrono")
            # Exemple d'appel de la fonction game_over_screen
            game_over_screen(score, high_score, level)
            break

        if special_apple is not None:
            # Calculer le temps écoulé
            elapsed_time = (pygame.time.get_ticks() - special_apple.start_time) / 1000  # En secondes
            remaining_time = special_apple.time_limit - elapsed_time

            if remaining_time <= 0:
                special_apple = None  # La pomme spéciale disparaît

            if special_apple is not None and special_apple.time_limit > 0:
                # Calculer la largeur de la barre de progression
                progress_width = int(special_apple.progress_bar_width * (remaining_time / special_apple.time_limit))

                # Dessiner la barre de progression en haut de l'écran
                pygame.draw.rect(display, GRAY, (
                WIDTH // 2 - special_apple.progress_bar_width // 2, 50, special_apple.progress_bar_width,
                special_apple.progress_bar_height))
                pygame.draw.rect(display, ORANGE, (
                WIDTH // 2 - special_apple.progress_bar_width // 2, 50, progress_width,
                special_apple.progress_bar_height))

        if snake.body[0] == apple.position:
            son_pomme.play()
            snake.grow()
            score += 10
            apple.respawn(snake, obstacles)
            if score % 100 == 0 or (special_apple is None and random.random() < 0.1):
                special_apple = Apple(snake, obstacles, special=True)

        if special_apple and snake.body[0] == special_apple.position:
            son_pomme.play()
            snake.grow()
            snake.grow()
            score += 20
            special_apple = None

        if snake.check_collision(obstacles):
            save_high_score(score, level, mode="chrono")
            game_over_screen(score, high_score, level)
            pygame.mixer.music.stop()  # Arrêter la musique de fond
            son_game_over.play()

        snake.draw(display)
        apple.draw(display)
        draw_score(display, score, high_score, level)

        if special_apple:
            special_apple.draw(display)

        for obs in obstacles:
            pygame.draw.rect(display, GRAY, pygame.Rect(obs[0], obs[1], GRID_SIZE, GRID_SIZE))

        pygame.draw.rect(display, WHITE, pygame.Rect(0, 0, WIDTH, HEIGHT), 2)

        pygame.display.flip()
        clock.tick(speed)

if __name__ == "__main__":
    main_menu()  # Démarre le jeu par le menu


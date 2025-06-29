import pygame
import sys
import time
import random
import os
import neat
import pickle
import visualize

# ### CONFIGURAÇÃO: Defina como True para executar sem gráficos (máxima velocidade)
HEADLESS_MODE = True  # Mude para False se quiser ver os gráficos

# ### NEAT: Variável para contar as gerações
gen = 0

# --- Constantes do Jogo ---
WIDTH, HEIGHT = 350, 622
FLOOR_Y = 550

# --- Inicialização do Pygame ---
pygame.init()

if not HEADLESS_MODE:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Flappy Bird AI")
else:
    # Modo headless: definir um modo de display mínimo para permitir convert_alpha()
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    screen = pygame.display.set_mode((1, 1))

# Flag para controlar se deve mostrar gráficos (apenas para as melhores gerações)
SHOW_GRAPHICS = False

# --- Carregando Imagens ---
def load_image(file_name):
    img = pygame.image.load(os.path.join("assets", file_name))
    return img.convert_alpha() if not HEADLESS_MODE else img.convert()

try:
    if not HEADLESS_MODE:
        back_img = load_image("img_46.png")
        over_img = load_image("img_45.png")
    else:
        back_img = None
        over_img = None
    
    floor_img = load_image("img_50.png")
    pipe_img = load_image("greenpipe.png")
    
    bird_down = load_image("img_47.png")
    bird_mid = load_image("img_48.png")
    bird_up = load_image("img_49.png")
    BIRDS_IMGS = [bird_down, bird_mid, bird_up]
except pygame.error as e:
    print(f"Erro ao carregar imagem: {e}")
    print("Verifique se a pasta 'assets' existe e contém todas as imagens .png no mesmo diretório do script.")
    sys.exit()

# --- Fontes (apenas se não estiver em modo headless) ---
if not HEADLESS_MODE:
    score_font = pygame.font.Font("freesansbold.ttf", 27)

class Bird:
    IMGS = BIRDS_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.gravity = 0.17
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        displacement = self.vel * self.tick_count + 0.5 * self.gravity * self.tick_count ** 2
        
        if displacement >= 16:
            displacement = 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        # Rotação simplificada (apenas para colisão)
        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
    
    def draw(self, win):
        if HEADLESS_MODE or not SHOW_GRAPHICS:
            return
        self.img_count += 1
        
        # Animação de bater de asas
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
            
        # Se o pássaro estiver caindo, não bate asas
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 400)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        if HEADLESS_MODE or not SHOW_GRAPHICS:
            return
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
        
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        return False

class Floor:
    VEL = 5
    WIDTH = floor_img.get_width()
    IMG = floor_img

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        if HEADLESS_MODE or not SHOW_GRAPHICS:
            return
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, floor, score, gen):
    if HEADLESS_MODE or not SHOW_GRAPHICS:
        return
    
    win.blit(back_img, (0,0))
    
    for pipe in pipes:
        pipe.draw(win)

    floor.draw(win)
    
    for bird in birds:
        bird.draw(win)

    # Placar
    score_label = score_font.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (WIDTH - score_label.get_width() - 15, 10))
    
    # Geração
    gen_label = score_font.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(gen_label, (10, 10))

    # Pássaros Vivos
    alive_label = score_font.render("Alive: " + str(len(birds)), 1, (255, 255, 255))
    win.blit(alive_label, (10, 50))

    pygame.display.update()


# ### NEAT: Esta é a função principal que o NEAT vai chamar para cada geração
def eval_genomes(genomes, config):
    global gen, SHOW_GRAPHICS
    gen += 1
    
    # Em modo headless, nunca mostrar gráficos
    if HEADLESS_MODE:
        SHOW_GRAPHICS = False
    else:
        SHOW_GRAPHICS = (gen % 10 == 0) or (gen > 45)

    # ### NEAT: Listas para manter o controle de cada pássaro, sua rede neural e seu genoma
    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(67, 300))
        g.fitness = 0 # Inicia a "aptidão" (pontuação) de cada pássaro com 0
        ge.append(g)

    floor = Floor(FLOOR_Y)
    pipes = [Pipe(450)]
    score = 0
    
    # Contador de frames para limitar tempo máximo por geração
    frame_count = 0
    max_frames = 3000  # Limite máximo de frames por geração
    
    running = True
    while running and len(birds) > 0 and frame_count < max_frames:
        # Processar eventos apenas se não estiver em modo headless
        if not HEADLESS_MODE and SHOW_GRAPHICS:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()

        frame_count += 1
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        for x, bird in enumerate(birds):
            bird.move()
            # ### NEAT: Recompensa menor por se manter vivo para acelerar a seleção
            ge[x].fitness += 0.1

            # ### NEAT: Ativa a rede neural do pássaro
            # Os inputs são: a posição Y do pássaro, a distância até o topo do cano e a distância até a base do cano.
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            # ### NEAT: Se a saída da rede for maior que 0.5, o pássaro pula.
            if output[0] > 0.5:
                bird.jump()

        # Movimentação dos canos e checagem de colisões
        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    # ### NEAT: Penalidade maior por colisão para acelerar a eliminação
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            pipe.move()

        if add_pipe:
            score += 1
            # ### NEAT: Recompensa grande por passar por um cano
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(450))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            # Checa se o pássaro bateu no chão ou no teto
            if bird.y + bird.img.get_height() >= FLOOR_Y or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
        
        floor.move()
        
        # Desenhar apenas se não estiver em modo headless
        if not HEADLESS_MODE and SHOW_GRAPHICS and frame_count % 2 == 0:
            draw_window(screen, birds, pipes, floor, score, gen)


# ### NEAT: Função para rodar o NEAT
def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    
    # Cria a população
    p = neat.Population(config)

    # Adiciona "reporters" para mostrar o progresso no terminal
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # ### NEAT: Roda a simulação por até 50 gerações, chamando a função eval_genomes a cada geração
    winner = p.run(eval_genomes, 1000)
    
    # Mostra as estatísticas do melhor genoma encontrado
    print('\nMelhor genoma:\n{!s}'.format(winner))
    with open('winner.pkl', 'wb') as output:
      pickle.dump(winner, output, 1)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
import pygame
import neat
import os
import pickle
from flappy_ai import Bird, Pipe, Floor, draw_window # Importa as classes do seu outro arquivo

def play_best_bird(config_path, genome_path="winner.pkl"):
    # Carrega a configuração do NEAT
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    # Carrega o genoma vencedor do arquivo
    with open(genome_path, "rb") as f:
        genome = pickle.load(f)

    # Cria a rede neural a partir do genoma
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    # --- Lógica do Jogo (similar ao loop principal, mas para um único pássaro) ---
    bird = Bird(67, 300)
    floor = Floor(550)
    pipes = [Pipe(450)]
    score = 0
    
    win = pygame.display.set_mode((350, 622))
    pygame.display.set_caption("Flappy Bird - Campeão")
    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick(60) # Roda em uma velocidade mais agradável para assistir
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                quit()

        # Usa o mesmo índice de cano que antes
        pipe_ind = 0
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        # Move o pássaro
        bird.move()

        # Ativa a rede neural para decidir se pula
        output = net.activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
        if output[0] > 0.5:
            bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            if pipe.collide(bird):
                # Se colidir, para o jogo
                running = False
                break

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True
            
            pipe.move()
        
        if not running:
            break

        if add_pipe:
            score += 1
            pipes.append(Pipe(450))

        for r in rem:
            pipes.remove(r)
            
        if bird.y + bird.img.get_height() >= 550 or bird.y < 0:
            # Se bater no chão ou no teto, para o jogo
            running = False

        floor.move()
        draw_window(win, [bird], pipes, floor, score, "Campeão")


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    play_best_bird(config_path)
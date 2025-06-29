import pygame
import neat
import os
import pickle
import sys

def play_best_bird(config_path, genome_path="winner.pkl"):
    print("🎮 Iniciando jogo com AI...")
    
    # Limpar variáveis de ambiente do pygame
    if 'SDL_VIDEODRIVER' in os.environ:
        del os.environ['SDL_VIDEODRIVER']
    
    pygame.init()
    
    # Configurações básicas
    WIDTH, HEIGHT = 350, 622
    FLOOR_Y = 550
    
    # Carrega a configuração do NEAT
    try:
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                    neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                    config_path)
        print("✅ Configuração NEAT carregada")
    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        return

    # Carrega o genoma vencedor do arquivo
    try:
        with open(genome_path, "rb") as f:
            genome = pickle.load(f)
        print(f"✅ Genoma carregado! Fitness: {genome.fitness}")
    except FileNotFoundError:
        print(f"❌ Arquivo {genome_path} não encontrado! Execute python flappy_ai.py primeiro.")
        return
    except Exception as e:
        print(f"❌ Erro ao carregar genoma: {e}")
        return

    # Cria a rede neural
    try:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        print("✅ Rede neural criada")
    except Exception as e:
        print(f"❌ Erro ao criar rede neural: {e}")
        return

    # Tentar carregar imagens - se falhar, usar formas simples
    images_loaded = False
    try:
        back_img = pygame.image.load("img_46.png").convert()
        floor_img = pygame.image.load("img_50.png").convert()
        pipe_img = pygame.image.load("greenpipe.png").convert()
        bird_img = pygame.image.load("img_48.png").convert()
        images_loaded = True
        print("✅ Imagens carregadas da pasta raiz")
    except:
        print("⚠️ Imagens não encontradas, usando gráficos simples")

    # Configurar janela
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Flappy Bird - AI Campeão")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    # Classes simplificadas (sem dependência de imagens)
    class SimpleBird:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.vel = 0
            self.gravity = 0.17
            self.tick_count = 0

        def jump(self):
            self.vel = -10.5
            self.tick_count = 0

        def move(self):
            self.tick_count += 1
            displacement = self.vel * self.tick_count + 0.5 * self.gravity * (self.tick_count ** 2)
            
            if displacement >= 16:
                displacement = 16
            if displacement < 0:
                displacement -= 2

            self.y += displacement

    class SimplePipe:
        def __init__(self, x):
            self.x = x
            self.height = __import__('random').randrange(50, 400)
            self.GAP = 200
            self.passed = False

        def move(self):
            self.x -= 5

    class SimpleFloor:
        def __init__(self):
            self.x1 = 0
            self.x2 = WIDTH

        def move(self):
            self.x1 -= 5
            self.x2 -= 5
            if self.x1 <= -WIDTH:
                self.x1 = self.x2 + WIDTH
            if self.x2 <= -WIDTH:
                self.x2 = self.x1 + WIDTH

    # Inicializar objetos do jogo
    bird = SimpleBird(67, 300)
    floor = SimpleFloor()
    pipes = [SimplePipe(700)]  # Mesma distância do treinamento
    score = 0
    running = True

    print("🚀 Jogo iniciado! Pressione ESC para sair.")

    while running:
        clock.tick(60)

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Determinar cano mais próximo
        pipe_ind = 0
        if len(pipes) > 1 and bird.x > pipes[0].x + 52:
            pipe_ind = 1

        # Mover pássaro
        bird.move()

        # ### MESMOS INPUTS DO TREINAMENTO ###
        gap_center = pipes[pipe_ind].height + pipes[pipe_ind].GAP/2
        vertical_diff = (bird.y - gap_center) / 100
        horizontal_dist = max(0, pipes[pipe_ind].x - bird.x) / 400
        velocity = bird.vel / 10

        # Ativar rede neural
        try:
            output = net.activate((vertical_diff, horizontal_dist, velocity))
            if output[0] > 0.3:  # Mesmo limiar do treinamento
                bird.jump()
        except Exception as e:
            print(f"❌ Erro na rede neural: {e}")
            break

        # Lógica dos canos
        add_pipe = False
        pipes_to_remove = []

        for pipe in pipes:
            pipe.move()

            # Verificar se passou pelo cano
            if not pipe.passed and bird.x >= pipe.x + 52 - 10:
                pipe.passed = True
                add_pipe = True
                score += 1
                print(f"🎉 Passou pelo cano! Score: {score}")

            # Verificar colisão (mesma lógica do treinamento)
            bird_center_x = bird.x + 17
            bird_center_y = bird.y + 12
            
            if (bird_center_x > pipe.x - 10 and bird_center_x < pipe.x + 60):
                if (bird_center_y < pipe.height + 10 or bird_center_y > pipe.height + pipe.GAP - 10):
                    print(f"💥 Colidiu com cano! Score final: {score}")
                    running = False
                    break

            # Remover canos que saíram da tela
            if pipe.x + 52 < 0:
                pipes_to_remove.append(pipe)

        # Adicionar novo cano
        if add_pipe:
            pipes.append(SimplePipe(700))

        # Remover canos antigos
        for pipe in pipes_to_remove:
            pipes.remove(pipe)

        # Verificar colisão com chão/teto
        if bird.y + 30 >= FLOOR_Y or bird.y < -5:
            print(f"💥 Bateu no chão/teto! Score final: {score}")
            running = False

        floor.move()

        # ### DESENHAR ###
        # Fundo
        win.fill((135, 206, 235))  # Azul céu

        if images_loaded:
            # Desenhar com imagens
            win.blit(back_img, (0, 0))
            
            # Canos
            for pipe in pipes:
                pipe_top = pygame.transform.flip(pipe_img, False, True)
                win.blit(pipe_top, (pipe.x, pipe.height - pipe_img.get_height()))
                win.blit(pipe_img, (pipe.x, pipe.height + pipe.GAP))
            
            # Chão
            win.blit(floor_img, (floor.x1, FLOOR_Y))
            win.blit(floor_img, (floor.x2, FLOOR_Y))
            
            # Pássaro
            win.blit(bird_img, (bird.x, bird.y))
        else:
            # Desenhar com formas simples
            # Chão
            pygame.draw.rect(win, (222, 216, 149), (0, FLOOR_Y, WIDTH, HEIGHT-FLOOR_Y))
            
            # Canos
            for pipe in pipes:
                # Cano superior
                pygame.draw.rect(win, (0, 128, 0), (pipe.x, 0, 52, pipe.height))
                # Cano inferior
                pygame.draw.rect(win, (0, 128, 0), (pipe.x, pipe.height + pipe.GAP, 52, HEIGHT - pipe.height - pipe.GAP))
            
            # Pássaro
            pygame.draw.circle(win, (255, 255, 0), (bird.x + 17, bird.y + 12), 12)

        # Textos
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        win.blit(score_text, (10, 10))
        
        ai_text = font.render("AI Jogando", True, (255, 255, 255))
        win.blit(ai_text, (10, 50))
        
        fitness_text = font.render(f"Fitness: {genome.fitness:.1f}", True, (255, 255, 255))
        win.blit(fitness_text, (10, 90))

        pygame.display.flip()

    # Resultado final
    print(f"\n🏁 Jogo finalizado!")
    print(f"🏆 Score final: {score}")
    print(f"📊 Fitness do genoma: {genome.fitness}")
    
    pygame.quit()
    print("Pressione Enter para fechar...")
    input()


if __name__ == '__main__':
    try:
        local_dir = os.path.dirname(__file__)
        config_path = os.path.join(local_dir, 'config-feedforward.txt')
        
        if not os.path.exists('winner.pkl'):
            print("❌ Arquivo winner.pkl não encontrado!")
            print("Execute primeiro: python flappy_ai.py")
            input("Pressione Enter para fechar...")
            sys.exit(1)
            
        play_best_bird(config_path)
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        input("Pressione Enter para fechar...")
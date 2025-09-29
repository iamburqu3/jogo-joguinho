import random
import pygame
import supabase
import os
from supabase import create_client, Client

# --- CONSTANTES GLOBAIS ---
METEOR_TYPE = "METEORO"
STAR_TYPE = "ESTRELA"
ENEMY_TYPE = "INIMIGO"
BULLET_TYPE = "PROJETIL_INIMIGO"
BOSS_TYPE = "BOSS"
PLAYER_BULLET_TYPE = "TIRO_PLAYER"

# Cores para Placeholders
AZUL_ESCURO = (10, 10, 40)
BRANCO = (255, 255, 255)
VERMELHO = (200, 50, 50)
AMARELO = (255, 255, 0)
VERDE = (0, 200, 0)
ROXO = (150, 0, 150)
AZUL_CLARO = (0, 150, 255)

# Configurações do Supabase (MANTIDAS)
SUPABASE_URL = "https://uxagbrbcgzyqahqkdpbs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4YWdicmJjZ3p5cWFocWtkcGJzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzI5MDc1OSwiZXhwIjoyMDcyODY2NzU5fQ.TFGARD7msT8whJ4c8Y9Q_EPy31w2Vp2qTfX-4_Pj4_8g"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

pygame.init()

largura, altura = 400, 600
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("Space Collector - Ciclo de Bosses com Pausa!")
clock = pygame.time.Clock()

# === VARIÁVEIS DE JOGO E LEVEL UP ===
fonte = pygame.font.Font(None, 36)
fonte_pequena = pygame.font.Font(None, 24)

tempo_inicio = pygame.time.get_ticks()
tempo_atual = 0

# VARIÁVEIS DO SISTEMA DE LEVEL
nivel = 1
xp_atual = 0
xp_proximo_nivel = 100
VELOCIDADE_INIMIGOS = 3
COOLDOWN_PROJETIL_BASE = 120
XP_POR_ESTRELA = 25
PLAYER_DANO = 10

# VARIÁVEIS DO SISTEMA DE BOSS
boss_ativo = False
tempo_proximo_boss = 30
boss_hp_base = 50
boss_cooldown_base = 30
boss_padrao_atual = 0

# VARIÁVEIS DA ARMA DO JOGADOR
player_projeteis = []
player_cooldown_max = 15
player_cooldown = 0
player_velocidade_tiro = 10

jogador = pygame.Rect(180, 500, 30, 40)
velocidade = 5
obstaculos = []
projeteis_inimigos = []

objetos_assets = [
    {'img': None, 'type': METEOR_TYPE, 'xp': 0, 'cor': VERMELHO, 'hp': 1, 'dano_boss': False},
    {'img': None, 'type': STAR_TYPE, 'xp': XP_POR_ESTRELA, 'cor': AMARELO, 'hp': 0, 'dano_boss': False},
    {'img': None, 'type': ENEMY_TYPE, 'xp': 0, 'cor': VERDE, 'hp': 1, 'dano_boss': True},
    {'img': None, 'type': BOSS_TYPE, 'xp': 100, 'cor': ROXO, 'hp': boss_hp_base, 'dano_boss': True},
]

nome_jogador = ""


# --- FUNÇÕES SUPABASE ---
def salvar_pontuacao(nome, nivel, tempo):
    try:
        data = supabase.table("ranking").insert({
            "nome": nome,
            "pontuacao": nivel,
            "tempo": tempo
        }).execute()
        return True
    except Exception as e:
        print(f"Erro ao salvar pontuação: {e}")
        return False


def obter_top_pontuacoes():
    try:
        response = supabase.table("ranking") \
            .select("*") \
            .order("pontuacao", desc=True) \
            .limit(3) \
            .execute()
        return response.data
    except Exception as e:
        print(f"Erro ao obter pontuações: {e}")
        return []


# --- FUNÇÕES DE PADRÃO DE ATAQUE (CORRIGIDAS) ---

def atirar_padrao_boss(boss_obj, padrao):
    """
    Função que implementa os diferentes padrões de ataque do Boss.
    Retorna uma lista de novos projéteis e o cooldown ajustado.
    """
    novos_projeteis = []
    cooldown_ajustado = 60  # Cooldown padrão de 1 segundo

    # TRATAMENTO DO ERRO: Se boss_obj for None (na inicialização), não tenta acessar as coordenadas.
    if boss_obj is None:
        boss_x = largura // 2 - 60  # Valor placeholder
        boss_y = 50
    else:
        boss_x = boss_obj["rect"].x
        boss_y = boss_obj["rect"].y

    if padrao == 1:
        # Padrão 1: Tiro Duplo Rápido e Focado
        if boss_obj is not None:
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 10, boss_y))
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 70, boss_y))
        cooldown_ajustado = 30

    elif padrao == 2:
        # Padrão 2: Tiro Triplo em Leque (Espalhado)
        if boss_obj is not None:
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 5, boss_y))
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 45, boss_y))
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 85, boss_y))
        cooldown_ajustado = 60

    elif padrao == 3:
        # Padrão 3: Tiro central lento e grande
        if boss_obj is not None:
            rect_tiro = pygame.Rect(boss_x + 40, boss_y + 40, 40, 40)
            novos_projeteis.append({"rect": rect_tiro, "cor": VERMELHO, "velocidade": 4})
        cooldown_ajustado = 90

    elif padrao == 4:
        # Padrão 4: PAUSA (Não atira)
        cooldown_ajustado = 60  # Pausa por 1 segundo

    else:
        cooldown_ajustado = 60

        # O cooldown final é reduzido pelo nível para aumentar a dificuldade progressivamente
    cooldown_final = max(10, cooldown_ajustado - (nivel * 2))
    return novos_projeteis, cooldown_final


# --- FUNÇÕES DE OBJETO E PROJÉTIL ---
def criar_objeto():
    """Cria um objeto regular (Estrela, Meteoro, Inimigo)"""
    x = random.randint(0, largura - 40)

    chance = random.random()
    if chance < 0.6:
        asset_info = objetos_assets[1]  # Estrela
    elif chance < 0.8:
        asset_info = objetos_assets[0]  # Meteoro
    else:
        asset_info = objetos_assets[2]  # Inimigo

    rect = pygame.Rect(x, -40, 40, 40)

    objeto = {"rect": rect, "asset_info": asset_info, "hp": asset_info['hp']}

    if asset_info['type'] == ENEMY_TYPE:
        cooldown_ajustado = max(30, COOLDOWN_PROJETIL_BASE - (nivel * 5))
        objeto['cooldown'] = random.randint(cooldown_ajustado - 30, cooldown_ajustado)

    return objeto


def criar_objeto_boss():
    """Cria o objeto Boss (Parado na posição inicial)"""
    asset_info = objetos_assets[3]  # Boss

    # Boss FIXO na parte superior da tela
    rect = pygame.Rect(largura // 2 - 60, 50, 120, 80)

    boss_hp_atual = asset_info['hp'] + (nivel * 50)

    # Inicia com um padrão de ataque ofensivo (1, 2 ou 3)
    padrao_inicial = random.randint(1, 3)

    # Obtém o cooldown inicial apenas chamando a função com None para boss_obj
    _, cooldown_inicial = atirar_padrao_boss(None, padrao_inicial)

    objeto = {
        "rect": rect,
        "asset_info": asset_info,
        "hp": boss_hp_atual,
        "max_hp": boss_hp_atual,
        "cooldown": cooldown_inicial,
        "padrao": padrao_inicial
    }
    return objeto


def criar_projetil_inimigo(x, y):
    """Cria o projétil atirado pelas Naves Inimigas ou Boss."""
    rect = pygame.Rect(x + 15, y + 40, 10, 20)
    return {"rect": rect, "cor": VERMELHO, "velocidade": 8}


def criar_player_projetil():
    """Cria o projétil atirado pelo jogador."""
    rect = pygame.Rect(jogador.x + 10, jogador.y - 20, 10, 20)
    return {"rect": rect, "cor": BRANCO}


# --- FUNÇÕES DE LEVEL UP E POWER-UP ---
POWER_UPS = [
    {"nome": "Hyper-Speed", "descricao": "Aumenta a velocidade de movimento da sua nave (V + 1)."},
    {"nome": "Dano Aprimorado", "descricao": "Aumenta o dano da sua arma (+5 Dano)."},
    {"nome": "Sorte do Saqueador", "descricao": "Aumenta o XP ganho por estrela coletada."},
    {"nome": "Fogo Rápido", "descricao": "Diminui o Cooldown do seu tiro (Atira mais rápido)."},
]


def aplicar_power_up(nome_power_up):
    global velocidade, COOLDOWN_PROJETIL_BASE, XP_POR_ESTRELA, objetos_assets, player_cooldown_max, PLAYER_DANO

    if nome_power_up == "Hyper-Speed":
        velocidade += 1
    elif nome_power_up == "Dano Aprimorado":
        PLAYER_DANO += 5
    elif nome_power_up == "Sorte do Saqueador":
        XP_POR_ESTRELA += 10
        objetos_assets[1]['xp'] = XP_POR_ESTRELA
    elif nome_power_up == "Fogo Rápido":
        player_cooldown_max = max(5, player_cooldown_max - 3)

    print(f"Power-up '{nome_power_up}' aplicado! Nível: {nivel}")


def desenhar_botao(texto, x, y, largura, altura, cor_normal, cor_hover, mouse_pos):
    cor = cor_hover if (x <= mouse_pos[0] <= x + largura and y <= mouse_pos[1] <= y + altura) else cor_normal
    pygame.draw.rect(tela, cor, (x, y, largura, altura))
    pygame.draw.rect(tela, BRANCO, (x, y, largura, altura), 2)
    texto_botao = fonte.render(texto, True, BRANCO)
    texto_x = x + (largura - texto_botao.get_width()) // 2
    texto_y = y + (altura - texto_botao.get_height()) // 2
    tela.blit(texto_botao, (texto_x, texto_y))


def desenhar_power_up_tela(power_ups_escolhidos, mouse_pos):
    tela.fill(AZUL_ESCURO)

    texto_titulo = fonte.render(f"NÍVEL {nivel} ALCANÇADO!", True, AMARELO)
    texto_instrucao = fonte.render("Escolha um Power-up:", True, BRANCO)
    tela.blit(texto_titulo, (largura // 2 - texto_titulo.get_width() // 2, 50))
    tela.blit(texto_instrucao, (largura // 2 - texto_instrucao.get_width() // 2, 100))

    botoes = []
    y_start = 180

    for i, pu in enumerate(power_ups_escolhidos):
        x, y, w, h = 50, y_start + i * 130, 300, 100
        botoes.append((x, y, w, h, pu))

        cor_normal = (50, 50, 100)
        cor_hover = (80, 80, 150)

        desenhar_botao(pu['nome'], x, y, w, h, cor_normal, cor_hover, mouse_pos)

        texto_desc = fonte_pequena.render(pu['descricao'], True, BRANCO)
        tela.blit(texto_desc, (x + 10, y + h // 2 + 10))

    pygame.display.flip()
    return botoes


def tela_escolha_power_up():
    power_ups_escolhidos = random.sample(POWER_UPS, 3)

    escolhendo = True
    while escolhendo:
        mouse_pos = pygame.mouse.get_pos()
        botoes = desenhar_power_up_tela(power_ups_escolhidos, mouse_pos)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    for x, y, w, h, pu in botoes:
                        if x <= mouse_pos[0] <= x + w and y <= mouse_pos[1] <= y + h:
                            aplicar_power_up(pu['nome'])
                            escolhendo = False
                            return True
        clock.tick(60)
    return True


def checar_level_up(ganho_xp):
    global nivel, xp_atual, xp_proximo_nivel
    xp_atual += ganho_xp

    if xp_atual >= xp_proximo_nivel:
        nivel += 1
        xp_atual = xp_atual - xp_proximo_nivel
        xp_proximo_nivel = int(xp_proximo_nivel * 1.5)

        if not tela_escolha_power_up():
            return False

    return True


# --- FUNÇÕES DE INTERFACE E CONTROLE ---
def atualizar_pontuacao():
    global tempo_atual
    tempo_atual = (pygame.time.get_ticks() - tempo_inicio) // 1000


def desenhar_interface():
    atualizar_pontuacao()

    minutos = tempo_atual // 60
    segundos = tempo_atual % 60
    texto_tempo = fonte.render(f"Tempo: {minutos:02d}:{segundos:02d}", True, BRANCO)
    tela.blit(texto_tempo, (10, 10))

    texto_nivel = fonte.render(f"Nível: {nivel}", True, AZUL_CLARO)
    tela.blit(texto_nivel, (largura - texto_nivel.get_width() - 10, 10))

    # Barra de XP
    barra_largura = 150
    barra_altura = 10
    xp_percent = xp_atual / xp_proximo_nivel
    xp_preenchido = int(barra_largura * xp_percent)

    pygame.draw.rect(tela, (50, 50, 50), (largura - barra_largura - 10, 50, barra_largura, barra_altura))
    pygame.draw.rect(tela, AZUL_CLARO, (largura - barra_largura - 10, 50, xp_preenchido, barra_altura))
    pygame.draw.rect(tela, BRANCO, (largura - barra_largura - 10, 50, barra_largura, barra_altura), 1)


def desenhar_barra_boss(boss_obj):
    """Desenha a barra de vida do Boss."""
    hp_percent = boss_obj['hp'] / boss_obj['max_hp']
    barra_largura_total = 300
    barra_preenchida = int(barra_largura_total * hp_percent)

    x, y = largura // 2 - barra_largura_total // 2, 90

    pygame.draw.rect(tela, (50, 50, 50), (x, y, barra_largura_total, 15))
    pygame.draw.rect(tela, ROXO, (x, y, barra_preenchida, 15))
    pygame.draw.rect(tela, BRANCO, (x, y, barra_largura_total, 15), 2)

    texto_hp = fonte_pequena.render(f"BOSS HP: {int(boss_obj['hp'])}", True, BRANCO)
    tela.blit(texto_hp, (x + 10, y + 2))


def desenhar_campo_texto(texto, x, y, largura, altura, ativo):
    cor = (100, 100, 100) if ativo else (70, 70, 70)
    pygame.draw.rect(tela, cor, (x, y, largura, altura))
    pygame.draw.rect(tela, BRANCO, (x, y, largura, altura), 2)
    texto_surface = fonte.render(texto, True, BRANCO)
    tela.blit(texto_surface, (x + 5, y + (altura - texto_surface.get_height()) // 2))
    if ativo:
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = x + 5 + texto_surface.get_width()
            pygame.draw.line(tela, BRANCO, (cursor_x, y + 5), (cursor_x, y + altura - 5), 2)


def reiniciar_jogo():
    global jogador, obstaculos, tempo_inicio, tempo_atual, nome_jogador, projeteis_inimigos
    global nivel, xp_atual, xp_proximo_nivel, boss_ativo, tempo_proximo_boss, player_projeteis
    global player_cooldown_max, PLAYER_DANO, XP_POR_ESTRELA, VELOCIDADE_INIMIGOS, COOLDOWN_PROJETIL_BASE, velocidade

    # Resetar variáveis de jogo
    jogador = pygame.Rect(180, 500, 30, 40)
    obstaculos = []
    projeteis_inimigos = []
    player_projeteis = []
    tempo_inicio = pygame.time.get_ticks()
    tempo_atual = 0
    nome_jogador = ""

    # Resetar status de nível/poderes (voltando aos valores originais)
    nivel = 1
    xp_atual = 0
    xp_proximo_nivel = 100
    boss_ativo = False
    tempo_proximo_boss = 30

    # Resetar Power-ups para o estado inicial
    velocidade = 5
    PLAYER_DANO = 10
    XP_POR_ESTRELA = 25
    player_cooldown_max = 15
    objetos_assets[1]['xp'] = XP_POR_ESTRELA


def tela_digitar_nome():
    global nome_jogador
    nome_jogador = ""
    digitando = True
    campo_ativo = True
    while digitando:
        mouse_pos = pygame.mouse.get_pos()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            elif evento.type == pygame.KEYDOWN:
                if campo_ativo:
                    if evento.key == pygame.K_RETURN and nome_jogador.strip():
                        digitando = False
                    elif evento.key == pygame.K_BACKSPACE:
                        nome_jogador = nome_jogador[:-1]
                    elif evento.key == pygame.K_ESCAPE:
                        return False
                    elif len(nome_jogador) < 15:
                        nome_jogador += evento.unicode
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                campo_rect = pygame.Rect(largura // 2 - 150, altura // 2, 300, 40)
                campo_ativo = campo_rect.collidepoint(mouse_pos)
        tela.fill(AZUL_ESCURO)
        texto_titulo = fonte.render("DIGITE SEU NOME", True, BRANCO)
        texto_instrucao = fonte_pequena.render("Pressione ENTER para continuar", True, (200, 200, 200))
        tela.blit(texto_titulo, (largura // 2 - texto_titulo.get_width() // 2, altura // 2 - 60))
        tela.blit(texto_instrucao, (largura // 2 - texto_instrucao.get_width() // 2, altura // 2 + 50))
        desenhar_campo_texto(nome_jogador, largura // 2 - 150, altura // 2, 300, 40, campo_ativo)
        pygame.display.flip()
        clock.tick(60)
    return True


def tela_game_over():
    global rodando, nome_jogador

    if nome_jogador:
        salvar_pontuacao(nome_jogador, nivel, tempo_atual)

    top_pontuacoes = obter_top_pontuacoes()

    botao_reiniciar_rect = (largura // 2 - 100, altura // 2 + 160, 200, 50)
    botao_sair_rect = (largura // 2 - 100, altura // 2 + 220, 200, 50)

    aguardando = True
    while aguardando:
        mouse_pos = pygame.mouse.get_pos()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                aguardando = False; rodando = False; return False
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    if (botao_reiniciar_rect[0] <= mouse_pos[0] <= botao_reiniciar_rect[0] + botao_reiniciar_rect[2] and
                            botao_reiniciar_rect[1] <= mouse_pos[1] <= botao_reiniciar_rect[1] + botao_reiniciar_rect[
                                3]):
                        reiniciar_jogo();
                        aguardando = False;
                        return True
                    elif (botao_sair_rect[0] <= mouse_pos[0] <= botao_sair_rect[0] + botao_sair_rect[2] and
                          botao_sair_rect[1] <= mouse_pos[1] <= botao_sair_rect[1] + botao_sair_rect[3]):
                        aguardando = False;
                        rodando = False;
                        return False

        tela.fill(AZUL_ESCURO)

        texto_game_over = fonte.render("NAVE DESTRUIDA!", True, VERMELHO)
        texto_nivel_final = fonte.render(f"Nível Máximo Alcançado: {nivel}", True, BRANCO)
        texto_tempo_final = fonte.render(f"Tempo de Sobrevivência: {tempo_atual // 60:02d}:{tempo_atual % 60:02d}",
                                         True, BRANCO)

        tela.blit(texto_game_over, (largura // 2 - texto_game_over.get_width() // 2, altura // 2 - 150))
        tela.blit(texto_nivel_final, (largura // 2 - texto_nivel_final.get_width() // 2, altura // 2 - 110))
        tela.blit(texto_tempo_final, (largura // 2 - texto_tempo_final.get_width() // 2, altura // 2 - 70))

        texto_ranking = fonte.render("TOP 3 NÍVEIS", True, AMARELO)
        tela.blit(texto_ranking, (largura // 2 - texto_ranking.get_width() // 2, altura // 2 - 30))

        for i, record in enumerate(top_pontuacoes):
            texto_record = fonte_pequena.render(
                f"{i + 1}. {record['nome']}: NÍVEL {record['pontuacao']} - {record['tempo'] // 60:02d}:{record['tempo'] % 60:02d}",
                True, BRANCO
            )
            tela.blit(texto_record, (largura // 2 - texto_record.get_width() // 2, altura // 2 + i * 25))

        desenhar_botao("REINICIAR MISSAO", botao_reiniciar_rect[0], botao_reiniciar_rect[1],
                       botao_reiniciar_rect[2], botao_reiniciar_rect[3],
                       (0, 100, 0), (0, 150, 0), mouse_pos)
        desenhar_botao("SAIR", botao_sair_rect[0], botao_sair_rect[1],
                       botao_sair_rect[2], botao_sair_rect[3],
                       (100, 0, 0), (150, 0, 0), mouse_pos)

        pygame.display.flip()
        clock.tick(60)
    return False


# --- LOOP PRINCIPAL DO JOGO ---
rodando = True
while rodando:
    tela.fill(AZUL_ESCURO)

    # 1. TRATAMENTO DE INPUT E TIRO DO JOGADOR
    teclas = pygame.key.get_pressed()

    if teclas[pygame.K_LEFT] and jogador.left > 0: jogador.x -= velocidade
    if teclas[pygame.K_RIGHT] and jogador.right < largura: jogador.x += velocidade
    if teclas[pygame.K_UP] and jogador.top > 0: jogador.y -= velocidade
    if teclas[pygame.K_DOWN] and jogador.bottom < altura: jogador.y += velocidade

    player_cooldown = max(0, player_cooldown - 1)
    if teclas[pygame.K_SPACE] and player_cooldown == 0:
        player_projeteis.append(criar_player_projetil())
        player_cooldown = player_cooldown_max

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    # 2. GERAÇÃO DE OBJETOS E BOSS

    if not boss_ativo and tempo_atual >= tempo_proximo_boss:
        obstaculos.append(criar_objeto_boss())
        boss_ativo = True
        tempo_proximo_boss += 30

    if not boss_ativo and random.randint(1, 30) == 1:
        obstaculos.append(criar_objeto())

    # 3. LÓGICA DO PROJÉTIL DO JOGADOR
    novos_projeteis_player = []

    for p_proj in player_projeteis:
        p_proj["rect"].y -= player_velocidade_tiro
        acertou_alvo = False

        novos_obstaculos_temp = []
        for obstaculo in obstaculos:
            if obstaculo["rect"].colliderect(p_proj["rect"]):
                obj_type = obstaculo["asset_info"]["type"]

                if obj_type != STAR_TYPE:
                    obstaculo["hp"] -= PLAYER_DANO
                    acertou_alvo = True

                    if obstaculo["hp"] <= 0:
                        if obj_type == BOSS_TYPE:
                            xp_ganho = obstaculo["asset_info"]["xp"] * nivel
                            if not checar_level_up(xp_ganho): rodando = False; break

                            boss_ativo = False

                        elif obj_type == ENEMY_TYPE or obj_type == METEOR_TYPE:
                            pass

                        continue

            novos_obstaculos_temp.append(obstaculo)

        obstaculos = novos_obstaculos_temp

        if not acertou_alvo and p_proj["rect"].y > 0:
            novos_projeteis_player.append(p_proj)
            pygame.draw.rect(tela, p_proj["cor"], p_proj["rect"])

    player_projeteis = novos_projeteis_player
    if not rodando: break

    # 4. LÓGICA DE OBSTÁCULOS E PROJÉTEIS INIMIGOS
    novos_obstaculos = []

    for obstaculo in obstaculos:

        obj_type = obstaculo["asset_info"]["type"]

        # Movimento: Apenas Inimigos e Meteoros caem. Boss FICA PARADO.
        if obj_type != BOSS_TYPE:
            obstaculo["rect"].y += VELOCIDADE_INIMIGOS

            # LÓGICA DE ATAQUE INIMIGO/BOSS
        if obj_type == ENEMY_TYPE or obj_type == BOSS_TYPE:
            obstaculo['cooldown'] -= 1
            if obstaculo['cooldown'] <= 0:

                if obj_type == BOSS_TYPE:
                    # 1. Executa o ataque atual (somente se não for pausa)
                    novos_tiros = []
                    if obstaculo['padrao'] != 4:
                        novos_tiros, _ = atirar_padrao_boss(obstaculo, obstaculo['padrao'])
                        projeteis_inimigos.extend(novos_tiros)

                    # 2. Define o próximo estado (ataque ou pausa)
                    if obstaculo['padrao'] == 4:
                        # Se estava em pausa, o próximo será um ataque ofensivo (1, 2 ou 3)
                        obstaculo['padrao'] = random.randint(1, 3)
                    else:
                        # Se atacou, há 50% de chance de pausar (Padrão 4) ou 50% de chance de outro ataque (1, 2 ou 3)
                        if random.random() < 0.5:
                            obstaculo['padrao'] = 4
                        else:
                            obstaculo['padrao'] = random.randint(1, 3)

                    # 3. Define o cooldown para o PRÓXIMO estado/padrão
                    _, cooldown_proximo = atirar_padrao_boss(obstaculo, obstaculo['padrao'])
                    obstaculo['cooldown'] = random.randint(cooldown_proximo - 10, cooldown_proximo)

                else:  # Nave Inimiga Padrão
                    projeteis_inimigos.append(criar_projetil_inimigo(obstaculo["rect"].x, obstaculo["rect"].y))
                    cooldown_atual = max(30, COOLDOWN_PROJETIL_BASE - (nivel * 5))
                    obstaculo['cooldown'] = random.randint(cooldown_atual - 10, cooldown_atual)

        # COLISÃO DO JOGADOR COM OBJETOS MAIORES
        if obstaculo["rect"].colliderect(jogador):
            if obj_type == STAR_TYPE:
                if not checar_level_up(obstaculo["asset_info"]["xp"]): rodando = False; break
                continue

            elif obj_type != STAR_TYPE:
                if tela_digitar_nome():
                    if not tela_game_over(): rodando = False; break
                else:
                    rodando = False; break

        # Desenho e Manutenção
        if obstaculo["rect"].y < altura:
            novos_obstaculos.append(obstaculo)

            obj_cor = obstaculo["asset_info"]["cor"]
            pygame.draw.rect(tela, obj_cor, obstaculo["rect"])

            if obj_type == BOSS_TYPE:
                desenhar_barra_boss(obstaculo)

    obstaculos = novos_obstaculos
    if not rodando: break

    # 5. MOVIMENTO E COLISÃO DOS PROJÉTEIS INIMIGOS
    novos_projeteis_inimigos = []
    for p_inimigo in projeteis_inimigos:
        velocidade_tiro = p_inimigo.get("velocidade", 8)
        p_inimigo["rect"].y += velocidade_tiro

        if p_inimigo["rect"].colliderect(jogador):
            if tela_digitar_nome():
                if not tela_game_over(): rodando = False; break
            else:
                rodando = False; break

        if p_inimigo["rect"].y < altura:
            novos_projeteis_inimigos.append(p_inimigo)
            pygame.draw.rect(tela, p_inimigo["cor"], p_inimigo["rect"])

    projeteis_inimigos = novos_projeteis_inimigos
    if not rodando: break

    # 6. ATUALIZAÇÃO DA TELA
    desenhar_interface()

    # Desenhar jogador
    pygame.draw.rect(tela, BRANCO, jogador)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
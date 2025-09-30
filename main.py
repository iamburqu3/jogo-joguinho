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

# Cores para Placeholders (Mantidas, mas menos usadas)
AZUL_ESCURO = (10, 10, 40)
BRANCO = (255, 255, 255)
VERMELHO = (200, 50, 50)
AMARELO = (255, 255, 0)
VERDE = (0, 200, 0)
ROXO = (150, 0, 150)
AZUL_CLARO = (0, 150, 255)

# Configurações do Supabase (MANTIDAS)
SUPABASE_URL = "https://uxagbrbcgzyqahqkdpbs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4YWdicmJjZ3p5cWFocWtkcGJzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzI5MDc1OSwiZXhwIjoyMDcyODY2NzU5fQ.TFGARD7msT8whH4c8Y9Q_EPy31w2Vp2qTfX-4_Pj4_8g"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

pygame.init()

largura, altura = 400, 600
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("Space Collector - Dificuldade Escalonada!")
clock = pygame.time.Clock()

# --- CARREGAMENTO DE IMAGENS ---
try:
    # Fundo e Obstáculos
    IMAGEM_FUNDO = pygame.image.load(os.path.join('fundo.png')).convert()
    IMAGEM_FUNDO = pygame.transform.scale(IMAGEM_FUNDO, (largura, altura))

    IMAGEM_ESTRELA = pygame.image.load(os.path.join('estrela.png')).convert_alpha()
    IMAGEM_ESTRELA = pygame.transform.scale(IMAGEM_ESTRELA, (40, 40))

    IMAGEM_METEORO = pygame.image.load(os.path.join('asteroide.png')).convert_alpha()
    IMAGEM_METEORO = pygame.transform.scale(IMAGEM_METEORO, (40, 40))

    # Imagens do Jogo
    IMAGEM_PLAYER = pygame.image.load(os.path.join('player.png')).convert_alpha()
    IMAGEM_PLAYER = pygame.transform.scale(IMAGEM_PLAYER, (30, 40))  # Tamanho da Nave do Jogador

    IMAGEM_NAVE_INIMIGA = pygame.image.load(os.path.join('inimigo.png')).convert_alpha()
    IMAGEM_NAVE_INIMIGA = pygame.transform.scale(IMAGEM_NAVE_INIMIGA, (40, 40))  # Tamanho da Nave Inimiga

    IMAGEM_BOSS = pygame.image.load(os.path.join('boss.png')).convert_alpha()
    IMAGEM_BOSS = pygame.transform.scale(IMAGEM_BOSS, (120, 80))  # Tamanho do Boss

    # Projéteis
    IMAGEM_PROJETIL = pygame.image.load(os.path.join('projetil.png')).convert_alpha()
    IMAGEM_PROJETIL = pygame.transform.scale(IMAGEM_PROJETIL, (10, 20))

except pygame.error as e:
    print(
        f"ERRO AO CARREGAR IMAGEM: {e}. Certifique-se de que todas as imagens (fundo.png, estrela.png, asteroide.png, projetil.png, player.png, inimigo.png, boss.png) estão na pasta correta.")
    # Define superfícies padrão caso as imagens falhem
    IMAGEM_FUNDO = pygame.Surface((largura, altura));
    IMAGEM_FUNDO.fill(AZUL_ESCURO)
    IMAGEM_ESTRELA = pygame.Surface((40, 40));
    IMAGEM_ESTRELA.fill(AMARELO)
    IMAGEM_METEORO = pygame.Surface((40, 40));
    IMAGEM_METEORO.fill(VERMELHO)
    IMAGEM_PROJETIL = pygame.Surface((10, 20));
    IMAGEM_PROJETIL.fill(BRANCO)
    IMAGEM_PLAYER = pygame.Surface((30, 40));
    IMAGEM_PLAYER.fill(BRANCO)
    IMAGEM_NAVE_INIMIGA = pygame.Surface((40, 40));
    IMAGEM_NAVE_INIMIGA.fill(VERDE)
    IMAGEM_BOSS = pygame.Surface((120, 80));
    IMAGEM_BOSS.fill(ROXO)

# === VARIÁVEIS DE JOGO E LEVEL UP ===
fonte = pygame.font.Font(None, 36)
fonte_pequena = pygame.font.Font(None, 24)

tempo_inicio = pygame.time.get_ticks()
tempo_atual = 0

# VARIÁVEIS DO SISTEMA DE LEVEL
nivel = 1
xp_atual = 0
xp_proximo_nivel = 100
# VARIÁVEIS AJUSTADAS PARA ESCALONAMENTO
VELOCIDADE_INIMIGOS_BASE = 3  # Base para a descida lenta
COOLDOWN_INIMIGO_BASE = 120
SPAWN_CHANCE_BASE = 30
XP_POR_ESTRELA = 25
PLAYER_DANO = 10
VELOCIDADE_DIAGONAL_METEORO = 2

# VARIÁVEIS DO SISTEMA DE BOSS
boss_ativo = False
tempo_proximo_boss = 30
boss_hp_base = 50
boss_cooldown_base = 30
boss_padrao_atual = 0
VELOCIDADE_PROJETIL_BASE = 8

# VARIÁVEIS DA ARMA DO JOGADOR
player_projeteis = []
player_cooldown_max = 15
player_cooldown = 0
player_velocidade_tiro = 10

# Ajusta o Rect do jogador para corresponder ao novo tamanho de IMAGEM_PLAYER
jogador = IMAGEM_PLAYER.get_rect(x=180, y=500)
velocidade = 5
obstaculos = []
projeteis_inimigos = []

# --- LISTA DE ASSETS ATUALIZADA ---
objetos_assets = [
    {'img': IMAGEM_METEORO, 'type': METEOR_TYPE, 'xp': 0, 'cor': VERMELHO, 'hp': 1, 'dano_boss': False},
    {'img': IMAGEM_ESTRELA, 'type': STAR_TYPE, 'xp': XP_POR_ESTRELA, 'cor': AMARELO, 'hp': 0, 'dano_boss': False},
    {'img': IMAGEM_NAVE_INIMIGA, 'type': ENEMY_TYPE, 'xp': 0, 'cor': VERDE, 'hp': 1, 'dano_boss': True},
    {'img': IMAGEM_BOSS, 'type': BOSS_TYPE, 'xp': 100, 'cor': ROXO, 'hp': boss_hp_base, 'dano_boss': True},
]

# --- DEFINIÇÕES DE PROJÉTEIS ---
largura_proj = IMAGEM_PROJETIL.get_width()
altura_proj = IMAGEM_PROJETIL.get_height()

nome_jogador = ""


# --- FUNÇÕES SUPABASE (MANTIDAS) ---
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


# --- FUNÇÕES DE PADRÃO DE ATAQUE (MANTIDAS) ---
def atirar_padrao_boss(boss_obj, padrao):
    novos_projeteis = []
    cooldown_ajustado = 60

    if boss_obj is None:
        boss_x = largura // 2 - 60
        boss_y = 50
    else:
        boss_x = boss_obj["rect"].x
        boss_y = boss_obj["rect"].y

    cooldown_base_reduzido = max(10, boss_cooldown_base - (nivel * 3))

    if padrao == 1:
        if boss_obj is not None:
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 10, boss_y))
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 70, boss_y))
        cooldown_ajustado = 30
    elif padrao == 2:
        if boss_obj is not None:
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 5, boss_y))
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 45, boss_y))
            novos_projeteis.append(criar_projetil_inimigo(boss_x + 85, boss_y))
        cooldown_ajustado = 60
    elif padrao == 3:
        if boss_obj is not None:
            # Projétil do Boss do tipo especial - Usa imagem redimensionada
            proj_boss_img = pygame.transform.scale(IMAGEM_PROJETIL, (largura_proj * 2, altura_proj * 2))
            rect_tiro = proj_boss_img.get_rect(x=boss_x + 40, y=boss_y + 40)
            novos_projeteis.append({"rect": rect_tiro, "velocidade": max(4, VELOCIDADE_PROJETIL_BASE + (nivel // 3)),
                                    "img": proj_boss_img})
        cooldown_ajustado = 90
    elif padrao == 4:
        cooldown_ajustado = 60
    else:
        cooldown_ajustado = 60

    cooldown_final = max(10, cooldown_ajustado - (nivel * 2))
    return novos_projeteis, cooldown_final


# --- FUNÇÕES DE OBJETO E PROJÉTIL (MANTIDAS) ---
def criar_objeto():
    x = random.randint(0, largura - 40)
    chance = random.random()

    if chance < 0.6:
        asset_info = objetos_assets[1]  # Estrela
    elif chance < 0.8:
        asset_info = objetos_assets[0]  # Meteoro
    else:
        asset_info = objetos_assets[2]  # Inimigo

    rect = pygame.Rect(x, -40, asset_info['img'].get_width(), asset_info['img'].get_height())

    hp_ajustado = asset_info['hp'] + (nivel // 5) if asset_info['type'] != STAR_TYPE else 0
    objeto = {"rect": rect, "asset_info": asset_info, "hp": hp_ajustado}

    if asset_info['type'] == ENEMY_TYPE:
        cooldown_ajustado = max(30, COOLDOWN_INIMIGO_BASE - (nivel * 5))
        objeto['cooldown'] = random.randint(cooldown_ajustado - 30, cooldown_ajustado)

    if asset_info['type'] == METEOR_TYPE:
        # Define a direção horizontal (1 para direita, -1 para esquerda)
        objeto['direcao_horizontal'] = random.choice([-1, 1])
        objeto['velocidade_horizontal'] = VELOCIDADE_DIAGONAL_METEORO + (nivel // 5)

    return objeto


def criar_objeto_boss():
    asset_info = objetos_assets[3]  # Boss

    rect = IMAGEM_BOSS.get_rect(x=largura // 2 - 60, y=50)

    boss_hp_atual = asset_info['hp'] + (nivel * 100)
    padrao_inicial = random.randint(1, 3)
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
    # Usa as dimensões da imagem
    rect = IMAGEM_PROJETIL.get_rect(centerx=x + (IMAGEM_NAVE_INIMIGA.get_width() // 2),
                                    top=y + IMAGEM_NAVE_INIMIGA.get_height())
    velocidade_tiro = VELOCIDADE_PROJETIL_BASE + (nivel // 5)
    return {"rect": rect, "velocidade": velocidade_tiro, "img": IMAGEM_PROJETIL}


def criar_player_projetil():
    # Usa as dimensões da imagem
    rect = IMAGEM_PROJETIL.get_rect(centerx=jogador.centerx, bottom=jogador.top)
    # Inverte a imagem do projétil para simular o tiro para cima
    img_invertida = pygame.transform.flip(IMAGEM_PROJETIL, False, True)
    return {"rect": rect, "img": img_invertida}


# --- FUNÇÕES DE LEVEL UP E POWER-UP (MANTIDAS) ---
POWER_UPS = [
    {"nome": "Hyper-Speed", "descricao": "Aumenta a velocidade de movimento da sua nave (V + 1)."},
    {"nome": "Dano Aprimorado", "descricao": "Aumenta o dano da sua arma (+5 Dano)."},
    {"nome": "Sorte do Saqueador", "descricao": "Aumenta o XP ganho por estrela coletada."},
    {"nome": "Fogo Rápido", "descricao": "Diminui o Cooldown do seu tiro (Atira mais rápido)."},
]


def aplicar_power_up(nome_power_up):
    global velocidade, COOLDOWN_INIMIGO_BASE, XP_POR_ESTRELA, objetos_assets, player_cooldown_max, PLAYER_DANO

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
        xp_excedente = xp_atual - xp_proximo_nivel

        nivel += 1
        xp_atual = xp_excedente

        # --- FÓRMULA DE DIFICULDADE AUMENTADA ---
        xp_base = 100
        fator_crescimento = 60
        expoente = 1.5

        xp_proximo_nivel = xp_base + int((nivel ** expoente) * fator_crescimento)

        if not tela_escolha_power_up():
            return False

    return True


# --- FUNÇÕES DE INTERFACE E CONTROLE (MANTIDAS) ---
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

    barra_largura = 150
    barra_altura = 10
    xp_percent = (xp_atual / xp_proximo_nivel) if xp_proximo_nivel > 0 else 0
    xp_preenchido = int(barra_largura * xp_percent)

    pygame.draw.rect(tela, (50, 50, 50), (largura - barra_largura - 10, 50, barra_largura, barra_altura))
    pygame.draw.rect(tela, AZUL_CLARO, (largura - barra_largura - 10, 50, xp_preenchido, barra_altura))
    pygame.draw.rect(tela, BRANCO, (largura - barra_largura - 10, 50, barra_largura, barra_altura), 1)


def desenhar_barra_boss(boss_obj):
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
    global player_cooldown_max, PLAYER_DANO, XP_POR_ESTRELA, VELOCIDADE_INIMIGOS_BASE, COOLDOWN_INIMIGO_BASE, velocidade

    # Reinicia a posição do jogador usando o novo Rect
    jogador = IMAGEM_PLAYER.get_rect(x=180, y=500)
    obstaculos = []
    projeteis_inimigos = []
    player_projeteis = []
    tempo_inicio = pygame.time.get_ticks()
    tempo_atual = 0
    nome_jogador = ""

    nivel = 1
    xp_atual = 0
    xp_proximo_nivel = 100
    boss_ativo = False
    tempo_proximo_boss = 30

    velocidade = 5
    PLAYER_DANO = 10
    XP_POR_ESTRELA = 25
    player_cooldown_max = 15
    objetos_assets[1]['xp'] = XP_POR_ESTRELA


def tela_digitar_nome():
    """Função CORRIGIDA para tratar eventos de teclado corretamente."""
    global nome_jogador
    nome_jogador = ""
    digitando = True
    campo_ativo = True
    campo_rect = pygame.Rect(largura // 2 - 150, altura // 2, 300, 40)  # Define o retângulo do campo

    while digitando:
        mouse_pos = pygame.mouse.get_pos()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            elif evento.type == pygame.KEYDOWN:  # Apenas K_DOWN
                if campo_ativo:
                    if evento.key == pygame.K_RETURN and nome_jogador.strip():
                        digitando = False
                    elif evento.key == pygame.K_BACKSPACE:
                        nome_jogador = nome_jogador[:-1]
                    elif evento.key == pygame.K_ESCAPE:
                        return False
                    # Use a função `unicode` para capturar a letra digitada
                    elif evento.unicode.isalnum() or evento.unicode in " _-":  # Permitir letras, números e alguns símbolos
                        if len(nome_jogador) < 15:
                            nome_jogador += evento.unicode
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                campo_ativo = campo_rect.collidepoint(mouse_pos)

        tela.fill(AZUL_ESCURO)
        texto_titulo = fonte.render("DIGITE SEU NOME", True, BRANCO)
        texto_instrucao = fonte_pequena.render("Pressione ENTER para continuar", True, (200, 200, 200))
        tela.blit(texto_titulo, (largura // 2 - texto_titulo.get_width() // 2, altura // 2 - 60))
        tela.blit(texto_instrucao, (largura // 2 - texto_instrucao.get_width() // 2, altura // 2 + 50))

        # Desenha o campo e checa se está ativo
        desenhar_campo_texto(nome_jogador, campo_rect.x, campo_rect.y, campo_rect.width, campo_rect.height, campo_ativo)
        pygame.display.flip()
        clock.tick(60)
    return True


def tela_game_over():
    global rodando, nome_jogador

    # O jogo pede o nome SOMENTE quando o jogador morre, se o nome não estiver definido
    if not nome_jogador and not tela_digitar_nome():
        return False

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


def tela_de_inicio():
    botao_iniciar_rect = (largura // 2 - 100, altura // 2, 200, 50)
    botao_sair_rect = (largura // 2 - 100, altura // 2 + 70, 200, 50)
    while True:
        mouse_pos = pygame.mouse.get_pos()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: return False
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    if (botao_iniciar_rect[0] <= mouse_pos[0] <= botao_iniciar_rect[0] + botao_iniciar_rect[2] and
                            botao_iniciar_rect[1] <= mouse_pos[1] <= botao_iniciar_rect[1] + botao_iniciar_rect[3]):
                        return True
                    if (botao_sair_rect[0] <= mouse_pos[0] <= botao_sair_rect[0] + botao_sair_rect[2] and
                            botao_sair_rect[1] <= mouse_pos[1] <= botao_sair_rect[1] + botao_sair_rect[3]):
                        return False

        tela.fill(AZUL_ESCURO)
        tela.blit(IMAGEM_FUNDO, (0, 0))  # Desenha o fundo na tela de início

        texto_titulo = fonte.render("SPACE COLLECTOR", True, AMARELO)
        tela.blit(texto_titulo, (largura // 2 - texto_titulo.get_width() // 2, 150))
        texto_instrucao1 = fonte_pequena.render("Use as SETAS para mover", True, BRANCO)
        texto_instrucao2 = fonte_pequena.render("Use a tecla ESPAÇO para atirar", True, BRANCO)
        tela.blit(texto_instrucao1, (largura // 2 - texto_instrucao1.get_width() // 2, 220))
        tela.blit(texto_instrucao2, (largura // 2 - texto_instrucao2.get_width() // 2, 250))

        desenhar_botao("INICIAR JOGO", botao_iniciar_rect[0], botao_iniciar_rect[1], botao_iniciar_rect[2],
                       botao_iniciar_rect[3], (0, 100, 0), (0, 150, 0), mouse_pos)
        desenhar_botao("SAIR", botao_sair_rect[0], botao_sair_rect[1], botao_sair_rect[2], botao_sair_rect[3],
                       (100, 0, 0), (150, 0, 0), mouse_pos)

        pygame.display.flip()
        clock.tick(60)


# --- LOOP PRINCIPAL DO JOGO ---
rodando = tela_de_inicio()

if rodando:
    if not tela_digitar_nome():
        rodando = False

while rodando:
    # --- Desenha o fundo antes de tudo ---
    tela.blit(IMAGEM_FUNDO, (0, 0))

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
        tempo_proximo_boss += 60
    chance_spawn = max(5, SPAWN_CHANCE_BASE - (nivel // 2))
    if not boss_ativo and random.randint(1, chance_spawn) == 1:
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
            # --- DESENHA PROJÉTIL USANDO IMAGEM ---
            tela.blit(p_proj["img"], p_proj["rect"])
    player_projeteis = novos_projeteis_player
    if not rodando: break

    # 4. LÓGICA DE OBSTÁCULOS E PROJÉTEIS INIMIGOS (Movimentação ajustada)
    novos_obstaculos = []
    # Velocidade base para todos os objetos (inimigos, estrelas, meteoros)
    velocidade_queda_atual = VELOCIDADE_INIMIGOS_BASE + (nivel // 4)
    for obstaculo in obstaculos:
        obj_type = obstaculo["asset_info"]["type"]

        # MOVIMENTAÇÃO VERTICAL PADRÃO
        if obj_type != BOSS_TYPE:
            obstaculo["rect"].y += velocidade_queda_atual

        # MOVIMENTAÇÃO HORIZONTAL DOS METEOROS
        if obj_type == METEOR_TYPE:
            vel_h = obstaculo['velocidade_horizontal']
            direcao = obstaculo['direcao_horizontal']
            obstaculo["rect"].x += vel_h * direcao

        if obj_type == ENEMY_TYPE or obj_type == BOSS_TYPE:
            obstaculo['cooldown'] -= 1
            if obstaculo['cooldown'] <= 0:
                if obj_type == BOSS_TYPE:
                    novos_tiros = []
                    if obstaculo['padrao'] != 4:
                        novos_tiros, _ = atirar_padrao_boss(obstaculo, obstaculo['padrao'])
                        projeteis_inimigos.extend(novos_tiros)
                    if obstaculo['padrao'] == 4:
                        obstaculo['padrao'] = random.randint(1, 3)
                    else:
                        if random.random() < 0.5:
                            obstaculo['padrao'] = 4
                        else:
                            obstaculo['padrao'] = random.randint(1, 3)
                    _, cooldown_proximo = atirar_padrao_boss(obstaculo, obstaculo['padrao'])
                    obstaculo['cooldown'] = random.randint(cooldown_proximo - 10, cooldown_proximo)
                else:
                    projeteis_inimigos.append(criar_projetil_inimigo(obstaculo["rect"].x, obstaculo["rect"].y))
                    cooldown_atual = max(30, COOLDOWN_INIMIGO_BASE - (nivel * 5))
                    obstaculo['cooldown'] = random.randint(cooldown_atual - 10, cooldown_atual)

        # COLISÃO COM JOGADOR
        if obstaculo["rect"].colliderect(jogador):
            if obj_type == STAR_TYPE:
                if not checar_level_up(obstaculo["asset_info"]["xp"]): rodando = False; break
                continue
            elif obj_type != STAR_TYPE:
                if not tela_game_over(): rodando = False; break

        # Condição de remoção de objetos (saiu pela borda inferior OU pelas laterais)
        if (obstaculo["rect"].bottom > 0 and obstaculo["rect"].top < altura and
                obstaculo["rect"].left < largura and obstaculo["rect"].right > 0):

            novos_obstaculos.append(obstaculo)
            # --- DESENHO DO OBJETO USANDO IMAGEM ---
            tela.blit(obstaculo["asset_info"]["img"], obstaculo["rect"])

            if obj_type == BOSS_TYPE:
                desenhar_barra_boss(obstaculo)

    obstaculos = novos_obstaculos
    if not rodando: break

    # 5. MOVIMENTO E COLISÃO DOS PROJÉTEIS INIMIGOS
    novos_projeteis_inimigos = []
    for p_inimigo in projeteis_inimigos:
        velocidade_tiro = p_inimigo.get("velocidade", VELOCIDADE_PROJETIL_BASE)
        p_inimigo["rect"].y += velocidade_tiro
        if p_inimigo["rect"].colliderect(jogador):
            if not tela_game_over(): rodando = False; break
        if p_inimigo["rect"].y < altura:
            novos_projeteis_inimigos.append(p_inimigo)
            # --- DESENHA PROJÉTIL INIMIGO USANDO IMAGEM ---
            tela.blit(p_inimigo["img"], p_inimigo["rect"])
    projeteis_inimigos = novos_projeteis_inimigos
    if not rodando: break

    # 6. ATUALIZAÇÃO DA TELA
    desenhar_interface()

    # Desenhar jogador
    tela.blit(IMAGEM_PLAYER, jogador)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

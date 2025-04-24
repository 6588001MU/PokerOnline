import pygame
import os
import random
import cairosvg
from io import BytesIO
from collections import Counter

# Pygame setup
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Two Player Poker - Five Card Draw with Betting")
font = pygame.font.SysFont(None, 36)
hold_font = pygame.font.SysFont(None, 28, bold=True)
label_font = pygame.font.SysFont(None, 30, bold=True)

# Card dimensions
CARD_WIDTH, CARD_HEIGHT = 100, 140

# Folder containing SVG cards
base_dir = os.path.dirname(__file__)
cards_folder = os.path.join(base_dir, "cards/svg-cards")

# Function to convert SVG to Pygame surface
def svg_to_pygame_image(svg_path, width, height):
    with open(svg_path, 'rb') as f:
        svg_data = f.read()
    png_data = cairosvg.svg2png(bytestring=svg_data)
    image = pygame.image.load(BytesIO(png_data))
    return pygame.transform.scale(image, (width, height))

# Generate simple card back image
def create_card_back(width, height):
    surface = pygame.Surface((width, height))
    surface.fill((20, 20, 120))
    pygame.draw.rect(surface, (255, 255, 255), (10, 10, width - 20, height - 20), 4)
    text = font.render("POKER", True, (255, 255, 255))
    text_rect = text.get_rect(center=(width // 2, height // 2))
    surface.blit(text, text_rect)
    return surface

card_back_image = create_card_back(CARD_WIDTH, CARD_HEIGHT)

# Create deck
suits = ['hearts', 'diamonds', 'clubs', 'spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
rank_values = {r: i for i, r in enumerate(ranks, start=2)}
original_deck = []

for suit in suits:
    for rank in ranks:
        filename = f"{rank}_of_{suit}.svg"
        path = os.path.join(cards_folder, filename)
        if os.path.exists(path):
            image = svg_to_pygame_image(path, CARD_WIDTH, CARD_HEIGHT)
            original_deck.append((rank, suit, image))

# Functions for gameplay
def draw_hand(deck, num_cards=5):
    return [deck.pop() for _ in range(num_cards)]

def evaluate_hand(hand):
    ranks_in_hand = [card[0] for card in hand]
    counts = Counter(ranks_in_hand).values()
    if 4 in counts:
        return (7, "Four of a Kind")
    elif 3 in counts and 2 in counts:
        return (6, "Full House")
    elif 3 in counts:
        return (3, "Three of a Kind")
    elif list(counts).count(2) == 2:
        return (2, "Two Pair")
    elif 2 in counts:
        return (1, "One Pair")
    else:
        high = max(rank_values[card[0]] for card in hand)
        return (0, f"High Card {high}")

def reset_bets():
    global current_bets
    current_bets = [0, 0]

def apply_bets():
    global pot, player_chips
    for i in range(2):
        pot += current_bets[i]
        player_chips[i] -= current_bets[i]
    reset_bets()

# Game variables
player_hands = [[], []]
holds = [[False] * 5, [False] * 5]
current_player = 0
winner_message = ""
game_phase = "choose_mode"
deck = original_deck[:]
random.shuffle(deck)

# Betting variables
player_chips = [980, 980]
current_bets = [20, 20]
pot = 40
betting_player = 0
minimum_raise = 50

# Game loop
running = True
while running:
    screen.fill((60, 139, 34))

    if game_phase == "choose_mode":
        instruction = "Press 1 to start Five-Card Draw."
    elif game_phase == "deal":
        instruction = "Press SPACE to deal cards."
    elif game_phase.startswith("bet") or game_phase.startswith("second_bet"):
        instruction = f"Player {betting_player + 1}: Press C to Call, R to Raise"
    elif game_phase == "hold":
        instruction = f"Player {current_player + 1}: Click cards to hold/discard. Press RETURN when done."
    elif game_phase == "redraw":
        instruction = f"Player {current_player + 1}: Press SPACE to redraw."
    else:
        instruction = winner_message + " Press SPACE to play again."

    text = font.render(instruction, True, (255, 255, 255))
    screen.blit(text, text.get_rect(topright=(WIDTH - 50, 20)))

    pot_text = font.render(f"Pot: ${pot}", True, (255, 255, 255))
    screen.blit(pot_text, (WIDTH // 2 - 60, 60))

    chip_text1 = font.render(f"Chips: ${player_chips[0]}", True, (255, 255, 255))
    chip_text2 = font.render(f"Chips: ${player_chips[1]}", True, (255, 255, 255))
    screen.blit(chip_text1, (30, 30))
    screen.blit(chip_text2, (30, 330))

    # Display player's hands based on game phase
    for p in range(2):
        for i, card in enumerate(player_hands[p]):
            _, _, image = card
            x = 100 + i * (CARD_WIDTH + 10)
            y = 100 if p == 0 else 400

            # Display cards based on the game phase
            if game_phase == "show":
                # Show all cards in the final showdown
                screen.blit(image, (x, y))
            elif p == betting_player and (game_phase.startswith("bet") or game_phase.startswith("second_bet")):
                # Only the current betting player sees their cards
                screen.blit(image, (x, y))
            elif p == current_player and (game_phase == "hold" or game_phase == "redraw"):
                # Only the current player sees their cards during hold/redraw phase
                screen.blit(image, (x, y))
            else:
                # Hide cards for the non-active player
                screen.blit(card_back_image, (x, y))

            if game_phase == "hold" and p == current_player:
                color = (0, 255, 0) if holds[p][i] else (255, 0, 0)
                pygame.draw.rect(screen, color, (x, y, CARD_WIDTH, CARD_HEIGHT), 3)
                label = hold_font.render("HOLD" if holds[p][i] else "DISCARD", True, (255, 255, 255))
                screen.blit(label, (x + 10, y + CARD_HEIGHT + 5))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if game_phase == "choose_mode" and event.key == pygame.K_1:
                deck = original_deck[:]
                random.shuffle(deck)
                player_hands = [draw_hand(deck), draw_hand(deck)]
                holds = [[False] * 5, [False] * 5]
                pot = 0
                reset_bets()
                game_phase = "bet_player_1"
                betting_player = 0

            elif game_phase == "bet_player_1":
                if event.key == pygame.K_c:
                    current_bets[0] = current_bets[1]
                    game_phase = "bet_player_2"
                    betting_player = 1
                elif event.key == pygame.K_r:
                    current_bets[0] += minimum_raise
                    game_phase = "bet_player_2"
                    betting_player = 1

            elif game_phase == "bet_player_2":
                if event.key == pygame.K_c:
                    current_bets[1] = current_bets[0]
                    apply_bets()
                    game_phase = "hold"
                    current_player = 0
                elif event.key == pygame.K_r:
                    current_bets[1] += minimum_raise
                    apply_bets()
                    game_phase = "hold"
                    current_player = 0

            elif game_phase == "hold":
                if event.key == pygame.K_RETURN:
                    game_phase = "redraw"

            elif game_phase == "redraw" and event.key == pygame.K_SPACE:
                new_hand = []
                for i, hold in enumerate(holds[current_player]):
                    new_hand.append(player_hands[current_player][i] if hold else deck.pop())
                player_hands[current_player] = new_hand
                if current_player == 0:
                    current_player = 1
                    game_phase = "hold"
                else:
                    game_phase = "second_bet_player_1"
                    betting_player = 0

            # Reuse logic for second call/raise phase (same as first)
            elif game_phase == "second_bet_player_1":
                if event.key == pygame.K_c:
                    current_bets[0] = current_bets[1]
                    game_phase = "second_bet_player_2"
                    betting_player = 1
                elif event.key == pygame.K_r:
                    current_bets[0] += minimum_raise
                    game_phase = "second_bet_player_2"
                    betting_player = 1

            elif game_phase == "second_bet_player_2":
                if event.key == pygame.K_c:
                    current_bets[1] = current_bets[0]
                    apply_bets()
                    score1, desc1 = evaluate_hand(player_hands[0])
                    score2, desc2 = evaluate_hand(player_hands[1])
                    if score1 > score2:
                        winner_message = f"Player 1 wins with {desc1}"
                        player_chips[0] += pot
                    elif score2 > score1:
                        winner_message = f"Player 2 wins with {desc2}"
                        player_chips[1] += pot
                    else:
                        winner_message = f"It's a tie! Both have {desc1}"
                        player_chips[0] += pot // 2
                        player_chips[1] += pot // 2
                    pot = 0
                    game_phase = "show"
                elif event.key == pygame.K_r:
                    current_bets[1] += minimum_raise
                    apply_bets()
                    score1, desc1 = evaluate_hand(player_hands[0])
                    score2, desc2 = evaluate_hand(player_hands[1])
                    if score1 > score2:
                        winner_message = f"Player 1 wins with {desc1}"
                        player_chips[0] += pot
                    elif score2 > score1:
                        winner_message = f"Player 2 wins with {desc2}"
                        player_chips[1] += pot
                    else:
                        winner_message = f"It's a tie! Both have {desc1}"
                        player_chips[0] += pot // 2
                        player_chips[1] += pot // 2
                    pot = 0
                    game_phase = "show"

            elif game_phase == "show" and event.key == pygame.K_SPACE:
                game_phase = "choose_mode"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_phase == "hold":
            x, y = event.pos
            for i in range(5):
                card_rect = pygame.Rect(100 + i * (CARD_WIDTH + 10), 100 if current_player == 0 else 400, CARD_WIDTH, CARD_HEIGHT)
                if card_rect.collidepoint(x, y):
                    holds[current_player][i] = not holds[current_player][i]

    pygame.display.flip()

pygame.quit()







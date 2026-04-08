import pygame, sys, subprocess, os
from rdkit import Chem
from rdkit.Chem import Draw

# usage: python3 intro.py

pygame.init()

# ---------------- WINDOW ---------------- #
screen = pygame.display.set_mode((1000, 850), pygame.RESIZABLE)
pygame.display.set_caption("Stage 0 – Lipid Explorer")

# ---------------- FONT ---------------- #
FONT_PATH = os.path.join("fonts", "GravitasOne.ttf")
if not os.path.exists(FONT_PATH):
    print("⚠️ Warning: GravitasOne.ttf not found in fonts/. Falling back to default font.")
    font = pygame.font.SysFont(None, 18)
else:
    font = pygame.font.Font(FONT_PATH, 18)

clock = pygame.time.Clock()

# ---------------- COLORS ---------------- #
WHITE = (255, 255, 255)
GREY = (200, 200, 200)
BLUE = (60, 140, 255)
BLACK = (0, 0, 0)
GREEN = (0, 150, 0)
RED = (200, 0, 0)
YELLOW = (240, 200, 0)

# ---------------- STORY / PRELUDE ---------------- #
story_pages = [
    "Welcome to the Lipid Learning Adventure!",
    "You will explore different lipid classes and their functions.",
    "Click 'Next' to start your journey."
]
story_index = 0

# ---------------- PRE-QUIZ FUNCTIONAL GROUPS ---------------- #
prequiz_questions = [
    {"question": "Which functional group is -OH?",
     "options": ["Hydroxyl", "Phosphate", "Carboxyl", "Amine"],
     "answer": "Hydroxyl",
     "smiles": "[OH-]"},

    {"question": "Which functional group is -PO4?",
     "options": ["Phosphate", "Hydroxyl", "Ketone", "Methyl"],
     "answer": "Phosphate",
     "smiles": "P(=O)(O)O"},

    {"question": "Which of the below best represents an aliphatic hydrocarbon chain?",
     "options": ["CH3-(CH2)n-CH3", "Benzene", "COOH", "OH"],
     "answer": "CH3-(CH2)n-CH3",
     "smiles": "CCCC"},


   {"question": "Which functional group is -COOH?",
     "options": ["Carboxylic acid", "Benzene", "COOH", "OH"],
     "answer": "Carboxylic acid",
     "smiles": "C(=O)O"},

]
prequiz_index = 0
prequiz_score = 0
show_prequiz_feedback = False
prequiz_feedback_text = ""
prequiz_feedback_color = GREEN
prequiz_feedback_timer = 0

# ---------------- LIPID CLASS INFO ---------------- #
lipid_info = [
    {"name": "Fatty Acids", "text": "Simple hydrocarbon tails; building blocks.",
     "variants": ["CCCCCCCCCCCCCCCC(=O)O"], "fact": "Some fatty acids are essential because the body cannot synthesize them."},
    {"name": "Glycerolipids", "text": "Glycerol + tails; store energy.",
     "variants": ["CCCCCCCCCCCCCCCC(=O)OCC(COC(=O)CCCCCCCCCCCCCCC)OC(=O)CCCCCCCCCCCCCCC"],
     "fact": "Triglycerides are the main form of energy storage in animals."},
    {"name": "Glycerophospholipids", "text": "Membrane builders with phosphate heads.",
     "variants": ["CCCCCCCCCCCCCCCC(=O)OCC(COP(=O)(OCC[N+](C)(C)C)O)OC(=O)CCCCCCCCCCCCCCC"],
     "fact": "They are major components of cell membranes."},
    {"name": "Sphingolipids", "text": "Signaling lipids; found in nerve cells.",
     "variants": ["CCCCCCCCCCCCCCCC(CCO)NC(=O)CCCCCCCCCCCCCCCOP(=O)(OCC[N+](C)(C)C)O"],
     "fact": "Sphingolipids are abundant in the myelin sheath of neurons."},
    {"name": "Sterols", "text": "Four fused rings; regulate fluidity.",
     "variants": ["CC(C)CCCC(C)C1CCC2C3CCC4=CC(O)CCC4(C)C3CCC12C"], "fact": "Cholesterol is the most well-known sterol."},
    {"name": "Prenols", "text": "Built from isoprene units; vitamins & pigments.",
     "variants": ["CC(=CCC/C(C)=C/CO)C"], "fact": "Prenols include molecules like Vitamin K and Coenzyme Q."},
    {"name": "Saccharolipids", "text": "Sugar backbone + fatty acids.",
     "variants": ["CCCCC(=O)OC1C(O)C(O)C(O)C(O)C1O"], "fact": "Saccharolipids are rare but important in bacterial membranes."},
    {"name": "Polyketides", "text": "Alternating C=O chains; antibiotics & pigments.",
     "variants": ["CC(C)CC1OC2CC3OC(=O)C(C)CC3(O)C(C)C2(O)C1(C)O"], "fact": "Many antibiotics are polyketides."},
]

# ---------------- SMILES → PYGAME SURFACE ---------------- #
def mol_to_surface(smiles, size=(200,200)):
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        pil_img = Draw.MolToImage(mol, size=size)
        mode = pil_img.mode
        size = pil_img.size
        data = pil_img.tobytes()
        return pygame.image.fromstring(data, size, mode)
    else:
        surf = pygame.Surface(size)
        surf.fill((220,220,220))
        return surf

# Precompute lipid images
for lipid in lipid_info:
    lipid["images"] = [mol_to_surface(smiles, size=(200,200)) for smiles in lipid["variants"]]
    lipid["current_variant"] = 0

# ---------------- CARDS ---------------- #
cards = []
cols = 4
for i, lipid in enumerate(lipid_info):
    row, col = divmod(i, cols)
    x = 80 + col * 230
    y = 100 + row * 180
    rect = pygame.Rect(x, y, 200, 100)
    cards.append({"rect": rect, "index": i})

selected_index = None
explored = [False] * len(lipid_info)
show_glossary = False
stage = "story"  # start with story

# ---------------- QUIZ DATA ---------------- #
quiz_lipids = [
    {"smiles": "CCCCCC=CCC=CCC=CCC=CCCCC(=O)O", "name": "Arachidonic acid", "class": "Fatty Acids",
     "function": "Provides energy, contributes to membranes, participates in eicosanoid synthesis."},
    {"smiles": "CC1=C(C(CCC1)(C)C)C=CC(=CC=CC(=CC=O)C)C", "name": "Retinal", "class": "Prenols",
     "function": "Plays roles in Vitamin A metabolism and vision."},
    {"smiles": "CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C", "name": "Testosterone", "class": "Sterols",
     "function": "Key role in development of reproductive tissues."},
]
quiz_options = [l["name"] for l in lipid_info]
quiz_index = 0
quiz_score = 0
show_feedback = False
feedback_text = ""
feedback_color = GREEN
feedback_timer = 0

# ---------------- GLOSSARY DRAW ---------------- #
def draw_glossary():
    glossary = pygame.Rect(150, 80, 700, 540)
    pygame.draw.rect(screen, WHITE, glossary, border_radius=10)
    pygame.draw.rect(screen, BLACK, glossary, 2, border_radius=10)
    title = font.render("Lipid Class Glossary", True, BLACK)
    screen.blit(title, (glossary.x + 20, glossary.y + 10))
    for i, lipid in enumerate(lipid_info):
        text = font.render(f"{i+1}. {lipid['name']}: {lipid['text']}", True, BLACK)
        screen.blit(text, (glossary.x + 20, glossary.y + 50 + i*30))
    close_btn = font.render("Close [X]", True, RED)
    screen.blit(close_btn, (glossary.x + glossary.width - 120, glossary.y + 10))

# ---------------- DRAW CARD ---------------- #
def draw_card(card, index):
    color = BLUE if index == selected_index else GREY
    pygame.draw.rect(screen, color, card["rect"], border_radius=10)
    label = font.render(lipid_info[index]["name"], True, WHITE)
    screen.blit(label, label.get_rect(center=card["rect"].center))

def draw_popup(lipid, win_height):
    popup_height = 300
    popup = pygame.Rect(100, 380, 800, popup_height)
    pygame.draw.rect(screen, WHITE, popup, border_radius=10)
    pygame.draw.rect(screen, BLACK, popup, 2, border_radius=10)

    name = font.render(lipid["name"], True, BLACK)
    text = font.render(lipid["text"], True, BLACK)
    fact = font.render("Fun Fact: " + lipid["fact"], True, YELLOW)
    screen.blit(name, (popup.x + 20, popup.y + 10))
    screen.blit(text, (popup.x + 20, popup.y + 40))
    screen.blit(fact, (popup.x + 20, popup.y + 70))

    available_height = popup.height - 120
    available_width = popup.width - 40
    img = lipid["images"][lipid["current_variant"]]
    img_w, img_h = img.get_size()
    scale = min(available_width/img_w, available_height/img_h)
    new_size = (int(img_w*scale), int(img_h*scale))
    img_scaled = pygame.transform.smoothscale(img, new_size)
    img_x = popup.x + (popup.width - new_size[0])//2
    img_y = popup.y + 100 + (available_height - new_size[1])//2
    screen.blit(img_scaled, (img_x, img_y))

    next_btn = None
    if all(explored):
        next_btn = pygame.Rect(popup.x + popup.width - 140, popup.y + popup.height - 50, 120, 35)
        pygame.draw.rect(screen, BLUE, next_btn, border_radius=5)
        text_surf = font.render("Next →", True, WHITE)
        screen.blit(text_surf, text_surf.get_rect(center=next_btn.center))
    return next_btn

def draw_progress(win_width, win_height):
    total = len(lipid_info)
    clicked = sum(explored)
    bar_width = win_width - 100
    bar_height = 20
    bar_x = 50
    bar_y = win_height - 50
    pygame.draw.rect(screen, GREY, (bar_x, bar_y, bar_width, bar_height), border_radius=5)
    pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_width*clicked/total, bar_height), border_radius=5)
    prog_text = font.render(f"Progress: {clicked}/{total} lipids explored", True, BLACK)
    screen.blit(prog_text, (bar_x, bar_y - 30))

glossary_btn = pygame.Rect(850, 40, 120, 35)

# ---------------- MAIN LOOP ---------------- #
while True:
    dt = clock.tick(60)/1000
    win_width, win_height = screen.get_size()
    screen.fill(WHITE)

    next_btn = None
    if stage == "explore" and selected_index is not None:
        next_btn = draw_popup(lipid_info[selected_index], win_height)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if show_glossary:
                if 150+700-120 <= event.pos[0] <= 150+700 and 80 <= event.pos[1] <= 80+35:
                    show_glossary = False
            elif glossary_btn.collidepoint(event.pos):
                show_glossary = True

            elif stage == "story":
                story_index += 1
                if story_index >= len(story_pages):
                    stage = "prequiz"

            elif stage == "prequiz" and not show_prequiz_feedback:
                for i, option in enumerate(prequiz_questions[prequiz_index]["options"]):
                    btn_rect = pygame.Rect(200, 400 + i*80, 600, 50)
                    if btn_rect.collidepoint(event.pos):
                        correct = option == prequiz_questions[prequiz_index]["answer"]
                        if correct:
                            prequiz_score += 1
                            prequiz_feedback_text = "Correct!"
                            prequiz_feedback_color = GREEN
                        else:
                            prequiz_feedback_text = f"Wrong! Correct: {prequiz_questions[prequiz_index]['answer']}"
                            prequiz_feedback_color = RED
                        show_prequiz_feedback = True
                        prequiz_feedback_timer = 0

            elif stage == "explore":
                for card in cards:
                    if card["rect"].collidepoint(event.pos):
                        selected_index = card["index"]
                        explored[selected_index] = True
                        lipid_info[selected_index]["current_variant"] = 0
                if selected_index is not None:
                    popup_rect = pygame.Rect(100, 380, 800, 300)
                    if popup_rect.collidepoint(event.pos):
                        lipid_info[selected_index]["current_variant"] += 1
                        lipid_info[selected_index]["current_variant"] %= len(lipid_info[selected_index]["images"])
                if next_btn and next_btn.collidepoint(event.pos):
                    stage = "quiz"
                    quiz_index = 0
                    quiz_score = 0
                    show_feedback = False

            elif stage == "quiz" and not show_feedback:
                for i, option in enumerate(quiz_options):
                    btn_rect = pygame.Rect(150 + (i%4)*200, 550 + (i//4)*60, 180, 50)
                    if btn_rect.collidepoint(event.pos):
                        correct = option == quiz_lipids[quiz_index]["class"]
                        if correct:
                            quiz_score += 1
                            feedback_text = "Correct!"
                            feedback_color = GREEN
                        else:
                            feedback_text = "Wrong!"
                            feedback_color = RED
                        show_feedback = True
                        feedback_timer = 0

            elif stage == "finished":
                if retake_btn.collidepoint(event.pos):
                    stage = "quiz"
                    quiz_index = 0
                    quiz_score = 0
                    show_feedback = False
                elif next_stage_btn.collidepoint(event.pos):
                    pygame.quit()
                    subprocess.Popen(["python3", os.path.join(os.path.dirname(__file__), "stage1.py")])
                    sys.exit()

    # ---------------- DRAW STAGES ---------------- #
    if stage == "story":
        text_surf = font.render(story_pages[story_index], True, BLACK)
        screen.blit(text_surf, text_surf.get_rect(center=(win_width//2, win_height//2)))
        next_surf = font.render("Next →", True, BLUE)
        screen.blit(next_surf, next_surf.get_rect(center=(win_width//2, win_height//2 + 50)))

    elif stage == "prequiz":
        smiles = prequiz_questions[prequiz_index]["smiles"]
        img_surface = mol_to_surface(smiles, size=(200,200))
        img_rect = img_surface.get_rect(center=(win_width//2, 250))
        screen.blit(img_surface, img_rect)

        # Draw question
        question = prequiz_questions[prequiz_index]["question"]
        question_surf = font.render(question, True, BLACK)
        screen.blit(question_surf, question_surf.get_rect(center=(win_width//2, 100)))

        # Draw buttons
        button_y_start = 400
        button_gap = 80
        for i, option in enumerate(prequiz_questions[prequiz_index]["options"]):
            btn_rect = pygame.Rect(200, button_y_start + i*button_gap, 600, 50)
            pygame.draw.rect(screen, GREY, btn_rect, border_radius=5)
            label = font.render(option, True, WHITE)
            screen.blit(label, label.get_rect(center=btn_rect.center))

        # Draw feedback bubble ABOVE the buttons
        if show_prequiz_feedback:
            bubble_width = 500
            bubble_height = 70
            bubble_x = (win_width - bubble_width) // 2
            bubble_y = button_y_start - bubble_height - 20
            bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
            pygame.draw.rect(screen, WHITE, bubble_rect, border_radius=20)
            pygame.draw.rect(screen, prequiz_feedback_color, bubble_rect, 4, border_radius=20)
            feedback_surf = font.render(prequiz_feedback_text, True, prequiz_feedback_color)
            screen.blit(feedback_surf, feedback_surf.get_rect(center=bubble_rect.center))

            prequiz_feedback_timer += dt
            if prequiz_feedback_timer > 1.5:
                show_prequiz_feedback = False
                prequiz_feedback_timer = 0
                prequiz_index += 1
                if prequiz_index >= len(prequiz_questions):
                    stage = "explore"

    elif stage == "explore":
        title = font.render("Click each lipid to learn its structure and role!", True, BLACK)
        screen.blit(title, (180, 40))
        pygame.draw.rect(screen, BLUE, glossary_btn, border_radius=5)
        text_surf = font.render("Glossary", True, WHITE)
        screen.blit(text_surf, text_surf.get_rect(center=glossary_btn.center))
        for i, card in enumerate(cards):
            draw_card(card, i)
        if show_glossary:
            draw_glossary()
        draw_progress(win_width, win_height)

    elif stage == "quiz":
        title = font.render("Stage 0 Quiz – Identify the Lipid Class", True, BLACK)
        screen.blit(title, (250, 40))
        img_surface = mol_to_surface(quiz_lipids[quiz_index]["smiles"], size=(400,400))
        img_rect = img_surface.get_rect(center=(win_width//2, 300))
        screen.blit(img_surface, img_rect)

        for i, option in enumerate(quiz_options):
            btn_rect = pygame.Rect(150 + (i%4)*200, 550 + (i//4)*60, 180, 50)
            pygame.draw.rect(screen, GREY, btn_rect, border_radius=5)
            label = font.render(option, True, WHITE)
            screen.blit(label, label.get_rect(center=btn_rect.center))

        if show_feedback:
            feedback_surf = font.render(feedback_text, True, feedback_color)
            screen.blit(feedback_surf, feedback_surf.get_rect(center=(win_width//2, 750)))
            feedback_timer += dt
            if feedback_timer > 1.5:
                show_feedback = False
                feedback_timer = 0
                quiz_index += 1
                if quiz_index >= len(quiz_lipids):
                    stage = "finished"

    elif stage == "finished":
        msg = font.render(f"You finished Stage 0! Score: {quiz_score}/{len(quiz_lipids)}", True, BLACK)
        screen.blit(msg, msg.get_rect(center=(win_width//2, 300)))
        retake_btn = pygame.Rect(350, 400, 120, 40)
        next_stage_btn = pygame.Rect(550, 400, 120, 40)
        pygame.draw.rect(screen, BLUE, retake_btn, border_radius=5)
        pygame.draw.rect(screen, GREEN, next_stage_btn, border_radius=5)
        screen.blit(font.render("Retake", True, WHITE), font.render("Retake", True, WHITE).get_rect(center=retake_btn.center))
        screen.blit(font.render("Next →", True, WHITE), font.render("Next →", True, WHITE).get_rect(center=next_stage_btn.center))

    pygame.display.flip()

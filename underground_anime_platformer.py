# --- Portal Animation Helper ---
def load_portal_frames(filename, frame_w, frame_h):
    """
    Load a 3x2 spritesheet and return a list of 6 frames.
    """
    sheet = pg.image.load(filename).convert_alpha()
    frames = []
    for row in range(2):
        for col in range(3):
            rect = pg.Rect(col*frame_w, row*frame_h, frame_w, frame_h)
            frame = sheet.subsurface(rect).copy()
            frames.append(frame)
    return frames

# Example Portal class
class Portal:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frames = load_portal_frames("assets/portal.png", frame_w=64, frame_h=64)  # Change 64 to your frame size
        self.frame_idx = 0
        self.anim_timer = 0
        self.anim_speed = 100  # ms per frame

    def update(self, dt):
        self.anim_timer += dt
        if self.anim_timer > self.anim_speed:
            self.anim_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)

    def draw(self, surf):
        frame = self.frames[self.frame_idx]
        surf.blit(frame, (self.x, self.y))
def show_smeltery(screen, player):
    # Load smeltery and anvil images
    try:
        smeltery_bg = pg.image.load("assets/smeltery.png").convert()
        smeltery_bg = pg.transform.scale(smeltery_bg, (WIDTH, HEIGHT))
    except Exception as e:
        print("Failed to load smeltery.png:", e)
        smeltery_bg = None
    try:
        anvil_img = pg.image.load("assets/anvil.png").convert_alpha()
    except Exception as e:
        print("Failed to load anvil.png:", e)
        anvil_img = None
    smeltery_waiting = True
    stage = 0  # 0: intro, 1: anvil UI
    input_slots = [None, None]  # Holds (item, idx) tuples
    output_item = None
    output_ready = False
    margin, size = 20, 50
    startx, starty = 100, 100
    dragging = None  # (item, idx, from_inv:bool)
    smelt_msg = ""
    smelt_msg_timer = 0
    while smeltery_waiting:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if stage == 1:
                        # Return all items from input slots to inventory
                        for i in range(2):
                            if input_slots[i]:
                                item, idx = input_slots[i]
                                for j in range(len(player.inventory)):
                                    if player.inventory[j] is None:
                                        player.inventory[j] = item
                                        break
                                input_slots[i] = None
                        # Reset output
                        output_item = None
                        output_ready = False
                        stage = 0
                    else:
                        smeltery_waiting = False
                        show_start_screen()
                        return
                if stage == 0 and event.key == pg.K_RETURN:
                    stage = 1
            if stage == 1:
                mx, my = pg.mouse.get_pos()
                # Start dragging from inventory or input slots
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    # Inventory
                    for i in range(10):
                        r = pg.Rect(40 + i*(size+margin), HEIGHT-80, size, size)
                        if r.collidepoint(mx, my) and player.inventory[i]:
                            dragging = (player.inventory[i], i, True)
                            break
                    # Input slots
                    for i in range(2):
                        slot_rect = pg.Rect(WIDTH//2 - 60 + i*80, HEIGHT//2 - 30, 60, 60)
                        if slot_rect.collidepoint(mx, my) and input_slots[i]:
                            dragging = (input_slots[i][0], i, False)
                            break
                    # Output slot
                    output_rect = pg.Rect(WIDTH//2 - 60, HEIGHT - 120, 120, 80)
                    if output_ready and output_rect.collidepoint(mx, my) and output_item:
                        for j in range(len(player.inventory)):
                            if player.inventory[j] is None:
                                player.inventory[j] = output_item
                                output_item = None
                                output_ready = False
                                input_slots = [None, None]
                                break
                # Drop onto input slots or inventory
                if event.type == pg.MOUSEBUTTONUP and event.button == 1 and dragging:
                    item, idx, from_inv = dragging
                    dropped = False
                    # Input slots
                    for i in range(2):
                        slot_rect = pg.Rect(WIDTH//2 - 60 + i*80, HEIGHT//2 - 30, 60, 60)
                        if slot_rect.collidepoint(mx, my):
                            # Only allow if slot empty and (other slot empty or matches type/rarity)
                            other = input_slots[1-i][0] if input_slots[1-i] else None
                            if input_slots[i] is None:
                                if other is None or (other.type == item.type and other.rarity == item.rarity):
                                    input_slots[i] = (item, None)
                                    if from_inv:
                                        player.inventory[idx] = None
                                    else:
                                        input_slots[idx] = None
                                    dropped = True
                                    break
                    # Inventory bar
                    for i in range(10):
                        r = pg.Rect(40 + i*(size+margin), HEIGHT-80, size, size)
                        if r.collidepoint(mx, my) and player.inventory[i] is None:
                            player.inventory[i] = item
                            if from_inv:
                                player.inventory[idx] = None
                            else:
                                input_slots[idx] = None
                            dropped = True
                            break
                    dragging = None
        screen.fill((40, 30, 30))
        if smeltery_bg:
            screen.blit(smeltery_bg, (0, 0))
        # Speech bubble (stage 0)
        if stage == 0:
            bubble_w, bubble_h = 340, 74
            bubble_x = WIDTH//2 - bubble_w//2
            bubble_y = HEIGHT//2 - 180
            bubble = pg.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
            pg.draw.rect(screen, (255,255,180), bubble, border_radius=12)
            pg.draw.rect(screen, (0,0,0), bubble, width=3, border_radius=12)
            pointer = [(WIDTH//2-10, bubble.bottom), (WIDTH//2+10, bubble.bottom), (WIDTH//2, bubble.bottom+16)]
            pg.draw.polygon(screen, (255,255,180), pointer)
            pg.draw.polygon(screen, (0,0,0), pointer, width=2)
            txt = font16.render("Anything you want to smelt?", True, (0,0,0))
            screen.blit(txt, (bubble.x+24, bubble.y+24))
        # Anvil UI (stage 1)
        if stage == 1:
            overlay = pg.Surface((WIDTH, HEIGHT), flags=pg.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            if anvil_img:
                screen.blit(anvil_img, (WIDTH//2 - anvil_img.get_width()//2, HEIGHT//2 - anvil_img.get_height()//2))
            # Draw input slots
            for i in range(2):
                slot_rect = pg.Rect(WIDTH//2 - 60 + i*80, HEIGHT//2 - 30, 60, 60)
                pg.draw.rect(screen, (220,220,220), slot_rect, 4)
                if input_slots[i]:
                    item, idx = input_slots[i]
                    item.draw(screen, slot_rect.x+10, slot_rect.y+10, 40)
            # Draw output slot
            output_rect = pg.Rect(WIDTH//2 - 60, HEIGHT - 120, 120, 80)
            pg.draw.rect(screen, (200,200,255), output_rect, border_radius=10, width=4)
            if output_ready and output_item:
                output_item.draw(screen, output_rect.x+30, output_rect.y+20, 60)
            # Smelt logic: only if both slots filled, not output_ready, and both items match
            if not output_ready and input_slots[0] and input_slots[1]:
                item0, idx0 = input_slots[0]
                item1, idx1 = input_slots[1]
                if item0.type == item1.type and item0.rarity == item1.rarity:
                    rarity_order = ["common","uncommon","rare","holy","godlike"]
                    r_idx = rarity_order.index(item0.rarity)
                    # Smelting cost by rarity
                    cost_table = [ (5,10), (5,10), (10,20), (15,40), (30,100) ]
                    exp_cost, coin_cost = cost_table[r_idx]
                    # Check player coins and exp
                    if hasattr(player, "exp") and hasattr(player, "coins"):
                        if player.exp < exp_cost or player.coins < coin_cost:
                            smelt_msg = f"Need {exp_cost} XP, {coin_cost} coins!"
                            smelt_msg_timer = pg.time.get_ticks()
                        else:
                            player.exp -= exp_cost
                            player.coins -= coin_cost
                            if r_idx < len(rarity_order)-1:
                                chances = [0.5, 0.3, 0.15, 0.05]
                                upgrade = random.random() < chances[r_idx]
                                new_rarity = rarity_order[r_idx+1] if upgrade else item0.rarity
                                output_item = Item(item0.name, item0.type, new_rarity)
                                output_ready = True
                            else:
                                output_item = Item(item0.name, item0.type, item0.rarity)
                                output_ready = True
                    else:
                        smelt_msg = "No exp/coin attributes!"
                        smelt_msg_timer = pg.time.get_ticks()
            # If not matching, do not allow smelt (no output)
            elif not output_ready:
                output_item = None
                output_ready = False
    # Draw inventory bar at bottom
        for i in range(10):
            r = pg.Rect(40 + i*(size+margin), HEIGHT-80, size, size)
            pg.draw.rect(screen, (230,230,230), r)
            pg.draw.rect(screen, (200,200,200), r, 3)
            if player.inventory[i]:
                player.inventory[i].draw(screen, r.x+10, r.y+10, size-20)
            if i == player.selected:
                pg.draw.rect(screen, (255,255,0), r.inflate(8,8), 5)
        # Show smelt cost message if needed
        if smelt_msg and pg.time.get_ticks() - smelt_msg_timer < 1800:
            msgsurf = font16.render(smelt_msg, True, (255,40,40))
            screen.blit(msgsurf, (WIDTH//2 - msgsurf.get_width()//2, HEIGHT//2 + 120))
        # Draw dragging item
        if stage == 1 and dragging:
            item, idx, from_inv = dragging
            mx, my = pg.mouse.get_pos()
            item.draw(screen, mx-20, my-20, 40)
        pg.display.flip()
        clock.tick(60)
# Utility: draw a button with a background image and black outline covering corners
# Utility: draw a button with a background image and black outline covering corners
def draw_button_with_bg(surf, rect, bg_img, border_radius=18):
    button_surf = pg.Surface(rect.size, pg.SRCALPHA)
    # Blit the background image, clipped to the button rect
    if bg_img:
        button_surf.blit(bg_img, (0, 0), area=pg.Rect(0, 0, rect.w, rect.h))
    # Mask to rounded rect
    mask = pg.Surface(rect.size, pg.SRCALPHA)
    pg.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=border_radius)
    button_surf.blit(mask, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    # Blit to main surface
    surf.blit(button_surf, rect.topleft)
    # Draw the black outline
    pg.draw.rect(surf, (0, 0, 0), rect, width=7, border_radius=border_radius)
import pygame as pg, math, random, sys, os
import json
from typing import List, Dict, Optional, Tuple
import glob, os

# ----------------------------- ANIMSPRITE CLASS -----------------------
class AnimSprite:
    """
    Handles loading and animating a sequence of PNG images from a folder.
    """
    def __init__(self, folder: str, fps=10, loop=True):
        """
        Initialize the animation sprite from a folder of images.
        Args:
            folder (str): Path to folder with PNGs.
            fps (int): Frames per second.
            loop (bool): Whether to loop the animation.
        """
        # folder contains 32×32 PNGs – already sliced
        self.frames = [pg.image.load(f).convert_alpha() for f in sorted(glob.glob(folder))]
        self.timer = 0
        self.idx = 0
        self.fps = fps
        self.loop = loop
    def update(self, dt):
        """
        Advance the animation timer by dt milliseconds.
        """
        self.timer += dt
        if self.timer > 1000/self.fps:
            self.timer = 0
            next_idx = self.idx + 1
            if next_idx >= len(self.frames):
                next_idx = 0 if self.loop else len(self.frames)-1
            self.idx = next_idx
    def image(self):
        """
        Return the current animation frame (pygame.Surface).
        """
        return self.frames[self.idx]

# ----------------------------- CONFIG ---------------------------------
WIDTH, HEIGHT = 1200, 700
FPS = 60
GRAVITY = 0.6
JUMP_STR = -14
MOVE_SPEED = 5
# BLOCK_CD = 5000  # ms


# ----------------------------- CONFIG ---------------------------------
WIDTH, HEIGHT = 1200, 700
FPS = 60
GRAVITY = 0.6
JUMP_STR = -14
MOVE_SPEED = 5
BLOCK_CD = 5000  # ms
BACKSTAB_DEG = 120  # deg behind enemy
DAGGER_RANGE = 90
SWORD_RANGE = 120
RAPIER_RANGE = 145
THROWN_RAPIER_SPEED = 12
FIST_RANGE=90
FIST_DAMAGE=4
FIST_SPEED=150
# ----------------------------- FULLSCREEN FIX --------------------------
pg.init()
info = pg.display.Info()
FULLSCREEN_W, FULLSCREEN_H = info.current_w, info.current_h
WIDTH, HEIGHT = FULLSCREEN_W, FULLSCREEN_H
# rarity colours
RARITY_COL = {
    "common": (200, 200, 200),
    "uncommon": (50, 200, 50),
    "rare": (50, 150, 255),
    "holy": (255, 215, 0),
    "godlike": (255, 50, 255),
}
RARITY_LVL = {"common": 1, "uncommon": 2, "rare": 3, "holy": 4, "godlike": 5}
# ----------------------------------------------------------------------


pg.init()

# --- Save/load helpers ---
def save_player_data(player):
    try:
        with open("player_save.json", "w") as f:
            json.dump(player.to_dict(), f)
    except Exception as e:
        print("Failed to save player data:", e)

def load_player_data(player):
    try:
        with open("player_save.json", "r") as f:
            data = json.load(f)
        player.from_dict(data)
    except Exception:
        # No save file: ensure empty inventory and armor
        player.inventory = [None]*10
        player.armor = {"helmet":None,"chest":None,"legs":None,"boots":None}
WIDTH, HEIGHT = FULLSCREEN_W, FULLSCREEN_H
screen = pg.display.set_mode((WIDTH, HEIGHT), pg.FULLSCREEN)
fullscreen = True
pg.display.set_caption("Anime Underground Platformer")
clock = pg.time.Clock()
font20 = pg.font.SysFont(["Comic Sans MS", "Brush Script MT", "cursive", "arial"], 20, italic=True)
font16 = pg.font.SysFont(["Comic Sans MS", "Brush Script MT", "cursive", "arial"], 16, italic=True)

# Load floor/ledge sprite
floor_img = None
try:
    floor_img = pg.image.load("assets/floor.png").convert_alpha()
except Exception as e:
    print("[DEBUG] Failed to load floor.png:", e)

# Load background image (after display is initialized)
game_bg_img = None
try:
    game_bg_img = pg.image.load("assets/background.png").convert()
    game_bg_img = pg.transform.scale(game_bg_img, (WIDTH, HEIGHT))
    print("[DEBUG] Background image loaded successfully.")
except Exception as e:
    print(f"[DEBUG] Failed to load background image: {e}")
    game_bg_img = None

dragging_item = None  # (item, from_slot)
drag_offset = (0, 0)
drag_pos = (0, 0)

# ----------------------------- MAIN GAME LOOP --------------------------
def run_game():
    player = Player(100, HEIGHT-200)
    load_player_data(player)
    stage_num = 1
    stage = Stage(stage_num)
    player.hp = player.max_hp
    player.invincible_until = pg.time.get_ticks() + 3000  # 3 seconds invincibility at spawn
    running = True
    show_inventory = False
    game_over = False
    global screen, fullscreen
    while running:
        dt = clock.tick(FPS)
        now = pg.time.get_ticks()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                save_player_data(player)
                running = False
            if event.type == pg.KEYDOWN:
                # Robust F11 fullscreen toggle
                if event.key == pg.K_ESCAPE:
                    save_player_data(player)
                    running = False
                if event.key == pg.K_e:
                    show_inventory = not show_inventory
                # F11 toggle: support both symbolic and numeric keycode, and try toggle_fullscreen
                if event.key == pg.K_F11 or event.key == 1073741892:
                    fullscreen = not fullscreen
                    try:
                        # Try pygame's toggle_fullscreen (works on some platforms)
                        pg.display.toggle_fullscreen()
                    except Exception:
                        # Fallback to set_mode
                        if fullscreen:
                            screen = pg.display.set_mode((WIDTH, HEIGHT), pg.FULLSCREEN)
                        else:
                            screen = pg.display.set_mode((WIDTH, HEIGHT))
                    # Ensure global screen is updated
                    globals()['screen'] = screen
                if event.key == pg.K_SPACE:
                    # Try to pick up an item if in range
                    pickup_range = 60
                    for drop in stage.drops[:]:
                        if dist(player.rect.center, (drop.x, drop.y)) < pickup_range:
                            # Find first empty inventory slot
                            for i in range(len(player.inventory)):
                                if player.inventory[i] is None:
                                    player.inventory[i] = drop
                                    stage.drops.remove(drop)
                                    break
                            break
            # Scroll wheel inventory selection
            if event.type == pg.MOUSEWHEEL:
                player.selected = (player.selected - event.y) % len(player.inventory)
            # Drag-and-drop for armor in inventory overlay (only in game)
            if show_inventory:
                margin, size = 20, 50
                startx, starty = 100, 100
                center_x = WIDTH // 2
                center_y = HEIGHT // 2 + 40
                armor_slots = ["helmet", "chest", "legs", "boots"]
                slot_rects = [pg.Rect(startx + i*(size+margin), starty, size, size) for i in range(10)]
                armor_rects = [(slot, pg.Rect(center_x-80, center_y-40+idx*45, 40, 40)) for idx, slot in enumerate(armor_slots)]
                global dragging_item, drag_offset, drag_pos
                mouse_x, mouse_y = pg.mouse.get_pos()
                mouse_held = pg.mouse.get_pressed()[0]
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and not dragging_item:
                    for i, r in enumerate(slot_rects):
                        if r.collidepoint(event.pos) and player.inventory[i]:
                            dragging_item = (player.inventory[i], i)
                            drag_offset = (event.pos[0] - r.x, event.pos[1] - r.y)
                            break
                    # Start dragging from armor slots (for unequip)
                    for slot, slot_rect in armor_rects:
                        if slot_rect.collidepoint(event.pos) and player.armor[slot]:
                            dragging_item = (player.armor[slot], slot)
                            drag_offset = (event.pos[0] - slot_rect.x, event.pos[1] - slot_rect.y)
                            break
                if event.type == pg.MOUSEBUTTONUP and event.button == 1 and dragging_item:
                    item, from_slot = dragging_item
                    dropped = False
                    # Dropping onto armor slot (equip)
                    for slot, slot_rect in armor_rects:
                        if slot_rect.collidepoint(event.pos):
                            if item.type == slot:
                                # If equipping from inventory
                                if isinstance(from_slot, int):
                                    player.armor[slot] = item
                                    player.inventory[from_slot] = None
                                # If swapping between armor slots
                                elif isinstance(from_slot, str):
                                    player.armor[slot] = item
                                    player.armor[from_slot] = None
                                player.calc_set_bonus()
                                dropped = True
                                break
                    # Dropping onto inventory slot (unequip)
                    if not dropped and isinstance(from_slot, str):
                        for i, r in enumerate(slot_rects):
                            if r.collidepoint(event.pos) and player.inventory[i] is None:
                                player.inventory[i] = item
                                player.armor[from_slot] = None
                                dropped = True
                                break
                    dragging_item = None
                if dragging_item and mouse_held:
                    drag_pos = (mouse_x, mouse_y)
                elif dragging_item and not mouse_held:
                    dragging_item = None

        # Pause game logic if inventory overlay is open
        if not show_inventory and not game_over:
            player.update(stage.platforms, stage.mobs, now)
            stage.update(player)
            for mob in stage.mobs:
                mob.update(player, stage.platforms)
            # Debug: print number of enemies
            # Check for player death
            if player.hp <= 0:
                player.move_armor_to_inventory()
                game_over = True
                death_time = now

        # Drawing
        if game_bg_img:
            screen.blit(game_bg_img, (0, 0))
        else:
            screen.fill((30,30,40))
        stage.draw(screen)
        player.draw(screen)
        # Always show bottom inventory bar
        draw_inventory(screen, player)
        # Show full inventory overlay if toggled
        if show_inventory:
            overlay = pg.Surface((WIDTH, HEIGHT), flags=pg.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            draw_full_inventory_with_drag(screen, player)
        # Portal to next level
        if stage.portal and player.rect.colliderect(stage.portal):
            stage_num += 1
            stage = Stage(stage_num)
            player.rect.x, player.rect.y = 100, HEIGHT-200
            player.hp = player.max_hp
            player.invincible_until = pg.time.get_ticks() + 2000

        pg.display.flip()
        if game_over:
            # Show game over message
            txt = font20.render("GAME OVER", True, (255, 50, 50))
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - txt.get_height()//2))
            pg.display.flip()
            pg.time.wait(2000)
            show_start_screen()
            return

def draw_full_inventory(surf, player):
    # This is the original full inventory UI, centered on screen
    margin, size = 20, 50
    startx, starty = 100, 100
    global dragging_item, drag_offset, drag_pos
    mouse_x, mouse_y = pg.mouse.get_pos()
    slot_rects = []
    armor_slots = ["helmet", "chest", "legs", "boots"]
    armor_rects = []
    # Inventory slots
    for i in range(10):
        r = pg.Rect(startx + i*(size+margin), starty, size, size)
        slot_rects.append(r)
        pg.draw.rect(surf, (200,200,200), r, 3)
        if player.inventory[i] and (not dragging_item or dragging_item[1] != i):
            player.inventory[i].draw(surf, r.x+10, r.y+10, size-20)
        if i == player.selected:
            pg.draw.rect(surf, (255,255,0), r.inflate(8,8), 5)
    # Armor slots
    center_x = WIDTH // 2
    center_y = HEIGHT // 2 + 40
    for idx, slot in enumerate(armor_slots):
        slot_y = center_y - 40 + idx*45
        slot_rect = pg.Rect(center_x-80, slot_y, 40, 40)
        armor_rects.append((slot, slot_rect))
        pg.draw.rect(surf, (150,150,150), slot_rect, 3)
        if player.armor[slot]:
            player.armor[slot].draw(surf, slot_rect.x+5, slot_rect.y+5, 30)
        label = font16.render(slot[0].upper(), True, (180,180,180))
        surf.blit(label, (slot_rect.x-18, slot_rect.y+12))
    # Drag and drop logic
    mouse_held = pg.mouse.get_pressed()[0]
    # Only start dragging on mouse down, keep dragging while held, drop on mouse up
    for event in pg.event.get([pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP]):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and not dragging_item:
            for i, r in enumerate(slot_rects):
                if r.collidepoint(event.pos) and player.inventory[i]:
                    dragging_item = (player.inventory[i], i)
                    drag_offset = (event.pos[0] - r.x, event.pos[1] - r.y)
                    break
        if event.type == pg.MOUSEBUTTONUP and event.button == 1 and dragging_item:
            item, from_slot = dragging_item
            dropped = False
            for slot, slot_rect in armor_rects:
                if slot_rect.collidepoint(event.pos):
                    if item.type == slot:
                        player.armor[slot] = item
                        player.inventory[from_slot] = None
                        player.calc_set_bonus()
                        dropped = True
                        break
            dragging_item = None
    # If dragging, update drag position to current mouse
    if dragging_item and mouse_held:
        drag_pos = (mouse_x, mouse_y)
    elif dragging_item and not mouse_held:
        # If mouse released outside event, cancel drag
        dragging_item = None
    # Draw dragged item
    if dragging_item:
        item, from_slot = dragging_item
        item.draw(surf, mouse_x - drag_offset[0], mouse_y - drag_offset[1], size-20)
        r = pg.Rect(startx + from_slot*(size+margin), starty, size, size)
        pg.draw.rect(surf, (200,200,200), r, 3)
        if player.inventory[from_slot]:
            player.inventory[from_slot].draw(surf, r.x+10, r.y+10, size-20)
        if from_slot == player.selected:
            pg.draw.rect(surf, (255,255,0), r.inflate(8,8), 5)
    center_x = WIDTH // 2
    center_y = HEIGHT // 2 + 40
    mini_size = 90
    mini_rect = pg.Rect(center_x-25, center_y-45, 50, 90)
    try:
        surf.blit(pg.transform.scale(player.anim.image(), (50, 90)), mini_rect)
    except Exception:
        pg.draw.rect(surf, (255,100,100), mini_rect)
    armor_slots = ["helmet", "chest", "legs", "boots"]
    for idx, slot in enumerate(armor_slots):
        slot_y = center_y - 40 + idx*45
        slot_rect = pg.Rect(center_x-80, slot_y, 40, 40)
        pg.draw.rect(surf, (150,150,150), slot_rect, 3)
        if player.armor[slot]:
            player.armor[slot].draw(surf, slot_rect.x+5, slot_rect.y+5, 30)
        label = font16.render(slot[0].upper(), True, (180,180,180))
        surf.blit(label, (slot_rect.x-18, slot_rect.y+12))
    shield_rect = pg.Rect(center_x+40, center_y-10, 40, 40)
    pg.draw.rect(surf, (100,100,255), shield_rect, 3)
    if player.shield:
        player.shield.draw(surf, shield_rect.x+5, shield_rect.y+5, 30)
    surf.blit(font16.render("S", True, (180,180,255)), (shield_rect.x+48, shield_rect.y+12))
    grid_bottom = starty + size + 20
    tx = startx
    surf.blit(font20.render(f"XP: {player.xp}", True, (255,255,255)), (tx, grid_bottom))
    surf.blit(font20.render("E to close", True, (255,255,255)), (tx, grid_bottom + 30))


# --- Enhanced inventory overlay for drag-and-drop in main game only ---
def draw_full_inventory_with_drag(surf, player):
    global dragging_item, drag_offset, drag_pos
    margin, size = 20, 50
    startx, starty = 100, 100
    mouse_x, mouse_y = pg.mouse.get_pos()
    slot_rects = []
    armor_slots = ["helmet", "chest", "legs", "boots"]
    # Inventory slots
    for i in range(10):
        r = pg.Rect(startx + i*(size+margin), starty, size, size)
        slot_rects.append(r)
        # Fill slot with light grey
        pg.draw.rect(surf, (230,230,230), r)
        # Draw border
        pg.draw.rect(surf, (200,200,200), r, 3)
        if player.inventory[i] and (not dragging_item or dragging_item[1] != i):
            player.inventory[i].draw(surf, r.x+10, r.y+10, size-20)
        if i == player.selected:
            pg.draw.rect(surf, (255,255,0), r.inflate(8,8), 5)
    # Armor slots
    center_x = WIDTH // 2
    center_y = HEIGHT // 2 + 40
    for idx, slot in enumerate(armor_slots):
        slot_y = center_y - 40 + idx*45
        slot_rect = pg.Rect(center_x-80, slot_y, 40, 40)
        pg.draw.rect(surf, (150,150,150), slot_rect, 3)
        if player.armor[slot]:
            player.armor[slot].draw(surf, slot_rect.x+5, slot_rect.y+5, 30)
        label = font16.render(slot[0].upper(), True, (180,180,180))
        surf.blit(label, (slot_rect.x-18, slot_rect.y+12))
    # Draw dragged item
    if dragging_item:
        item, from_slot = dragging_item
        item.draw(surf, mouse_x - drag_offset[0], mouse_y - drag_offset[1], size-20)
        if isinstance(from_slot, int):
            r = pg.Rect(startx + from_slot*(size+margin), starty, size, size)
            pg.draw.rect(surf, (200,200,200), r, 3)
            if player.inventory[from_slot]:
                player.inventory[from_slot].draw(surf, r.x+10, r.y+10, size-20)
            if from_slot == player.selected:
                pg.draw.rect(surf, (255,255,0), r.inflate(8,8), 5)

# ----------------------------- ENTRY POINT ----------------------------



def draw_inventory(surf, player):
    """Draw the inventory UI, including items, armor, weapon, and shield."""
    # Only show the first line of inventory at the left bottom, stretching horizontally
    margin, size = 10, 50
    num_slots = 10
    total_width = num_slots * size + (num_slots - 1) * margin
    startx = 20
    starty = HEIGHT - 83 + (40 - size)//2  # Align with new floor height, center inventory in ground
    global dragging_item, drag_pos
    mouse_x, mouse_y = pg.mouse.get_pos()
    slot_rects = []
    for i in range(num_slots):
        r = pg.Rect(startx + i * (size + margin), starty, size, size)
        slot_rects.append(r)
        # Fill slot with light grey
        pg.draw.rect(surf, (230,230,230), r)
        # Draw border
        pg.draw.rect(surf, (200,200,200), r, 3)
        if player.inventory[i] and (not dragging_item or dragging_item[1] != i):
            player.inventory[i].draw(surf, r.x+10, r.y+10, size-20)
        if i == player.selected:
            pg.draw.rect(surf, (255,255,0), r.inflate(8,8), 5)
    if dragging_item:
        item, from_slot = dragging_item
        item.draw(surf, mouse_x - drag_offset[0], mouse_y - drag_offset[1], size-20)
        if isinstance(from_slot, int):
            r = pg.Rect(startx + from_slot * (size + margin), starty, size, size)
            pg.draw.rect(surf, (200,200,200), r, 3)
            if player.inventory[from_slot]:
                player.inventory[from_slot].draw(surf, r.x+10, r.y+10, size-20)
            if from_slot == player.selected:
                pg.draw.rect(surf, (255,255,0), r.inflate(8,8), 5)
# ----------- TAVERN SCREEN -----------
def show_tavern(screen, player):
    try:
        tavern_bg = pg.image.load("assets/tavern.png").convert_alpha()
        tavern_bg = pg.transform.scale(tavern_bg, (WIDTH, HEIGHT))
    except Exception as e:
        print("Failed to load tavern.png:", e)
        tavern_bg = None
    bubble_w, bubble_h = 220, 60
    bubble_x = WIDTH//2 - bubble_w//2
    bubble_y = HEIGHT - 220
    bubble_rect = pg.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
    bubble_color = (255,255,255)
    bubble_border = (0,0,0)
    bubble_text = font20.render("anything to sell?", True, (0,0,0))
    tavern_waiting = True
    inv_open = False
    offer_idx = None  # Index of item being offered
    offer_msg = None  # Message to show after selling
    margin, size = 20, 50
    startx, starty = 100, 100
    while tavern_waiting:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if offer_idx is not None:
                        offer_idx = None  # Cancel offer bubble
                        offer_msg = None
                    else:
                        tavern_waiting = False
                        show_start_screen()
                        return
                if event.key == pg.K_e:
                    inv_open = not inv_open
                if inv_open and offer_idx is not None and event.key == pg.K_RETURN:
                    # Accept offer: remove item, add coins, show message
                    item = player.inventory[offer_idx]
                    if item:
                        # Set base values for weapons and armor
                        base_values = {
                            "dagger": 15,
                            "sword": 30,
                            "rapier": 45,
                            "helmet": 15,
                            "chest": 35,
                            "legs": 30,
                            "boots": 20
                        }
                        # For armor, use item.type (helmet, chest, legs, boots)
                        base = base_values.get(item.type, 0)
                        rarity_bonus = {"common": 0, "uncommon": 0.15, "rare": 0.20, "holy": 0.25, "godlike": 0.30}.get(item.rarity, 0)
                        coins = int(base * (1 + rarity_bonus))
                        player.coins += coins
                        offer_msg = f"Sold for {coins} coins!"
                        player.inventory[offer_idx] = None
                        save_player_data(player)
                    offer_idx = None
            if inv_open and event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                # Right click: check if on an item in the overlay grid only
                mx, my = pg.mouse.get_pos()
                slot_found = False
                for i in range(10):
                    r = pg.Rect(startx + i*(size+margin), starty, size, size)
                    if r.collidepoint(mx, my):
                        slot_found = True
                        if player.inventory[i]:
                            offer_idx = i
                            offer_msg = None
                        else:
                            pass
                            break
                if not slot_found:
                    pass
            screen.fill((60, 40, 30))
        if tavern_bg:
            screen.blit(tavern_bg, (0,0))
        # Draw speech bubble above the guy in the image
        pg.draw.rect(screen, bubble_color, bubble_rect, border_radius=18)
        pg.draw.rect(screen, bubble_border, bubble_rect, width=3, border_radius=18)
        screen.blit(bubble_text, (bubble_rect.x+18, bubble_rect.y+18))
        # Only show inventory and offer bubble if inventory is open
        if inv_open:
            overlay = pg.Surface((WIDTH, HEIGHT), flags=pg.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            # Draw overlay inventory grid with highlight
            margin, size = 20, 50
            startx, starty = 100, 100
            for i in range(10):
                r = pg.Rect(startx + i*(size+margin), starty, size, size)
                pg.draw.rect(screen, (220,220,220), r, 4)
                # Always show the item sprite, even if offer_idx == i
                if player.inventory[i]:
                    player.inventory[i].draw(screen, r.x+10, r.y+10, size-20)
                if i == player.selected:
                    pg.draw.rect(screen, (255,255,0), r.inflate(8,8), 5)
            # Draw dragged item if any (not used in tavern, but for consistency)
            global dragging_item, drag_pos
            mouse_x, mouse_y = pg.mouse.get_pos()
            if dragging_item:
                item, from_slot = dragging_item
                item.draw(screen, mouse_x - drag_offset[0], mouse_y - drag_offset[1], size-20)
                r = pg.Rect(startx + from_slot*(size+margin), starty, size, size)
                pg.draw.rect(screen, (200,200,200), r, 3)
                if player.inventory[from_slot]:
                    player.inventory[from_slot].draw(screen, r.x+10, r.y+10, size-20)
                if from_slot == player.selected:
                    pg.draw.rect(screen, (255,255,0), r.inflate(8,8), 5)
            if offer_idx is not None:
                r = pg.Rect(startx + offer_idx*(size+margin), starty, size, size)
                # Make the bubble even wider and taller, and center it above the slot
                bubble_w, bubble_h = size+180, 74
                bubble_x = r.centerx - bubble_w//2
                bubble_y = r.y - bubble_h - 12
                bubble = pg.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
                # Draw a more visible bubble with a pointer
                pg.draw.rect(screen, (255,255,180), bubble, border_radius=12)
                pg.draw.rect(screen, (0,0,0), bubble, width=3, border_radius=12)
                # Draw a triangle pointer centered to the slot
                pointer = [(r.centerx-10, bubble.bottom), (r.centerx+10, bubble.bottom), (r.centerx, bubble.bottom+16)]
                pg.draw.polygon(screen, (255,255,180), pointer)
                pg.draw.polygon(screen, (0,0,0), pointer, width=2)
                txt = font16.render("Do you want to sell this item?", True, (0,0,0))
                screen.blit(txt, (bubble.x+24, bubble.y+16))
                txt2 = font16.render("Press Enter to confirm", True, (80,80,80))
                screen.blit(txt2, (bubble.x+24, bubble.y+40))
            if offer_msg:
                msg_rect = pg.Rect(WIDTH//2-80, HEIGHT//2-100, 160, 32)
                pg.draw.rect(screen, (255,255,200), msg_rect, border_radius=10)
                pg.draw.rect(screen, (0,0,0), msg_rect, width=2, border_radius=10)
                txt = font16.render(offer_msg, True, (0,0,0))
                screen.blit(txt, (msg_rect.x+12, msg_rect.y+6))
        pg.display.flip()
        clock.tick(60)

# ----------- START SCREEN -----------
def show_start_screen():
    waiting = True
    """
    Display the start screen with a play button and wait for the user to click to start the game.
    """
    # Restore all start screen variables
    try:
        cover_img = pg.image.load("assets/cover.png").convert_alpha()
        cover_img = pg.transform.scale(cover_img, (WIDTH, HEIGHT))
    except Exception as e:
        print("Failed to load cover.png:", e)
        cover_img = None
    button_w, button_h = 200, 80
    button_gap = 30
    total_height = 3 * button_h + 2 * button_gap
    start_y = HEIGHT//2 - total_height//2 + 180
    play_rect = pg.Rect(WIDTH//2 - button_w//2, start_y, button_w, button_h)
    smeltery_rect = pg.Rect(WIDTH//2 - button_w//2, start_y + button_h + button_gap, button_w, button_h)
    tavern_rect = pg.Rect(WIDTH//2 - button_w//2, start_y + 2*(button_h + button_gap), button_w, button_h)
    try:
        play_btn_img = pg.image.load("assets/play-button.png").convert_alpha()
        play_btn_img = pg.transform.scale(play_btn_img, (button_w, button_h))
    except Exception as e:
        print("Failed to load play-button.png:", e)
        play_btn_img = None
    shake_phases = [0, 0, 0]
    # Create a dummy player for the tavern screen (not used for gameplay)
    dummy_player = Player(100, HEIGHT-200)
    load_player_data(dummy_player)
    global screen
    while waiting:
        mouse_pos = pg.mouse.get_pos()
        hovered = [play_rect.collidepoint(mouse_pos), smeltery_rect.collidepoint(mouse_pos), tavern_rect.collidepoint(mouse_pos)]
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return False
            if event.type == pg.MOUSEBUTTONDOWN:
                if hovered[0]:
                    return True
                if hovered[1]:
                    show_smeltery(screen, dummy_player)
                if hovered[2]:
                    show_tavern(screen, dummy_player)
        screen.fill((0,0,0))
        if cover_img:
            screen.blit(cover_img, (0,0))
        button_rects = [play_rect, smeltery_rect, tavern_rect]
        button_labels = ["PLAY", "SMELTERY", "TAVERN"]
        for i, rect in enumerate(button_rects):
            shake_offset = 0
            if hovered[i]:
                shake_phases[i] += 0.25
                shake_offset = int(math.sin(shake_phases[i]) * 6)
            else:
                shake_phases[i] = 0
            shaken_rect = rect.move(shake_offset, 0)
            # Use the new utility for button background and outline
            draw_button_with_bg(screen, shaken_rect, play_btn_img if play_btn_img else None, border_radius=18)
            grass_green = (50, 200, 50)
            txt = font20.render(button_labels[i], True, grass_green)
            screen.blit(txt, (shaken_rect.x + shaken_rect.w//2 - txt.get_width()//2, shaken_rect.y + shaken_rect.h//2 - txt.get_height()//2))
        pg.display.flip()
        clock.tick(60)


def sign(x):
    """
    Return 1 if x > 0, -1 if x < 0, 0 if x == 0.
    """
    return 1 if x > 0 else -1 if x < 0 else 0
def dist(a, b):
    """
    Return the Euclidean distance between points a and b.
    """
    return math.hypot(a[0]-b[0], a[1]-b[1])
def angle(a, b):
    """
    Return the angle in degrees from point a to point b.
    """
    return math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))

# ----------------------------- ITEMS ----------------------------------
class Item:
    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'rarity': self.rarity
        }

    @staticmethod
    def from_dict(data):
        if data is None:
            return None
        return Item(data['name'], data['type'], data['rarity'])
    """
    Represents a weapon or armor item with stats and sprite.
    """
    def __init__(self, name: str, type_: str, rarity: str):
        """
        Initialize an item.
        Args:
            name (str): Name of the item.
            type_ (str): Type (dagger, sword, rapier, helmet, chest, legs, boots).
            rarity (str): Rarity string.
        """
        self.name = name
        self.type = type_  # dagger/sword/rapier/helmet/chest/legs/boots
        self.rarity = rarity
        self.dmg = self.base_dmg()
        self.attack_speed = self.base_as()
    def base_dmg(self):
        """
        Return base damage for the item type.
        """
        if self.type == "dagger":
            return 12  # Increased base dagger damage
        if self.type == "sword":
            return 10
        if self.type == "rapier":
            return 14
        return 0
    def base_as(self):
        """
        Return base attack speed for the item type.
        """
        if self.type == "dagger": return 200  # ms
        if self.type == "sword": return 400
        if self.type == "rapier": return 500
        return 0
    def upgrade(self):
        """
        Upgrade the item's rarity and stats.
        """
        order = ["common","uncommon","rare","holy","godlike"]
        idx = order.index(self.rarity)
        if idx < len(order)-1:
            self.rarity = order[idx+1]
            self.dmg = int(self.dmg * 1.5)
            self.attack_speed = int(self.attack_speed * 0.9)
    def colour(self):
        """
        Return the color for the item's rarity.
        """
        return RARITY_COL[self.rarity]
    dagger_sprite = None  # class variable for dagger sprite
    sword_sprite = None   # class variable for sword sprite
    rapier_sprite = None # class variable for rapier sprite
    def draw(self, surf, x, y, size=30):
        """
        Draw the item sprite or shape on the given surface.
        """
        c = self.colour()
        if self.type == "dagger":
            if Item.dagger_sprite is None:
                try:
                    Item.dagger_sprite = pg.image.load("assets/dagger.png").convert_alpha()
                except Exception as e:
                    print("Failed to load dagger sprite:", e)
                    Item.dagger_sprite = None
            if Item.dagger_sprite:
                img = pg.transform.scale(Item.dagger_sprite, (size, size))
                surf.blit(img, (x, y))
            else:
                pg.draw.rect(surf, c, (x, y, size, size//3))
        elif self.type == "sword":
            if Item.sword_sprite is None:
                try:
                    Item.sword_sprite = pg.image.load("assets/sword.png").convert_alpha()
                except Exception as e:
                    print("Failed to load sword sprite:", e)
                    Item.sword_sprite = None
            if Item.sword_sprite:
                img = pg.transform.scale(Item.sword_sprite, (size, size))
                surf.blit(img, (x, y))
            else:
                pg.draw.rect(surf, c, (x, y, size, size//3))
        elif self.type == "rapier":
            if Item.rapier_sprite is None:
                try:
                    Item.rapier_sprite = pg.image.load("assets/rapier.png").convert_alpha()
                except Exception as e:
                    print("Failed to load rapier sprite:", e)
                    Item.rapier_sprite = None
            if Item.rapier_sprite:
                img = pg.transform.scale(Item.rapier_sprite, (size, size))
                surf.blit(img, (x, y))
            else:
                pg.draw.rect(surf, c, (x, y, size, size//3))
        else:  # armour piece
            # Armor sprites by set and slot
            armor_sprites = {
                "ninja": {
                    "helmet": "assets/ninja-helmet.png",
                    "chest": "assets/ninja-chestplate.png",
                    "legs": "assets/ninja-legs.png",
                    "boots": "assets/ninja-boots.png"
                },
                "knight": {
                    "helmet": "assets/knight-helmet.png",
                    "chest": "assets/knight-chestplate.png",
                    "legs": "assets/knight-leggings.png",
                    "boots": "assets/knight-boots.png"
                },
                "mage": {
                    "helmet": "assets/mage-helmet.png",
                    "chest": "assets/mage-chestplate.png",
                    "legs": "assets/mage-leggings.png",
                    "boots": "assets/mage-boots.png"
                }
            }
            prefix = self.name.split()[0].lower() if self.name else ""
            slot = self.type
            sprite = None
            if prefix in armor_sprites and slot in armor_sprites[prefix]:
                sprite_attr = f"{prefix}_{slot}_sprite"
                if not hasattr(Item, sprite_attr):
                    try:
                        setattr(Item, sprite_attr, pg.image.load(armor_sprites[prefix][slot]).convert_alpha())
                    except Exception as e:
                        print(f"Failed to load {armor_sprites[prefix][slot]}: {e}")
                        setattr(Item, sprite_attr, None)
                sprite = getattr(Item, sprite_attr, None)
            if sprite:
                img = pg.transform.scale(sprite, (size, size))
                surf.blit(img, (x, y))
            else:
                pg.draw.circle(surf, c, (x+size//2, y+size//2), size//2)
        # Draw a thick, vivid 'L' rarity indicator: diagonal (middle left to bottom left), then horizontal (bottom left to middle bottom)
        rarity_stripe_colors = {
            "common": (200, 200, 200),         # bright grey
            "uncommon": (0, 255, 0),           # bright green
            "rare": (0, 120, 255),             # bright blue
            "holy": (200, 0, 255),             # bright purple
            "godlike": (255, 220, 40),         # gold/yellow
        }
        stripe_col = rarity_stripe_colors.get(self.rarity, (200,200,200))
        stripe_surface = pg.Surface((size, size), pg.SRCALPHA)
        thickness = max(5, size//6)
        # Diagonal: from (0, size//4) to (0, size-1) (start higher for longer line)
        pg.draw.line(stripe_surface, stripe_col, (0, size//4), (0, size-1), thickness)
        # Horizontal: from (0, size-1) to (size//2 + size//6, size-1) (extend further right)
        pg.draw.line(stripe_surface, stripe_col, (0, size-1), (size//2 + size//6, size-1), thickness)
        surf.blit(stripe_surface, (x, y))

def random_weapon(rarity: Optional[str]=None) -> Item:
    """
    Return a random weapon item, optionally of a given rarity.
    """
    if rarity is None:
        r = random.choices(["common","uncommon","rare","holy","godlike"],
                           weights=[50,30,15,4,1])[0]
    else: r = rarity
    t = random.choice(["dagger","sword","rapier"])
    return Item(t, t, r)

def random_armour_piece(slot: str, rarity: Optional[str]=None) -> Item:
    """
    Return a random armor item for the given slot and optional rarity.
    """
    if rarity is None:
        r = random.choices(["common","uncommon","rare","holy","godlike"],
                           weights=[50,30,15,4,1])[0]
    else: r = rarity
    name = random.choice(["ninja","knight","mage"]) + " " + slot
    return Item(name, slot, r)

# ----------------------------- ENTITY ---------------------------------
class Entity:
    """
    Base class for all moving game entities (player, enemies, etc).
    """
    def __init__(self, x, y, w, h, hp, colour):
        """
        Initialize an entity.
        Args:
            x, y (int): Position.
            w, h (int): Size.
            hp (int): Health points.
            colour (tuple): RGB color.
        """
        self.rect = pg.Rect(x, y, w, h)
        self.vx, self.vy = 0, 0
        self.hp = self.max_hp = hp
        self.colour = colour
        self.facing = 1
        self.on_ground = False
    def draw_bar(self, surf, off=-20):
        """
        Draw the health bar above the entity.
        """
        pg.draw.rect(surf, (50,50,50), (self.rect.x-10, self.rect.y+off, self.rect.w+20, 6))
        pg.draw.rect(surf, (0,200,0), (self.rect.x-10, self.rect.y+off,
                                        int((self.rect.w+20)*(self.hp/self.max_hp)), 6))
    def move(self, dx, dy, platforms):
        """
        Move the entity and handle collisions with platforms.
        """
        self.rect.x += dx
        for p in platforms:
            if p.colliderect(self.rect):
                if dx > 0: self.rect.right = p.left
                elif dx < 0: self.rect.left = p.right
        self.rect.y += dy
        self.on_ground = False
        for p in platforms:
            if p.colliderect(self.rect):
                if dy > 0:
                    self.rect.bottom = p.top
                    self.on_ground = True
                    self.vy = 0
                elif dy < 0:
                    self.rect.top = p.bottom
                    self.vy = 0

class Player(Entity):
    def move_armor_to_inventory(self):
        # Move all equipped armor to first available inventory slots
        for slot, item in self.armor.items():
            if item:
                for i in range(len(self.inventory)):
                    if self.inventory[i] is None:
                        self.inventory[i] = item
                        self.armor[slot] = None
                        break
    def to_dict(self):
        return {
            'xp': self.xp,
            'coins': self.coins,
            'inventory': [item.to_dict() if item else None for item in self.inventory],
            'armor': {slot: (item.to_dict() if item else None) for slot, item in self.armor.items()},
        }
    """
    The player character, inherits from Entity.
    """
    def __init__(self, x, y):
        """
        Initialize the player character.
        """
        super().__init__(x, y, 40, 60, 100, (255,100,100))
        self.xp = 0
        self.coins = 0
        self.inventory = [None]*10
        self.armor = {"helmet":None,"chest":None,"legs":None,"boots":None}
        self.weapon = None
        self.shield = None
        self.selected = 0  # inventory index
        self.inv_open = False
        self.throwing = None  # rapier projectile
        self.speed_mult = 1
        self.jump_mult = 1
        self.last_attack = 0
        self.anim = AnimSprite("assets/*.png", fps=10)
        self.can_double_jump = True
        self.invincible_until = 0  # timestamp in ms
    def from_dict(self, data):
        self.xp = data.get('xp', 0)
        self.coins = data.get('coins', 0)
        inv = data.get('inventory', [None]*10)
        self.inventory = [Item.from_dict(it) if it else None for it in inv]
        armor_data = data.get('armor', {})
        for slot in self.armor:
            it = armor_data.get(slot)
            self.armor[slot] = Item.from_dict(it) if it else None
        self.last_attack = 0
        self.block_cd = 0
        self.throwing = None  # rapier projectile
        self.inv_open = False
        self.selected = 0  # inventory indexa
        self.dual = False
        self.speed_mult = 1
        self.jump_mult = 1
        self.dagger_bonus = 0
        self.calc_set_bonus()
        self.anim = AnimSprite("assets/*.png", fps=10)
    def calc_set_bonus(self):
        """
        Apply set bonuses for equipped armor.
        """
        sets = {}
        for slot, it in self.armor.items():
            if it is None:
                continue
            prefix = it.name.split()[0]
            sets[prefix] = sets.get(prefix, 0) + 1
        self.dual = False
        self.speed_mult = 1
        self.jump_mult = 1
        self.dagger_bonus = 0
        for pre, c in sets.items():
            if c == 4:
                if pre == "ninja":
                    self.dual = True
                    self.speed_mult = 1.4
                    self.jump_mult = 1.3
                    self.dagger_bonus = 5
    def attack(self, enemies, now):
        """
        Attack enemies with weapon or fist fallback.
        """
        if not self.weapon:
            # Fist fallback attack
            if now - self.last_attack < FIST_SPEED:
                return
            self.last_attack = now
            mx, my = pg.mouse.get_pos()
            ang = angle(self.rect.center, (mx, my))
            r = FIST_RANGE
            dmg = FIST_DAMAGE
            for e in enemies:
                if dist(self.rect.center, e.rect.center) < r + e.rect.w//2:
                    e.hp -= dmg
                    # Instantly max awareness if attacked
                    e.awareness = 5.0
                    e.aware = True
            return
        if now - self.last_attack < self.weapon.attack_speed:
            return
        self.last_attack = now
        mx, my = pg.mouse.get_pos()
        ang = angle(self.rect.center, (mx, my))
        r = {"dagger":DAGGER_RANGE,"sword":SWORD_RANGE,"rapier":RAPIER_RANGE}[self.weapon.type]
        EXTRA = 50
        r += EXTRA
        hitbox = self.rect.centerx + math.cos(math.radians(ang))*r, self.rect.centery + math.sin(math.radians(ang))*r
        dmg = self.weapon.dmg
        # backstab for dagger
        if self.weapon.type == "dagger":
            for e in enemies:
                a = angle(e.rect.center, self.rect.center)
                diff = (ang - a + 180) % 360 - 180
                if abs(diff) > BACKSTAB_DEG/2:
                    # Backstab: deal 1/4th of enemy's current health as bonus damage
                    dmg += int(e.hp * 0.25)
        # apply
        for e in enemies:
            if dist(self.rect.center, e.rect.center) < r + e.rect.w//2:
                e.hp -= dmg
                # Instantly max awareness if attacked
                e.awareness = 5.0
                e.aware = True
    def block(self, now):
        """
        Block with a sword if available.
        """
        if now - self.block_cd < BLOCK_CD: return False
        if not self.weapon or self.weapon.type != "sword": return False
        self.block_cd = now
        return True
    def throw_rapier(self, now):
        """
        Throw a rapier projectile if equipped.
        """
        if not self.weapon or self.weapon.type != "rapier": return
        if self.throwing: return
        mx, my = pg.mouse.get_pos()
        ang = angle(self.rect.center, (mx, my))
        self.throwing = ThrownRapier(self.rect.center, ang, self.weapon.dmg*2)
    def update(self, platforms, enemies, now):
        """
        Update player state, handle input, and apply physics.
        """
        self.vy += GRAVITY
        keys = pg.key.get_pressed()
        # Horizontal movement
        self.vx = (keys[pg.K_d] - keys[pg.K_a]) * MOVE_SPEED * self.speed_mult
        # Jumping
        if (keys[pg.K_SPACE] or keys[pg.K_w]) and self.on_ground:
            self.vy = JUMP_STR * self.jump_mult
            self.on_ground = False
        elif (keys[pg.K_SPACE] or keys[pg.K_w]) and self.can_double_jump and not self.on_ground:
            self.vy = JUMP_STR * self.jump_mult
            self.can_double_jump = False
        self.move(self.vx, self.vy, platforms)
        # Reset double jump if landed
        if self.on_ground:
            self.can_double_jump = True
        # Prevent player from going outside the level boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
        if self.throwing:
            self.throwing.update()
            if self.throwing.ttl <= 0:
                self.throwing = None
                self.anim.update(16)
        # attack
        if pg.mouse.get_pressed()[0]:
            self.attack(enemies, now)
        # block
        if keys[pg.K_q] and self.weapon and self.weapon.type == "sword":
            self.block(now)
        if keys[pg.K_q] and self.weapon and self.weapon.type == "rapier":
            self.throw_rapier(now)
    def draw(self, surf):
        """
        Draw the player and health bar. Show invincibility feedback if active.
        """
        img = pg.transform.flip(self.anim.image(), self.facing < 0, False)
        if pg.time.get_ticks() < self.invincible_until:
            # Flicker effect for invincibility
            if (pg.time.get_ticks() // 100) % 2 == 0:
                img.set_alpha(128)
            else:
                img.set_alpha(255)
        else:
            img.set_alpha(255)
        surf.blit(img, self.rect)
        self.draw_bar(surf)
        if self.throwing:
            self.throwing.draw(surf)


class ThrownRapier:
    """
    Represents a thrown rapier projectile.
    """
    def __init__(self, pos, ang, dmg):
        """
        Initialize the thrown rapier.
        Args:
            pos (tuple): Starting position.
            ang (float): Angle in degrees.
            dmg (int): Damage value.
        """
        self.x, self.y = pos
        self.ang = ang
        self.dmg = dmg
        self.ttl = 90  # frames
        self.hit = False
    def update(self):
        """
        Move the projectile forward.
        """
        self.x += math.cos(math.radians(self.ang)) * THROWN_RAPIER_SPEED
        self.y += math.sin(math.radians(self.ang)) * THROWN_RAPIER_SPEED
        self.ttl -= 1
    def draw(self, surf):
        """
        Draw the rapier projectile as a line.
        """
        c = (255,255,255)
        end = (self.x + math.cos(math.radians(self.ang))*30,
               self.y + math.sin(math.radians(self.ang))*30)
        pg.draw.line(surf, c, (self.x, self.y), end, 4)

# ----------------------------- ENEMY & BOSS --------------------------
class Enemy(Entity):
    def has_line_of_sight(self, player, platforms):
        """
        Returns True if there is a clear line of sight between enemy and player (not blocked by platforms).
        """
        x1, y1 = self.rect.centerx, self.rect.centery
        x2, y2 = player.rect.centerx, player.rect.centery
        for p in platforms:
            if p.clipline((x1, y1), (x2, y2)):
                return False
        return True
    """
    Enemy character, inherits from Entity.
    """
    enemy_sprite = None  # class variable for sprite
    qmark_img = None  # class variable for question mark image
    def __init__(self, x, y, hp, dmg, colour):
        """
        Initialize an enemy.
        """
        super().__init__(x, y, 40, 50, hp, colour)
        self.dmg = dmg
        self.ai_timer = 0
        self.awareness = 0.0  # 0 to 5
        self.aware = False
        self.awareness_timer = 0
        self.awareness_gain = 0.0
        self.last_player_attack = 0
        if Enemy.qmark_img is None:
            try:
                Enemy.qmark_img = pg.image.load("assets/qmark.png").convert_alpha()
            except Exception as e:
                print("Failed to load qmark.png:", e)
                Enemy.qmark_img = None
    def ai(self, player, platforms):
        """
        Improved AI: enemies avoid walking off ledges and can jump.
        """
        self.ai_timer += 1
        # Awareness logic
        if not self.aware:
            px, py = player.rect.centerx, player.rect.centery
            ex, ey = self.rect.centerx, self.rect.centery
            dist = math.hypot(px-ex, py-ey)
            facing_vec = self.facing
            player_dir = 1 if px > ex else -1
            now = pg.time.get_ticks()
            los = self.has_line_of_sight(player, platforms)
            # Awareness field: reduced to 100px, and must have line of sight
            if ((player_dir != facing_vec) and (dist > 100 or not los)):
                self.awareness_gain = 0.0
                # Start timer for awareness decrease
                if not hasattr(self, 'awareness_lose_timer') or self.awareness_lose_timer is None:
                    self.awareness_lose_timer = now
                elif now - self.awareness_lose_timer > 3000:
                    self.awareness = max(0.0, self.awareness - 1.0/60.0)  # Lose awareness slowly
            else:
                if los and dist < 100:
                    self.awareness_gain = 1.0/60.0  # 1 per second
                    self.awareness_lose_timer = None
                else:
                    self.awareness_gain = 0.0
            # If attacked, instantly max awareness
            if self.last_player_attack and now - self.last_player_attack < 200:
                self.awareness = 5.0
            else:
                self.awareness += self.awareness_gain
            if self.awareness >= 5.0:
                self.aware = True
        # Ledge awareness: check if next step is a ledge
        step = int(self.vx/abs(self.vx)) if self.vx != 0 else 0
        if step != 0 and self.on_ground:
            test_rect = self.rect.move(step*2, 2)
            test_rect.y += self.rect.h//2
            on_platform = False
            for p in platforms:
                if p.colliderect(test_rect):
                    on_platform = True
                    break
            if not on_platform:
                self.vx = 0
        if self.aware:
            if self.ai_timer % 60 == 0:
                self.vx = random.choice([-1,0,1])
            if self.rect.centerx < player.rect.centerx: self.vx += 0.05
            else: self.vx -= 0.05
            self.vx = max(-1.5, min(1.5, self.vx))
            if random.random() < 0.005 and self.on_ground:
                self.vy = -8
        else:
            self.vx = 0
    def update(self, player, platforms):
        """
        Update enemy state, handle collisions, and apply fall damage.
        """
        self.ai(player, platforms)
        self.vy += GRAVITY
        prev_vy = self.vy
        prev_on_ground = self.on_ground
        self.move(self.vx, self.vy, platforms)
        # Fall damage: if just landed and was falling fast
        if not prev_on_ground and self.on_ground and prev_vy > 10:
            self.hp -= int((prev_vy-10)*2)
        # Only damage player if enemy is alive and player is alive
        if self.hp > 0 and player.hp > 0 and self.rect.colliderect(player.rect):
            if pg.time.get_ticks() >= getattr(player, 'invincible_until', 0):
                self.awareness = 5.0
                self.aware = True
                player.hp -= self.dmg
                self.rect.x += sign(self.rect.centerx - player.rect.centerx) * 30
    def draw(self, surf):
        """
        Draw the enemy and health bar.
        """
        if type(self).enemy_sprite:
            img = pg.transform.scale(type(self).enemy_sprite, (self.rect.w, self.rect.h))
            surf.blit(img, self.rect)
        else:
            pg.draw.rect(surf, self.colour, self.rect)
        # Awareness indicator: only show if currently gaining awareness
        if not self.aware and self.awareness_gain > 0 and Enemy.qmark_img:
            # Awareness fill: darken qmark from bottom up
            # Scale qmark to enemy width (max 1.2x width, keep aspect)
            scale_w = min(int(self.rect.w * 1.2), Enemy.qmark_img.get_width()*2)
            scale_h = int(scale_w * Enemy.qmark_img.get_height() / Enemy.qmark_img.get_width())
            qmark = pg.transform.smoothscale(Enemy.qmark_img, (scale_w, scale_h)).copy()
            fill = min(1.0, self.awareness/5.0)
            h = qmark.get_height()
            darken = pg.Surface((qmark.get_width(), int(h*fill)), pg.SRCALPHA)
            darken.fill((0,0,0,120))
            qmark.blit(darken, (0, h-int(h*fill)))
            surf.blit(qmark, (self.rect.centerx - qmark.get_width()//2, self.rect.top - qmark.get_height() - 8))
        self.draw_bar(surf)

class Boss(Enemy):
    """
    Boss enemy, inherits from Enemy.
    """
    boss_sprite = None  # class variable for boss sprite
    def __init__(self, x, y):
        """
        Initialize the boss enemy.
        """
        super().__init__(x, y, 300, 15, (150,50,255))
        self.rect.w, self.rect.h = 60, 80
        # Load boss sprite once
        if Boss.boss_sprite is None:
            try:
                Boss.boss_sprite = pg.image.load("assets/rock-boss.png").convert_alpha()
            except Exception as e:
                print("Failed to load boss sprite:", e)
                Boss.boss_sprite = None

    def draw(self, surf):
        """
        Draw the boss and health bar.
        """
        if type(self).boss_sprite:
            img = pg.transform.scale(type(self).boss_sprite, (self.rect.w, self.rect.h))
            surf.blit(img, self.rect)
        else:
            pg.draw.rect(surf, self.colour, self.rect)
        self.draw_bar(surf)

# ----------------------------- LEVELS ---------------------------------
try:
    Enemy.enemy_sprite = pg.image.load("assets/rock-monster.png").convert_alpha()
except Exception as e:
    print("Failed to load enemy sprite:", e)
    Enemy.enemy_sprite = None

class Stage:
    """
    Represents a game level (stage).
    """
    def __init__(self, num):
        """
        Initialize the stage with platforms, mobs, and drops.
        """
        self.num = num
        self.platforms = self.make_platforms()
        self.mobs: List[Enemy] = []
        self.drops: List[Item] = []
        self.portal = None  # Will be a Portal object
        self.boss_dead = False
        self.spawn_initial_mobs()
    def make_platforms(self):
        """
        Generate at least 6 platforms (excluding ground), each within max jump height and distance from the previous, with some randomization.
        """
        ground_height = 100
        base = [pg.Rect(0, HEIGHT - ground_height, WIDTH, ground_height)]
        min_platforms = 6
        max_jump = 160  # Player can jump about 160px
        max_dx = 260    # Max horizontal jump distance (tunable)
        min_dx = 80     # Min horizontal distance for variety
        min_dy = 80     # Min vertical gap for variety
        max_dy = max_jump
        min_dist = 60   # Minimum distance between any two platforms (horizontal or vertical)
        platforms = []
        prev_rect = base[0]
        y = HEIGHT - ground_height - random.randint(min_dy, max_dy)
        for i in range(min_platforms):
            tries = 0
            while True:
                w = random.randint(150, 300)
                dx = random.randint(min_dx, max_dx)
                if prev_rect.x < WIDTH // 2:
                    x = min(prev_rect.x + dx, WIDTH - w - 20)
                else:
                    x = max(prev_rect.x - dx, 20)
                y = max(y, 60)
                rect = pg.Rect(x, y, w, 20)
                # Check for overlap/too close to any previous platform
                too_close = False
                for p in platforms:
                    if abs(rect.y - p.y) < min_dy//2 and (rect.right > p.x and rect.x < p.right):
                        too_close = True
                        break
                    if abs(rect.x - p.x) < min_dist and abs(rect.y - p.y) < min_dist:
                        too_close = True
                        break
                if not too_close or tries > 10:
                    break
                tries += 1
                y -= 10  # try a bit higher if stuck
            platforms.append(rect)
            prev_rect = rect
            y -= random.randint(min_dy, max_dy)
        # Optionally add a few more random platforms for density, but enforce spacing
        extra = random.randint(0, 3)
        for _ in range(extra):
            tries = 0
            while True:
                px = random.randint(40, WIDTH-340)
                py = random.randint(60, HEIGHT-200)
                pw = random.randint(120, 260)
                rect = pg.Rect(px, py, pw, 20)
                too_close = False
                for p in platforms:
                    if abs(rect.y - p.y) < min_dy//2 and (rect.right > p.x and rect.x < p.right):
                        too_close = True
                        break
                    if abs(rect.x - p.x) < min_dist and abs(rect.y - p.y) < min_dist:
                        too_close = True
                        break
                if not too_close or tries > 10:
                    break
                tries += 1
        
            platforms.append(rect)
        # Always include ground
        all_platforms = base + platforms
        all_platforms.sort(key=lambda r: r.y)
        return all_platforms
    def spawn_initial_mobs(self):
        """
        Spawn the initial set of enemies for the stage.
        """
        for i in range(10):
            x = random.randint(100, WIDTH-100)
            y = 100
            self.mobs.append(Enemy(x, y, 40 + self.num*10, 5 + self.num*2, (200,200,50)))
    def spawn_boss(self):
        """
        Spawn the boss enemy for the stage.
        """
        self.mobs.append(Boss(WIDTH//2, 150))
    def update(self, player):
        """
        Update mobs, drops, and portal state for the stage.
        """
        # drop loot
        for m in self.mobs[:]:
            if m.hp <= 0:
                self.mobs.remove(m)
                player.xp += 5 + self.num*3
                # chance drop
                drop_item = None
                if isinstance(m, Boss):
                    drop_item = random_weapon("godlike")
                    self.boss_dead = True
                elif random.random() < 0.3:
                    if random.random() < 0.5:
                        drop_item = random_weapon()
                    else:
                        drop_item = random_armour_piece(random.choice(["helmet","chest","legs","boots"]))
                if drop_item:
                    drop_item.x, drop_item.y = m.rect.centerx, m.rect.centery
                    self.drops.append(drop_item)

        # Boss spawns only after all regular enemies are dead
        regular_enemies = [m for m in self.mobs if not isinstance(m, Boss)]
        if not self.boss_dead and len(regular_enemies) == 0 and not any(isinstance(m, Boss) for m in self.mobs):
            self.spawn_boss()
        # portal
        if self.boss_dead and not self.portal:
            self.portal = Portal(WIDTH-100, HEIGHT-100)
    def draw(self, surf):
        """
        Draw platforms, drops, portal, and enemies for the stage.
        """
        for i, p in enumerate(self.platforms):
            if floor_img:
                if i == 0:
                    # Ground: tile the image, only draw full tiles (no stretching, no cropping)
                    tile_w, tile_h = floor_img.get_width(), floor_img.get_height()
                    x_start = p.x
                    y_start = p.y
                    x_end = p.x + p.w
                    y_end = p.y + p.h
                    for x in range(x_start, x_end, tile_w):
                        for y in range(y_start, y_end, tile_h):
                            if x + tile_w <= x_end and y + tile_h <= y_end:
                                surf.blit(floor_img, (x, y))
                    # Optionally, fill the right/bottom edge with color if you want no gaps
                else:
                    # Platforms: stretch the image
                    stretched = pg.transform.scale(floor_img, (p.w, p.h))
                    surf.blit(stretched, (p.x, p.y))
            else:
                pg.draw.rect(surf, (100,100,120), p)
        for d in self.drops:
            d.draw(surf, d.x, d.y)
        if self.portal:
            self.portal.draw(surf)
        if self.portal:
            self.portal.update(1000//FPS)  # Update animation (dt in ms)
        # Draw all enemies on top
        for m in self.mobs:
            m.draw(surf)

dragging_item = None  # (item, from_slot)
drag_offset = (0, 0)
drag_pos = (0, 0)

# ----------------------------- ENTRY POINT ----------------------------
if __name__ == "__main__":
    # Only start the game if PLAY is clicked on the start screen
    show_game = show_start_screen()
    if show_game:
        run_game()
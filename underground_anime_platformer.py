import pygame as pg, math, random, sys, os
import json
from typing import List, Dict, Optional, Tuple
import glob, os
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
BLOCK_CD = 5000  # ms
BACKSTAB_DEG = 120  # deg behind enemy
DAGGER_RANGE = 90
SWORD_RANGE = 120
RAPIER_RANGE = 145
THROWN_RAPIER_SPEED = 12
FIST_RANGE=90
FIST_DAMAGE=4
FIST_SPEED=150
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
        pass
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Anime Underground Platformer")
clock = pg.time.Clock()
font20 = pg.font.SysFont("arial", 20)
font16 = pg.font.SysFont("arial", 16)

dragging_item = None  # (item, from_slot)
drag_offset = (0, 0)
drag_pos = (0, 0)

def draw_inventory(surf, player):
    """Draw the inventory UI, including items, armor, weapon, and shield."""
    margin, size = 20, 50
    startx, starty = 100, 100
    global dragging_item, drag_pos
    mouse_x, mouse_y = pg.mouse.get_pos()
    slot_rects = []
    for i in range(10):
        r = pg.Rect(startx + i*(size+margin), starty, size, size)
        slot_rects.append(r)
        pg.draw.rect(surf, (200,200,200), r, 3)
        if player.inventory[i] and (not dragging_item or dragging_item[1] != i):
            player.inventory[i].draw(surf, r.x+10, r.y+10, size-20)
        if i == player.selected:
            pg.draw.rect(surf, (255,255,0), r.inflate(8,8), 5)
    if dragging_item:
        item, from_slot = dragging_item
        item.draw(surf, mouse_x - drag_offset[0], mouse_y - drag_offset[1], size-20)
        r = pg.Rect(startx + i*(size+margin), starty, size, size)
        pg.draw.rect(surf, (200,200,200), r, 3)
        if player.inventory[i]:
            player.inventory[i].draw(surf, r.x+10, r.y+10, size-20)
        if i == player.selected:
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
# ----------- TAVERN SCREEN -----------
def show_tavern(screen, player):
    try:
        tavern_bg = pg.image.load("tavern.png").convert_alpha()
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
                    tavern_waiting = False
                    show_start_screen(player)
                    return
                if event.key == pg.K_e:
                    inv_open = not inv_open
                if offer_idx is not None and event.key == pg.K_RETURN:
                    # Accept offer: remove item, add coins, show message
                    item = player.inventory[offer_idx]
                    if item:
                        base = {"dagger": 15, "sword": 30, "rapier": 45}.get(item.type, 0)
                        rarity_bonus = {"common": 0, "uncommon": 0.15, "rare": 0.20, "holy": 0.25, "godlike": 0.30}.get(item.rarity, 0)
                        coins = int(base * (1 + rarity_bonus))
                        player.coins += coins
                        offer_msg = f"Sold for {coins} coins!"
                        player.inventory[offer_idx] = None
                        save_player_data(player)
                    offer_idx = None
            if inv_open and event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                # Right click: check if on an item
                mx, my = pg.mouse.get_pos()
                for i in range(10):
                    r = pg.Rect(startx + i*(size+margin), starty, size, size)
                    if r.collidepoint(mx, my) and player.inventory[i]:
                        offer_idx = i
                        offer_msg = None
                        break
        screen.fill((60,40,30))
        if tavern_bg:
            screen.blit(tavern_bg, (0,0))
        # Draw speech bubble above the guy in the image
        pg.draw.rect(screen, bubble_color, bubble_rect, border_radius=18)
        pg.draw.rect(screen, bubble_border, bubble_rect, width=3, border_radius=18)
        screen.blit(bubble_text, (bubble_rect.x+18, bubble_rect.y+18))
        # Draw inventory if open
        if inv_open:
            overlay = pg.Surface((WIDTH, HEIGHT), flags=pg.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            draw_inventory(screen, player)
            # Draw offer bubble if right-clicked
            if offer_idx is not None:
                r = pg.Rect(startx + offer_idx*(size+margin), starty, size, size)
                bubble = pg.Rect(r.x, r.y-40, 170, 32)
                pg.draw.rect(screen, (255,255,255), bubble, border_radius=10)
                pg.draw.rect(screen, (0,0,0), bubble, width=2, border_radius=10)
                txt = font16.render("want to offer this item?", True, (0,0,0))
                screen.blit(txt, (bubble.x+8, bubble.y+6))
            if offer_msg:
                msg_rect = pg.Rect(WIDTH//2-80, HEIGHT//2-100, 160, 32)
                pg.draw.rect(screen, (255,255,200), msg_rect, border_radius=10)
                pg.draw.rect(screen, (0,0,0), msg_rect, width=2, border_radius=10)
                txt = font16.render(offer_msg, True, (0,0,0))
                screen.blit(txt, (msg_rect.x+12, msg_rect.y+6))
        pg.display.flip()
        clock.tick(60)

# ----------- START SCREEN -----------
def show_start_screen(player):
    waiting = True
    """
    Display the start screen with a play button and wait for the user to click to start the game.
    """
    # Restore all start screen variables
    try:
        cover_img = pg.image.load("cover.png").convert_alpha()
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
        play_btn_img = pg.image.load("play-button.png").convert_alpha()
        play_btn_img = pg.transform.scale(play_btn_img, (button_w, button_h))
    except Exception as e:
        print("Failed to load play-button.png:", e)
        play_btn_img = None
    shake_phases = [0, 0, 0]
    while waiting:
        mouse_pos = pg.mouse.get_pos()
        hovered = [play_rect.collidepoint(mouse_pos), smeltery_rect.collidepoint(mouse_pos), tavern_rect.collidepoint(mouse_pos)]
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                if hovered[0]:
                    waiting = False
                if hovered[2]:
                    show_tavern(screen, player)
                    waiting = False
        if not waiting:
            break
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
            if play_btn_img:
                screen.blit(play_btn_img, shaken_rect)
            else:
                pg.draw.rect(screen, (255,255,0), shaken_rect, border_radius=18)
            outline_rect = shaken_rect.inflate(-4, -4)
            pg.draw.rect(screen, (0,0,0), outline_rect, width=7, border_radius=18)
            grass_green = (50, 200, 50)
            txt = font20.render(button_labels[i], True, grass_green)
            screen.blit(txt, (shaken_rect.x + shaken_rect.w//2 - txt.get_width()//2, shaken_rect.y + shaken_rect.h//2 - txt.get_height()//2))
        pg.display.flip()
        clock.tick(60)
    if not waiting:
        return
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
            if play_btn_img:
                screen.blit(play_btn_img, shaken_rect)
            else:
                pg.draw.rect(screen, (255,255,0), shaken_rect, border_radius=18)
            outline_rect = shaken_rect.inflate(-4, -4)
            pg.draw.rect(screen, (0,0,0), outline_rect, width=7, border_radius=18)
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
        if self.type == "dagger": return 6
        if self.type == "sword": return 10
        if self.type == "rapier": return 14
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
                    Item.dagger_sprite = pg.image.load("dagger.png").convert_alpha()
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
                    Item.sword_sprite = pg.image.load("sword.png").convert_alpha()
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
                    Item.rapier_sprite = pg.image.load("rapier.png").convert_alpha()
                except Exception as e:
                    print("Failed to load rapier sprite:", e)
                    Item.rapier_sprite = None
            if Item.rapier_sprite:
                img = pg.transform.scale(Item.rapier_sprite, (size, size))
                surf.blit(img, (x, y))
            else:
                pg.draw.rect(surf, c, (x, y, size, size//3))
        else:  # armour piece
            # Ninja armor sprites
            ninja_sprites = {
                "helmet": "ninja-helmet.png",
                "chest": "ninja-chestplate.png",
                "legs": "ninja-legs.png",
                "boots": "ninja-boots.png"
            }
            prefix = self.name.split()[0] if self.name else ""
            slot = self.type
            sprite_attr = f"ninja_{slot}_sprite"
            if prefix == "ninja" and slot in ninja_sprites:
                if not hasattr(Item, sprite_attr):
                    try:
                        setattr(Item, sprite_attr, pg.image.load(ninja_sprites[slot]).convert_alpha())
                    except Exception as e:
                        print(f"Failed to load {ninja_sprites[slot]}: {e}")
                        setattr(Item, sprite_attr, None)
                sprite = getattr(Item, sprite_attr, None)
                if sprite:
                    img = pg.transform.scale(sprite, (size, size))
                    surf.blit(img, (x, y))
                else:
                    pg.draw.circle(surf, c, (x+size//2, y+size//2), size//2)
            else:
                pg.draw.circle(surf, c, (x+size//2, y+size//2), size//2)
        txt = font16.render(self.rarity[0].upper(), True, (0,0,0))
        surf.blit(txt, (x+4, y+4))

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
    def to_dict(self):
        return {
            'xp': self.xp,
            'coins': self.coins,
            'inventory': [item.to_dict() if item else None for item in self.inventory],
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
        self.anim = AnimSprite("/home/matej/anime-game/Kunoichi/*.png", fps=10)
        self.can_double_jump = True
    def from_dict(self, data):
        self.xp = data.get('xp', 0)
        self.coins = data.get('coins', 0)
        inv = data.get('inventory', [None]*10)
        self.inventory = [Item.from_dict(it) if it else None for it in inv]
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
        self.anim = AnimSprite("/home/matej/anime-game/Kunoichi/*.png", fps=10)
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
            return
        if now - self.last_attack < self.weapon.ataack_speed: return
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
                    dmg += self.dagger_bonus + 4
        # apply
        for e in enemies:
            if dist(self.rect.center, e.rect.center) < r + e.rect.w//2:
                e.hp -= dmg
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
        # input
        keys = pg.key.get_pressed()
        self.vx = (keys[pg.K_d]-keys[pg.K_a]) * MOVE_SPEED * self.speed_mult
        # attack
        if pg.mouse.get_pressed()[0]:
            self.attack(enemies, now)
        # block
        if keys[pg.K_q] and self.weapon and self.weapon.type=="sword":
            self.block(now)
        if keys[pg.K_q] and self.weapon and self.weapon.type=="rapier":
            self.throw_rapier(now)
    def draw(self, surf):
        """
        Draw the player and health bar.
        """
        surf.blit(pg.transform.flip(self.anim.image(), self.facing < 0, False), self.rect)
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
    """
    Enemy character, inherits from Entity.
    """
    enemy_sprite = None  # class variable for sprite
    def __init__(self, x, y, hp, dmg, colour):
        """
        Initialize an enemy.
        """
        super().__init__(x, y, 40, 50, hp, colour)
        self.dmg = dmg
        self.ai_timer = 0
    def ai(self, player, platforms):
        """
        Simple AI movement logic for the enemy.
        """
        self.ai_timer += 1
        if self.ai_timer % 60 == 0:
            self.vx = random.choice([-1,0,1])  # slower movement
        if self.rect.centerx < player.rect.centerx: self.vx += 0.05
        else: self.vx -= 0.05
        self.vx = max(-1.5, min(1.5, self.vx))
        if random.random() < 0.005 and self.on_ground:
            self.vy = -8
    def update(self, player, platforms):
        """
        Update enemy state and handle collisions.
        """
        self.ai(player, platforms)
        self.vy += GRAVITY
        self.move(self.vx, self.vy, platforms)
        if self.rect.colliderect(player.rect):
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
                Boss.boss_sprite = pg.image.load("rock-boss.png").convert_alpha()
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
    Enemy.enemy_sprite = pg.image.load(os.path.join("rock-monster", "rock-monster.png")).convert_alpha()
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
        self.portal = None
        self.boss_dead = False
        self.spawn_initial_mobs()
    def make_platforms(self):
        """
        Generate platforms for the level.
        """
        base = [pg.Rect(0, HEIGHT-40, WIDTH, 40)]
        min_gap = 140  # Increased gap for easier jumping between floors
        platforms = []
        attempts = 0
        while len(platforms) < 14 and attempts < 100:
            x = random.randint(100, WIDTH-200)
            y = random.randint(200, HEIGHT-100)
            w = random.randint(150, 300)
            new_rect = pg.Rect(x, y, w, 20)
            # Ensure vertical gap from all other platforms
            too_close = False
            for p in base + platforms:
                if abs(new_rect.y - p.y) < min_gap:
                    too_close = True
                    break
            if not too_close:
                platforms.append(new_rect)
            attempts += 1
        base.extend(platforms)
        return base
    def spawn_initial_mobs(self):
        """
        Spawn the initial set of enemies for the stage.
        """
        for i in range(10):
            x = random.randint(100, WIDTH-100)
            self.mobs.append(Enemy(x, 100, 40 + self.num*10, 5 + self.num*2, (200,200,50)))
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
            self.portal = pg.Rect(WIDTH-100, HEIGHT-100, 60, 80)
    def draw(self, surf):
        """
        Draw platforms, drops, and portal for the stage.
        """
        for p in self.platforms:
            pg.draw.rect(surf, (100,100,120), p)
        for d in self.drops:
            d.draw(surf, d.x, d.y)
        if self.portal:
            pg.draw.rect(surf, (255,255,0), self.portal)

# ----------------------------- INVENTORY ------------------------------
dragging_item = None  # (item, from_slot)
drag_offset = (0, 0)
drag_pos = (0, 0)

def draw_inventory(surf, player):
    """
    Draw the inventory UI, including items, armor, weapon, and shield.
    """
    margin, size = 20, 50
    startx, starty = 100, 100
    # 10 slots    
    global dragging_item, drag_pos
    mouse_x, mouse_y = pg.mouse.get_pos()
    slot_rects = []
    for i in range(10):
        r = pg.Rect(startx + i*(size+margin), starty, size, size)
        slot_rects.append(r)
        pg.draw.rect(surf, (200,200,200), r, 3)
        # Draw item if not being dragged
        if player.inventory[i] and (not dragging_item or dragging_item[1] != i):
            player.inventory[i].draw(surf, r.x+10, r.y+10, size-20)
        if i == player.selected:
            pg.draw.rect(surf, (255,255,0), r.inflate(8,8), 5)
    # Draw dragged item on top
    if dragging_item:
        item, from_slot = dragging_item
        item.draw(surf, mouse_x - drag_offset[0], mouse_y - drag_offset[1], size-20)
        r = pg.Rect(startx + i*(size+margin), starty, size, size)
        pg.draw.rect(surf, (200,200,200), r, 3)
        if player.inventory[i]:
            player.inventory[i].draw(surf, r.x+10, r.y+10, size-20)
        if i == player.selected:
            # Thicker, more visible outline for selected slot
            pg.draw.rect(surf, (255,255,0), r.inflate(8,8), 5)
    # --- Miniature player figure and armor/shield slots ---
    center_x = WIDTH // 2
    center_y = HEIGHT // 2 + 40
    mini_size = 90
    # Draw player figure (miniature)
    mini_rect = pg.Rect(center_x-25, center_y-45, 50, 90)
    try:
        surf.blit(pg.transform.scale(player.anim.image(), (50, 90)), mini_rect)
    except Exception:
        pg.draw.rect(surf, (255,100,100), mini_rect)

    # Armor slots (left side, vertically aligned)
    armor_slots = ["helmet", "chest", "legs", "boots"]
    for idx, slot in enumerate(armor_slots):
        slot_y = center_y - 40 + idx*45
        slot_rect = pg.Rect(center_x-80, slot_y, 40, 40)
        pg.draw.rect(surf, (150,150,150), slot_rect, 3)
        if player.armor[slot]:
            player.armor[slot].draw(surf, slot_rect.x+5, slot_rect.y+5, 30)
        # Label
        label = font16.render(slot[0].upper(), True, (180,180,180))
        surf.blit(label, (slot_rect.x-18, slot_rect.y+12))

    # Shield slot (right side, centered vertically)
    shield_rect = pg.Rect(center_x+40, center_y-10, 40, 40)
    pg.draw.rect(surf, (100,100,255), shield_rect, 3)
    if player.shield:
        player.shield.draw(surf, shield_rect.x+5, shield_rect.y+5, 30)
    surf.blit(font16.render("S", True, (180,180,255)), (shield_rect.x+48, shield_rect.y+12))
    # info
    # Move XP and 'E to close' text below the inventory grid
    grid_bottom = starty + size + 20  # 1 row, add some margin
    tx = startx
    surf.blit(font20.render(f"XP: {player.xp}", True, (255,255,255)), (tx, grid_bottom))
    surf.blit(font20.render("E to close", True, (255,255,255)), (tx, grid_bottom + 30))

def inventory_input(event, player):
    """
    Handles inventory controls: selecting, picking up, upgrading, equipping, and scrolling items.
    """
    # Mouse wheel scroll to change selected slot
    if event.type == pg.MOUSEWHEEL:
        player.selected = (player.selected - event.y) % 10
    if event.type == pg.KEYDOWN:
        if pg.K_1 <= event.key <= pg.K_0:
            idx = (event.key - pg.K_1) % 10
            player.selected = idx
        if event.key == pg.K_i or event.key == pg.K_SPACE:
            # pick up
            for d in stage.drops[:]:
                if dist(player.rect.center, (d.x, d.y)) < 60:
                    for i, it in enumerate(player.inventory):
                        if it is None:
                            player.inventory[i] = d
                            stage.drops.remove(d)
                            break
        if event.key == pg.K_u:
            # upgrade selected
            sel = player.inventory[player.selected]
            if sel and player.xp >= 10:
                sel.upgrade()
                player.xp -= 10
        if event.key == pg.K_e:
            # equip/unequip only if selected slot is not None
            sel = player.inventory[player.selected]
            if sel:
                if sel.type in ("dagger","sword","rapier"):
                    # Only swap if the inventory slot is not None
                    if player.weapon is not None:
                        player.inventory[player.selected], player.weapon = player.weapon, sel
                    else:
                        player.weapon = sel
                        player.inventory[player.selected] = None
                elif sel.type in ("helmet","chest","legs","boots"):
                    old = player.armor[sel.type]
                    player.armor[sel.type] = sel
                    player.inventory[player.selected] = old
                    player.calc_set_bonus()

player = Player(100, HEIGHT-200)
load_player_data(player)
stage = Stage(1)

show_start_screen(player)

running = True
while running:
    for e in pg.event.get():
        if e.type == pg.QUIT:
            running = False
        # Always allow toggling inventory with E
        if e.type == pg.KEYDOWN and e.key == pg.K_e:
            player.inv_open = not player.inv_open
        # Handle jump and double jump on W key press (event-based)
        if not player.inv_open and e.type == pg.KEYDOWN and e.key == pg.K_w:
            if player.on_ground:
                player.vy = JUMP_STR * player.jump_mult
            elif player.can_double_jump:
                player.vy = JUMP_STR * player.jump_mult
                player.can_double_jump = False
        # Inventory open: handle drag/drop and inventory input
        if player.inv_open:
            margin, size = 20, 50
            startx, starty = 100, 100
            slot_rects = [pg.Rect(startx + i*(size+margin), starty, size, size) for i in range(10)]
            if e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(slot_rects):
                    if r.collidepoint(e.pos) and player.inventory[i]:
                        dragging_item = (player.inventory[i], i)
                        drag_offset = (e.pos[0] - r.x, e.pos[1] - r.y)
                        drag_pos = e.pos
                        player.inventory[i] = None
                        break
            elif e.type == pg.MOUSEBUTTONUP and e.button == 1 and dragging_item:
                dropped = False
                for i, r in enumerate(slot_rects):
                    if r.collidepoint(e.pos):
                        if not player.inventory[i]:
                            player.inventory[i] = dragging_item[0]
                            dropped = True
                        else:
                            # Swap items
                            player.inventory[dragging_item[1]] = player.inventory[i]
                            player.inventory[i] = dragging_item[0]
                            dropped = True
                        break
                if not dropped:
                    player.inventory[dragging_item[1]] = dragging_item[0]
                dragging_item = None
            elif e.type == pg.MOUSEMOTION and dragging_item:
                drag_pos = e.pos
            else:
                inventory_input(e, player)
        # Inventory closed: allow picking up items with Space
        elif e.type == pg.KEYDOWN and e.key == pg.K_SPACE:
            for d in stage.drops[:]:
                if player.rect.colliderect(pg.Rect(d.x, d.y, 30, 30)):
                    for i, it in enumerate(player.inventory):
                        if it is None:
                            player.inventory[i] = d
                            stage.drops.remove(d)
                            break
        # Mouse wheel scroll always changes selected slot
        if e.type == pg.MOUSEWHEEL:
            player.selected = (player.selected - e.y) % 10

    if not player.inv_open:
        # Game updates only when inventory is closed
        now = pg.time.get_ticks()
        player.update(stage.platforms, stage.mobs, now)
        for m in stage.mobs:
            m.update(player, stage.platforms)
        stage.update(player)
        # next stage
        if stage.portal and player.rect.colliderect(stage.portal):
            if stage.num == 5:
                print("YOU REACHED THE SURFACE – YOU WIN!")
                running = False
                continue
            stage = Stage(stage.num+1)
            player.rect.topleft = (100, HEIGHT-200)
        # death
        if player.hp <= 0:
            print("GAME OVER")
            save_player_data(player)
            show_start_screen(player)
            # Re-initialize game state after returning from start screen
            player = Player(100, HEIGHT-200)
            load_player_data(player)
            stage = Stage(1)
            continue
pg.quit()
sys.exit()

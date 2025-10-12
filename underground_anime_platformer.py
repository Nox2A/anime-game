import pygame as pg, math, random, sys, os
from typing import List, Dict, Optional, Tuple
import glob, os
class AnimSprite:
    def __init__(self, folder: str, fps=10, loop=True):
        # folder contains 32×32 PNGs – already sliced
        self.frames = [pg.image.load(f).convert_alpha() for f in sorted(glob.glob(folder))]
        self.timer = 0
        self.idx = 0
        self.fps = fps
        self.loop = loop
    def update(self, dt):
        self.timer += dt
        if self.timer > 1000/self.fps:
            self.timer = 0
            next_idx = self.idx + 1
            if next_idx >= len(self.frames):
                next_idx = 0 if self.loop else len(self.frames)-1
            self.idx = next_idx
    def image(self): return self.frames[self.idx]
# ----------------------------- CONFIG ---------------------------------
WIDTH, HEIGHT = 1200, 700
FPS = 60
GRAVITY = 0.6
JUMP_STR = -14
MOVE_SPEED = 5
BLOCK_CD = 5000  # ms
BACKSTAB_DEG = 120  # deg behind enemy
DAGGER_RANGE = 70
SWORD_RANGE = 90
RAPIER_RANGE = 110
THROWN_RAPIER_SPEED = 12
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
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Anime Underground Platformer")
clock = pg.time.Clock()
font20 = pg.font.SysFont("arial", 20)
font16 = pg.font.SysFont("arial", 16)

def sign(x): return 1 if x > 0 else -1 if x < 0 else 0
def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])
def angle(a, b): return math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))

# ----------------------------- ITEMS ----------------------------------
class Item:
    def __init__(self, name: str, type_: str, rarity: str):
        self.name = name
        self.type = type_  # dagger/sword/rapier/helmet/chest/legs/boots
        self.rarity = rarity
        self.dmg = self.base_dmg()
        self.attack_speed = self.base_as()
    def base_dmg(self):
        if self.type == "dagger": return 6
        if self.type == "sword": return 10
        if self.type == "rapier": return 14
        return 0
    def base_as(self):
        if self.type == "dagger": return 200  # ms
        if self.type == "sword": return 400
        if self.type == "rapier": return 500
        return 0
    def upgrade(self):
        order = ["common","uncommon","rare","holy","godlike"]
        idx = order.index(self.rarity)
        if idx < len(order)-1:
            self.rarity = order[idx+1]
            self.dmg = int(self.dmg * 1.5)
            self.attack_speed = int(self.attack_speed * 0.9)
    def colour(self): return RARITY_COL[self.rarity]
    def draw(self, surf, x, y, size=30):
        c = self.colour()
        if self.type in ("dagger","sword","rapier"):
            pg.draw.rect(surf, c, (x, y, size, size//3))
        else:  # armour piece
            pg.draw.circle(surf, c, (x+size//2, y+size//2), size//2)
        txt = font16.render(self.rarity[0].upper(), True, (0,0,0))
        surf.blit(txt, (x+4, y+4))

def random_weapon(rarity: Optional[str]=None) -> Item:
    if rarity is None:
        r = random.choices(["common","uncommon","rare","holy","godlike"],
                           weights=[50,30,15,4,1])[0]
    else: r = rarity
    t = random.choice(["dagger","sword","rapier"])
    return Item(t, t, r)

def random_armour_piece(slot: str, rarity: Optional[str]=None) -> Item:
    if rarity is None:
        r = random.choices(["common","uncommon","rare","holy","godlike"],
                           weights=[50,30,15,4,1])[0]
    else: r = rarity
    name = random.choice(["ninja","knight","mage"]) + " " + slot
    return Item(name, slot, r)

# ----------------------------- ENTITY ---------------------------------
class Entity:
    def __init__(self, x, y, w, h, hp, colour):
        self.rect = pg.Rect(x, y, w, h)
        self.vx, self.vy = 0, 0
        self.hp = self.max_hp = hp
        self.colour = colour
        self.facing = 1
        self.on_ground = False
    def draw_bar(self, surf, off=-20):
        pg.draw.rect(surf, (50,50,50), (self.rect.x-10, self.rect.y+off, self.rect.w+20, 6))
        pg.draw.rect(surf, (0,200,0), (self.rect.x-10, self.rect.y+off,
                                        int((self.rect.w+20)*(self.hp/self.max_hp)), 6))
    def move(self, dx, dy, platforms):
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
    def __init__(self, x, y):
        super().__init__(x, y, 40, 60, 100, (255,100,100))
        self.xp = 0
        self.inventory: List[Optional[Item]] = [None]*10
        self.armor: Dict[str, Optional[Item]] = {"helmet":None,"chest":None,"legs":None,"boots":None}
        self.weapon: Optional[Item] = None
        self.shield: Optional[Item] = None
        self.last_attack = 0
        self.block_cd = 0
        self.throwing = None  # rapier projectile
        self.inv_open = False
        self.selected = 0  # inventory index
        self.dual = False
        self.speed_mult = 1
        self.jump_mult = 1
        self.dagger_bonus = 0
        self.calc_set_bonus()
        self.anim = AnimSprite("/home/matej/anime-game/Kunoichi/*.png", fps=10)
    def calc_set_bonus(self):
        sets = {}
        for slot, it in self.armor.items():
            if it is None: continue
            prefix = it.name.split()[0]
            sets[prefix] = sets.get(prefix,0)+1
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
        if not self.weapon: return
        if now - self.last_attack < self.weapon.attack_speed: return
        self.last_attack = now
        mx, my = pg.mouse.get_pos()
        ang = angle(self.rect.center, (mx, my))
        r = {"dagger":DAGGER_RANGE,"sword":SWORD_RANGE,"rapier":RAPIER_RANGE}[self.weapon.type]
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
        if now - self.block_cd < BLOCK_CD: return False
        if not self.weapon or self.weapon.type != "sword": return False
        self.block_cd = now
        return True
    def throw_rapier(self, now):
        if not self.weapon or self.weapon.type != "rapier": return
        if self.throwing: return
        mx, my = pg.mouse.get_pos()
        ang = angle(self.rect.center, (mx, my))
        self.throwing = ThrownRapier(self.rect.center, ang, self.weapon.dmg*2)
    def update(self, platforms, enemies, now):
        self.vy += GRAVITY
        self.move(self.vx, self.vy, platforms)
        if self.throwing:
            self.throwing.update()
            if self.throwing.ttl <= 0:
                self.throwing = None
                self.anim.update(16)
        # input
        keys = pg.key.get_pressed()
        self.vx = (keys[pg.K_d]-keys[pg.K_a]) * MOVE_SPEED * self.speed_mult
        if keys[pg.K_w] and self.on_ground:
            self.vy = JUMP_STR * self.jump_mult
        # attack
        if pg.mouse.get_pressed()[0]:
            self.attack(enemies, now)
        # block
        if keys[pg.K_q] and self.weapon and self.weapon.type=="sword":
            self.block(now)
        if keys[pg.K_q] and self.weapon and self.weapon.type=="rapier":
            self.throw_rapier(now)
    def draw(self, surf):
        surf.blit(pg.transform.flip(self.anim.image(), self.facing < 0, False), self.rect)
        self.draw_bar(surf)
        if self.throwing:
            self.throwing.draw(surf)

class ThrownRapier:
    def __init__(self, pos, ang, dmg):
        self.x, self.y = pos
        self.ang = ang
        self.dmg = dmg
        self.ttl = 90  # frames
        self.hit = False
    def update(self):
        self.x += math.cos(math.radians(self.ang)) * THROWN_RAPIER_SPEED
        self.y += math.sin(math.radians(self.ang)) * THROWN_RAPIER_SPEED
        self.ttl -= 1
    def draw(self, surf):
        c = (255,255,255)
        end = (self.x + math.cos(math.radians(self.ang))*30,
               self.y + math.sin(math.radians(self.ang))*30)
        pg.draw.line(surf, c, (self.x, self.y), end, 4)

class Enemy(Entity):
    def __init__(self, x, y, hp, dmg, colour):
        super().__init__(x, y, 40, 50, hp, colour)
        self.dmg = dmg
        self.ai_timer = 0
    def ai(self, player, platforms):
        self.ai_timer += 1
        if self.ai_timer % 60 == 0:
            self.vx = random.choice([-2,0,2])
        if self.rect.centerx < player.rect.centerx: self.vx += 0.1
        else: self.vx -= 0.1
        self.vx = max(-3, min(3, self.vx))
        if random.random() < 0.01 and self.on_ground:
            self.vy = -10
    def update(self, player, platforms):
        self.ai(player, platforms)
        self.vy += GRAVITY
        self.move(self.vx, self.vy, platforms)
        if self.rect.colliderect(player.rect):
            player.hp -= self.dmg
            self.rect.x += sign(self.rect.centerx - player.rect.centerx) * 30

class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 300, 15, (150,50,255))
        self.rect.w, self.rect.h = 60, 80

# ----------------------------- LEVELS ---------------------------------
class Stage:
    def __init__(self, num):
        self.num = num
        self.platforms = self.make_platforms()
        self.mobs: List[Enemy] = []
        self.drops: List[Item] = []
        self.portal = None
        self.boss_dead = False
        self.spawn_mobs()
    def make_platforms(self):
        base = [pg.Rect(0, HEIGHT-40, WIDTH, 40)]
        # simple random platforms
        for i in range(8):
            x = random.randint(100, WIDTH-200)
            y = random.randint(200, HEIGHT-100)
            w = random.randint(150, 300)
            base.append(pg.Rect(x, y, w, 20))
        return base
    def spawn_mobs(self):
        for i in range(6 + self.num*2):
            x = random.randint(100, WIDTH-100)
            self.mobs.append(Enemy(x, 100, 40 + self.num*10, 5 + self.num*2, (200,200,50)))
        # miniboss
        self.mobs.append(Enemy(WIDTH//2, 200, 80 + self.num*20, 10, (255,150,0)))
    def spawn_boss(self):
        self.mobs.append(Boss(WIDTH//2, 150))
    def update(self, player):
        # drop loot
        for m in self.mobs[:]:
            if m.hp <= 0:
                self.mobs.remove(m)
                player.xp += 5 + self.num*3
                # chance drop
                if isinstance(m, Boss):
                    self.drops.append(random_weapon("godlike"))
                    self.boss_dead = True
                elif random.random() < 0.3:
                    if random.random() < 0.5:
                        self.drops.append(random_weapon())
                    else:
                        self.drops.append(random_armour_piece(random.choice(["helmet","chest","legs","boots"])))
        # boss spawn
        if not self.mobs and not self.boss_dead:
            self.spawn_boss()
        # portal
        if self.boss_dead and not self.portal:
            self.portal = pg.Rect(WIDTH-100, HEIGHT-100, 60, 80)
    def draw(self, surf):
        for p in self.platforms:
            pg.draw.rect(surf, (100,100,120), p)
        for d in self.drops:
            d.draw(surf, d.x, d.y)
        if self.portal:
            pg.draw.rect(surf, (255,255,0), self.portal)

# ----------------------------- INVENTORY ------------------------------
def draw_inventory(surf, player):
    margin, size = 20, 50
    startx, starty = 100, 100
    # 10 slots
    for i in range(10):
        r = pg.Rect(startx + i*(size+margin), starty, size, size)
        pg.draw.rect(surf, (200,200,200), r, 3)
        if player.inventory[i]:
            player.inventory[i].draw(surf, r.x+10, r.y+10, size-20)
        if i == player.selected:
            pg.draw.rect(surf, (255,255,0), r, 4)
    # armour
    arm_y = starty + 100
    for idx, slot in enumerate(["helmet","chest","legs","boots"]):
        r = pg.Rect(startx + idx*(size+margin), arm_y, size, size)
        pg.draw.rect(surf, (150,150,150), r, 3)
        if player.armor[slot]:
            player.armor[slot].draw(surf, r.x+10, r.y+10, size-20)
    # weapon/shield
    w_r = pg.Rect(startx + 5*(size+margin), arm_y, size, size)
    pg.draw.rect(surf, (255,100,100), w_r, 3)
    if player.weapon:
        player.weapon.draw(surf, w_r.x+10, w_r.y+10, size-20)
    s_r = pg.Rect(startx + 6*(size+margin), arm_y, size, size)
    pg.draw.rect(surf, (100,100,255), s_r, 3)
    if player.shield:
        player.shield.draw(surf, s_r.x+10, s_r.y+10, size-20)
    # info
    tx = startx + 8*(size+margin)
    surf.blit(font20.render(f"XP: {player.xp}", True, (255,255,255)), (tx, starty))
    surf.blit(font20.render("E to close", True, (255,255,255)), (tx, starty+30))

def inventory_input(event, player):
    if event.type == pg.KEYDOWN:
        if pg.K_1 <= event.key <= pg.K_0:
            idx = (event.key - pg.K_1) % 10
            player.selected = idx
        if event.key == pg.K_i:
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
            # equip/unequip
            sel = player.inventory[player.selected]
            if sel:
                if sel.type in ("dagger","sword","rapier"):
                    player.weapon, player.inventory[player.selected] = sel, player.weapon
                elif sel.type in ("helmet","chest","legs","boots"):
                    old = player.armor[sel.type]
                    player.armor[sel.type], player.inventory[player.selected] = sel, old
                    player.calc_set_bonus()

# ----------------------------- MAIN LOOP ------------------------------
player = Player(100, HEIGHT-200)
stage = Stage(1)
running = True
while running:
    now = pg.time.get_ticks()
    for e in pg.event.get():
        if e.type == pg.QUIT: running = False
        if player.inv_open:
            inventory_input(e, player)
        if e.type == pg.KEYDOWN and e.key == pg.K_e:
            player.inv_open = not player.inv_open
    # update
    if not player.inv_open:
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
        running = False
    # draw
    screen.fill((30,30,40))
    stage.draw(screen)
    player.draw(screen)
    for m in stage.mobs:
        pg.draw.rect(screen, m.colour, m.rect)
        m.draw_bar(screen)
    if player.inv_open:
        draw_inventory(screen, player)
    # quick bar
    if not player.inv_open:
        y = HEIGHT-60
        for i in range(10):
            r = pg.Rect(10 + i*55, y, 50, 50)
            pg.draw.rect(screen, (200,200,200), r, 2)
            if player.inventory[i]:
                player.inventory[i].draw(screen, r.x+5, r.y+5, 40)
    pg.display.flip()
    clock.tick(FPS)

pg.quit()
sys.exit()

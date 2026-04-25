"""
╔══════════════════════════════════════════════════════════╗
║          🗡  STICKMAN MAZE COMBAT  🗡                    ║
║  Run:  python finish_main.py                             ║
║  Deps: pip install pygame opencv-python numpy            ║
║  F11 → toggle fullscreen                                 ║
╚══════════════════════════════════════════════════════════╝
Controls – MAZE:
  SPACE / click dice = roll
  Arrow keys = move (one step per key-press, uses dice steps)
Controls – COMBAT:
  A/D = move  |  W = jump  |  SPACE = attack
End screens: R = restart  |  Q = quit
"""

import pygame, pygame.gfxdraw, sys, os, math, time, random, collections, heapq

from maze_game.maze.dfs_generator import generate_maze_dfs
from maze_game.maze.a_star_solver import astar_solver
from maze_game.movement.bfs import bfs_reachable_tiles
from maze_game.movement.constraints import csp_valid_moves
from maze_game.core.spawn_logic import spawn_goal_tree
from maze_game.core.combat_ai import hill_climbing_movement, forward_chaining_combat
from maze_game.core.state_logic import evaluate_game_state, S_MENU, S_MODE, S_MAZE, S_COMBAT, S_OVER, S_WIN

try:
    import cv2, numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# ── Asset Paths ────────────────────────────────────────────
_BASE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maze_game", "assets")
DICE_DIR = os.path.join(_BASE, "images", "dice")
MAZE_DIR = os.path.join(_BASE, "images", "maze")
VID_PATH = os.path.join(_BASE, "videos", "dice_roll.mp4")

# ── Canvas ─────────────────────────────────────────────────
CW, CH     = 1280, 720
SIDEBAR_W  = 300
MAZE_W     = CW - SIDEBAR_W   # 980
MAZE_H     = CH
SIDEBAR_X  = MAZE_W

MAZE_COLS, MAZE_ROWS = 21, 17  # must be odd
TILE = min(MAZE_W // MAZE_COLS, MAZE_H // MAZE_ROWS)  # 42
MPW  = TILE * MAZE_COLS
MPH  = TILE * MAZE_ROWS
MOX  = (MAZE_W - MPW) // 2
MOY  = (MAZE_H - MPH) // 2

FPS = 60

# ── Physics ────────────────────────────────────────────────
GRAV, JF, FRIC, MAXFALL = 0.55, -13, 0.80, 16
PSPD, ESPD = 4.5, 2.8

# ── Colours ────────────────────────────────────────────────
BG          = (  8,   8,  16)
WHITE       = (240, 240, 250)
YELLOW      = (255, 215,  50)
CYAN        = ( 50, 220, 230)
BLUE        = ( 60, 130, 255)
RED         = (220,  50,  50)
GREEN       = ( 50, 200,  80)
ORANGE      = (240, 130,  30)
PURPLE      = (160,  60, 200)
GOLD        = (255, 200,  50)
SIDEBAR_BG  = ( 14,  14,  28)
SIDEBAR_SEP = ( 48,  48,  72)

# ── Difficulty Config ──────────────────────────────────────
DIFFICULTIES = {
    "Easy":   {"player_hp":150, "enemy_hp":80,  "dmg_mult":0.7,  "enemy_speed": 2.0, "label":"Easy",   "col":(50,220,80),   "desc":"More HP · Weaker enemies · Forgiving"},
    "Medium": {"player_hp":120, "enemy_hp":120, "dmg_mult":1.0,  "enemy_speed": 2.8, "label":"Medium", "col":(255,215,50),  "desc":"Balanced · Default experience"},
    "Hard":   {"player_hp":90,  "enemy_hp":160, "dmg_mult":1.35, "enemy_speed": 3.8, "label":"Tough",  "col":(220,50,50),   "desc":"Low HP · Tough enemies · High risk"},
}

# ── Game States ────────────────────────────────────────────
# (Imported from maze_game.core.state_logic)

# ── Font Cache ─────────────────────────────────────────────
_fc = {}
def font(sz, bold=False):
    k=(sz,bold)
    if k not in _fc:
        try:    _fc[k]=pygame.font.SysFont("segoeui",sz,bold=bold)
        except: _fc[k]=pygame.font.SysFont(None,sz,bold=bold)
    return _fc[k]

def txt(surf, t, sz, col, cx, cy, bold=False):
    s=font(sz,bold).render(str(t),True,col)
    surf.blit(s,s.get_rect(center=(cx,cy)))
    return s.get_rect(center=(cx,cy))

def txt_tl(surf, t, sz, col, x, y, bold=False):
    s=font(sz,bold).render(str(t),True,col)
    surf.blit(s,(x,y))

def rrect(surf, col, rect, r=8, w=0):
    pygame.draw.rect(surf, col, rect, w, border_radius=r)

def sep_line(surf, y):
    pygame.draw.line(surf,SIDEBAR_SEP,(SIDEBAR_X+8,y),(CW-8,y),1)

def hp_bar(surf, x, y, w, h, cur, mx, label="", lcol=WHITE):
    ratio=max(0,min(1,cur/mx))
    rrect(surf,(35,10,10),(x,y,w,h),5)
    if ratio>0:
        c=GREEN if ratio>.5 else YELLOW if ratio>.25 else RED
        rrect(surf,c,(x,y,int(w*ratio),h),5)
    rrect(surf,(100,100,130),(x,y,w,h),5,w=1)
    if label: txt_tl(surf,label,16,lcol,x,y-20,bold=True)
    s=font(14).render(f"{max(0,cur)}/{mx}",True,WHITE)
    surf.blit(s,(x+w//2-s.get_width()//2,y+h//2-s.get_height()//2))

# ── Asset Loaders ──────────────────────────────────────────
def load_img(path, size, fb=(80,80,80)):
    try:
        img=pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img,size)
    except:
        s=pygame.Surface(size,pygame.SRCALPHA)
        s.fill((*fb,255))
        return s

def load_video_frames(path,size):
    if not HAS_CV2: return []
    try:
        cap=cv2.VideoCapture(path); out=[]
        while True:
            ok,frame=cap.read()
            if not ok: break
            frame=cv2.resize(frame,size)
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            out.append(pygame.image.frombuffer(rgb.tobytes(),size,'RGB').convert())
        cap.release(); return out
    except Exception as e:
        print(f"[video] {e}"); return []

# ══════════════════════════════════════════════════════════
#  MAZE  – DFS
# ══════════════════════════════════════════════════════════
# (Imported from maze_game.maze.dfs_generator)

# ══════════════════════════════════════════════════════════
#  PATHFINDING
# ══════════════════════════════════════════════════════════
# (Imported from maze_game.maze.a_star_solver)

# ══════════════════════════════════════════════════════════
#  WEAPON
# ══════════════════════════════════════════════════════════
class Weapon:
    def __init__(self,name,wtype,dmg,kb,col):
        self.name=name; self.wtype=wtype; self.dmg=dmg; self.kb=kb; self.col=col

def SWORD():  return Weapon("Sword",     "MELEE",  22,  9, ORANGE)
def GUN():    return Weapon("Energy Gun","RANGED",  12,  6, CYAN)
def HSWORD(): return Weapon("War Axe",   "MELEE",  30, 14, PURPLE)
def RLAUNCHER(): return Weapon("Rocket Launcher", "RANGED", 35, 18, RED)
def SPEAR():  return Weapon("Spear",     "MELEE",  18, 10, GREEN)

ALL_WEAPONS = [SWORD, GUN, HSWORD, RLAUNCHER, SPEAR]

# ══════════════════════════════════════════════════════════
#  PARTICLE SYSTEM  (combat effects)
# ══════════════════════════════════════════════════════════
class Particle:
    def __init__(self, x, y, col):
        self.x=float(x); self.y=float(y)
        angle=random.uniform(0,math.pi*2)
        speed=random.uniform(2,8)
        self.vx=math.cos(angle)*speed
        self.vy=math.sin(angle)*speed - random.uniform(1,4)
        self.col=col
        self.life=random.randint(18,35)
        self.max_life=self.life
        self.r=random.randint(2,5)

    def update(self):
        self.x+=self.vx; self.y+=self.vy
        self.vy+=0.3    # gravity
        self.vx*=0.92
        self.life-=1

    def draw(self,surf):
        ratio=self.life/self.max_life
        a=int(255*ratio)
        r=max(1,int(self.r*ratio))
        ps=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(ps,(*self.col,a),(r,r),r)
        surf.blit(ps,(int(self.x)-r,int(self.y)-r))

class ParticleSystem:
    def __init__(self): self.particles=[]
    def burst(self,x,y,col,count=18):
        for _ in range(count): self.particles.append(Particle(x,y,col))
    def update(self):
        self.particles=[p for p in self.particles if p.life>0]
        for p in self.particles: p.update()
    def draw(self,surf):
        for p in self.particles: p.draw(surf)

# ══════════════════════════════════════════════════════════
#  PROJECTILE
# ══════════════════════════════════════════════════════════
class Proj:
    R=6
    def __init__(self,x,y,vx,owner,col):
        self.x=float(x); self.y=float(y); self.vx=vx
        self.owner=owner; self.col=col; self.trail=[]
    def update(self):
        self.trail.append((int(self.x),int(self.y)))
        if len(self.trail)>10: self.trail.pop(0)
        self.x+=self.vx
    def rect(self): return pygame.Rect(self.x-self.R,self.y-self.R,self.R*2,self.R*2)
    def draw(self,surf):
        for i,(tx,ty) in enumerate(self.trail):
            a=int(200*(i/len(self.trail)))
            r=max(1,self.R-2)
            ts=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(ts,(*self.col,a),(r,r),r)
            surf.blit(ts,(tx-r,ty-r))
        pygame.draw.circle(surf,self.col,(int(self.x),int(self.y)),self.R)
        # core white flash
        pygame.draw.circle(surf,WHITE,(int(self.x),int(self.y)),self.R//2)
        # glow
        gr=self.R*3
        gs=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
        pygame.draw.circle(gs,(*self.col,50),(gr,gr),gr)
        surf.blit(gs,(int(self.x)-gr,int(self.y)-gr))

# ══════════════════════════════════════════════════════════
#  STICKMAN  (aa drawing via gfxdraw for smooth look)
# ══════════════════════════════════════════════════════════
def aa_line(surf, col, p1, p2, width=2):
    """Multi-pass anti-aliased thick line."""
    pygame.gfxdraw.line(surf, p1[0], p1[1], p2[0], p2[1], col)
    if width > 1:
        pygame.draw.line(surf, col, p1, p2, width)

def aa_circle(surf, col, pos, r, width=2):
    """Anti-aliased circle outline."""
    pygame.gfxdraw.aacircle(surf, pos[0], pos[1], r, col)
    if width > 1:
        pygame.draw.circle(surf, col, pos, r, width)

class Stickman:
    W,H=28,68
    def __init__(self,x,y,col,weapon,is_player=True,diff=None):
        self.x=float(x); self.y=float(y)
        self.vx=self.vy=0.0
        self.col=col; self.weapon=weapon; self.is_player=is_player
        # HP based on difficulty
        if diff:
            self.hp=self.max_hp=diff["player_hp"] if is_player else diff["enemy_hp"]
        else:
            self.hp=self.max_hp=120
        self.on_ground=False; self.facing=1 if is_player else -1
        self.atk_cd=0; self.hit_flash=0; self.swing_anim=0
        self.dmg_mult=1.0 if is_player else (diff["dmg_mult"] if diff else 1.0)
        self.speed = ESPD if is_player else (diff["enemy_speed"] if diff else ESPD)
        
        self.weapon_img = None
        try:
            wpn_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maze_combat", "weapons")
            img_path = os.path.join(wpn_dir, f"{self.weapon.name}.png")
            if os.path.exists(img_path):
                raw_img = pygame.image.load(img_path).convert_alpha()
                w, h = raw_img.get_size()
                scale = 80.0 / max(w, h)
                self.weapon_img = pygame.transform.smoothscale(raw_img, (int(w * scale), int(h * scale)))
        except:
            pass

    @property
    def rect(self): return pygame.Rect(int(self.x),int(self.y),self.W,self.H)

    def move(self,dx):
        self.vx+=dx
        if dx>0: self.facing=1
        elif dx<0: self.facing=-1

    def jump(self):
        if self.on_ground: self.vy=JF; self.on_ground=False

    def apply_kb(self,direction,weapon):
        self.vx=direction*weapon.kb; self.vy=-5; self.hit_flash=14

    def update(self,floor_y,lw,rw):
        self.vy+=GRAV
        if self.vy>MAXFALL: self.vy=MAXFALL
        self.x+=self.vx; self.y+=self.vy
        self.vx*=FRIC
        if abs(self.vx)<0.2: self.vx=0.0
        if self.y+self.H>=floor_y:
            self.y=float(floor_y-self.H); self.vy=0; self.on_ground=True
        else: self.on_ground=False
        if self.x<lw: self.x=float(lw); self.vx=0
        if self.x+self.W>rw: self.x=float(rw-self.W); self.vx=0
        if self.atk_cd>0: self.atk_cd-=1
        if self.hit_flash>0: self.hit_flash-=1
        if self.swing_anim>0: self.swing_anim-=1

    def melee_rect(self):
        sw=38
        if self.facing==1: return pygame.Rect(int(self.x+self.W),int(self.y+10),sw,30)
        else:               return pygame.Rect(int(self.x-sw),int(self.y+10),sw,30)

    def draw(self, surf):
        cx=int(self.x+self.W//2)
        hy=int(self.y+12)      # head centre y
        hip=int(self.y+self.H-28)
        foot=int(self.y+self.H)
        arm_y=int(self.y+26)
        arm_ex=cx+self.facing*26

        # Flash colour on hit
        dc=(255,80,80) if self.hit_flash>0 else self.col

        # ── shadow ellipse ────────────────────────────────
        shadow=pygame.Surface((self.W+10,8),pygame.SRCALPHA)
        pygame.gfxdraw.filled_ellipse(shadow,self.W//2+5,4,(self.W//2+4),4,(0,0,0,55))
        surf.blit(shadow,(cx-self.W//2-5,foot))

        # ── head: filled + outlined ────────────────────────
        pygame.gfxdraw.filled_circle(surf,cx,hy,11,(0,0,0,120))
        pygame.gfxdraw.filled_circle(surf,cx,hy,10,(*dc,200))
        aa_circle(surf,dc,(cx,hy),10,1)

        # ── eye ───────────────────────────────────────────
        eye_x=cx+4*self.facing
        pygame.gfxdraw.filled_circle(surf,eye_x,hy-1,2,(*dc,255))
        pygame.gfxdraw.aacircle(surf,eye_x,hy-1,2,dc)

        # ── body (polygons) ────────────────────────────────
        # Core colors
        body_col = (40, 40, 45) # Sleek dark suit
        outline_col = WHITE if dc == WHITE else dc # Neon highlights

        def draw_limb(p1, p2, thickness):
            pygame.draw.line(surf, outline_col, p1, p2, thickness+2)
            pygame.draw.line(surf, body_col, p1, p2, thickness-2)
            pygame.draw.circle(surf, outline_col, p1, thickness//2+1)
            pygame.draw.circle(surf, body_col, p1, thickness//2-1)
            pygame.draw.circle(surf, outline_col, p2, thickness//2+1)
            pygame.draw.circle(surf, body_col, p2, thickness//2-1)

        # Back arm
        draw_limb((cx, arm_y), (arm_ex, arm_y+5), 7)

        # Legs
        draw_limb((cx, hip), (cx-10, foot), 8)
        draw_limb((cx, hip), (cx+10, foot), 8)
        
        # Torso (Armored Shape)
        pygame.draw.polygon(surf, outline_col, [(cx-9, hy+8), (cx+9, hy+8), (cx+5, hip+4), (cx-5, hip+4)])
        pygame.draw.polygon(surf, body_col, [(cx-7, hy+10), (cx+7, hy+10), (cx+3, hip+2), (cx-3, hip+2)])
        
        # Head
        pygame.draw.circle(surf, outline_col, (cx, hy), 14)
        pygame.draw.circle(surf, body_col, (cx, hy), 12)
        # Eye glow
        pygame.draw.circle(surf, WHITE, (eye_x, hy-2), 4)
        pygame.draw.circle(surf, dc, (eye_x, hy-2), 6, 2)

        # Front arm
        # draw_limb((cx, arm_y), (arm_ex, arm_y+5), 10) # (We'll let weapon layer handle it, or stick to one arm visible for 2D profile)

        # ── weapon ────────────────────────────────────────
        if self.weapon.wtype=="MELEE":
            if self.swing_anim>0:
                ang=math.radians(self.swing_anim*7*self.facing)
                wx=arm_ex+self.facing*int(32*math.cos(ang))
                wy=arm_y+5-int(32*math.sin(ang))
            else:
                wx,wy=arm_ex+self.facing*24, arm_y-24
            
            hx, hy_w = arm_ex-self.facing*8, arm_y+15
            
            if hasattr(self, "weapon_img") and self.weapon_img:
                angle_deg = -self.swing_anim*7*self.facing if self.facing == 1 else self.swing_anim*7*self.facing
                img = pygame.transform.flip(self.weapon_img, True, False) if self.facing == -1 else self.weapon_img
                rot_img = pygame.transform.rotate(img, angle_deg)
                rect = rot_img.get_rect(center=(wx, wy))
                surf.blit(rot_img, rect.topleft)
            else:
                # SIMPLE FALLBACK WEAPONS
                if self.weapon.name == "War Axe":
                    aa_line(surf, (150, 100, 50), (hx, hy_w), (arm_ex, arm_y+5), 5)
                    aa_line(surf, (150, 100, 50), (arm_ex, arm_y+5), (wx, wy), 5)
                    pygame.draw.circle(surf, (200, 200, 200), (int(wx), int(wy)), 12)
                    pygame.draw.polygon(surf, (180, 180, 180), [(wx-5, wy-15), (wx+self.facing*25, wy), (wx-5, wy+15)])
                elif self.weapon.name == "Energy Lance":
                    aa_line(surf, (100, 100, 100), (hx, hy_w), (wx, wy), 4)
                    pygame.draw.circle(surf, self.weapon.col, (int(wx), int(wy)), 8)
                    pygame.draw.polygon(surf, WHITE, [(wx-4, wy-4), (wx+self.facing*15, wy), (wx-4, wy+4)])
                elif self.weapon.name == "Spear":
                    aa_line(surf, (120, 80, 40), (hx-self.facing*10, hy_w+10), (wx, wy), 4)
                    pygame.draw.polygon(surf, (200, 200, 200), [(wx-2, wy-4), (wx+self.facing*15, wy), (wx-2, wy+4)])
                else: # Sword
                    aa_line(surf, GOLD, (hx, hy_w), (arm_ex, arm_y+5), 4)
                    aa_line(surf, self.weapon.col, (arm_ex, arm_y+5), (wx, wy), 8)
                    aa_line(surf, WHITE, (arm_ex, arm_y+5), (wx, wy), 3)

        else: # Gun
            bx2=arm_ex+self.facing*30
            rx = min(arm_ex, bx2)
            
            if hasattr(self, "weapon_img") and self.weapon_img:
                img = pygame.transform.flip(self.weapon_img, True, False) if self.facing == -1 else self.weapon_img
                rect = img.get_rect(center=(rx+15, arm_y+5))
                surf.blit(img, rect.topleft)
            else:
                pygame.draw.rect(surf, (60, 60, 60), (rx, arm_y-2, 30, 10))
                pygame.draw.rect(surf, self.weapon.col, (rx+5, arm_y, 20, 6))

        # ── HP bar above head ─────────────────────────────
        bx=cx-26; by=hy-32
        rrect(surf,(25,8,8),(bx,by,52,7),3)
        ratio=max(0,self.hp/self.max_hp)
        if ratio>0:
            c=GREEN if ratio>.5 else YELLOW if ratio>.25 else RED
            rrect(surf,c,(bx,by,int(52*ratio),7),3)
        rrect(surf,(80,80,100),(bx,by,52,7),3,w=1)

# ══════════════════════════════════════════════════════════
#  DICE
# ══════════════════════════════════════════════════════════
DICE_SZ=(180,180)

class Dice:
    ROLL_DUR=2.0
    def __init__(self):
        self.face_imgs={}; self.vid_frames=[]
        self.value=1; self.state="IDLE"
        self._t0=0.0; self._vframe=0
        self.rect=pygame.Rect(0,0,*DICE_SZ)

    def load(self):
        for i in range(1,7):
            p=os.path.join(DICE_DIR,f"dice_{i}.png")
            self.face_imgs[i]=load_img(p,DICE_SZ,fb=(240,240,240))
        self.vid_frames=load_video_frames(VID_PATH,DICE_SZ)

    def place(self,cx,cy):
        self.rect=pygame.Rect(cx-DICE_SZ[0]//2,cy-DICE_SZ[1]//2,*DICE_SZ)

    def start_roll(self):
        if self.state=="ROLLING": return
        self.state="ROLLING"; self._t0=time.time(); self._vframe=0

    def update(self):
        if self.state=="ROLLING":
            elapsed=time.time()-self._t0
            if self.vid_frames:
                self._vframe=min(int(elapsed/self.ROLL_DUR*len(self.vid_frames)),
                                 len(self.vid_frames)-1)
            if elapsed>=self.ROLL_DUR:
                self.value=random.randint(1,6); self.state="DONE"

    def reset(self): self.state="IDLE"
    @property
    def ready(self): return self.state=="DONE"

    def handle_click(self,pos):
        if self.rect.collidepoint(pos) and self.state in ("IDLE","DONE"):
            self.start_roll(); return True
        return False

    def draw(self,surf):
        if self.state=="ROLLING":
            if self.vid_frames:
                surf.blit(self.vid_frames[min(self._vframe,len(self.vid_frames)-1)],self.rect.topleft)
            else:
                fake=pygame.time.get_ticks()//120%6+1
                surf.blit(self.face_imgs[fake],self.rect.topleft)
        else:
            surf.blit(self.face_imgs[self.value],self.rect.topleft)
            if self.state=="IDLE":
                t=pygame.time.get_ticks()/600
                a=int(140+100*math.sin(t))
                brd=pygame.Surface(DICE_SZ,pygame.SRCALPHA)
                pygame.draw.rect(brd,(*GOLD,a),(0,0,*DICE_SZ),3,border_radius=10)
                surf.blit(brd,self.rect.topleft)
        if self.state=="ROLLING":
            t=pygame.time.get_ticks()/280
            a=int(100+80*math.sin(t))
            r=pygame.Surface(DICE_SZ,pygame.SRCALPHA)
            pygame.draw.rect(r,(*CYAN,a),(0,0,*DICE_SZ),4,border_radius=10)
            surf.blit(r,self.rect.topleft)

# ══════════════════════════════════════════════════════════
#  COMBAT ARENA  (dramatic, aa-rendered, particle effects)
# ══════════════════════════════════════════════════════════
class Arena:
    FY=CH-90; LW=0; RW=CW

    def __init__(self,surf):
        self.surf=surf
        self._bg=self._make_bg_default()
        self._shake=0; self._shake_off=(0,0)
        self.player=self.enemy=None
        self.projectiles=[]; self.result=None
        self.ps=ParticleSystem()
        self._screen_flash=0   # frames of red flash
        self._diff=None

    def _make_bg_default(self):
        s=pygame.Surface((CW,CH))
        # gradient sky
        for y in range(CH):
            t=y/CH
            r=int(8+18*t); g_=int(4+8*t); b=int(16+24*t)
            pygame.draw.line(s,(r,g_,b),(0,y),(CW,y))
        # arena floor planks
        for x in range(self.LW,self.RW,60):
            pygame.draw.rect(s,(38,32,50),(x,self.FY,58,CH-self.FY))
            pygame.draw.line(s,(50,44,65),(x,self.FY),(x,CH),1)
        pygame.draw.line(s,(70,60,90),(self.LW,self.FY),(self.RW,self.FY),3)
        # torchlight spots on left/right walls
        for tx,ty in [(self.LW-6,220),(self.RW+6,220),(self.LW-6,420),(self.RW+6,420)]:
            for rad in range(60,0,-10):
                a=int(12*(rad/60))
                pygame.draw.circle(s,(255,150,30,a),(tx,ty),rad)  # won't work with SRCALPHA but fine
        # vertical pillars
        pygame.draw.rect(s,(50,44,65),(self.LW-18,0,18,self.FY))
        pygame.draw.rect(s,(50,44,65),(self.RW,0,18,self.FY))
        pygame.draw.rect(s,(70,60,90),(self.LW-18,0,4,self.FY))
        pygame.draw.rect(s,(70,60,90),(self.RW+14,0,4,self.FY))
        return s

    def init_fight(self,pw,ew,diff):
        self._diff=diff
        self.player=Stickman(160,self.FY-Stickman.H,BLUE,pw,True,diff)
        self.enemy =Stickman(CW-160-Stickman.W,self.FY-Stickman.H,RED,ew,False,diff)
        self.enemy.facing=-1
        self.projectiles=[]; self.result=None
        self.ps=ParticleSystem()
        self._shake=0; self._screen_flash=0
        self.randomize_bg()

    def randomize_bg(self):
        bg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maze_combat", "backgrounds")
        try:
            choice = random.randint(1, 6)
            img_path = os.path.join(bg_dir, f"{choice}.jpeg")
            if os.path.exists(img_path):
                img = pygame.image.load(img_path).convert()
                self._bg = pygame.transform.smoothscale(img, (CW, CH))
            else:
                self._bg = self._make_bg_default()
        except Exception as e:
            print(f"Error loading background: {e}")
            self._bg = self._make_bg_default()

    def _do_hit(self,victim,attacker):
        raw=attacker.weapon.dmg+random.randint(-3,3)
        dmg=int(raw*attacker.dmg_mult)
        victim.hp-=dmg
        d=1 if attacker.x<victim.x else -1
        victim.apply_kb(d,attacker.weapon)
        attacker.swing_anim=9
        self._shake=9
        hx=int(victim.x+victim.W//2); hy=int(victim.y+victim.H//3)
        self.ps.burst(hx,hy,attacker.weapon.col,22)
        if not victim.is_player:
            pass
        else:
            self._screen_flash=10  # red screen flash when player is hit

    def _player_attack(self):
        if self.player.atk_cd>0: return
        self.player.atk_cd=32
        if self.player.weapon.wtype=="MELEE":
            if self.player.melee_rect().colliderect(self.enemy.rect):
                self._do_hit(self.enemy,self.player)
        else:
            bx=self.player.x+Stickman.W//2; by=self.player.y+26
            self.projectiles.append(Proj(bx,by,12*self.player.facing,"player",self.player.weapon.col))

    def _enemy_ai(self):
        e, p = self.enemy, self.player
        if not e or not p: return
        
        if e.weapon.wtype == "MELEE":
            dist = abs(p.x - e.x)
            # Hill Climbing: move toward player to maximise damage opportunity
            spd, facing = hill_climbing_movement(e.x, p.x, e.speed)
            e.facing = facing
            if dist > 50:
                e.move(spd)
            elif e.atk_cd == 0:
                e.atk_cd = 52
                # Forward Chaining: IF collision THEN apply damage THEN knockback
                is_hit, dmg, kb_dir = forward_chaining_combat(
                    e.melee_rect(), p.rect, e.weapon.dmg
                )
                if is_hit:
                    raw = dmg + random.randint(-3, 3)
                    p.hp -= int(raw * e.dmg_mult)
                    p.apply_kb(kb_dir, e.weapon)
                    e.swing_anim = 9
                    self._shake = 9
                    self.ps.burst(int(p.x + p.W//2), int(p.y + p.H//3), e.weapon.col, 22)
                    self._screen_flash = 10
            if e.on_ground and abs(e.vx) < 0.5 and dist > 70:
                e.jump()
        else:
            dx = p.x - e.x; dist = abs(dx)
            e.facing = 1 if dx > 0 else -1
            if dist < 130:   e.move(-e.speed * e.facing)
            elif dist > 280: e.move(e.speed * e.facing)
            if e.atk_cd == 0 and 100 <= dist <= 320:
                e.atk_cd = 58
                bx = e.x + Stickman.W//2; by = e.y + 26
                vx = 11 if e.facing == 1 else -11
                self.projectiles.append(Proj(bx, by, vx, "enemy", e.weapon.col))
            if e.on_ground and abs(e.vx) < 0.5: e.jump()

    def update(self):
        if self.result: return self.result
        keys=pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.player.move(-PSPD)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.player.move(PSPD)
        if keys[pygame.K_w] or keys[pygame.K_UP]:    self.player.jump()
        if keys[pygame.K_SPACE]:                     self._player_attack()
        self._enemy_ai()
        if self._screen_flash>0: self._screen_flash-=1

        if self._shake>0:
            self._shake_off=(random.randint(-self._shake,self._shake),
                             random.randint(-self._shake,self._shake))
            self._shake=max(0,self._shake-1)
        else: self._shake_off=(0,0)

        self.player.update(self.FY,self.LW,self.RW)
        self.enemy.update(self.FY,self.LW,self.RW)

        for pr in self.projectiles[:]:
            pr.update()
            if pr.x<self.LW or pr.x>self.RW:
                self.projectiles.remove(pr); continue
            if pr.owner=="player" and pr.rect().colliderect(self.enemy.rect):
                self._do_hit(self.enemy,self.player); self.projectiles.remove(pr)
            elif pr.owner=="enemy" and pr.rect().colliderect(self.player.rect):
                self._do_hit(self.player,self.enemy); self.projectiles.remove(pr)

        self.ps.update()

        if self.player.hp<=0: self.result="PLAYER_DEAD"
        elif self.enemy.hp<=0: self.result="ENEMY_DEAD"
        return self.result

    def draw(self):
        s=self.surf
        ox,oy=self._shake_off
        s.blit(self._bg,(ox,oy))

        # Draw consistent platform base over the background
        base_h = CH - self.FY
        pygame.draw.rect(s, (35, 30, 45), (0, self.FY, CW, base_h))
        pygame.draw.rect(s, (50, 45, 65), (0, self.FY, CW, base_h), width=4)
        for x in range(0, CW, 80):
            pygame.draw.line(s, (25, 20, 35), (x, self.FY), (x, CH), 2)
            pygame.draw.line(s, (50, 45, 65), (x+2, self.FY), (x+2, CH), 1)

        for pr in self.projectiles: pr.draw(s)
        self.ps.draw(s)

        if self.player: self.player.draw(s)
        if self.enemy:  self.enemy.draw(s)

        # ── Screen flash red when player takes damage ─────
        if self._screen_flash>0:
            fl=pygame.Surface((CW,CH),pygame.SRCALPHA)
            a=int(120*(self._screen_flash/10))
            fl.fill((200,0,0,a))
            s.blit(fl,(0,0))

        # ── TOP HUD ───────────────────────────────────────
        bar=pygame.Surface((CW,75),pygame.SRCALPHA)
        bar.fill((0,0,0,170))
        s.blit(bar,(0,0))

        hp_bar(s,16,22,260,24,self.player.hp,self.player.max_hp,"PLAYER",BLUE)
        txt_tl(s,f" {self.player.weapon.name}  DMG:{self.player.weapon.dmg}",
               15,self.player.weapon.col,16,48)

        hp_bar(s,CW-276,22,260,24,self.enemy.hp,self.enemy.max_hp,"ENEMY",RED)
        txt_tl(s,f" {self.enemy.weapon.name}  DMG:{self.enemy.weapon.dmg}",
               15,self.enemy.weapon.col,CW-276,48)

        # pulsing title
        t=pygame.time.get_ticks()/800
        a=int(200+55*math.sin(t))
        cs=font(34,True).render("⚔  COMBAT  ⚔",True,YELLOW)
        cs.set_alpha(a)
        s.blit(cs,(CW//2-cs.get_width()//2,18))

        # difficulty badge
        if self._diff:
            dc=self._diff["col"]
            dname=self._diff["label"]
            badge=font(14,True).render(f"[ {dname.upper()} ]",True,dc)
            s.blit(badge,(CW//2-badge.get_width()//2,54))

        # BOTTOM hint bar
        hint=pygame.Surface((CW,32),pygame.SRCALPHA)
        hint.fill((0,0,0,130))
        s.blit(hint,(0,CH-32))
        txt(s,"A/D = Move   W = Jump   SPACE = Attack",18,WHITE,CW//2,CH-16)

# ══════════════════════════════════════════════════════════
#  MAZE TILE TEXTURES
# ══════════════════════════════════════════════════════════
def make_maze_tiles():
    src=load_img(os.path.join(MAZE_DIR,"background.png"),(TILE*4,TILE*4),(70,60,50))
    wall=pygame.transform.scale(src,(TILE,TILE))
    path=wall.copy()
    dark=pygame.Surface((TILE,TILE),pygame.SRCALPHA)
    dark.fill((0,0,0,208)); path.blit(dark,(0,0))
    hi=pygame.Surface((TILE,TILE),pygame.SRCALPHA)
    pygame.draw.rect(hi,(255,255,255,20),(1,1,TILE-2,TILE-2),1)
    wall.blit(hi,(0,0))
    pdot=load_img(os.path.join(MAZE_DIR,"player_dot.png"),(TILE-6,TILE-6))
    goal=load_img(os.path.join(MAZE_DIR,"Goal.png"),(TILE-4,TILE-4))
    return wall,path,pdot,goal

# ══════════════════════════════════════════════════════════
#  MAIN GAME
# ══════════════════════════════════════════════════════════
class Game:
    def __init__(self,screen):
        self.screen=screen
        self.canvas=pygame.Surface((CW,CH))
        self.state=S_MENU
        self.fullscreen=False
        self.diff_name="Medium"   # selected difficulty
        self._hover_diff=None

        self.wall_tile,self.path_tile,self.pdot,self.goal_img=make_maze_tiles()

        self.dice=Dice(); self.dice.load()
        self.dice.place(SIDEBAR_X+SIDEBAR_W//2, 260)

        # highlight tiles (pre-built)
        self._hl_move=pygame.Surface((TILE,TILE),pygame.SRCALPHA)
        self._hl_move.fill((80,200,255,70))
        pygame.draw.rect(self._hl_move,(80,200,255,200),(0,0,TILE,TILE),2)

        self._hl_gold=pygame.Surface((TILE,TILE),pygame.SRCALPHA)
        self._hl_gold.fill((255,200,50,25))

        self.arena=Arena(self.canvas)
        self.p_weapon=SWORD()
        self.p_hp_max=120; self.p_hp=120  # persistent across combats
        self._weapon_queue = []
        self._new_game()
        self.state = S_MODE

    # ── Reset maze state ───────────────────────────────────
    def _new_game(self):
        # DFS Algorithm: generate a brand new maze
        self.grid, self.start, self.exit = generate_maze_dfs(MAZE_ROWS, MAZE_COLS)
        self.ppos = self.start
        # A* Algorithm: compute optimal path from start to exit once
        self.opt = astar_solver(self.grid, self.start, self.exit)
        self._path_steps_walked = 0   # track how far player has progressed on A*
        self.dice.reset(); self.dice.value = 1
        self.maze_mode = "WAIT_ROLL"
        self.steps_left = 0
        # BFS/CSP: cached reachable tiles for current dice roll
        self._bfs_reachable = {}    # {tile: steps_from_player}
        self._csp_valid    = []     # tiles exactly dice_value steps away
        self.enemy_present = False
        self.epos_tile = None
        self.e_weapon = None
        self.show_pickup = False
        self.pickup_w = None
        diff = DIFFICULTIES[self.diff_name]
        self.p_hp_max = diff["player_hp"]
        self.p_hp = self.p_hp_max
        self.state = S_MAZE

    @property
    def diff(self): return DIFFICULTIES[self.diff_name]

    def _valid_moves(self):
        """Returns adjacent open tiles the player can step into with remaining steps."""
        r, c = self.ppos
        moves = {}
        for key, dr, dc in [(pygame.K_UP,-1,0),(pygame.K_DOWN,1,0),
                            (pygame.K_LEFT,0,-1),(pygame.K_RIGHT,0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<len(self.grid) and 0<=nc<len(self.grid[0]) and self.grid[nr][nc]==0:
                moves[key] = (nr, nc)
        return moves

    # ── Events ─────────────────────────────────────────────
    def handle(self,ev):
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_F11: self._toggle_fs()
            if ev.key==pygame.K_q and self.state in (S_OVER,S_WIN):
                pygame.quit(); sys.exit()
            if ev.key==pygame.K_r and self.state in (S_OVER,S_WIN):
                self.p_weapon=SWORD(); self._new_game()

            # Mode select: 1/2/3 keys
            if self.state==S_MODE:
                if ev.key==pygame.K_1: self.diff_name="Easy"
                if ev.key==pygame.K_2: self.diff_name="Medium"
                if ev.key==pygame.K_3: self.diff_name="Hard"
                if ev.key==pygame.K_RETURN or ev.key==pygame.K_SPACE:
                    self.p_weapon=SWORD(); self._new_game()

            if self.state==S_MAZE:
                if ev.key==pygame.K_SPACE:
                    if self.show_pickup:
                        self.show_pickup=False; self.pickup_w=None
                    elif self.maze_mode=="WAIT_ROLL":
                        self.dice.start_roll(); self.maze_mode="ROLLING"
                if ev.key==pygame.K_p and self.show_pickup:
                    self.p_weapon=self.pickup_w
                    self.show_pickup=False; self.pickup_w=None

                # ── Arrow key tile movement ────────────────
                if self.maze_mode=="WAIT_MOVE" and not self.show_pickup:
                    vm=self._valid_moves()
                    if ev.key in vm:
                        self.ppos=vm[ev.key]
                        self.steps_left-=1
                        # BFS: re-compute reachable from NEW position with remaining steps
                        self._bfs_reachable = bfs_reachable_tiles(self.grid, self.ppos, self.steps_left)
                        # CSP: re-filter exact-step valid destinations
                        self._csp_valid = csp_valid_moves(self._bfs_reachable, self.steps_left, self.exit)
                        self._step_check()
                        if self.state==S_COMBAT: return
                        if self.steps_left<=0:
                            self.maze_mode="WAIT_ROLL"
                            self.dice.reset()

        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            mp=pygame.mouse.get_pos()

            # Mode select buttons
            if self.state==S_MODE:
                for i,dname in enumerate(["Easy","Medium","Hard"]):
                    btn=self._diff_btn_rect(i)
                    if btn.collidepoint(mp):
                        self.diff_name=dname
                        return
                play_btn = pygame.Rect(CW//2-120, CH-100, 240, 60)
                if play_btn.collidepoint(mp):
                    self.p_weapon=SWORD(); self._new_game()
                    return

            if self.state==S_MAZE:
                # Click dice
                if self.maze_mode=="WAIT_ROLL" and not self.show_pickup:
                    if self.dice.handle_click(mp):
                        self.maze_mode="ROLLING"

        if ev.type==pygame.MOUSEMOTION and self.state==S_MODE:
            mp=pygame.mouse.get_pos()
            self._hover_diff=None
            for i,dname in enumerate(["Easy","Medium","Hard"]):
                if self._diff_btn_rect(i).collidepoint(mp):
                    self._hover_diff=dname

    def _toggle_fs(self):
        self.fullscreen=not self.fullscreen
        flags=pygame.FULLSCREEN|pygame.SCALED if self.fullscreen else pygame.SCALED
        pygame.display.set_mode((CW,CH),flags)

    def _diff_btn_rect(self,i):
        w,h=260,130; gap=40
        total=(w+gap)*3-gap
        x=CW//2-total//2+i*(w+gap)
        y=CH//2-20
        return pygame.Rect(x,y,w,h)

    # ── Update ─────────────────────────────────────────────
    def update(self):
        if   self.state==S_MAZE:   self._upd_maze()
        elif self.state==S_COMBAT: self._upd_combat()

    def _upd_maze(self):
        self.dice.update()
        if self.maze_mode=="ROLLING" and self.dice.ready:
            self.steps_left=self.dice.value
            # BFS Algorithm: find all tiles reachable within dice steps
            self._bfs_reachable = bfs_reachable_tiles(self.grid, self.ppos, self.steps_left)
            # CSP: filter to tiles that are EXACTLY dice_value steps (or exit if within range)
            self._csp_valid = csp_valid_moves(self._bfs_reachable, self.steps_left, self.exit)
            self.maze_mode="WAIT_MOVE"

    def _step_check(self):
        if self.ppos == self.exit:
            # Propositional Logic: player reached exit → WIN
            self.state = evaluate_game_state(S_MAZE, 1, 1, self.ppos, self.exit, False)
            return

        # Track A* path progress for Goal Tree
        if self.ppos in self.opt:
            self._path_steps_walked = self.opt.index(self.ppos) + 1

        if not self.enemy_present:
            # Goal Tree + Propositional Logic: decide whether to spawn
            progress = self._path_steps_walked / len(self.opt) if self.opt else 0
            should_spawn, spawn_pos = spawn_goal_tree(
                self.grid, self.ppos, self.exit, self.opt, self._path_steps_walked
            )
            if should_spawn and spawn_pos:
                self.epos_tile = spawn_pos
                if not self._weapon_queue:
                    self._weapon_queue = [w() for w in ALL_WEAPONS]
                    random.shuffle(self._weapon_queue)
                self.e_weapon = self._weapon_queue.pop(0)
                self.enemy_present = True

        # Trigger combat when player steps on enemy tile
        if self.enemy_present and self.ppos == self.epos_tile:
            self.arena.init_fight(self.p_weapon, self.e_weapon, self.diff)
            self.arena.player.hp = self.p_hp
            self.arena.player.max_hp = self.p_hp_max
            self.steps_left = 0; self.maze_mode = "WAIT_ROLL"
            self.state = S_COMBAT

    def _upd_combat(self):
        r = self.arena.update()
        # Forward Chaining + Propositional Logic: evaluate state after combat update
        enemy_hp = self.arena.enemy.hp if hasattr(self.arena, 'enemy') else 1
        player_hp = self.arena.player.hp if hasattr(self.arena, 'player') else 1
        new_state = evaluate_game_state(S_COMBAT, player_hp, enemy_hp, self.ppos, self.exit, False)
        if r=="PLAYER_DEAD" or new_state == S_OVER:
            self.state = S_OVER
        elif r=="ENEMY_DEAD" or new_state == S_MAZE:
            # Restore player HP after win (Rule: Win → restore HP)
            self.p_hp = self.p_hp_max
            self.pickup_w = self.e_weapon
            self.show_pickup = True
            self.enemy_present = False; self.epos_tile = None
            self.state = S_MAZE

    # ── Draw ───────────────────────────────────────────────
    def draw(self):
        c=self.canvas
        if   self.state==S_MENU:   self._draw_menu(c)
        elif self.state==S_MODE:   self._draw_mode(c)
        elif self.state==S_MAZE:   self._draw_maze(c)
        elif self.state==S_COMBAT: self.arena.draw()
        elif self.state==S_OVER:   self._draw_over(c)
        elif self.state==S_WIN:    self._draw_win(c)
        self.screen.blit(c,(0,0))
        pygame.display.flip()

    # ── MODE SELECT (MAIN MENU) ────────────────────────────────────────
    def _draw_mode(self,c):
        c.fill(BG)
        for y in range(CH):
            t=y/CH
            pygame.draw.line(c,(int(8+10*t),int(8+5*t),int(16+20*t)),(0,y),(CW,y))
        
        # Title
        txt(c,"🗡  STICKMAN MAZE COMBAT  🗡",58,GOLD,CW//2,CH//2-220,bold=True)
        txt(c,"Select Difficulty",24,WHITE,CW//2,CH//2-140)

        for i,dname in enumerate(["Easy","Medium","Hard"]):
            d=DIFFICULTIES[dname]
            btn=self._diff_btn_rect(i)
            mp=pygame.mouse.get_pos()
            hover=btn.collidepoint(mp)
            sel=(self.diff_name==dname)

            # Card BG
            base_col=(20,20,35) if not hover else (28,28,48)
            rrect(c,base_col,btn,14)
            # Coloured top bar
            top=pygame.Rect(btn.x,btn.y,btn.w,6)
            rrect(c,d["col"],top,14)
            # Border
            border_col=d["col"] if (hover or sel) else (50,50,80)
            rrect(c,border_col,btn,14,w=2)

            # Label
            txt(c,d["label"],34,d["col"],btn.centerx,btn.y+40,bold=True)
            # Key hint
            txt(c,f"[{i+1}]",18,(160,160,180),btn.centerx,btn.y+72)
            # Description
            txt(c,d["desc"],15,WHITE,btn.centerx,btn.y+100)

            if sel:
                sm=font(13,True).render("✓ SELECTED",True,d["col"])
                c.blit(sm,(btn.x+btn.w//2-sm.get_width()//2,btn.bottom-22))
        
        # PLAY BUTTON
        play_btn = pygame.Rect(CW//2-120, CH-100, 240, 60)
        mp = pygame.mouse.get_pos()
        play_hover = play_btn.collidepoint(mp)
        rrect(c, GREEN if play_hover else (40,150,60), play_btn, 10)
        txt(c, "START GAME", 30, WHITE, play_btn.centerx, play_btn.centery, bold=True)

    # ── MAZE ───────────────────────────────────────────────
    def _draw_maze(self,c):
        c.fill((5,5,12))
        g=self.grid
        rows,cols=len(g),len(g[0])

        for r in range(rows):
            for cc2 in range(cols):
                tx=MOX+cc2*TILE; ty=MOY+r*TILE
                c.blit(self.wall_tile if g[r][cc2]==1 else self.path_tile,(tx,ty))

        # Subtle A* path hint (golden tiles)
        for pr2, pc2 in self.opt:
            c.blit(self._hl_gold,(MOX+pc2*TILE,MOY+pr2*TILE))

        # BFS/CSP: highlight valid destination tiles (exactly dice_value steps)
        if self.maze_mode=="WAIT_MOVE" and not self.show_pickup:
            for nr, nc in self._csp_valid:
                c.blit(self._hl_move,(MOX+nc*TILE,MOY+nr*TILE))

        # EXIT glow
        er,ec=self.exit
        c.blit(self.goal_img,(MOX+ec*TILE+2,MOY+er*TILE+2))
        t=pygame.time.get_ticks()/500
        ea=int(160+95*math.sin(t))
        es=pygame.Surface((TILE,TILE),pygame.SRCALPHA)
        pygame.draw.rect(es,(*GREEN,ea),(0,0,TILE,TILE),3,border_radius=4)
        c.blit(es,(MOX+ec*TILE,MOY+er*TILE))

        # Player token
        pr,pc=self.ppos
        c.blit(self.pdot,(MOX+pc*TILE+3,MOY+pr*TILE+3))
        t2=pygame.time.get_ticks()/400
        pa=int(180+75*math.sin(t2))
        ps=pygame.Surface((TILE,TILE),pygame.SRCALPHA)
        pygame.draw.rect(ps,(*BLUE,pa),(0,0,TILE,TILE),2,border_radius=4)
        c.blit(ps,(MOX+pc*TILE,MOY+pr*TILE))

        # Steps remaining indicator above player
        if self.maze_mode=="WAIT_MOVE" and self.steps_left>0:
            px=MOX+pc*TILE+TILE//2; py=MOY+pr*TILE-14
            badge=pygame.Surface((28,18),pygame.SRCALPHA)
            badge.fill((0,0,0,150))
            c.blit(badge,(px-14,py-9))
            txt(c,str(self.steps_left),16,YELLOW,px,py,bold=True)

        if self.show_pickup and self.pickup_w:
            ov_rect = pygame.Rect(MOX + MPW//2 - 160, MOY + MPH//2 - 70, 320, 140)
            rrect(c, (20,20,30), ov_rect, 10)
            rrect(c, GOLD, ov_rect, 10, w=3)
            txt(c,"ENEMY DEFEATED!",24,YELLOW,ov_rect.centerx,ov_rect.y+30,bold=True)
            txt(c,f"Pick up {self.pickup_w.name}?",20,WHITE,ov_rect.centerx,ov_rect.y+70)
            txt(c,"Press P (Yes) or SPACE (No)",16,CYAN,ov_rect.centerx,ov_rect.y+110)

        self._draw_sidebar(c)

    def _draw_sidebar(self,c):
        sb=pygame.Surface((SIDEBAR_W,CH),pygame.SRCALPHA)
        sb.fill((*SIDEBAR_BG,245))
        c.blit(sb,(SIDEBAR_X,0))
        pygame.draw.line(c,SIDEBAR_SEP,(SIDEBAR_X,0),(SIDEBAR_X,CH),2)
        SX=SIDEBAR_X; SCX=SX+SIDEBAR_W//2

        # Header Box
        header_rect = pygame.Rect(SX+12, 12, SIDEBAR_W-24, 70)
        rrect(c, (20,20,35), header_rect, 10)
        rrect(c, (40,40,65), header_rect, 10, w=2)
        txt(c,"MAZE COMBAT",22,GOLD,SCX,35,bold=True)
        dc=self.diff["col"]
        badge_s=font(13,True).render(f"[ {self.diff_name.upper()} ]",True,dc)
        c.blit(badge_s,(SCX-badge_s.get_width()//2,53))

        # Dice Section
        dice_y = 105
        txt(c,"— DICE —",17,CYAN,SCX,dice_y)
        
        # Status hint
        if not self.show_pickup:
            if   self.maze_mode=="WAIT_ROLL": hint="Click dice or SPACE to roll"
            elif self.maze_mode=="ROLLING":   hint="Rolling…"
            elif self.maze_mode=="WAIT_MOVE": hint=f"Rolled {self.dice.value}  — Steps left: {self.steps_left}"
            else: hint=""
            if hint: txt(c,hint,15,YELLOW,SCX,dice_y+25)
        if self.maze_mode=="WAIT_MOVE" and not self.show_pickup:
            txt(c,"Use ↑ ↓ ← → to move",14,(180,220,255),SCX,dice_y+45)

        self.dice.draw(c)

        # Player Section
        py = 440
        player_rect = pygame.Rect(SX+12, py, SIDEBAR_W-24, 150)
        rrect(c, (20,20,35), player_rect, 12)
        rrect(c, (40,40,65), player_rect, 12, w=2)
        txt(c,"— PLAYER —",17,CYAN,SCX,py+20)
        hp_bar(c,SX+28,py+45,SIDEBAR_W-56,24,self.p_hp,self.p_hp_max,"HP",WHITE)
        txt(c,f"⚔  {self.p_weapon.name}",18,self.p_weapon.col,SCX,py+105)
        txt(c,f"({self.p_weapon.wtype}   DMG:{self.p_weapon.dmg})",14,WHITE,SCX,py+125)

        # Controls Section
        cy = 610
        ctrl_rect = pygame.Rect(SX+12, cy, SIDEBAR_W-24, 100)
        rrect(c, (20,20,35), ctrl_rect, 12)
        rrect(c, (40,40,65), ctrl_rect, 12, w=2)
        controls=[("SPACE","Roll dice"),("Arrows","Move"),("F11","Fullscreen"),("R","Restart")]
        for i,(key,val) in enumerate(controls):
            y=cy+12+i*20
            txt_tl(c,key,13,GOLD,SX+35,y,bold=True)
            txt_tl(c,f"= {val}",13,WHITE,SX+110,y)

    # ── End Screens ────────────────────────────────────────
    def _draw_over(self,c):
        c.fill((8,4,4))
        for y in range(CH):
            t=y/CH; pygame.draw.line(c,(int(30+40*t),4,4),(0,y),(CW,y))
        txt(c,"GAME OVER",78,(255,60,60),CW//2,CH//2-80,bold=True)
        txt(c,"You were defeated...",28,WHITE,CW//2,CH//2+10)
        txt(c,"R = Restart    Q = Quit",22,YELLOW,CW//2,CH//2+70)

    def _draw_win(self,c):
        c.fill((4,10,4))
        for y in range(CH):
            t=y/CH; pygame.draw.line(c,(4,int(20+40*t),8),(0,y),(CW,y))
        txt(c,"YOU ESCAPED!",76,GREEN,CW//2,CH//2-80,bold=True)
        txt(c,"The maze couldn't hold you.",28,CYAN,CW//2,CH//2+10)
        txt(c,"R = Play Again    Q = Quit",22,YELLOW,CW//2,CH//2+70)

    # ── Main Loop ──────────────────────────────────────────
    def run(self):
        clock=pygame.time.Clock()
        while True:
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT:
                    pygame.quit(); sys.exit()
                self.handle(ev)
            self.update()
            self.draw()
            clock.tick(FPS)

# ══════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════
def main():
    pygame.init()
    screen=pygame.display.set_mode((CW,CH),pygame.SCALED|pygame.RESIZABLE)
    pygame.display.set_caption("⚔  Stickman Maze Combat")
    try:
        icon=load_img(os.path.join(MAZE_DIR,"player_dot.png"),(32,32))
        pygame.display.set_icon(icon)
    except: pass
    Game(screen).run()

if __name__=="__main__":
    main()

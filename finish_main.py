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
S_MENU, S_MODE, S_MAZE, S_COMBAT, S_OVER, S_WIN = \
    "MENU","MODE","MAZE","COMBAT","OVER","WIN"

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
def make_maze():
    rows,cols=MAZE_ROWS,MAZE_COLS
    g=[[1]*cols for _ in range(rows)]
    sr,sc=1,1; g[sr][sc]=0
    stack=[(sr,sc)]; D=[(0,-2),(0,2),(-2,0),(2,0)]
    while stack:
        r,c=stack[-1]; random.shuffle(D); moved=False
        for dr,dc in D:
            nr,nc=r+dr,c+dc
            if 1<=nr<rows-1 and 1<=nc<cols-1 and g[nr][nc]==1:
                g[r+dr//2][c+dc//2]=0; g[nr][nc]=0
                stack.append((nr,nc)); moved=True; break
        if not moved: stack.pop()
    er,ec=rows-2,cols-2; g[er][ec]=0
    if g[er-1][ec]==1 and g[er][ec-1]==1: g[er-1][ec]=0
    return g,(sr,sc),(er,ec)

# ══════════════════════════════════════════════════════════
#  PATHFINDING
# ══════════════════════════════════════════════════════════
def grid_nb(g, r, c):
    for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr,nc=r+dr,c+dc
        if 0<=nr<len(g) and 0<=nc<len(g[0]) and g[nr][nc]==0:
            yield (nr,nc)

def astar(g, start, goal):
    def h(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])
    q=[(h(start,goal),0,start)]; came={start:None}; cost={start:0}
    while q:
        _,c,cur=heapq.heappop(q)
        if cur==goal:
            path=[]; n=cur
            while n!=start: path.append(n); n=came[n]
            return path[::-1]
        for nb in grid_nb(g,*cur):
            nc2=c+1
            if nb not in cost or nc2<cost[nb]:
                cost[nb]=nc2; came[nb]=cur
                heapq.heappush(q,(nc2+h(nb,goal),nc2,nb))
    return []

# ══════════════════════════════════════════════════════════
#  WEAPON
# ══════════════════════════════════════════════════════════
class Weapon:
    def __init__(self,name,wtype,dmg,kb,col):
        self.name=name; self.wtype=wtype; self.dmg=dmg; self.kb=kb; self.col=col

def SWORD():  return Weapon("Sword",     "MELEE",  22,  9, ORANGE)
def GUN():    return Weapon("Energy Gun","RANGED",  12,  6, CYAN)
def HSWORD(): return Weapon("War Axe",   "MELEE",  30, 14, PURPLE)
def LANCE():  return Weapon("Energy Lance", "MELEE",  26, 12, BLUE)
def SPEAR():  return Weapon("Spear",     "MELEE",  18, 10, GREEN)

ALL_WEAPONS = [SWORD, GUN, HSWORD, LANCE, SPEAR]

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
            
            if self.weapon.name == "War Axe":
                # Long handle
                aa_line(surf, (100, 80, 60), (hx-self.facing*10, hy_w+10), (wx, wy), 7)
                # Pommel and wraps
                pygame.draw.circle(surf, (50,50,50), (int(hx-self.facing*10), int(hy_w+10)), 6)
                # Top spike
                pygame.draw.polygon(surf, (180,180,180), [(wx-2, wy-2), (wx+self.facing*15, wy-15), (wx+2, wy+2)])
                # Giant Axe Head
                head_poly = [
                    (wx-self.facing*5, wy-20),
                    (wx+self.facing*20, wy-30),
                    (wx+self.facing*40, wy-15),
                    (wx+self.facing*45, wy+10),
                    (wx+self.facing*20, wy+35),
                    (wx-self.facing*5, wy+20)
                ]
                pygame.draw.polygon(surf, (150,150,150), head_poly)
                pygame.draw.polygon(surf, WHITE, head_poly, 3)
                # Axe Core Glow
                pygame.draw.circle(surf, self.weapon.col, (int(wx+self.facing*15), int(wy)), 18)
                pygame.draw.circle(surf, WHITE, (int(wx+self.facing*15), int(wy)), 6)

            elif self.weapon.name == "Energy Lance":
                # Shaft
                aa_line(surf, (50,50,60), (hx, hy_w), (wx, wy), 6)
                # Energy Rings
                for i in range(1, 5):
                    px = arm_ex + (wx - arm_ex)*i/4
                    py = arm_y+5 + (wy - (arm_y+5))*i/4
                    pygame.draw.circle(surf, self.weapon.col, (int(px), int(py)), 10)
                    pygame.draw.circle(surf, WHITE, (int(px), int(py)), 4)
                # Massive Energy Blade Tip
                tip_poly = [
                    (wx-self.facing*10, wy-15),
                    (wx+self.facing*40, wy),
                    (wx-self.facing*10, wy+15)
                ]
                pygame.draw.polygon(surf, self.weapon.col, tip_poly)
                pygame.draw.polygon(surf, WHITE, tip_poly, 3)
                # Core line inside tip
                aa_line(surf, WHITE, (wx, wy), (wx+self.facing*35, wy), 4)

            elif self.weapon.name == "Spear":
                # Long wooden shaft
                aa_line(surf, (120, 70, 30), (hx-self.facing*15, hy_w+15), (wx, wy), 6)
                # Red Tassel / Ribbon
                pygame.draw.polygon(surf, RED, [(wx-self.facing*5, wy+5), (wx-self.facing*20, wy+25), (wx-self.facing*10, wy+30), (wx-self.facing*2, wy+15)])
                # Spear Head Base (Gold/Bronze)
                pygame.draw.circle(surf, GOLD, (int(wx), int(wy)), 6)
                # Spear Blade (Steel)
                blade_poly = [
                    (wx, wy-8),
                    (wx+self.facing*15, wy-12),
                    (wx+self.facing*35, wy),
                    (wx+self.facing*15, wy+12),
                    (wx, wy+8)
                ]
                pygame.draw.polygon(surf, (220,220,230), blade_poly)
                pygame.draw.polygon(surf, (150,150,160), blade_poly, 2)
                # Center ridge
                aa_line(surf, (100,100,110), (wx, wy), (wx+self.facing*32, wy), 2)

            else: # Sword
                # Handle
                aa_line(surf, (80,60,50), (hx, hy_w), (arm_ex, arm_y+5), 5)
                # Pommel
                pygame.draw.circle(surf, GOLD, (int(hx), int(hy_w)), 4)
                # Crossguard
                p1 = (arm_ex - 8, arm_y + 12)
                p2 = (arm_ex + 8, arm_y - 2)
                aa_line(surf, GOLD, p1, p2, 6)
                # Blade Glow
                aa_line(surf, self.weapon.col, (arm_ex, arm_y+5), (wx, wy), 16)
                # Blade Core
                aa_line(surf, WHITE, (arm_ex, arm_y+5), (wx, wy), 6)
                # Blade Tip
                pygame.draw.polygon(surf, WHITE, [(wx-self.facing*4, wy-4), (wx+self.facing*12, wy), (wx-self.facing*4, wy+4)])

        else: # Gun
            bx2=arm_ex+self.facing*40
            rx = min(arm_ex, bx2)
            # Base Gun Body
            pygame.draw.rect(surf, (40,40,45), (rx, arm_y-2, 40, 16), border_radius=4)
            # Energy Chamber
            pygame.draw.rect(surf, self.weapon.col, (rx+5, arm_y, 30, 8), border_radius=2)
            pygame.draw.rect(surf, WHITE, (rx+10, arm_y+2, 20, 4), border_radius=2)
            # Barrel
            pygame.draw.rect(surf, (80,80,90), (rx+35 if self.facing==1 else rx-10, arm_y+2, 15, 8), border_radius=2)
            # Underbarrel
            pygame.draw.rect(surf, (60,60,65), (rx+10, arm_y+14, 25, 6), border_radius=2)
            
            # Muzzle flash/glow
            pygame.draw.circle(surf, self.weapon.col, (int(bx2), int(arm_y+6)), 20)
            pygame.draw.circle(surf, WHITE, (int(bx2), int(arm_y+6)), 8)
            if self.atk_cd<6:
                pygame.draw.circle(surf, WHITE, (int(bx2), int(arm_y+6)), 35)
                # Laser beam shot
                aa_line(surf, self.weapon.col, (bx2, arm_y+6), (bx2+self.facing*800, arm_y+6), 12)
                aa_line(surf, WHITE, (bx2, arm_y+6), (bx2+self.facing*800, arm_y+6), 6)

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
    FY=CH-90; LW=80; RW=CW-80

    def __init__(self,surf):
        self.surf=surf
        self._bg=self._make_bg()
        self._shake=0; self._shake_off=(0,0)
        self.player=self.enemy=None
        self.projectiles=[]; self.result=None
        self.ps=ParticleSystem()
        self._screen_flash=0   # frames of red flash
        self._diff=None

    def _make_bg(self):
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
        self.player=Stickman(self.LW+80,self.FY-Stickman.H,BLUE,pw,True,diff)
        self.enemy =Stickman(self.RW-80-Stickman.W,self.FY-Stickman.H,RED,ew,False,diff)
        self.enemy.facing=-1
        self.projectiles=[]; self.result=None
        self.ps=ParticleSystem()
        self._shake=0; self._screen_flash=0

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
        e,p=self.enemy,self.player
        if not e or not p: return
        dx=p.x-e.x; dist=abs(dx); e.facing=1 if dx>0 else -1
        if e.weapon.wtype=="MELEE":
            if dist>50: e.move(e.speed*e.facing)
            elif e.atk_cd==0:
                e.atk_cd=52
                if e.melee_rect().colliderect(p.rect): self._do_hit(p,e)
            if e.on_ground and abs(e.vx)<0.5 and dist>70: e.jump()
        else:
            if dist<130:   e.move(-e.speed*e.facing)
            elif dist>280: e.move(e.speed*e.facing)
            if e.atk_cd==0 and 100<=dist<=320:
                e.atk_cd=58
                bx=e.x+Stickman.W//2; by=e.y+26
                vx=11 if e.facing==1 else -11
                self.projectiles.append(Proj(bx,by,vx,"enemy",e.weapon.col))
            if e.on_ground and abs(e.vx)<0.5: e.jump()

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

        # torchlight animated glow (overlay)
        for tx_,ty_ in [(self.LW-6,220),(self.RW+6,220),(self.LW-6,420),(self.RW+6,420)]:
            t=pygame.time.get_ticks()/600
            flick=int(40+20*math.sin(t+tx_))
            tg=pygame.Surface((120,120),pygame.SRCALPHA)
            for rr in range(60,0,-5):
                a=int(flick*(rr/60))
                pygame.draw.circle(tg,(255,140,20,a),(60,60),rr)
            s.blit(tg,(tx_-60+ox,ty_-60+oy))

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
        self.grid,self.start,self.exit=make_maze()
        self.ppos=self.start
        self.opt=astar(self.grid,self.start,self.exit)
        self.dice.reset(); self.dice.value=1
        self.maze_mode="WAIT_ROLL"
        self.steps_left=0          # how many steps remain this dice roll
        self.enemy_present=False
        self.epos_tile=None
        self.e_weapon=None
        self.show_pickup=False
        self.pickup_w=None
        diff=DIFFICULTIES[self.diff_name]
        self.p_hp_max=diff["player_hp"]
        self.p_hp=self.p_hp_max
        self.state=S_MAZE

    @property
    def diff(self): return DIFFICULTIES[self.diff_name]

    # ── valid adjacent open tiles ──────────────────────────
    def _valid_moves(self):
        r,c=self.ppos
        moves={}
        for key,dr,dc in [(pygame.K_UP,-1,0),(pygame.K_DOWN,1,0),
                           (pygame.K_LEFT,0,-1),(pygame.K_RIGHT,0,1)]:
            nr,nc=r+dr,c+dc
            if 0<=nr<len(self.grid) and 0<=nc<len(self.grid[0]) and self.grid[nr][nc]==0:
                moves[key]=(nr,nc)
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
            self.maze_mode="WAIT_MOVE"

    def _step_check(self):
        if self.ppos==self.exit:
            self.state=S_WIN; return
        # Spawn enemy if moving along A* optimal path (hidden)
        if not self.enemy_present and self.ppos in self.opt:
            idx=self.opt.index(self.ppos)
            ahead=min(len(self.opt)-1,idx+random.randint(2,3))
            self.epos_tile=self.opt[ahead]
            if not self._weapon_queue:
                self._weapon_queue = [w() for w in ALL_WEAPONS]
                random.shuffle(self._weapon_queue)
            self.e_weapon = self._weapon_queue.pop(0)
            self.enemy_present=True
        # Trigger combat (hidden – player steps on tile silently)
        if self.enemy_present and self.ppos==self.epos_tile:
            self.arena.init_fight(self.p_weapon,self.e_weapon,self.diff)
            # Carry current player HP into combat
            self.arena.player.hp=self.p_hp
            self.arena.player.max_hp=self.p_hp_max
            self.steps_left=0; self.maze_mode="WAIT_ROLL"
            self.state=S_COMBAT

    def _upd_combat(self):
        r=self.arena.update()
        if r=="PLAYER_DEAD":
            self.state=S_OVER
        elif r=="ENEMY_DEAD":
            # Reset player HP back to max
            self.p_hp=self.p_hp_max
            self.pickup_w=self.e_weapon
            self.show_pickup=True
            self.enemy_present=False; self.epos_tile=None
            self.state=S_MAZE

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

        # subtle A* path hint
        for pr,pc in self.opt:
            c.blit(self._hl_gold,(MOX+pc*TILE,MOY+pr*TILE))

        # valid move highlights (adjacent open tiles when it's move time)
        if self.maze_mode=="WAIT_MOVE" and not self.show_pickup:
            for _,nb in self._valid_moves().items():
                nr,nc=nb
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

        txt(c,"MAZE COMBAT",22,GOLD,SCX,22,bold=True)
        # Difficulty badge
        dc=self.diff["col"]
        badge_s=font(14,True).render(f"[ {self.diff_name.upper()} ]",True,dc)
        c.blit(badge_s,(SCX-badge_s.get_width()//2,40))
        sep_line(c,58)

        txt(c,"— DICE —",17,CYAN,SCX,72)

        # Status hint
        if not self.show_pickup:
            if   self.maze_mode=="WAIT_ROLL": hint="Click dice or SPACE to roll"
            elif self.maze_mode=="ROLLING":   hint="Rolling…"
            elif self.maze_mode=="WAIT_MOVE": hint=f"Rolled {self.dice.value}  — Steps left: {self.steps_left}"
            else: hint=""
            if hint: txt(c,hint,15,YELLOW,SCX,88)
        if self.maze_mode=="WAIT_MOVE" and not self.show_pickup:
            txt(c,"Use ↑ ↓ ← → to move",14,(180,220,255),SCX,104)

        self.dice.draw(c)

        sep_line(c,462)

        txt(c,"— PLAYER —",17,CYAN,SCX,478)
        hp_bar(c,SX+20,500,SIDEBAR_W-40,22,self.p_hp,self.p_hp_max,"HP",WHITE)
        txt(c,f"⚔  {self.p_weapon.name}",18,self.p_weapon.col,SCX,546)
        txt(c,f"({self.p_weapon.wtype}   DMG:{self.p_weapon.dmg})",15,WHITE,SCX,564)

        sep_line(c,580)

        controls=[("SPACE","Roll dice"),("Arrows","Move"),("F11","Fullscreen"),("R","Restart")]
        for i,(key,val) in enumerate(controls):
            y=592+i*18
            txt_tl(c,key,13,GOLD,SX+16,y,bold=True)
            txt_tl(c,f"= {val}",13,WHITE,SX+80,y)

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

import pygame
import random
import sys

# --- Constants & Config ---
FPS = 60

# Colors
BG_COLOR = (44, 62, 80)
ROAD_COLOR = (52, 73, 94)
INTERSECTION_COLOR = (41, 58, 76)
STOP_LINE_COLOR = (236, 240, 241)
PANEL_COLOR = (26, 37, 47)
TEXT_COLOR = (236, 240, 241)
YELLOW_LINE = (241, 196, 15)

LIGHT_RED = (231, 76, 60)
LIGHT_YELLOW = (241, 196, 15)
LIGHT_GREEN = (46, 204, 113)
LIGHT_OFF = (30, 40, 50)

CAR_COLORS = [
    (26, 188, 156), (46, 204, 113), (52, 152, 219),
    (155, 89, 182), (241, 196, 15), (230, 126, 34), (231, 76, 60),
    (255, 105, 180), (0, 255, 255)
]

DIR_LIST = ['N', 'E', 'S', 'W']

DIR_CONFIG = {
    'N': {'q1': 'NW', 'q2': 'SW', 'get_rect': lambda p, l: pygame.Rect(375 - 12, p - l/2, 24, l)},
    'E': {'q1': 'NE', 'q2': 'NW', 'get_rect': lambda p, l: pygame.Rect(800 - p - l/2, 375 - 12, l, 24)},
    'S': {'q1': 'SE', 'q2': 'NE', 'get_rect': lambda p, l: pygame.Rect(425 - 12, 800 - p - l/2, 24, l)},
    'W': {'q1': 'SW', 'q2': 'SE', 'get_rect': lambda p, l: pygame.Rect(p - l/2, 425 - 12, l, 24)}
}

# --- Classes ---
class Explosion:
    def __init__(self, rect):
        self.rect = rect
        self.radius = 10
        self.max_radius = 45
        self.alpha = 255
        self.done = False

    def update(self, dt):
        self.radius += 120 * dt
        self.alpha -= 400 * dt
        if self.alpha <= 0:
            self.done = True

    def draw(self, surface):
        if self.alpha > 0 and self.radius > 0:
            s_alpha = max(0, min(255, int(self.alpha)))
            s = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (231, 76, 60, s_alpha), (self.max_radius, self.max_radius), int(self.radius))
            surface.blit(s, (self.rect.centerx - self.max_radius, self.rect.centery - self.max_radius))

class Car:
    def __init__(self, direction, start_pos=-40):
        self.direction = direction
        self.pos = start_pos
        self.vel = random.uniform(80, 120)
        self.max_speed = self.vel
        self.accel = 150
        self.decel = 350
        self.length = 40
        self.locked_q1 = False
        self.locked_q2 = False
        self.color = random.choice(CAR_COLORS)
        self.done = False
        self.state = 'NORMAL'  # NORMAL
        
    def update(self, dt, ahead_car, light_state, locks):
        front = self.pos + self.length / 2
        back = self.pos - self.length / 2

        conf = DIR_CONFIG[self.direction]
        q1_name = conf['q1']
        q2_name = conf['q2']

        obs_pos = float('inf')

        # 1. Car ahead (stop 15px behind)
        if ahead_car:
            obs_pos = min(obs_pos, ahead_car.pos - ahead_car.length / 2 - 15)

        # 2. Stop line boundary (1D space pos=330)
        if front <= 330 and not self.locked_q1:
            stop_at_line = False
            # Signal check
            if light_state == 'RED':
                stop_at_line = True
            elif light_state == 'YELLOW' and front < 280:
                stop_at_line = True
            
            # Intersection locks check    
            if light_state == 'GREEN' or not stop_at_line:
                if locks[q1_name] is not None and locks[q1_name] != self:
                    stop_at_line = True
                    
            if stop_at_line:
                obs_pos = min(obs_pos, 330)
            else:
                if front >= 320 and locks[q1_name] is None:
                    locks[q1_name] = self
                    self.locked_q1 = True

        # 3. Target Q2 boundary (inside intersection)
        if 330 < front <= 400:
            if not self.locked_q2:
                if locks[q2_name] is None:
                    locks[q2_name] = self
                    self.locked_q2 = True
                elif locks[q2_name] != self:
                    # Circular wait causes stop exactly inside Q1 before entering Q2
                    obs_pos = min(obs_pos, 395)

        # Free locks
        if self.locked_q1 and back > 400:
            locks[q1_name] = None
            self.locked_q1 = False
            
        if self.locked_q2 and back > 450:
            locks[q2_name] = None
            self.locked_q2 = False

        # Kinematics
        dist_to_obs = obs_pos - front
        safe_stop_dist = (self.vel ** 2) / (2 * self.decel)

        # Smooth braking
        if dist_to_obs <= safe_stop_dist + 5:
             self.vel -= self.decel * dt
             if self.vel < 0: self.vel = 0
        else:
             self.vel += self.accel * dt
             if self.vel > self.max_speed: self.vel = self.max_speed

        self.pos += self.vel * dt

        # Exit screen
        if self.pos > 850:
             self.done = True
             if self.locked_q1: locks[q1_name] = None
             if self.locked_q2: locks[q2_name] = None

class Controller:
    def __init__(self):
        self.mode = 'NORMAL'  # Modes: NORMAL, DEADLOCK_SIM, DEADLOCK_CRASHED, RESOLVING
        self.cars = {d: [] for d in DIR_LIST}
        self.locks = {"NW": None, "NE": None, "SW": None, "SE": None}
        
        self.lights = {'N': 'GREEN', 'S': 'GREEN', 'E': 'RED', 'W': 'RED'}
        self.timer = 0
        self.phase = 0
        self.spawn_timer = 0
        self.paused = False
        self.speed_mult = 1.0
        self.explosions = []
        
    def toggle_deadlock(self):
        if self.mode == 'NORMAL':
            self.mode = 'DEADLOCK_SIM'
            self.cars = {d: [] for d in DIR_LIST}
            self.locks = {"NW": None, "NE": None, "SW": None, "SE": None}
            self.timer = 0
            
            # Spawn one near intersection from each direction to trigger simultaneous arrival
            for d in DIR_LIST:
                c = Car(d, start_pos=220)
                c.vel = 120
                c.max_speed = 120
                self.cars[d].append(c)
                self.lights[d] = 'GREEN'
        else:
            self.reset()
            
    def resolve_deadlock(self):
        # Resolve by OS Process Termination (Kill one car)
        if self.mode == 'DEADLOCK_CRASHED':
            self.mode = 'RESOLVING'
            for d in DIR_LIST:
                self.lights[d] = 'RED'
            
            victim = self.locks["NW"]
            if victim:
                rect = DIR_CONFIG[victim.direction]['get_rect'](victim.pos, victim.length)
                self.explosions.append(Explosion(rect))
                victim.done = True
                self.locks["NW"] = None
                
    def reset(self):
        self.mode = 'NORMAL'
        self.cars = {d: [] for d in DIR_LIST}
        self.locks = {"NW": None, "NE": None, "SW": None, "SE": None}
        self.phase = 0
        self.timer = 0
        self.explosions = []
        self.update_lights()
        
    def update_lights(self):
        if self.phase == 0:
            self.lights['N'] = self.lights['S'] = 'GREEN'
            self.lights['E'] = self.lights['W'] = 'RED'
        elif self.phase == 1:
            self.lights['N'] = self.lights['S'] = 'YELLOW'
            self.lights['E'] = self.lights['W'] = 'RED'
        elif self.phase == 2:
            self.lights['N'] = self.lights['S'] = 'RED'
            self.lights['E'] = self.lights['W'] = 'GREEN'
        elif self.phase == 3:
            self.lights['N'] = self.lights['S'] = 'RED'
            self.lights['E'] = self.lights['W'] = 'YELLOW'

    def handle_spawning(self, dt):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = random.uniform(0.7, 1.8)
            d = random.choice(DIR_LIST)
            start_pos = -40
            q = self.cars[d]
            # Ensure no collision on spawn
            if not q or (q[-1].pos - q[-1].length/2 > start_pos + 60):
                self.cars[d].append(Car(d, start_pos))

    def update(self, dt):
        if self.paused: return
        dt *= self.speed_mult
        
        # Fair Round-Robin Scheduling
        if self.mode == 'NORMAL':
            self.timer += dt
            if self.phase == 0 and self.timer > 4.0:
                self.phase = 1; self.timer = 0; self.update_lights()
            elif self.phase == 1 and self.timer > 1.5:
                self.phase = 2; self.timer = 0; self.update_lights()
            elif self.phase == 2 and self.timer > 4.0:
                self.phase = 3; self.timer = 0; self.update_lights()
            elif self.phase == 3 and self.timer > 1.5:
                self.phase = 0; self.timer = 0; self.update_lights()
                
            self.handle_spawning(dt)
                    
        elif self.mode == 'DEADLOCK_SIM':
            for d in DIR_LIST: self.lights[d] = 'GREEN'
            
            held = set([c for c in self.locks.values() if c is not None])
            if len(held) == 4:
                # All 4 distinct cars hold 1 quadrant
                if all(c.vel < 5 for c in held):
                    self.mode = 'DEADLOCK_CRASHED'
                    
            self.handle_spawning(dt)
                    
        elif self.mode == 'RESOLVING':
            held = [c for c in self.locks.values() if c is not None]
            if len(held) == 0:
                self.mode = 'NORMAL'
                self.timer = 0
                self.phase = 0
                self.update_lights()
                
        elif self.mode == 'DEADLOCK_CRASHED':
            self.handle_spawning(dt)
                
        # Update explosions
        for exp in self.explosions:
            exp.update(dt)
        self.explosions = [e for e in self.explosions if not e.done]
            
        # Update cars
        for d in DIR_LIST:
            q = self.cars[d]
            for i, car in enumerate(q):
                ahead_car = q[i-1] if i > 0 else None
                car.update(dt, ahead_car, self.lights[d], self.locks)
            # Remove terminated or finished cars
            self.cars[d] = [c for c in q if not c.done]

def draw_road(surface):
    pygame.draw.rect(surface, ROAD_COLOR, (350, 0, 100, 800))
    pygame.draw.rect(surface, ROAD_COLOR, (0, 350, 800, 100))
    pygame.draw.rect(surface, INTERSECTION_COLOR, (350, 350, 100, 100))
    
    # Yellow Double Lines (Middle)
    pygame.draw.line(surface, YELLOW_LINE, (398, 0), (398, 350), 2)
    pygame.draw.line(surface, YELLOW_LINE, (402, 0), (402, 350), 2)
    pygame.draw.line(surface, YELLOW_LINE, (398, 450), (398, 800), 2)
    pygame.draw.line(surface, YELLOW_LINE, (402, 450), (402, 800), 2)
    
    pygame.draw.line(surface, YELLOW_LINE, (0, 398), (350, 398), 2)
    pygame.draw.line(surface, YELLOW_LINE, (0, 402), (350, 402), 2)
    pygame.draw.line(surface, YELLOW_LINE, (450, 398), (800, 398), 2)
    pygame.draw.line(surface, YELLOW_LINE, (450, 402), (800, 402), 2)
    
    # White dashed lane lines
    for i in range(0, 350, 40):
        pygame.draw.line(surface, STOP_LINE_COLOR, (350, i), (350, i+20), 2) 
        pygame.draw.line(surface, STOP_LINE_COLOR, (450, i), (450, i+20), 2) 
        pygame.draw.line(surface, STOP_LINE_COLOR, (350, i+450), (350, i+470), 2)
        pygame.draw.line(surface, STOP_LINE_COLOR, (450, i+450), (450, i+470), 2)
        
        pygame.draw.line(surface, STOP_LINE_COLOR, (i, 350), (i+20, 350), 2)
        pygame.draw.line(surface, STOP_LINE_COLOR, (i, 450), (i+20, 450), 2)
        pygame.draw.line(surface, STOP_LINE_COLOR, (i+450, 350), (i+470, 350), 2)
        pygame.draw.line(surface, STOP_LINE_COLOR, (i+450, 450), (i+470, 450), 2)
        
    # Thick Stop lines
    pygame.draw.rect(surface, STOP_LINE_COLOR, (350, 325, 50, 5)) # N
    pygame.draw.rect(surface, STOP_LINE_COLOR, (400, 470, 50, 5)) # S
    pygame.draw.rect(surface, STOP_LINE_COLOR, (325, 400, 5, 50)) # W
    pygame.draw.rect(surface, STOP_LINE_COLOR, (470, 350, 5, 50)) # E

def draw_lights(surface, ctrl):
    def draw_signal(x, y, state, horizontal=False):
        w, h = (60, 20) if horizontal else (20, 60)
        pygame.draw.rect(surface, (40, 40, 40), (x, y, w, h), border_radius=4)
        pygame.draw.rect(surface, (20, 20, 20), (x, y, w, h), width=2, border_radius=4)
        
        c1, c2, c3 = LIGHT_OFF, LIGHT_OFF, LIGHT_OFF
        if state == 'RED': c1 = LIGHT_RED
        elif state == 'YELLOW': c2 = LIGHT_YELLOW
        elif state == 'GREEN': c3 = LIGHT_GREEN
        
        if horizontal:
            pygame.draw.circle(surface, c1, (x+10, y+10), 6)
            pygame.draw.circle(surface, c2, (x+30, y+10), 6)
            pygame.draw.circle(surface, c3, (x+50, y+10), 6)
            # glow
            if state == 'RED': pygame.draw.circle(surface, c1, (x+10, y+10), 10, 2)
            if state == 'YELLOW': pygame.draw.circle(surface, c2, (x+30, y+10), 10, 2)
            if state == 'GREEN': pygame.draw.circle(surface, c3, (x+50, y+10), 10, 2)
        else:
            pygame.draw.circle(surface, c1, (x+10, y+10), 6)
            pygame.draw.circle(surface, c2, (x+10, y+30), 6)
            pygame.draw.circle(surface, c3, (x+10, y+50), 6)
            if state == 'RED': pygame.draw.circle(surface, c1, (x+10, y+10), 10, 2)
            if state == 'YELLOW': pygame.draw.circle(surface, c2, (x+10, y+30), 10, 2)
            if state == 'GREEN': pygame.draw.circle(surface, c3, (x+10, y+50), 10, 2)

    # N
    draw_signal(320, 250, ctrl.lights['N'])
    # S
    draw_signal(460, 490, ctrl.lights['S'])
    # E
    draw_signal(490, 320, ctrl.lights['E'], horizontal=True)
    # W
    draw_signal(250, 460, ctrl.lights['W'], horizontal=True)

class Button:
    def __init__(self, x, y, w, h, text, font, color, hover_color, action):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(surface, STOP_LINE_COLOR, self.rect, 2, border_radius=8)
            
        txt_surf = self.font.render(self.text, True, TEXT_COLOR)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)
        
    def check_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.action:
                self.action()

class UI:
    def __init__(self, controller):
        pygame.font.init()
        self.ctrl = controller
        
        try:
            self.font = pygame.font.SysFont("segoeui", 22)
            self.title_font = pygame.font.SysFont("segoeui", 28, bold=True)
        except:
            self.font = pygame.font.SysFont("arial", 22)
            self.title_font = pygame.font.SysFont("arial", 28, bold=True)
            
        self.buttons = []
        
        bx, by, bw, bh = 830, 200, 240, 45
        spacing = 60
        
        self.buttons.append(Button(bx, by, bw, bh, "Start / Pause", self.font, (52, 152, 219), (41, 128, 185), lambda: setattr(self.ctrl, 'paused', not self.ctrl.paused)))
        self.buttons.append(Button(bx, by+spacing*1, bw, bh, "Simulate Deadlock", self.font, (231, 76, 60), (192, 57, 43), self.ctrl.toggle_deadlock))
        self.buttons.append(Button(bx, by+spacing*2, bw, bh, "Resolve (Process Kill)", self.font, (46, 204, 113), (39, 174, 96), self.ctrl.resolve_deadlock))
        self.buttons.append(Button(bx, by+spacing*3, bw, bh, "Reset Simulation", self.font, (241, 196, 15), (243, 156, 18), self.ctrl.reset))
        self.buttons.append(Button(bx, by+spacing*4, bw, bh, "Toggle Fast Mode", self.font, (155, 89, 182), (142, 68, 173), self.toggle_speed))
        
    def toggle_speed(self):
        self.ctrl.speed_mult = 3.0 if self.ctrl.speed_mult == 1.0 else 1.0

    def draw(self, surface):
        pygame.draw.rect(surface, PANEL_COLOR, (800, 0, 300, 800))
        pygame.draw.line(surface, STOP_LINE_COLOR, (800, 0), (800, 800), 2)
        
        title = self.title_font.render("OS Scheduler", True, TEXT_COLOR)
        surface.blit(title, (850, 20))
        title2 = self.title_font.render("& Deadlock Sim", True, TEXT_COLOR)
        surface.blit(title2, (830, 55))
        
        # Status
        status_color = LIGHT_GREEN if self.ctrl.mode == 'NORMAL' else LIGHT_RED
        status_text = f"Mode: {self.ctrl.mode}"
        status_surf = self.font.render(status_text, True, status_color)
        surface.blit(status_surf, (820, 110))
        
        # Deadlock Info
        dl_info = "Status: OK (Round-Robin)"
        if self.ctrl.mode == 'DEADLOCK_CRASHED':
            dl_info = "DEADLOCK! Circular wait."
        elif self.ctrl.mode == 'RESOLVING':
            dl_info = "RESOLVING: Killing Process..."
            
        info_surf = self.font.render(dl_info, True, LIGHT_YELLOW if self.ctrl.mode != 'NORMAL' else TEXT_COLOR)
        surface.blit(info_surf, (820, 140))
        
        # Queue count
        y_q = 550
        q_title = self.title_font.render("Process Queues:", True, TEXT_COLOR)
        surface.blit(q_title, (820, y_q))
        
        for i, d in enumerate(DIR_LIST):
            q_txt = self.font.render(f"{d} Queue: {len(self.ctrl.cars[d])}", True, TEXT_COLOR)
            surface.blit(q_txt, (830, y_q + 40 + i*30))
            
        for btn in self.buttons:
            btn.draw(surface)

def main():
    pygame.init()
    screen = pygame.display.set_mode((1100, 800))
    pygame.display.set_caption("OS Concept: Deadlock & Scheduling Simulator")
    clock = pygame.time.Clock()
    
    ctrl = Controller()
    ui = UI(ctrl)
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for btn in ui.buttons:
                btn.check_event(event)
                
        ctrl.update(dt)
        
        # Render
        screen.fill(BG_COLOR)
        draw_road(screen)
        draw_lights(screen, ctrl)
        
        # Draw Quadrant Overlays if Deadlock or Resolving
        if ctrl.mode in ['DEADLOCK_CRASHED', 'RESOLVING']:
            s = pygame.Surface((100, 100), pygame.SRCALPHA)
            s.fill((231, 76, 60, 100))
            screen.blit(s, (350, 350))
            
        # Draw cars
        for d in DIR_LIST:
            for car in ctrl.cars[d]:
                rect = DIR_CONFIG[d]['get_rect'](car.pos, car.length)
                
                # Shadow
                shadow = rect.copy()
                shadow.x += 3; shadow.y += 3
                pygame.draw.rect(screen, (20, 30, 40), shadow, border_radius=6)
                
                # Car
                car_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                
                # Highlight if it has lock but is blocked
                pygame.draw.rect(car_surface, (*car.color, 255), (0, 0, rect.width, rect.height), border_radius=6)
                screen.blit(car_surface, rect.topleft)
                pygame.draw.rect(screen, (30, 30, 30), rect, width=1, border_radius=6)
                
                # Brake lights
                if car.vel < car.max_speed * 0.5:
                    if d == 'N': pygame.draw.rect(screen, (255,0,0), (rect.left+4, rect.top+2, 16, 4))
                    if d == 'S': pygame.draw.rect(screen, (255,0,0), (rect.left+4, rect.bottom-6, 16, 4))
                    if d == 'E': pygame.draw.rect(screen, (255,0,0), (rect.right-6, rect.top+4, 4, 16))
                    if d == 'W': pygame.draw.rect(screen, (255,0,0), (rect.left+2, rect.top+4, 4, 16))

        for exp in ctrl.explosions:
            exp.draw(screen)

        ui.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

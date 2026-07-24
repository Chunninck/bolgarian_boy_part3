import pygame
import pygine

screen_width = 800
screen_height = 600
gravity = 0.5
jump_strength = -10
move_speed = 200
frame_w = 64
frame_h = 64
platform_speed = 80
yellow_trap_speed = 60

def load_frames_by_numbers(path, tile_width, tile_height, frame_numbers):
    sheet = pygame.image.load(path).convert_alpha()
    sheet_w, sheet_h = sheet.get_size()
    cols = sheet_w // tile_width
    frames = []
    for num in frame_numbers:
        row = num // cols
        col = num % cols
        x = col * tile_width
        y = row * tile_height
        rect = pygame.Rect(x, y, tile_width, tile_height)
        frames.append(sheet.subsurface(rect))
    return frames

class Animation:
    def __init__(self, frames, fps=8, loop=True):
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.frame_duration = 1.0 / fps
        self.current_frame = 0
        self.timer = 0.0
        self.done = False

    def update(self, dt):
        if self.done:
            return
        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer -= self.frame_duration
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.done = True

    def get_image(self):
        return self.frames[self.current_frame]

    def reset(self):
        self.current_frame = 0
        self.timer = 0.0
        self.done = False

class Player:
    def __init__(self, x, y, frames_a, frames_b, max_jumps=2):
        self.state = "a"
        self.frames_a = frames_a
        self.frames_b = frames_b
        self.current_frames = frames_a
        self.anim_stance = Animation(frames_a["stance"], fps=8, loop=True)
        self.anim_run = Animation(frames_a["run"], fps=8, loop=True)
        self.anim_jump = Animation(frames_a["jump_fall"], fps=8, loop=True)
        self.current_anim = self.anim_stance
        self.x = x
        self.y = y
        self.width = self.anim_stance.get_image().get_width()
        self.height = self.anim_stance.get_image().get_height()
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.max_jumps = max_jumps
        self.jumps_left = max_jumps
        self.jump_key_down = False
        self.current_platform = None
        self.coins = 0

        self.dash_active = False
        self.dash_timer = 0.0
        self.dash_duration = 0.15
        self.dash_speed = 600
        self.dash_key_down = False
        self.invincible = False

    def switch_state(self):
        self.state = "b" if self.state == "a" else "a"
        if self.state == "a":
            self.current_frames = self.frames_a
        else:
            self.current_frames = self.frames_b
        prev_anim_type = None
        if self.current_anim == self.anim_stance:
            prev_anim_type = "stance"
        elif self.current_anim == self.anim_run:
            prev_anim_type = "run"
        elif self.current_anim == self.anim_jump:
            prev_anim_type = "jump_fall"
        self.anim_stance = Animation(self.current_frames["stance"], fps=8, loop=True)
        self.anim_run = Animation(self.current_frames["run"], fps=8, loop=True)
        self.anim_jump = Animation(self.current_frames["jump_fall"], fps=8, loop=True)
        if prev_anim_type == "stance":
            self.current_anim = self.anim_stance
        elif prev_anim_type == "run":
            self.current_anim = self.anim_run
        elif prev_anim_type == "jump_fall":
            self.current_anim = self.anim_jump
        else:
            self.current_anim = self.anim_stance

    def update(self, dt, keys, platforms, traps, coins, bouncy_platforms):
        if self.dash_active:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.dash_active = False
                self.invincible = False
                self.vel_x = 0
            else:
                self.x += self.vel_x * dt
                if self.x < 0:
                    self.x = 0
                if self.x + self.width > screen_width:
                    self.x = screen_width - self.width
                return "alive"

        self.vel_x = 0
        if keys[pygame.K_a]:
            self.vel_x = -move_speed
        if keys[pygame.K_d]:
            self.vel_x = move_speed

        if self.vel_x != 0:
            self.facing_right = self.vel_x > 0

        dash_key = keys[pygame.K_r]
        if dash_key and not self.dash_key_down and self.coins >= 5 and not self.dash_active:
            self.coins -= 5
            self.dash_active = True
            self.dash_timer = self.dash_duration
            self.invincible = True
            self.vel_x = self.dash_speed if self.facing_right else -self.dash_speed
            self.vel_y = 0
            self.on_ground = False
            self.current_platform = None
            self.dash_key_down = True
            return "alive"
        elif not dash_key:
            self.dash_key_down = False

        self.x += self.vel_x * dt

        for plat in platforms:
            if self.x + self.width > plat.x and self.x < plat.x + plat.width:
                if self.y + self.height > plat.y and self.y < plat.y + plat.height:
                    if self.vel_x > 0:
                        self.x = plat.x - self.width
                    elif self.vel_x < 0:
                        self.x = plat.x + plat.width

        if self.x < 0:
            self.x = 0
        if self.x + self.width > screen_width:
            self.x = screen_width - self.width

        self.vel_y += gravity
        self.y += self.vel_y
        self.on_ground = False
        self.current_platform = None

        for plat in platforms:
            if self.x + self.width > plat.x and self.x < plat.x + plat.width:
                if self.vel_y > 0 and self.y + self.height >= plat.y and self.y < plat.y:
                    self.y = plat.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                    self.current_platform = plat
                    if isinstance(plat, FallingPlatform) and not plat.falling:
                        plat.start_fall()
                elif self.vel_y < 0 and self.y <= plat.y + plat.height and self.y + self.height > plat.y + plat.height:
                    self.y = plat.y + plat.height
                    self.vel_y = 0

        if self.on_ground:
            self.jumps_left = self.max_jumps
            if self.current_platform is not None:
                if isinstance(self.current_platform, MovingPlatform):
                    self.x += self.current_platform.vx * dt
                elif isinstance(self.current_platform, VerticalMovingPlatform):
                    self.y += self.current_platform.vy * dt

        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for bp in bouncy_platforms:
            if player_rect.colliderect(pygame.Rect(bp.x, bp.y, bp.width, bp.height)):
                if self.vel_y > 0 and self.y + self.height >= bp.y and self.y < bp.y:
                    self.vel_y = -16
                    self.on_ground = False
                    self.current_platform = None

        if not self.invincible:
            for trap in traps:
                if player_rect.colliderect(trap.get_rect()):
                    return "dead"

        for coin in coins[:]:
            if player_rect.colliderect(pygame.Rect(coin.x, coin.y, coin.width, coin.height)):
                coins.remove(coin)
                self.coins += 1

        jump_key = keys[pygame.K_w] or keys[pygame.K_SPACE]
        if jump_key and not self.jump_key_down and self.jumps_left > 0:
            self.vel_y = jump_strength
            self.jumps_left -= 1
            self.on_ground = False
            self.current_platform = None
        self.jump_key_down = jump_key

        if not self.on_ground:
            self.current_anim = self.anim_jump
        elif self.vel_x != 0:
            self.current_anim = self.anim_run
        else:
            self.current_anim = self.anim_stance

        self.current_anim.update(dt)
        return "alive"

    def get_image(self):
        image = self.current_anim.get_image()
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
        return image

    def draw(self, surface):
        surface.blit(self.get_image(), (self.x, self.y))

class Platform:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def update(self, dt):
        pass

    def draw(self, surface):
        pygame.draw.rect(surface, (100, 100, 100), (self.x, self.y, self.width, self.height))

class MovingPlatform(Platform):
    def __init__(self, x, y, width, height, left_bound, right_bound):
        super().__init__(x, y, width, height)
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.vx = 0

    def update(self, dt):
        if self.vx != 0:
            self.x += self.vx * dt
            if self.x < self.left_bound:
                self.x = self.left_bound
                self.vx = 0
            elif self.x + self.width > self.right_bound:
                self.x = self.right_bound - self.width
                self.vx = 0

    def draw(self, surface):
        pygame.draw.rect(surface, (150, 150, 150), (self.x, self.y, self.width, self.height))

class VerticalMovingPlatform(Platform):
    def __init__(self, x, y, width, height, top_bound, bottom_bound):
        super().__init__(x, y, width, height)
        self.top_bound = top_bound
        self.bottom_bound = bottom_bound
        self.vy = 60

    def update(self, dt):
        self.y += self.vy * dt
        if self.y < self.top_bound:
            self.y = self.top_bound
            self.vy = -self.vy
        elif self.y + self.height > self.bottom_bound:
            self.y = self.bottom_bound - self.height
            self.vy = -self.vy

    def draw(self, surface):
        pygame.draw.rect(surface, (150, 150, 200), (self.x, self.y, self.width, self.height))

class FallingPlatform(Platform):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.falling = False
        self.fall_vy = 0
        self.alive = True

    def start_fall(self):
        self.falling = True

    def update(self, dt):
        if self.falling:
            self.fall_vy += gravity
            self.y += self.fall_vy
            if self.y > screen_height:
                self.alive = False

    def draw(self, surface):
        pygame.draw.rect(surface, (200, 100, 100), (self.x, self.y, self.width, self.height))

class YellowTrap:
    def __init__(self, x, y, size, left_bound, right_bound):
        self.x = x
        self.y = y
        self.size = size
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.vx = yellow_trap_speed

    def update(self, dt):
        self.x += self.vx * dt
        if self.x < self.left_bound:
            self.x = self.left_bound
            self.vx = -self.vx
        elif self.x + self.size > self.right_bound:
            self.x = self.right_bound - self.size
            self.vx = -self.vx

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, surface):
        cx = self.x + self.size // 2
        cy = self.y + self.size // 2
        points = [(cx, self.y), (self.x + self.size, cy), (cx, self.y + self.size), (self.x, cy)]
        pygame.draw.polygon(surface, (255, 255, 0), points)

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 0), (self.x + 8, self.y + 8), 8)

class BouncyPlatform(Platform):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

    def draw(self, surface):
        pygame.draw.rect(surface, (0, 200, 0), (self.x, self.y, self.width, self.height))

class PrologueScene(pygine.Scene):
    def __init__(self, name="PrologueScene"):
        super().__init__(name=name)
        self.next_scene = None
        self.bg = pygame.image.load("подвал2.png").convert()

        stance_numbers = [0, 1, 2, 3]
        run_numbers = [4, 5, 6, 7, 8, 9, 10, 11]
        jump_fall_numbers = [42, 43, 44, 45, 46, 47]
        frames_a = {
            "stance": load_frames_by_numbers("player.png", frame_w, frame_h, stance_numbers),
            "run": load_frames_by_numbers("player.png", frame_w, frame_h, run_numbers),
            "jump_fall": load_frames_by_numbers("player.png", frame_w, frame_h, jump_fall_numbers)
        }
        frames_b = {
            "stance": load_frames_by_numbers("playerp.png", frame_w, frame_h, stance_numbers),
            "run": load_frames_by_numbers("playerp.png", frame_w, frame_h, run_numbers),
            "jump_fall": load_frames_by_numbers("playerp.png", frame_w, frame_h, jump_fall_numbers)
        }

        self.ground = Platform(0, 500, screen_width, 20)
        self.player = Player(300, 500 - frame_h, frames_a, frames_b, max_jumps=2)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        status = self.player.update(dt, keys, [self.ground], [], [], [])
        if status == "dead":
            self.player = Player(300, 500 - frame_h, self.player.frames_a, self.player.frames_b, max_jumps=2)
        if self.player.x + self.player.width >= screen_width:
            self.next_scene = "main"

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))
        self.player.draw(screen)

class DualityScene(pygine.Scene):
    def __init__(self, name="DualityScene"):
        super().__init__(name=name)
        self.next_scene = None
        self.level = 0
        self.bg = pygame.image.load("подвал.jpg").convert()
        self.font = pygame.font.Font(None, 30)

        # 20 уровней с постепенным усложнением
        self.levels = [
            # 0 – ровный пол, только монеты
            {"static": [Platform(0, 500, screen_width, 20)],
             "coins": [(100, 480), (300, 480), (500, 480), (700, 480)],
             "player_start": (50, 500 - frame_h)},
            # 1 – движущаяся платформа
            {"static": [Platform(0, 500, 200, 20), Platform(350, 500, 150, 20), Platform(600, 500, 200, 20)],
             "moving": [{"x": 250, "y": 440, "width": 80, "height": 20, "left_bound": 200, "right_bound": 450}],
             "coins": [(280, 420), (500, 480)],
             "player_start": (30, 500 - frame_h)},
            # 2 – жёлтая ловушка
            {"static_a": [Platform(0, 550, 400, 20), Platform(100, 480, 100, 20), Platform(300, 410, 100, 20)],
             "static_b": [Platform(400, 550, 400, 20), Platform(550, 450, 100, 20), Platform(700, 380, 100, 20)],
             "traps": [{"type": "yellow", "x": 200, "y": 520, "size": 20, "left_bound": 180, "right_bound": 280}],
             "coins": [(200, 460), (600, 370)],
             "player_start": (50, 550 - frame_h)},
            # 3 – вертикальная платформа
            {"static": [Platform(0, 500, 150, 20), Platform(250, 420, 100, 20), Platform(400, 340, 100, 20), Platform(550, 260, 150, 20), Platform(740, 200, 50, 20)],
             "vertical": [{"x": 180, "y": 450, "width": 60, "height": 20, "top_bound": 380, "bottom_bound": 500}],
             "coins": [(200, 400), (450, 320), (650, 240)],
             "player_start": (20, 500 - frame_h)},
            # 4 – батут
            {"static_a": [Platform(0, 550, 200, 20), Platform(350, 480, 80, 20)],
             "static_b": [Platform(300, 550, 200, 20), Platform(600, 420, 100, 20), Platform(750, 360, 50, 20)],
             "bouncy": [{"x": 500, "y": 420, "width": 60, "height": 15}],
             "coins": [(280, 460), (620, 400)],
             "player_start": (50, 550 - frame_h)},
            # 5 – падающая платформа
            {"static_a": [Platform(0, 550, 250, 20), Platform(400, 480, 80, 20)],
             "static_b": [Platform(350, 550, 250, 20), Platform(650, 450, 100, 20), Platform(760, 380, 40, 20)],
             "falling": [{"x": 520, "y": 480, "width": 70, "height": 20}],
             "coins": [(450, 460)],
             "player_start": (50, 550 - frame_h)},
            # 6 – полностью из падающих платформ
            {"static": [],
             "falling": [{"x": 0, "y": 500, "width": 100, "height": 20},
                         {"x": 130, "y": 480, "width": 90, "height": 20},
                         {"x": 250, "y": 460, "width": 90, "height": 20},
                         {"x": 370, "y": 440, "width": 90, "height": 20},
                         {"x": 490, "y": 420, "width": 90, "height": 20},
                         {"x": 610, "y": 400, "width": 90, "height": 20},
                         {"x": 730, "y": 380, "width": 60, "height": 20}],
             "coins": [(200, 460), (400, 440), (600, 420)],
             "player_start": (20, 500 - frame_h)},
            # 7 – вертикальная платформа + ловушка
            {"static_a": [Platform(0, 550, 120, 20), Platform(220, 500, 80, 20)],
             "static_b": [Platform(130, 550, 120, 20), Platform(330, 480, 80, 20), Platform(580, 400, 80, 20)],
             "vertical": [{"x": 150, "y": 400, "width": 60, "height": 20, "top_bound": 300, "bottom_bound": 480}],
             "traps": [{"type": "yellow", "x": 250, "y": 460, "size": 20, "left_bound": 220, "right_bound": 320}],
             "coins": [(200, 480), (450, 400)],
             "player_start": (30, 550 - frame_h)},
            # 8 – две ловушки и батут
            {"static_a": [Platform(0, 550, 150, 20), Platform(250, 480, 100, 20), Platform(450, 410, 80, 20)],
             "static_b": [Platform(200, 550, 150, 20), Platform(400, 450, 100, 20), Platform(600, 380, 100, 20), Platform(750, 340, 50, 20)],
             "traps": [{"type": "yellow", "x": 300, "y": 460, "size": 20, "left_bound": 280, "right_bound": 380},
                       {"type": "yellow", "x": 550, "y": 380, "size": 20, "left_bound": 520, "right_bound": 620}],
             "bouncy": [{"x": 450, "y": 410, "width": 60, "height": 15}],
             "coins": [(200, 460), (500, 360)],
             "player_start": (50, 550 - frame_h)},
            # 9 – много вертикальных и падающих
            {"static_a": [Platform(0, 550, 120, 20), Platform(220, 500, 80, 20)],
             "static_b": [Platform(130, 550, 120, 20), Platform(330, 480, 80, 20), Platform(580, 400, 80, 20), Platform(730, 360, 60, 20)],
             "vertical": [{"x": 150, "y": 400, "width": 60, "height": 20, "top_bound": 300, "bottom_bound": 480},
                          {"x": 500, "y": 380, "width": 60, "height": 20, "top_bound": 280, "bottom_bound": 450}],
             "falling": [{"x": 450, "y": 440, "width": 70, "height": 20}],
             "coins": [(250, 480), (420, 420), (650, 380)],
             "player_start": (30, 550 - frame_h)},
            # 10 – все элементы
            {"static_a": [Platform(0, 550, 80, 20), Platform(180, 490, 60, 20)],
             "static_b": [Platform(100, 550, 80, 20), Platform(260, 480, 60, 20), Platform(430, 400, 60, 20), Platform(600, 330, 60, 20), Platform(740, 280, 50, 20)],
             "vertical": [{"x": 200, "y": 450, "width": 60, "height": 20, "top_bound": 380, "bottom_bound": 520},
                          {"x": 500, "y": 380, "width": 60, "height": 20, "top_bound": 300, "bottom_bound": 450}],
             "falling": [{"x": 350, "y": 480, "width": 70, "height": 20}],
             "bouncy": [{"x": 700, "y": 280, "width": 50, "height": 15}],
             "traps": [{"type": "yellow", "x": 300, "y": 500, "size": 24, "left_bound": 280, "right_bound": 380},
                       {"type": "yellow", "x": 600, "y": 350, "size": 24, "left_bound": 580, "right_bound": 680}],
             "coins": [(150, 470), (350, 410), (550, 350), (700, 260)],
             "player_start": (10, 550 - frame_h)},
            # Уровни 11-19: постепенное усложнение с большим количеством ловушек и платформ
            {"static": [Platform(0, 500, 200, 20), Platform(300, 450, 100, 20), Platform(500, 400, 100, 20), Platform(700, 350, 80, 20)],
             "vertical": [{"x": 250, "y": 400, "width": 60, "height": 20, "top_bound": 350, "bottom_bound": 480}],
             "traps": [{"type": "yellow", "x": 400, "y": 430, "size": 24, "left_bound": 380, "right_bound": 480}],
             "coins": [(350, 430), (600, 380)],
             "player_start": (30, 500 - frame_h)},
            {"static": [Platform(0, 500, 150, 20), Platform(250, 430, 100, 20), Platform(450, 370, 100, 20), Platform(650, 320, 100, 20), Platform(800, 280, 50, 20)],
             "moving": [{"x": 180, "y": 460, "width": 80, "height": 20, "left_bound": 150, "right_bound": 300}],
             "traps": [{"type": "yellow", "x": 350, "y": 410, "size": 24, "left_bound": 320, "right_bound": 420}],
             "coins": [(280, 440), (550, 350)],
             "player_start": (20, 500 - frame_h)},
            {"static_a": [Platform(0, 550, 200, 20), Platform(300, 480, 100, 20), Platform(500, 420, 80, 20)],
             "static_b": [Platform(150, 550, 200, 20), Platform(400, 500, 100, 20), Platform(600, 440, 80, 20), Platform(740, 400, 50, 20)],
             "falling": [{"x": 400, "y": 480, "width": 70, "height": 20}],
             "bouncy": [{"x": 600, "y": 420, "width": 60, "height": 15}],
             "coins": [(250, 460), (550, 400)],
             "player_start": (50, 550 - frame_h)},
            {"static": [Platform(0, 500, 100, 20), Platform(200, 440, 80, 20), Platform(380, 380, 80, 20), Platform(560, 320, 80, 20), Platform(740, 280, 50, 20)],
             "vertical": [{"x": 130, "y": 460, "width": 60, "height": 20, "top_bound": 400, "bottom_bound": 520},
                          {"x": 450, "y": 360, "width": 60, "height": 20, "top_bound": 300, "bottom_bound": 420}],
             "traps": [{"type": "yellow", "x": 300, "y": 420, "size": 24, "left_bound": 280, "right_bound": 380}],
             "coins": [(250, 480), (450, 360), (650, 300)],
             "player_start": (20, 500 - frame_h)},
            {"static_a": [Platform(0, 550, 120, 20), Platform(220, 500, 80, 20), Platform(420, 440, 80, 20)],
             "static_b": [Platform(150, 550, 120, 20), Platform(350, 490, 80, 20), Platform(550, 420, 80, 20), Platform(720, 380, 60, 20)],
             "moving": [{"x": 300, "y": 470, "width": 80, "height": 20, "left_bound": 250, "right_bound": 400}],
             "traps": [{"type": "yellow", "x": 500, "y": 420, "size": 24, "left_bound": 480, "right_bound": 580}],
             "bouncy": [{"x": 650, "y": 420, "width": 50, "height": 15}],
             "coins": [(300, 480), (550, 400)],
             "player_start": (30, 550 - frame_h)},
            {"static": [Platform(0, 500, 200, 20), Platform(350, 460, 100, 20), Platform(550, 400, 100, 20), Platform(750, 360, 50, 20)],
             "falling": [{"x": 250, "y": 460, "width": 70, "height": 20},
                         {"x": 450, "y": 400, "width": 70, "height": 20}],
             "coins": [(300, 440), (600, 380)],
             "player_start": (30, 500 - frame_h)},
            {"static_a": [Platform(0, 550, 150, 20), Platform(250, 490, 100, 20)],
             "static_b": [Platform(200, 550, 150, 20), Platform(400, 480, 100, 20), Platform(600, 410, 100, 20), Platform(750, 360, 50, 20)],
             "vertical": [{"x": 350, "y": 450, "width": 60, "height": 20, "top_bound": 380, "bottom_bound": 500},
                          {"x": 650, "y": 380, "width": 60, "height": 20, "top_bound": 320, "bottom_bound": 440}],
             "traps": [{"type": "yellow", "x": 500, "y": 440, "size": 24, "left_bound": 480, "right_bound": 580}],
             "coins": [(300, 470), (550, 390)],
             "player_start": (50, 550 - frame_h)},
            {"static": [Platform(0, 500, 100, 20), Platform(200, 440, 80, 20), Platform(400, 380, 80, 20), Platform(600, 320, 80, 20), Platform(760, 280, 40, 20)],
             "vertical": [{"x": 300, "y": 420, "width": 60, "height": 20, "top_bound": 360, "bottom_bound": 480}],
             "falling": [{"x": 500, "y": 380, "width": 70, "height": 20}],
             "bouncy": [{"x": 700, "y": 320, "width": 50, "height": 15}],
             "traps": [{"type": "yellow", "x": 400, "y": 420, "size": 24, "left_bound": 380, "right_bound": 480}],
             "coins": [(250, 480), (450, 400), (650, 340)],
             "player_start": (20, 500 - frame_h)},
            # Уровень 19 – финальный, сложнейший
            {"static_a": [Platform(0, 550, 80, 20), Platform(180, 490, 60, 20), Platform(350, 430, 60, 20), Platform(520, 370, 60, 20)],
             "static_b": [Platform(100, 550, 80, 20), Platform(260, 480, 60, 20), Platform(430, 400, 60, 20), Platform(600, 330, 60, 20), Platform(740, 280, 50, 20)],
             "vertical": [{"x": 200, "y": 450, "width": 60, "height": 20, "top_bound": 380, "bottom_bound": 520},
                          {"x": 500, "y": 380, "width": 60, "height": 20, "top_bound": 300, "bottom_bound": 450}],
             "falling": [{"x": 350, "y": 480, "width": 70, "height": 20},
                         {"x": 600, "y": 330, "width": 60, "height": 20}],
             "bouncy": [{"x": 700, "y": 280, "width": 50, "height": 15}],
             "traps": [{"type": "yellow", "x": 300, "y": 500, "size": 24, "left_bound": 280, "right_bound": 380},
                       {"type": "yellow", "x": 600, "y": 350, "size": 24, "left_bound": 580, "right_bound": 680},
                       {"type": "yellow", "x": 450, "y": 380, "size": 24, "left_bound": 430, "right_bound": 530}],
             "coins": [(150, 470), (350, 410), (550, 350), (700, 260)],
             "player_start": (10, 550 - frame_h)}
        ]
        self.g_pressed = False
        self.moving_platforms = []
        self.vertical_platforms = []
        self.falling_platforms = []
        self.traps = []
        self.coins = []
        self.bouncy_platforms = []
        self.dual_platforms = False
        self.static_platforms_a = []
        self.static_platforms_b = []
        self.static_platforms = []

    def load_frames(self):
        stance_numbers = [0, 1, 2, 3]
        run_numbers = [4, 5, 6, 7, 8, 9, 10, 11]
        jump_fall_numbers = [42, 43, 44, 45, 46, 47]
        self.frames_a = {
            "stance": load_frames_by_numbers("player.png", frame_w, frame_h, stance_numbers),
            "run": load_frames_by_numbers("player.png", frame_w, frame_h, run_numbers),
            "jump_fall": load_frames_by_numbers("player.png", frame_w, frame_h, jump_fall_numbers)
        }
        self.frames_b = {
            "stance": load_frames_by_numbers("playerp.png", frame_w, frame_h, stance_numbers),
            "run": load_frames_by_numbers("playerp.png", frame_w, frame_h, run_numbers),
            "jump_fall": load_frames_by_numbers("playerp.png", frame_w, frame_h, jump_fall_numbers)
        }

    def setup(self):
        if self.level >= len(self.levels):
            self.next_scene = "victory"
            return
        level_data = self.levels[self.level]

        old_coins = 0
        if hasattr(self, 'player'):
            old_coins = self.player.coins

        self.dual_platforms = "static_a" in level_data
        self.static_platforms_a = []
        self.static_platforms_b = []
        self.static_platforms = []

        if self.dual_platforms:
            for p in level_data["static_a"]:
                self.static_platforms_a.append(Platform(p.x, p.y, p.width, p.height))
            for p in level_data["static_b"]:
                self.static_platforms_b.append(Platform(p.x, p.y, p.width, p.height))
        else:
            self.static_platforms = level_data.get("static", [])

        self.moving_platforms = []
        for mp_data in level_data.get("moving", []):
            self.moving_platforms.append(
                MovingPlatform(mp_data["x"], mp_data["y"],
                               mp_data["width"], mp_data["height"],
                               mp_data["left_bound"], mp_data["right_bound"])
            )

        self.vertical_platforms = []
        for vp_data in level_data.get("vertical", []):
            self.vertical_platforms.append(
                VerticalMovingPlatform(vp_data["x"], vp_data["y"],
                                       vp_data["width"], vp_data["height"],
                                       vp_data["top_bound"], vp_data["bottom_bound"])
            )

        self.falling_platforms = []
        for fp_data in level_data.get("falling", []):
            self.falling_platforms.append(
                FallingPlatform(fp_data["x"], fp_data["y"],
                                fp_data["width"], fp_data["height"])
            )

        self.traps = []
        for t_data in level_data.get("traps", []):
            if t_data["type"] == "yellow":
                self.traps.append(YellowTrap(t_data["x"], t_data["y"], t_data["size"],
                                            t_data["left_bound"], t_data["right_bound"]))

        self.coins = []
        for (cx, cy) in level_data.get("coins", []):
            self.coins.append(Coin(cx, cy))

        self.bouncy_platforms = []
        for bp_data in level_data.get("bouncy", []):
            self.bouncy_platforms.append(BouncyPlatform(bp_data["x"], bp_data["y"],
                                                       bp_data["width"], bp_data["height"]))

        start_x, start_y = level_data["player_start"]
        self.player = Player(start_x, start_y, self.frames_a, self.frames_b, max_jumps=2)
        self.player.coins = old_coins
        self.g_pressed = False

    def on_enter(self):
        self.load_frames()
        self.level = 0
        self.setup()

    def get_current_platforms(self):
        platforms = []
        if self.dual_platforms:
            platforms += self.static_platforms_a if self.player.state == "a" else self.static_platforms_b
        else:
            platforms += self.static_platforms
        platforms += self.moving_platforms + self.vertical_platforms + self.falling_platforms
        return platforms

    def update(self, dt):
        if self.next_scene:
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_g] and not self.g_pressed:
            self.player.switch_state()
            self.g_pressed = True
        elif not keys[pygame.K_g]:
            self.g_pressed = False

        for mp in self.moving_platforms:
            if self.player.state == "b":
                mp.vx = -platform_speed
            else:
                mp.vx = platform_speed
            mp.update(dt)

        for vp in self.vertical_platforms:
            vp.update(dt)

        for fp in self.falling_platforms[:]:
            fp.update(dt)
            if not fp.alive:
                self.falling_platforms.remove(fp)

        for trap in self.traps:
            trap.update(dt)

        all_platforms = self.get_current_platforms()
        status = self.player.update(dt, keys, all_platforms, self.traps, self.coins, self.bouncy_platforms)

        if status == "dead" or self.player.y > screen_height:
            self.setup()

        if self.player.x + self.player.width >= screen_width:
            self.level += 1
            self.setup()

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))

        all_platforms = self.get_current_platforms()
        for plat in all_platforms:
            plat.draw(screen)

        for bp in self.bouncy_platforms:
            bp.draw(screen)

        for trap in self.traps:
            trap.draw(screen)

        for coin in self.coins:
            coin.draw(screen)

        self.player.draw(screen)

        level_text = self.font.render(f"Level {self.level+1}/{len(self.levels)}", True, (255, 255, 255))
        coin_text = self.font.render(f"Coins: {self.player.coins}", True, (255, 255, 0))
        dash_text = self.font.render("Press R to dash (5 coins)", True, (200, 200, 200))
        screen.blit(level_text, (10, 10))
        screen.blit(coin_text, (10, 40))
        screen.blit(dash_text, (10, 70))

class VictoryScene(pygine.Scene):
    def __init__(self, name="Victory"):
        super().__init__(name=name)
        self.next_scene = None
        self.font_big = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 36)
        self.timer = 0

    def on_enter(self):
        self.timer = 3

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.next_scene = "menu"

    def draw(self, screen):
        screen.fill((0, 0, 0))
        text = self.font_big.render("Вы победили!", True, (255, 215, 0))
        screen.blit(text, (screen_width//2 - text.get_width()//2, screen_height//2 - 50))
        prompt = self.font_small.render("Возврат в меню...", True, (200, 200, 200))
        screen.blit(prompt, (screen_width//2 - prompt.get_width()//2, screen_height//2 + 20))

class MenuScene(pygine.Scene):
    def __init__(self, name="Menu"):
        super().__init__(name=name)
        self.next_scene = None
        try:
            self.bg = pygame.image.load("меню.png").convert()
        except:
            self.bg = None
        self.font_title = pygame.font.Font(None, 74)
        self.font_prompt = pygame.font.Font(None, 36)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            self.next_scene = "prologue"

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
        else:
            screen.fill((20, 20, 20))
        title = self.font_title.render("Bolgarian Boy 3 DEMO", True, (255, 255, 255))
        prompt = self.font_prompt.render("Press ENTER to Start", True, (200, 200, 200))
        screen.blit(title, (screen_width // 2 - title.get_width() // 2, 200))
        screen.blit(prompt, (screen_width // 2 - prompt.get_width() // 2, 350))

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Shakal studio: Bolgarian boy 3 DEMO")
    clock = pygame.time.Clock()

    menu = MenuScene(name="menu")
    prologue = PrologueScene(name="prologue")
    game = DualityScene(name="main")
    victory = VictoryScene(name="victory")
    scenes = {"menu": menu, "prologue": prologue, "main": game, "victory": victory}
    current_scene = "menu"

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        scene = scenes[current_scene]
        scene.update(dt)

        if hasattr(scene, 'next_scene') and scene.next_scene:
            current_scene = scene.next_scene
            scene.next_scene = None
            if current_scene == "main":
                game.on_enter()
            elif current_scene == "victory":
                victory.on_enter()

        scene.draw(screen)
        pygame.display.flip()

    pygame.quit()
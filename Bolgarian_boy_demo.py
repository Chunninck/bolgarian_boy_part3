import pygame
import pygine

screen_width = 800
screen_height = 600
gravity = 0.5
jump_strength = -10
move_speed = 200
bg_color = (30, 30, 30)
frame_w = 64
frame_h = 64
platform_speed = 80
laser_speed = 60

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
    def __init__(self, x, y, frames_a, frames_b):
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
        self.jumps_left = 2

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

    def update(self, dt, keys, platforms):
        self.vel_x = 0
        if keys[pygame.K_a]:
            self.vel_x = -move_speed
        if keys[pygame.K_d]:
            self.vel_x = move_speed

        if self.vel_x != 0:
            self.facing_right = self.vel_x > 0

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

        for plat in platforms:
            if self.x + self.width > plat.x and self.x < plat.x + plat.width:
                if self.vel_y > 0 and self.y + self.height >= plat.y and self.y < plat.y:
                    self.y = plat.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0 and self.y <= plat.y + plat.height and self.y + self.height > plat.y + plat.height:
                    self.y = plat.y + plat.height
                    self.vel_y = 0

        if self.on_ground:
            self.jumps_left = 2
            for plat in platforms:
                if isinstance(plat, MovingPlatform):
                    if (self.x + self.width > plat.x and self.x < plat.x + plat.width and
                        abs((self.y + self.height) - plat.y) < 2):
                        self.x += plat.vx * dt

        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.jumps_left > 0:
            self.vel_y = jump_strength
            self.jumps_left -= 1
            self.on_ground = False

        if not self.on_ground:
            self.current_anim = self.anim_jump
        elif self.vel_x != 0:
            self.current_anim = self.anim_run
        else:
            self.current_anim = self.anim_stance

        self.current_anim.update(dt)

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
        self.x += self.vx * dt
        if self.x < self.left_bound:
            self.x = self.left_bound
            self.vx = 0
        elif self.x + self.width > self.right_bound:
            self.x = self.right_bound - self.width
            self.vx = 0

    def draw(self, surface):
        pygame.draw.rect(surface, (150, 150, 150), (self.x, self.y, self.width, self.height))

class LaserTrap:
    def __init__(self, x, y, width, height, left_bound, right_bound):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.vx = laser_speed

    def update(self, dt):
        self.x += self.vx * dt
        if self.x < self.left_bound:
            self.x = self.left_bound
            self.vx = -self.vx
        elif self.x + self.width > self.right_bound:
            self.x = self.right_bound - self.width
            self.vx = -self.vx

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), (self.x, self.y, self.width, self.height))

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
        self.player = Player(300, 500 - frame_h, frames_a, frames_b)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, [self.ground])
        if self.player.x + self.player.width >= screen_width:
            self.next_scene = "main"

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))
        self.player.draw(screen)

class DualityScene(pygine.Scene):
    def __init__(self, name="DualityScene"):
        super().__init__(name=name)
        self.level = 0
        self.bg = pygame.image.load("подвал.jpg").convert()

        self.levels = [
            # Уровень 0: колонны + движущаяся платформа
            {
                "static": [
                    Platform(-40, 400, 150, 400),
                    Platform(screen_width - 110, 200, 150, 400)
                ],
                "moving": [
                    {"x": 200, "y": 300, "width": 100, "height": 20, "left_bound": 150, "right_bound": 600}
                ],
                "lasers": [],
                "player_start": (30, 400 - frame_h)
            },
            # Уровень 1 (второй) – двойные полы, без переключения не пройти
            {
                "static_a": [
                    Platform(0, 550, 400, 20),          # левый пол
                    Platform(100, 480, 100, 20),         # левая площадка
                    Platform(300, 410, 100, 20)          # центральная площадка
                ],
                "static_b": [
                    Platform(400, 550, 400, 20),         # правый пол
                    Platform(550, 450, 100, 20),         # правая площадка
                    Platform(700, 380, 100, 20)          # выход
                ],
                "moving": [],
                "lasers": [],
                "player_start": (50, 550 - frame_h)
            },
            # Уровень 2 (третий) – движущаяся платформа + двойные полы
            {
                "static_a": [
                    Platform(0, 550, 300, 20),           # левый пол (обрыв)
                    Platform(150, 480, 100, 20)          # левая верхняя
                ],
                "static_b": [
                    Platform(500, 550, 300, 20),         # правый пол
                    Platform(650, 450, 100, 20),         # правая верхняя
                    Platform(750, 380, 80, 20)           # выход
                ],
                "moving": [
                    {"x": 250, "y": 440, "width": 100, "height": 20, "left_bound": 150, "right_bound": 500}
                ],
                "lasers": [],
                "player_start": (50, 550 - frame_h)
            }
        ]
        self.g_pressed = False
        self.moving_platforms = []
        self.lasers = []
        self.dual_platforms = False
        self.static_platforms_a = []
        self.static_platforms_b = []

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
        level_data = self.levels[self.level]

        self.dual_platforms = "static_a" in level_data
        self.static_platforms_a = []
        self.static_platforms_b = []

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
                MovingPlatform(mp_data["x"], mp_data["y"], mp_data["width"], mp_data["height"],
                               mp_data["left_bound"], mp_data["right_bound"])
            )

        self.lasers = []
        for l_data in level_data.get("lasers", []):
            self.lasers.append(
                LaserTrap(l_data["x"], l_data["y"], l_data["width"], l_data["height"],
                          l_data["left_bound"], l_data["right_bound"])
            )

        start_x, start_y = level_data["player_start"]
        self.player = Player(start_x, start_y, self.frames_a, self.frames_b)
        self.g_pressed = False

    def on_enter(self):
        self.load_frames()
        self.setup()

    def get_current_platforms(self):
        if self.dual_platforms:
            return (self.static_platforms_a if self.player.state == "a" else self.static_platforms_b) + self.moving_platforms
        else:
            return self.static_platforms + self.moving_platforms

    def update(self, dt):
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

        for laser in self.lasers:
            laser.update(dt)

        all_platforms = self.get_current_platforms()
        self.player.update(dt, keys, all_platforms)

        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for laser in self.lasers:
            laser_rect = pygame.Rect(laser.x, laser.y, laser.width, laser.height)
            if player_rect.colliderect(laser_rect) and abs(self.player.vel_x) > 0:
                self.setup()
                return

        if self.player.y > screen_height:
            self.setup()

        if self.player.x + self.player.width >= screen_width:
            self.level = (self.level + 1) % len(self.levels)
            self.setup()

    def draw(self, screen):
        screen.blit(self.bg, (0, 0))

        if self.dual_platforms:
            platforms_to_draw = self.static_platforms_a if self.player.state == "a" else self.static_platforms_b
        else:
            platforms_to_draw = self.static_platforms
        for plat in platforms_to_draw:
            plat.draw(screen)

        for mp in self.moving_platforms:
            mp.draw(screen)
        for laser in self.lasers:
            laser.draw(screen)
        self.player.draw(screen)

def main():
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Shakal studio: Bolgarion boy 3 DEMO")
    clock = pygame.time.Clock()

    prologue = PrologueScene(name="prologue")
    game = DualityScene(name="main")
    scenes = {"prologue": prologue, "main": game}
    current_scene = "prologue"

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

        scene.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
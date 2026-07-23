import pygame
import pygine

screen_width = 800
screen_height = 600
ground_y = 500
gravity = 0.5
jump_strength = -10
move_speed = 200
bg_color = (30, 30, 30)
frame_w = 64
frame_h = 64

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

    def update(self, dt, keys):
        self.vel_x = 0
        if keys[pygame.K_a]:
            self.vel_x = -move_speed
        if keys[pygame.K_d]:
            self.vel_x = move_speed

        self.x += self.vel_x * dt
        if self.x < 0:
            self.x = 0
        if self.x + self.width > screen_width:
            self.x = screen_width - self.width

        self.vel_y += gravity
        self.y += self.vel_y
        if self.y + self.height >= ground_y:
            self.y = ground_y - self.height
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vel_y = jump_strength
            self.on_ground = False

        if not self.on_ground:
            self.current_anim = self.anim_jump
        elif self.vel_x != 0:
            self.current_anim = self.anim_run
        else:
            self.current_anim = self.anim_stance

        self.current_anim.update(dt)

    def get_image(self):
        return self.current_anim.get_image()

    def draw(self, surface):
        surface.blit(self.get_image(), (self.x, self.y))

class DualityScene(pygine.Scene):
    def __init__(self, name="DualityScene"):
        super().__init__(name=name)

    def setup(self):
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

        self.player = Player(100, ground_y - frame_h, frames_a, frames_b)
        self.g_pressed = False

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_g] and not self.g_pressed:
            self.player.switch_state()
            self.g_pressed = True
        elif not keys[pygame.K_g]:
            self.g_pressed = False
        self.player.update(dt, keys)

    def draw(self, screen):
        screen.fill(bg_color)
        self.player.draw(screen)

def main():
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Shakal studio: Bolgarion boy 3 DEMO")
    clock = pygame.time.Clock()

    scene = DualityScene(name="main")
    scene.setup()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        scene.update(dt)
        scene.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
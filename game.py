import pygame
import os
import random
import math


class Background(pygame.sprite.Sprite):
    def __init__(self, image_path, width, height):
        super().__init__()
        self.image = pygame.image.load(image_path).convert()  # 加载背景图像并转换格式
        self.image = pygame.transform.scale(
            self.image, (width, height)
        )  
        self.rect = self.image.get_rect(topleft=(0, 0))  # 设置背景初始位置

    def draw(self, screen):
        """绘制背景"""
        screen.blit(self.image, self.rect.topleft)


class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.load_animations()  # 加载动画
        self.animas.change("Platform")  # 初始为平台动画

        # 创建平台图像和矩形区域
        self.image = self.animas.get_current_frame()  # 使用当前动画帧作为图像
        self.rect = self.image.get_rect(topleft=(x, y))  # 设置初始位置

    def load_animations(self):
        """加载所有动画"""
        # 假设有一张包含平台动画帧的图片
        platform_animation = Anima(
            "images/entity/Platform.png", 1, 1, 64, 16, 4, 0
        )  # 4帧动画示例

        self.animas = Animas()
        self.animas.load("Platform", platform_animation)

    def update(self, dt):
        """更新平台动画"""
        self.animas.update(dt)  # 更新动画帧
        self.update_image()

    def update_image(self):
        """更新平台的图像"""
        self.image = self.animas.get_current_frame()

    def draw(self, screen):
        """绘制平台"""
        screen.blit(self.image, self.rect.topleft)


class House(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.load_animations()
        self.animas.change("House")  # 初始为静止动画

        # 创建房子图像和矩形区域
        self.image = self.animas.get_current_frame()  # 使用当前动画帧作为图像
        self.rect = self.image.get_rect(topleft=(x, y))  # 设置初始位置

    def load_animations(self):
        """加载所有动画"""
        House = Anima("images/entity/House.png", 1, 1, 500, 500, 1, 0)  # 房子静止动画

        self.animas = Animas()
        self.animas.load("House", House)

    def update(self, dt):
        """更新房子动画"""
        self.animas.update(dt)  # 更新动画帧
        self.update_image()

    def update_image(self):
        """更新房子的图像"""
        self.image = self.animas.get_current_frame()

    def draw(self, screen):
        """绘制房子"""
        screen.blit(self.image, self.rect.topleft)


class Cloud(pygame.sprite.Sprite):
    def __init__(self, x, y, base_speed, scale_factor):
        super().__init__()
        self.scale_factor = scale_factor
        self.load_animations()
        self.animas.change("idle")

        # 获取初始帧并设置图像和矩形区域
        initial_frame = self.animas.get_current_frame()
        self.image = pygame.Surface(initial_frame.get_size(), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))

        self.base_speed = base_speed
        self.speed_variation = random.uniform(-5, 5)  # 小幅度的速度变化
        self.min_speed = self.calculate_min_speed()  # 根据缩放比例计算最小速度

    def load_animations(self):
        """加载所有动画"""
        idle = Anima(
            "images/entity/Cloud_Idle.png", 1, 1, 500, 500, 1, self.scale_factor
        )
        moving = Anima(
            "images/entity/Cloud_Moving.png", 1, 1, 500, 500, 1, self.scale_factor
        )

        self.animas = Animas()
        self.animas.load("idle", idle)
        self.animas.load("moving", moving)

    def calculate_min_speed(self):
        """根据缩放比例计算最小速度"""
        return max(15, 30 * (1 - self.scale_factor))  # 缩放比例越大，最小速度越快

    def update(self, dt, entities):
        """更新云朵位置和动画"""
        self.move_cloud(dt)
        self.animas.update(dt)
        self.image = self.get_scaled_image()

    def get_scaled_image(self):
        """根据缩放比例获取当前帧并缩放"""
        current_frame = self.animas.get_current_frame()
        return pygame.transform.scale(
            current_frame,
            (
                int(current_frame.get_width() * self.scale_factor),
                int(current_frame.get_height() * self.scale_factor),
            ),
        )

    def move_cloud(self, dt):
        """移动云朵"""
        # 使用正弦波来产生平滑的速度变化
        oscillation = (
            math.sin(pygame.time.get_ticks() * 0.001 + self.rect.y) * 3
        )  # 减小波动幅度
        speed = max(
            self.base_speed + self.speed_variation + oscillation, self.min_speed
        )  # 使用自适应最小速度
        self.rect.x += speed * dt

        # 循环云朵位置
        if self.rect.x > pygame.display.get_surface().get_width():
            self.rect.x = -self.rect.width

    def draw(self, screen):
        """绘制云朵"""
        screen.blit(self.image, self.rect.topleft)


class CloudGroup(pygame.sprite.Group):
    def __init__(self, cloud_count, screen_width, screen_height, distance=1.0):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.distance = distance
        self.create_clouds(cloud_count)

    def create_clouds(self, cloud_count):
        """生成云朵"""
        for _ in range(cloud_count):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height // 2)
            base_speed = self.calculate_speed()
            scale_factor = self.calculate_scale()
            cloud = Cloud(x, y, base_speed, scale_factor)
            self.add(cloud)
    
    def calculate_speed(self):
        """根据距离参数计算速度"""
        return (
            random.uniform(50, 100) * self.distance
        )  # 更改速度范围以更好地模拟云的漂浮

    def calculate_scale(self):
        """根据距离参数计算缩放比例"""
        return random.uniform(0.5, 1.5) * self.distance  # 调整缩放范围，使云朵更自然

    def update(self, dt, entities):
        """更新所有云朵"""
        for cloud in self.sprites():
            cloud.update(dt, entities)

    def draw(self, screen):
        """绘制所有云朵"""
        for cloud in self.sprites():
            cloud.draw(screen)


class Anima:
    def __init__(self, path, row, frames, width, height, frame_rate=0.05, scale=1):
        images = pygame.image.load(path)
        images = images.convert_alpha() if images.get_alpha() else images.convert()
        self.sheet = images
        self.frames = frames
        self.width = width
        self.height = height
        self.current_frame = 0
        self.frame_rate = frame_rate
        self.scale = scale  # 添加缩放比例
        self.animation_frames = self._load_frames(row)
        self.time = 0

    def _load_frames(self, row):
        frames = []
        for col in range(self.frames):
            frame_rect = pygame.Rect(
                col * self.width, (row - 1) * self.height, self.width, self.height
            )
            frame = self.sheet.subsurface(frame_rect).copy()
            if self.scale != 1:
                frame = pygame.transform.scale(
                    frame, (int(self.width * self.scale), int(self.height * self.scale))
                )
            frames.append(frame)
        return frames

    def update(self, dt):
        self.time += dt
        if self.time >= self.frame_rate:
            self.current_frame = (self.current_frame + 1) % self.frames
            self.time = 0

    def get_current_frame(self):
        return self.animation_frames[self.current_frame]


class Animas:
    def __init__(self):
        """管理多个动画状态"""
        self.animas = {}
        self.current = None

    def load(self, name, anima):
        """加载动画"""
        self.animas[name] = anima

    def change(self, name):
        """切换到指定动画"""
        if name in self.animas and self.current != self.animas[name]:
            self.current = self.animas[name]
            self.current.current_frame = 0  # 切换动画时重置帧数

    def update(self, dt):
        """更新当前动画"""
        if self.current:
            self.current.update(dt)

    def get_current_frame(self):
        """获取当前动画帧"""
        if self.current:
            return self.current.get_current_frame()
        return pygame.Surface((50, 50), pygame.SRCALPHA)  # 返回默认空白帧


class Audio:
    def __init__(self):
        """初始化音频管理器"""
        pygame.mixer.init()
        self.sounds = {}

    def load_sound(self, name, file_path):
        """加载音效"""
        try:
            self.sounds[name] = pygame.mixer.Sound(file_path)
        except pygame.error as e:
            print(f"无法加载音效 {file_path}: {e}")

    def play_sound(self, name, loops=0):
        """播放音效"""
        if name in self.sounds:
            self.sounds[name].play(loops)

    def stop_sound(self, name):
        """停止播放音效"""
        if name in self.sounds:
            self.sounds[name].stop()

    def is_playing(self, name):
        """检查音效是否正在播放"""
        if name in self.sounds:
            return self.sounds[name].get_num_channels() > 0
        return False

    def play_music(self, file_path, loops=-1):
        """播放背景音乐"""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(loops)
        except pygame.error as e:
            print(f"无法加载音乐 {file_path}: {e}")

    def stop_music(self):
        """停止背景音乐"""
        pygame.mixer.music.stop()


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 初始化动画
        self.load_animations()
        self.animas.change("idle")  # 初始为静止动画

        self.rect = pygame.Rect(x, y, 64, 128)  # 玩家矩形区域
        self.speed = 5  # 玩家移动速度
        self.is_running = False  # 判断玩家是否在奔跑
        self.movement = pygame.Vector2(0, 0)  # 用于存储玩家的移动向量
        self.facing = "down"  # 初始朝向

    def load_animations(self):
        """加载所有动画"""
        idle = Anima("images/player/Idle.png", 1, 8, 64, 128, 0.05)
        idle_left = Anima("images/player/Idle.png", 2, 8, 64, 128, 0.05)
        idle_right = Anima("images/player/Idle.png", 3, 8, 64, 128, 0.05)
        idle_back = Anima("images/player/Idle.png", 4, 8, 64, 128, 0.05)

        walking = Anima("images/player/Walking.png", 1, 8, 64, 128, 0.05)
        walking_left = Anima("images/player/Walking.png", 2, 8, 64, 128, 0.05)
        walking_right = Anima("images/player/Walking.png", 3, 8, 64, 128, 0.05)
        walking_back = Anima("images/player/Walking.png", 4, 8, 64, 128, 0.05)

        running = Anima("images/player/Running.png", 1, 8, 64, 128, 0.05)
        running_left = Anima("images/player/Running.png", 2, 8, 64, 128, 0.05)
        running_right = Anima("images/player/Running.png", 3, 8, 64, 128, 0.05)
        running_back = Anima("images/player/Running.png", 4, 8, 64, 128, 0.05)

        self.animas = Animas()
        self.animas.load("idle", idle)
        self.animas.load("idle_left", idle_left)
        self.animas.load("idle_right", idle_right)
        self.animas.load("idle_back", idle_back)
        self.animas.load("walking", walking)
        self.animas.load("walking_left", walking_left)
        self.animas.load("walking_right", walking_right)
        self.animas.load("walking_back", walking_back)
        self.animas.load("running", running)
        self.animas.load("running_left", running_left)
        self.animas.load("running_right", running_right)
        self.animas.load("running_back", running_back)
    def on_collision(self,entity):
        print("#on_collision",entity)

    def handle_key_down(self, key):
        """处理按键按下事件"""
        if key == pygame.K_LEFT:
            self.movement.x = -self.speed
            self.facing = "left"
        elif key == pygame.K_RIGHT:
            self.movement.x = self.speed
            self.facing = "right"

        if key == pygame.K_UP:
            self.movement.y = -self.speed
            self.facing = "up"
        elif key == pygame.K_DOWN:
            self.movement.y = self.speed
            self.facing = "down"

        if key == pygame.K_LSHIFT:  # 处理奔跑
            self.is_running = True

    def handle_key_up(self, key):
        """处理按键释放事件"""
        if key in [pygame.K_LEFT, pygame.K_RIGHT]:
            self.movement.x = 0

        if key in [pygame.K_UP, pygame.K_DOWN]:
            self.movement.y = 0

        if key == pygame.K_LSHIFT:
            self.is_running = False

    def update(self, dt, entities):
        """根据移动和奔跑状态更新位置和动画"""
        movement_length = self.movement.length()
        if movement_length > 0:
            self.move_player()
            self.change_anima()
        else:
            self.change_idle_animation()

        self.animas.update(dt)  # 更新动画帧

    def move_player(self):
        """移动玩家"""
        if self.is_running:
            self.rect.x += self.movement.x * 1.3  # 奔跑时加速
            self.rect.y += self.movement.y * 1.3
        else:
            self.rect.x += self.movement.x
            self.rect.y += self.movement.y
        # 更新rect以适应当前动画帧大小
        current_frame = self.animas.get_current_frame()
        self.rect = current_frame.get_rect(center=self.rect.center)

    def change_anima(self):
        """选择动画"""
        if self.is_running:
            if self.facing == "left":
                self.animas.change("running_left")
            elif self.facing == "right":
                self.animas.change("running_right")
            elif self.facing == "up":
                self.animas.change("running_back")
            else:
                self.animas.change("running")
        else:
            if self.facing == "left":
                self.animas.change("walking_left")
            elif self.facing == "right":
                self.animas.change("walking_right")
            elif self.facing == "up":
                self.animas.change("walking_back")
            else:
                self.animas.change("walking")

    def change_idle_animation(self):
        """选择静止时的动画"""
        if self.facing == "left":
            self.animas.change("idle_left")
        elif self.facing == "right":
            self.animas.change("idle_right")
        elif self.facing == "up":
            self.animas.change("idle_back")
        else:
            self.animas.change("idle")

    def draw(self, screen):
        """将当前动画帧绘制到屏幕上"""
        current_frame = self.animas.get_current_frame()
        screen.blit(current_frame, self.rect.topleft)


class GameBase:
    def __init__(self, width, height, fps=60, title="GameBase", images="images"):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.view = self.screen.get_rect()
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.running = True
        self.surfaces = {}
        self.display_surface = pygame.display.get_surface()
        self.assets = self.load_image(images)
        self.layers = {"background": [], "game": [], "foreground": [], "view": []}
        self.key_state = {}  # 追踪按键状态，优化按键流畅度

    def load_surface(self, layer):
        if layer in self.layers:
            self.surfaces[layer] = pygame.Surface(
                self.screen.get_size(), pygame.SRCALPHA
            )
        else:
            raise ValueError(f"层 '{layer}' 不存在")

    def load_entity(self, entity, layer="game"):
        if layer in self.layers:
            self.layers[layer].append(entity)
        else:
            raise ValueError(f"层 '{layer}' 不存在")
        
    def check_collisions(self):
        """检查各层之间的碰撞"""
        for layer in self.layers.values():
            for i, entity in enumerate(layer):
                for other_entity in layer[i + 1:]:
                    if self.mask_collision(entity, other_entity):
                        self.handle_collision(entity, other_entity)

    def mask_collision(self, entity, other_entity):
        """使用 pygame.mask 进行像素碰撞检测"""
        entity_rect = entity.get_rect() 
        other_rect = other_entity.get_rect()  
        
       
        if not entity_rect.colliderect(other_rect):
            return False
        
      
        entity_mask = pygame.mask.from_surface(entity.image) 
        other_mask = pygame.mask.from_surface(other_entity.image)  
        
        
        offset = (entity_rect.x - other_rect.x, entity_rect.y - other_rect.y)  
        return entity_mask.overlap(other_mask, offset) is not None  

    def handle_collision(self, entity, other_entity):
        """处理碰撞逻辑"""
        if hasattr(entity, "on_collision"):
            entity.on_collision(other_entity)
        if hasattr(other_entity, "on_collision"):
            other_entity.on_collision(entity)

    def load_image(self, directory, colorkey=(255, 0, 255), accept=(".png", ".jpg", ".bmp", ".gif")):
        graphics = {}
        for root, _, files in os.walk(directory):
            for image in files:
                name, ext = os.path.splitext(image)
                if ext.lower() in accept:
                    img = pygame.image.load(os.path.join(root, image))
                    img = img.convert_alpha() if img.get_alpha() else img.convert()
                    if colorkey is not None:
                        img.set_colorkey(colorkey)
                    relative_path = os.path.relpath(
                        os.path.join(root, image), directory
                    )
                    graphics[relative_path] = img
        return graphics

    def get_image(
        self, sheet, x=0, y=0, width=None, height=None, colorkey=None, scale=1
    ):
        width = width or sheet.get_width()
        height = height or sheet.get_height()
        image = pygame.Surface([width, height], pygame.SRCALPHA)
        image.blit(sheet, (0, 0), (x, y, width, height))
        if colorkey is not None:
            image.set_colorkey(colorkey)
        if scale != 1:
            image = pygame.transform.scale(
                image, (int(width * scale), int(height * scale))
            )
        return image

    def get_images(self, sheet, columns, rows, colorkey=None, scale=1):
        images = []
        cell_width = sheet.get_width() // columns
        cell_height = sheet.get_height() // rows
        for y in range(rows):
            for x in range(columns):
                image = self.get_image(
                    sheet,
                    x * cell_width,
                    y * cell_height,
                    cell_width,
                    cell_height,
                    colorkey,
                    scale,
                )
                images.append(image)
        return images

    def load(self):
        pass

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.key_state[event.key] = True
                self.handle_key_down(event.key)
            elif event.type == pygame.KEYUP:
                self.key_state[event.key] = False
                self.handle_key_up(event.key)
            elif event.type in (
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION,
            ):
                self.handle_mouse(event)

    def handle_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_down(event.button, event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.handle_mouse_up(event.button, event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self.handle_mouse_move(event.pos, event.rel)

    def handle_key_down(self, key):
        for layer in self.layers.values():
            for entity in layer:
                if hasattr(entity, "handle_key_down"):
                    entity.handle_key_down(key)

    def handle_key_up(self, key):
        for layer in self.layers.values():
            for entity in layer:
                if hasattr(entity, "handle_key_up"):
                    entity.handle_key_up(key)

    def handle_mouse_down(self, button, pos):
        for layer in self.layers.values():
            for entity in layer:
                if hasattr(entity, "handle_mouse_down"):
                    entity.handle_mouse_down(button, pos)

    def handle_mouse_up(self, button, pos):
        for layer in self.layers.values():
            for entity in layer:
                if hasattr(entity, "handle_mouse_up"):
                    entity.handle_mouse_up(button, pos)

    def handle_mouse_move(self, pos, rel):
        for layer in self.layers.values():
            for entity in layer:
                if hasattr(entity, "handle_mouse_move"):
                    entity.handle_mouse_move(pos, rel)

    def update(self, dt):
        for layer, entities in self.layers.items():
            for entity in entities:
                if layer == "game":
                    print(entity)
                entity.update(dt, entities)
        self.update_key_states()

    def update_key_states(self):
        """根据当前按键状态传递按键事件"""
        for key, pressed in self.key_state.items():
            if pressed:
                self.handle_key_down(key)

    def draw(self):
        if self.display_surface:
            self.display_surface.fill((90, 135, 200))
            for layer, entities in self.layers.items():
                surface = self.surfaces.get(layer)
                if surface:
                    surface.fill((0, 0, 0, 0))
                    for entity in entities:
                        entity.draw(surface)
                    self.display_surface.blit(surface, (0, 0))
                else:
                    for entity in entities:
                        entity.draw(self.display_surface)
        self.screen.blit(self.display_surface, (0, 0))
        pygame.display.flip()

    def run(self):
        self.load()
        for layer in self.layers.keys():
            self.load_surface(layer)
        while self.running:
            dt = self.clock.tick(self.fps) / 1000
            self.events()
            self.update(dt)
            self.check_collisions()
            self.draw()
        pygame.quit()


# 示例用法


if __name__ == "__main__":
    game = GameBase(1280, 720, 60, "My Game")
    background = Background("images/entity/background.png", 1280, 720)
    game.load_entity(background, "background")
    # cloud = CloudGroup(4, 1280, 200, 0.5)
    # game.load_entity(cloud, "background")
    # cloud = CloudGroup(2,1280,200,1)
    cloud = Cloud(10,10,5,1)
    game.load_entity(cloud,"foreground")
    player = Player(100, 100)
    game.load_entity(player)

    game.run()

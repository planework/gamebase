import pygame
import json
import os
import random
import math
from player import Player
from enemy import Enemy
from ai import AI


def lerp(start, end, t):
    """线性插值
    Args:
        start: 起始值
        end: 结束值
        t: 插值系数 (0.0 到 1.0)
    Returns:
        插值后的结果
    """
    return start + (end - start) * min(max(t, 0.0), 1.0)


class GameBase:
    """游戏基础类，处理基本的游戏循环和事件"""

    def __init__(self, caption="Game"):
        pygame.init()
        self.running = True
        self.paused = False
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.min_dt = 1.0 / self.fps  # 最小时间步长
        self.max_dt = 0.05  # 最大时间步长，防止大延迟
        self.dt = 0
        self.debug = False  # 添加debug标志
        self.frame_times = []
        self.max_frame_times = 60  # 保存最近60帧的时间

    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    self.debug = not self.debug  # 切换debug状态
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
            self.on_event(event)

    def on_event(self, event):
        """子类重写此方法以处理特定事件"""
        pass

    def update(self):
        """更新游戏状态"""
        pass

    def render(self):
        """渲染游戏画面"""
        pass

    def run(self):
        """主游戏循环"""
        while self.running:
            # 限制和平滑帧率
            self.dt = min(max(self.clock.tick(self.fps) / 1000.0, self.min_dt), self.max_dt)
            
            # 记录帧时间
            self.frame_times.append(self.dt)
            if len(self.frame_times) > self.max_frame_times:
                self.frame_times.pop(0)

            self.handle_events()
            if not self.paused:
                self.update()
            self.render()

            pygame.display.flip()
        pygame.quit()


class GameView:
    """游戏视图类，处理游戏的显示部分"""

    def __init__(self, screen):
        self.screen = screen
        self.background_color = (255, 255, 255)
        self._cached_fonts = {}
        self._cached_images = {}
        self._cached_backgrounds = {}  # 添加背景图片缓存
        self.render_layers = {}  # 添加渲染层级字典
        
    def add_to_layer(self, layer_name, drawable, z_index=0):
        """添加可绘制对象到指定层
        Args:
            layer_name: 层级名称
            drawable: 可绘制对象(必须有render方法)
            z_index: 层内排序索引(越大越靠前)
        """
        if layer_name not in self.render_layers:
            self.render_layers[layer_name] = []
        self.render_layers[layer_name].append((z_index, drawable))
        # 按z_index排序
        self.render_layers[layer_name].sort(key=lambda x: x[0])
        
    def clear_layer(self, layer_name):
        """清空指定层"""
        if layer_name in self.render_layers:
            self.render_layers[layer_name].clear()
            
    def remove_from_layer(self, layer_name, drawable):
        """从指定层移除对象"""
        if layer_name in self.render_layers:
            self.render_layers[layer_name] = [
                (z, d) for z, d in self.render_layers[layer_name] 
                if d != drawable
            ]
        
    def clear_screen(self, color=None):
        """清空屏幕"""
        self.screen.fill(color or self.background_color)

    def draw_text(self, text, position, color=(0, 0, 0), size=32, centered=False):
        """绘制文本
        Args:
            text: 要绘制的文本
            position: (x, y)位置元组
            color: RGB颜色元组
            size: 字体大
            centered: 是否居中绘制
        """
        if size not in self._cached_fonts:
            self._cached_fonts[size] = pygame.font.Font(None, size)

        font = self._cached_fonts[size]
        text_surface = font.render(text, True, color)

        if centered:
            text_rect = text_surface.get_rect()
            text_rect.center = position
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, position)

    def draw_sprite(self, sprite, position, centered=False):
        """绘制精灵
        Args:
            sprite: Surface对象或图片路径
            position: (x, y)位置元组
            centered: 是否居中绘制
        """
        if isinstance(sprite, str):
            if sprite not in self._cached_images:
                self._cached_images[sprite] = pygame.image.load(sprite).convert_alpha()
            sprite = self._cached_images[sprite]

        if centered:
            rect = sprite.get_rect()
            rect.center = position
            self.screen.blit(sprite, rect)
        else:
            self.screen.blit(sprite, position)

    def draw_rect(self, color, rect, width=0):
        """绘制矩形
        Args:
            color: RGB颜色元组
            rect: (x, y, width, height)或Rect对象
            width: 边框宽度，0表示填充
        """
        pygame.draw.rect(self.screen, color, rect, width)

    def load_background(self, filename, scale_mode='fit', scale_factor=1.0):
        """加载背景图片
        Args:
            filename: 背景图片文件名
            scale_mode: 缩放模式
                - 'fit': 适应屏幕(保持比例)
                - 'fill': 填充屏幕(可能裁剪)
                - 'stretch': 拉伸到屏幕大小
                - 'original': 保持原始大小
            scale_factor: 额外的缩放系数 (1.0 表示原始大小)
        Returns:
            加载并缓存的背景图片Surface对象
        """
        cache_key = (filename, scale_mode, scale_factor)
        if cache_key not in self._cached_backgrounds:
            try:
                path = os.path.join("assets", "backgrounds", filename)
                _, ext = os.path.splitext(filename)
                if ext.lower() in ['.png', '.gif']:
                    image = pygame.image.load(path).convert_alpha()
                else:
                    image = pygame.image.load(path).convert()
                    
                screen_width, screen_height = self.screen.get_size()
                image_width, image_height = image.get_size()
                
                # 根据不同的缩放模式处理图片
                if scale_mode != 'original':
                    if scale_mode == 'fit':
                        # 计算适应屏幕的缩放比例
                        scale = min(screen_width / image_width, 
                                  screen_height / image_height)
                    elif scale_mode == 'fill':
                        # 计算填充屏幕的缩放比例
                        scale = max(screen_width / image_width, 
                                  screen_height / image_height)
                    elif scale_mode == 'stretch':
                        # 分别计算水平和垂直缩放比例
                        scale_x = screen_width / image_width
                        scale_y = screen_height / image_height
                        new_width = int(image_width * scale_x * scale_factor)
                        new_height = int(image_height * scale_y * scale_factor)
                        image = pygame.transform.scale(image, (new_width, new_height))
                        self._cached_backgrounds[cache_key] = image
                        return image
                    
                    # 应用额外的缩放系数
                    final_scale = scale * scale_factor
                    new_width = int(image_width * final_scale)
                    new_height = int(image_height * final_scale)
                    image = pygame.transform.scale(image, (new_width, new_height))
                else:
                    # 即使是original模式也应用scale_factor
                    if scale_factor != 1.0:
                        new_width = int(image_width * scale_factor)
                        new_height = int(image_height * scale_factor)
                        image = pygame.transform.scale(image, (new_width, new_height))
                    
                self._cached_backgrounds[cache_key] = image
                
            except pygame.error as e:
                print(f"无法加载背景图片 {filename}: {e}")
                image = pygame.Surface(self.screen.get_size())
                image.fill((200, 220, 255))
                self._cached_backgrounds[cache_key] = image
            
        return self._cached_backgrounds[cache_key]
        
    def draw_background(self, background, camera_offset=(0, 0), 
                       parallax_factor=0.5, tile_mode='none', 
                       alignment='center', scale_factor=1.0):
        """绘制背景，支持视差滚动
        Args:
            background: 背景Surface对象或图片文件名
            camera_offset: 相机偏移量
            parallax_factor: 视差系数(0-1)
            tile_mode: 平铺模式 ('none', 'x', 'y', 'both')
            alignment: 对齐方式 ('center', 'top', 'bottom', 'left', 'right')
            scale_factor: 动态缩放系数 (1.0 表示原始大小)
        """
        if isinstance(background, str):
            background = self.load_background(background, scale_factor=scale_factor)
            
        # 获取屏幕和背景的尺寸
        screen_width, screen_height = self.screen.get_size()
        bg_width, bg_height = background.get_size()
        
        # 计算视差偏移
        parallax_x = int(camera_offset[0] * parallax_factor)
        parallax_y = int(camera_offset[1] * parallax_factor)
        
        if tile_mode == 'none':
            # 计算单个背景的位
            if alignment == 'center':
                x = (screen_width - bg_width) // 2 - parallax_x
                y = (screen_height - bg_height) // 2 - parallax_y
            elif alignment == 'top':
                x = (screen_width - bg_width) // 2 - parallax_x
                y = 0 - parallax_y
            elif alignment == 'bottom':
                x = (screen_width - bg_width) // 2 - parallax_x
                y = screen_height - bg_height - parallax_y
            elif alignment == 'left':
                x = 0 - parallax_x
                y = (screen_height - bg_height) // 2 - parallax_y
            elif alignment == 'right':
                x = screen_width - bg_width - parallax_x
                y = (screen_height - bg_height) // 2 - parallax_y
                
            self.screen.blit(background, (x, y))
            
        else:
            # 计算平铺范围
            if tile_mode in ['x', 'both']:
                start_x = -(parallax_x % bg_width)
                if start_x > 0:
                    start_x -= bg_width
                tiles_x = (screen_width // bg_width) + 2
            else:
                start_x = (screen_width - bg_width) // 2 - parallax_x
                tiles_x = 1
                
            if tile_mode in ['y', 'both']:
                start_y = -(parallax_y % bg_height)
                if start_y > 0:
                    start_y -= bg_height
                tiles_y = (screen_height // bg_height) + 2
            else:
                start_y = (screen_height - bg_height) // 2 - parallax_y
                tiles_y = 1
                
            # 绘制平铺背景
            for y in range(tiles_y):
                for x in range(tiles_x):
                    pos_x = start_x + (x * bg_width)
                    pos_y = start_y + (y * bg_height)
                    if (-bg_width <= pos_x <= screen_width and 
                        -bg_height <= pos_y <= screen_height):
                        self.screen.blit(background, (pos_x, pos_y))


class ObjectPool:
    """对象池管理类"""
    def __init__(self):
        self.pools = {}
        
    def get_object(self, obj_type):
        """从对象池获取对象"""
        if obj_type not in self.pools:
            self.pools[obj_type] = []
        
        if len(self.pools[obj_type]) > 0:
            return self.pools[obj_type].pop()
        return obj_type()
        
    def return_object(self, obj):
        """将对象返回象池"""
        obj_type = type(obj)
        if obj_type not in self.pools:
            self.pools[obj_type] = []
        self.pools[obj_type].append(obj)


class SpatialHash:
    """空间哈希分区"""
    def __init__(self, cell_size=64):
        self.cell_size = cell_size
        self.grid = {}
        
    def _get_cell(self, x, y):
        """获取坐标所在的网格单元"""
        return (int(x / self.cell_size), int(y / self.cell_size))
    
    def add_object(self, obj, rect):
        """添加对象到空间分区"""
        cell_start = self._get_cell(rect.left, rect.top)
        cell_end = self._get_cell(rect.right, rect.bottom)
        
        for x in range(cell_start[0], cell_end[0] + 1):
            for y in range(cell_start[1], cell_end[1] + 1):
                cell = (x, y)
                if cell not in self.grid:
                    self.grid[cell] = set()
                self.grid[cell].add(obj)
                
    def get_nearby_objects(self, rect):
        """获取指定区域附近的对"""
        cell_start = self._get_cell(rect.left, rect.top)
        cell_end = self._get_cell(rect.right, rect.bottom)
        
        nearby = set()
        for x in range(cell_start[0], cell_end[0] + 1):
            for y in range(cell_start[1], cell_end[1] + 1):
                cell = (x, y)
                if cell in self.grid:
                    nearby.update(self.grid[cell])
        return nearby


class Game(GameBase):
    """主游戏类，继承自GameBase"""

    def __init__(self):
        super().__init__("My Game")  # 设置游戏标题
        self.view = GameView(self.screen)
        self.gamemap = gamemap(self)
        # 创建玩家，位置在第一关的左侧
        self.player = Player(self.gamemap, 100, 300)
        self.load_maps()
        self.current_map = 1
        self.assets_dir = "assets"
        
        # 相机设置
        self.camera_x = 0
        self.camera_y = 0
        self.camera_smoothing = 4.0  # 降低平滑系数使移更柔和
        self.camera_lookahead = 100  # 减小前瞻距离
        self.camera_deadzone = 50  # 添加死区
        self.camera_vx = 0  # 添加相机速度
        self.camera_vy = 0  # 添加相机速度
        self.object_pool = ObjectPool()
        
        # 定义背景层级顺序
        self.background_layers = [
            'far_background',    # 最远层(天空)
            'background',        # 背景层(云、山)
            'midground',         # 中景层(树木、建筑)
            'playground',        # 游戏层(地图、玩家)
            'foreground',        # 前景层
            'ui'                 # UI层
        ]
        
        # 加载背景 - 添加层级名称
        self.backgrounds = {
            'sky': ('sky.png', 0.05, 'stretch', 'none', 'center', 2.0, 'far_background', 0),
            'clouds': ('clouds.png', 0.2, 'stretch', 'both', 'center', 2, 'background', 0),
            'mountains': ('mountains.png', 0.4, 'original', 'x', 'bottom', 1.5, 'foreground', 1),
            'trees': ('trees.png', 0.6, 'original', 'x', 'bottom', 1, 'foreground', 0),
        }
        
        # 预加载背景并设置层级
        self._setup_background_layers()
        
        # 将玩家地图添加到游戏层
        self.view.add_to_layer('playground', self.gamemap, 0)
        self.view.add_to_layer('playground', self.player, 1)
        
        # 添加debug信息配置
        self.debug_info = {
            'fps': True,          # FPS信息
            'player': True,       # 玩家信息
            'camera': True,       # 相机信息
            'level': True,        # 关卡信息
            'memory': True,       # 内存使用
            'background': True,   # 背景信息
        }
        
        # 修改敌人AI配置
        self.ai_config = {
            'spawn_range': (3, 5),    # 增加每个关卡生成的敌人数量
            'patrol_radius': 200,      # 巡逻范围
            'min_spawn_distance': 150, # 增加敌人之间的最小距离
            'min_player_distance': 200, # 与玩家的最小生成距离
            'debug_ai': True          # 是否显示AI调试信息
        }
        
        # 添加AI调试信息到debug_info
        self.debug_info.update({
            'ai': True,           # AI状态信息
            'pathfinding': True,  # 寻路信息
        })
        
        # 初始化敌人
        self.enemies = []
        self.active_enemies = []  # 添加活跃敌人列表
        self._spawn_enemies()
        
        self.projectiles = []  # 存储所有投射物
        
    def _setup_background_layers(self):
        """设置背景层级"""
        # 创建背景渲染器
        class BackgroundRenderer:
            def __init__(self, game, image_file, parallax_factor, scale_mode, 
                        tile_mode, alignment, scale_factor):
                self.game = game
                self.image_file = image_file
                self.parallax_factor = parallax_factor
                self.scale_mode = scale_mode
                self.tile_mode = tile_mode
                self.alignment = alignment
                self.scale_factor = scale_factor
                
            def render(self, camera_offset=(0, 0)):
                try:
                    background = self.game.view.load_background(
                        self.image_file,
                        self.scale_mode,
                        self.scale_factor
                    )
                    self.game.view.draw_background(
                        background,
                        camera_offset,
                        self.parallax_factor,
                        self.tile_mode,
                        self.alignment,
                        self.scale_factor
                    )
                except Exception as e:
                    print(f"无法染景 {self.image_file}: {e}")
        
        # 为每个背景创建渲染器并添加到对应层级
        for name, (image_file, parallax_factor, scale_mode, 
                  tile_mode, alignment, scale_factor, layer, z_index) in self.backgrounds.items():
            renderer = BackgroundRenderer(
                self,
                image_file,
                parallax_factor,
                scale_mode,
                tile_mode,
                alignment,
                scale_factor
            )
            self.view.add_to_layer(layer, renderer, z_index)
            
    def load_maps(self):
        """加载地图数据"""
        try:
            self.maps = {}
            maps_dir = "maps"
            if not os.path.exists(maps_dir):
                os.makedirs(maps_dir)
            
            for i in range(1, 6):  # 加载5个地图
                map_path = os.path.join(maps_dir, f"{i}.json")
                if os.path.exists(map_path):
                    try:
                        with open(map_path, "r", encoding='utf-8') as f:
                            self.maps[i] = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"地图 {i} 格式错误: {e}")
                    except Exception as e:
                        print(f"加载地图 {i} 失败: {e}")
                else:
                    print(f"地图文件不存在: {map_path}")
        except Exception as e:
            print(f"加载地图失败: {e}")
            self.maps = {}  # 确保maps初始化

    def load_image(self, filename):
        """加载图片资源"""
        path = os.path.join(self.assets_dir, filename)
        return pygame.image.load(path).convert_alpha()

    def on_event(self, event):
        """处理游戏特定事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_LEFT:
                self.current_map = max(1, self.current_map - 1)
            elif event.key == pygame.K_RIGHT:
                self.current_map = min(len(self.maps), self.current_map + 1)
            # 只处理数字键切换不同类型的调试信息
            elif self.debug and pygame.K_1 <= event.key <= pygame.K_6:
                debug_keys = list(self.debug_info.keys())
                key_index = event.key - pygame.K_1
                if key_index < len(debug_keys):
                    key = debug_keys[key_index]
                    self.debug_info[key] = not self.debug_info[key]

    def update(self):
        """更新游戏状态"""
        if not self.paused:
            # 更新玩家
            self.player.update(self.dt)
            
            # 更新敌人和AI
            player_pos = (self.player.x, self.player.y)
            screen_rect = pygame.Rect(
                self.camera_x - 100,  # 扩大一点检测范围
                self.camera_y - 100,
                self.screen.get_width() + 200,
                self.screen.get_height() + 200
            )
            
            # 更新活跃敌人列表
            self.active_enemies = [
                enemy for enemy in self.enemies
                if screen_rect.collidepoint(enemy.x, enemy.y)
            ]
            
            # 更新敌人
            enemies_to_remove = []
            for enemy in self.active_enemies:
                try:
                    enemy.update(self.dt)
                    enemy.ai.update(self.dt, player_pos)
                except Exception as e:
                    print(f"敌人AI更新错误: {e}")
                    enemies_to_remove.append(enemy)
            
            # 移除出错的敌人
            for enemy in enemies_to_remove:
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
                    self.view.remove_from_layer('playground', enemy)
            
            # 更新相机
            self._update_camera()
            
            # 检查玩家与敌人的碰撞
            self._check_enemy_collisions()
            
            # 更新投射物
            self._update_projectiles(self.dt)

    def _update_camera(self):
        """更新相机位置，使用更平滑的跟随系"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # 计算玩家中心点
        player_center_x = self.player.x + self.player.width / 2
        player_center_y = self.player.y + self.player.height / 2
        
        # 计算目标位置（添加前瞻）
        lookahead_x = 0
        if abs(self.player.vx) > 50:  # 只在玩家速度超过阈值时添加前瞻
            lookahead_x = self.camera_lookahead if self.player.vx > 0 else -self.camera_lookahead
        
        target_x = player_center_x + lookahead_x - screen_width / 2
        target_y = player_center_y - screen_height / 2
        
        # 应用死区
        dx = target_x - self.camera_x
        dy = target_y - self.camera_y
        
        if abs(dx) < self.camera_deadzone:
            target_x = self.camera_x
        if abs(dy) < self.camera_deadzone:
            target_y = self.camera_y
        
        # 限制目标位置范围
        target_x = max(0, min(target_x, self.gamemap.world_width - screen_width))
        target_y = max(0, min(target_y, self.gamemap.level_height - screen_height))
        
        # 计算目标速度
        target_vx = (target_x - self.camera_x) * 3.0  # 速度系数
        target_vy = (target_y - self.camera_y) * 3.0
        
        # 平滑相机速度
        self.camera_vx = lerp(self.camera_vx, target_vx, self.dt * self.camera_smoothing)
        self.camera_vy = lerp(self.camera_vy, target_vy, self.dt * self.camera_smoothing)
        
        # 应用速度
        self.camera_x += self.camera_vx * self.dt
        self.camera_y += self.camera_vy * self.dt
        
        # 确保相机位置不会超出边界
        self.camera_x = max(0, min(self.camera_x, self.gamemap.world_width - screen_width))
        self.camera_y = max(0, min(self.camera_y, self.gamemap.level_height - screen_height))

    def shake_camera(self, intensity=5.0, duration=0.5):
        """添加相机震动效果"""
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_timer = 0
        
    def _apply_camera_shake(self):
        """应用相机震动"""
        if self.shake_timer < self.shake_duration:
            self.shake_timer += self.dt
            shake_offset_x = random.uniform(-1, 1) * self.shake_intensity
            shake_offset_y = random.uniform(-1, 1) * self.shake_intensity
            self.camera_x += shake_offset_x
            self.camera_y += shake_offset_y

    def render(self):
        """渲染游戏画面"""
        self.view.clear_screen()
        
        # 按层级顺序渲染
        for layer_name in self.background_layers:
            if layer_name in self.view.render_layers:
                for _, drawable in self.view.render_layers[layer_name]:
                    drawable.render((self.camera_x, self.camera_y))
        
        # 渲染血量条
        self._render_health_bar()
        
        # 渲染AI调试信息
        if self.debug and self.debug_info.get('ai'):
            for enemy in self.enemies:
                enemy.ai.render_debug(self.screen, (self.camera_x, self.camera_y))
        
        # 渲染其他调试信息
        if self.debug:
            self._render_debug_info()
        
        # 渲染投射物
        for projectile in self.projectiles:
            screen_x = int(projectile['x'] - self.camera_x)
            screen_y = int(projectile['y'] - self.camera_y)
            pygame.draw.circle(
                self.screen,
                (255, 100, 100),  # 红色投射物
                (screen_x, screen_y),
                projectile['radius']
            )
    
    def _render_debug_info(self):
        """渲染调试信息"""
        y_offset = 10
        line_height = 20
        
        debug_lines = []
        
        # FPS信息
        if self.debug_info['fps']:
            current_fps = int(self.clock.get_fps())
            debug_lines.append(f"FPS: {current_fps}")
            
        # 玩家信息
        if self.debug_info['player']:
            debug_lines.extend([
                f"Player Pos: ({int(self.player.x)}, {int(self.player.y)})",
                f"Velocity: ({int(self.player.vx)}, {int(self.player.vy)})",
                f"On Ground: {self.player.on_ground}"
            ])
            
        # 机信息
        if self.debug_info['camera']:
            debug_lines.extend([
                f"Camera: ({int(self.camera_x)}, {int(self.camera_y)})",
                f"Camera V: ({int(self.camera_vx)}, {int(self.camera_vy)})"
            ])
            
        # 关卡信息
        if self.debug_info['level']:
            current_level = self.gamemap.get_current_level_index(self.player.x)
            total_levels = len(self.gamemap.levels)
            debug_lines.extend([
                f"Level: {current_level + 1}/{total_levels}",
                f"World Width: {self.gamemap.world_width}px"
            ])
            
        # 内存使用信息
        if self.debug_info['memory']:
            cached_images = len(self.view._cached_images)
            cached_backgrounds = len(self.view._cached_backgrounds)
            cached_fonts = len(self.view._cached_fonts)
            debug_lines.extend([
                f"Cached Images: {cached_images}",
                f"Cached Backgrounds: {cached_backgrounds}",
                f"Cached Fonts: {cached_fonts}"
            ])
            
        # 背景信息
        if self.debug_info['background']:
            active_layers = sum(1 for layer in self.background_layers 
                              if layer in self.view.render_layers)
            total_drawables = sum(len(layer) for layer in self.view.render_layers.values())
            debug_lines.extend([
                f"Active Layers: {active_layers}/{len(self.background_layers)}",
                f"Total Drawables: {total_drawables}"
            ])
        
        # 渲染所有调试信息
        for i, line in enumerate(debug_lines):
            self.view.draw_text(
                line,
                (10, y_offset + i * line_height),
                (255, 0, 0),  # 红色
                24
            )
            
    def _spawn_enemies(self):
        """生成敌人，优化生成逻辑"""
        if not self.maps:
            print("没有地图数据，无法生成敌人")
            return
            
        levels = self.gamemap.levels
        
        for level_index in range(len(levels)):
            # 获取有效生成区域
            valid_spawn_areas = self._get_valid_spawn_areas(level_index)
            if not valid_spawn_areas:
                continue
                
            # 决定这个关卡生成的敌人数
            num_enemies = random.randint(*self.ai_config['spawn_range'])
            spawned_positions = []  # 记录已生成的位置
            
            for i in range(num_enemies):
                # 尝试找到合适的生成位置
                max_attempts = 10
                for _ in range(max_attempts):
                    spawn_area = random.choice(valid_spawn_areas)
                    x = random.randint(spawn_area[0], spawn_area[1])
                    y = 100  # 初始y值
                    
                    # 检查与其他敌人的距离
                    if all(abs(x - pos[0]) >= self.ai_config['min_spawn_distance'] 
                           for pos in spawned_positions):
                        # 检查与玩家的距离
                        dx = x - self.player.x
                        if abs(dx) >= self.ai_config['min_player_distance']:
                            try:
                                # 创建敌人
                                enemy = Enemy(self.gamemap, x, y)
                                enemy.ai = AI(enemy, self.gamemap)
                                
                                # 初始化AI的行为权重
                                enemy.ai.behavior_weights = {
                                    'aggression': random.uniform(0.3, 0.8),
                                    'caution': random.uniform(0.2, 0.7),
                                    'intelligence': random.uniform(0.4, 0.9),
                                    'persistence': random.uniform(0.3, 0.8)
                                }
                                
                                # 生成巡逻点
                                patrol_area = (
                                    max(spawn_area[0], x - self.ai_config['patrol_radius']),
                                    min(spawn_area[1], x + self.ai_config['patrol_radius'])
                                )
                                patrol_points = self._generate_patrol_points_for_area(patrol_area)
                                enemy.ai.set_patrol_points(patrol_points)
                                
                                # 添加敌人
                                self.enemies.append(enemy)
                                self.view.add_to_layer('playground', enemy, 1)
                                spawned_positions.append((x, y))
                                break
                            except Exception as e:
                                print(f"生成敌人失败: {e}")
                                continue

    def _generate_patrol_points_for_area(self, area):
        """为特定区域生成巡逻点"""
        points = []
        area_width = area[1] - area[0]
        num_points = random.randint(3, 4)  # 减少巡逻点数量
        
        # 确保巡逻点在区域内均匀分布
        segment_width = area_width / (num_points - 1)
        
        for i in range(num_points):
            x = area[0] + i * segment_width
            if i > 0 and i < num_points - 1:
                # 添加一些随机偏移，但确保不会超出区域
                x += random.uniform(-segment_width/4, segment_width/4)
            points.append((x, 0))  # y坐标会在AI中自动调整
            
        return points

    def _check_enemy_collisions(self):
        """检查玩家与敌人的碰撞"""
        player_rect = pygame.Rect(
            self.player.x + 10,  # 缩小碰撞箱，使碰撞更精确
            self.player.y + 5,
            self.player.width - 20,
            self.player.height - 10
        )
        
        current_time = pygame.time.get_ticks() / 1000.0
        
        # 如果玩家在无敌时间内，不处理碰撞
        if current_time < self.player.invincible_time:
            return
        
        for enemy in self.enemies[:]:  # 使用切片创建副本以避免修改迭代中的列表
            enemy_rect = pygame.Rect(
                enemy.x + 5,  # 缩小敌人碰撞箱
                enemy.y + 5,
                enemy.width - 10,
                enemy.height - 10
            )
            
            if player_rect.colliderect(enemy_rect):
                # 计算碰撞点和方向
                player_center_x = self.player.x + self.player.width / 2
                player_center_y = self.player.y + self.player.height / 2
                enemy_center_x = enemy.x + enemy.width / 2
                enemy_center_y = enemy.y + enemy.height / 2
                
                # 如果玩家从上方���撞敌人
                if (self.player.vy > 0 and  # 玩家正在下落
                    self.player.y + self.player.height < enemy.y + enemy.height * 0.25):  # 更严格的上方判定
                    # 击败敌人
                    enemy.take_damage(100)
                    # 玩家弹跳
                    self.player.vy = -400  # 减小弹跳高度
                    # 短暂无敌时间
                    self.player.invincible_time = current_time + 0.5
                    
                    # 添加击败效果
                    self.shake_camera(intensity=3.0, duration=0.1)
                else:
                    # 玩家受伤
                    self.player.take_damage(10)
                    
                    # 计算击退方向和力度
                    dx = player_center_x - enemy_center_x
                    dy = player_center_y - enemy_center_y
                    
                    # 确定击退方向（从敌人到玩家的方向）
                    knockback_direction = -1 if dx > 0 else 1  # 反转方向
                    
                    # 增加基础击退力度
                    base_knockback_x = 800  # 增加水平击退力度 (从500增加到800)
                    base_knockback_y = 500  # 增加垂直击退力度 (从300增加到500)
                    
                    # 计算水平击退
                    knockback_x = knockback_direction * base_knockback_x
                    
                    # 计算垂直击退（总是向上）
                    knockback_y = -base_knockback_y
                    
                    # 根据敌人的攻击性增加击退效果
                    if hasattr(enemy, 'ai') and hasattr(enemy.ai, 'behavior_weights'):
                        aggression_bonus = enemy.ai.behavior_weights['aggression']
                        knockback_x *= (1 + aggression_bonus * 0.5)
                        knockback_y *= (1 + aggression_bonus * 0.5)
                    
                    # 应用击退（无论是否在地面）
                    self.player.vx = knockback_x
                    self.player.vy = knockback_y
                    
                    # 敌人的反作用力（向相反方向）
                    enemy.vx = -knockback_direction * base_knockback_x * 0.3
                    enemy.vy = -100
                    
                    # 给玩家一个较长的无敌时间
                    self.player.invincible_time = current_time + self.player.invincible_duration
                    
                    # 增加相机震动效果
                    self.shake_camera(
                        intensity=8.0,  # 增加震动强度 (从6.0增加到8.0)
                        duration=0.3    # 增加震动时间 (从0.25增加到0.3)
                    )

    def _get_valid_spawn_areas(self, level_index):
        """获取有效的敌人生成区域
        Args:
            level_index: 关卡索引
        Returns:
            list: 可生成区域的列表，每个元素为 (start_x, end_x) 元组
        """
        if not self.gamemap or not self.gamemap.levels:
            return []
        
        level_data = self.gamemap.levels[level_index]
        level_width = len(level_data[0]) * self.gamemap.tile_size
        level_start_x = level_index * level_width
        
        # 找出所有可能的生成区域
        valid_areas = []
        current_area_start = None
        min_area_width = 3 * self.gamemap.tile_size  # 最小区域宽度
        
        # 遍历每一列
        for x in range(len(level_data[0])):
            world_x = level_start_x + x * self.gamemap.tile_size
            
            # 检查这一列是否适合生成敌人
            is_valid = False
            for y in range(len(level_data) - 1, -1, -1):
                if level_data[y][x] in [self.gamemap.WALL, self.gamemap.PLATFORM]:
                    # 检查上方是否有足够空间
                    if y > 1 and all(level_data[y-i][x] == self.gamemap.EMPTY for i in range(1, 3)):
                        is_valid = True
                    break
            
            # 处理区域
            if is_valid:
                if current_area_start is None:
                    current_area_start = world_x
            elif current_area_start is not None:
                area_width = world_x - current_area_start
                if area_width >= min_area_width:
                    valid_areas.append((current_area_start, world_x))
                current_area_start = None
        
        # 处理最后一个区域
        if current_area_start is not None:
            area_width = level_start_x + level_width - current_area_start
            if area_width >= min_area_width:
                valid_areas.append((current_area_start, level_start_x + level_width))
        
        return valid_areas

    def _render_health_bar(self):
        """渲染玩家血量条"""
        # 血量条位置和大小
        bar_width = 200
        bar_height = 20
        x = 10
        y = 10
        
        # 计算当前血量比例
        health_ratio = self.player.health / self.player.max_health
        current_width = int(bar_width * health_ratio)
        
        # 绘制背景（深灰色）
        pygame.draw.rect(
            self.screen,
            (50, 50, 50),
            (x, y, bar_width, bar_height)
        )
        
        # 根据血量比例选择颜色
        if health_ratio > 0.7:
            color = (0, 255, 0)  # 绿色
        elif health_ratio > 0.3:
            color = (255, 255, 0)  # 黄色
        else:
            color = (255, 0, 0)  # 红色
        
        # 绘制当前血量（有颜色的部分）
        if current_width > 0:
            pygame.draw.rect(
                self.screen,
                color,
                (x, y, current_width, bar_height)
            )
        
        # 绘制边框
        pygame.draw.rect(
            self.screen,
            (200, 200, 200),
            (x, y, bar_width, bar_height),
            2
        )
        
        # 显示具体数值
        health_text = f"{int(self.player.health)}/{self.player.max_health}"
        font = pygame.font.Font(None, 24)
        text_surface = font.render(health_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.center = (x + bar_width // 2, y + bar_height // 2)
        self.screen.blit(text_surface, text_rect)
        
        # 如果玩家受伤，显示红色边缘效果
        if self.player.invincible_time > pygame.time.get_ticks() / 1000.0:
            alpha = int(((self.player.invincible_time - pygame.time.get_ticks() / 1000.0) 
                        / self.player.invincible_duration) * 128)
            damage_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            damage_surface.fill((255, 0, 0))
            damage_surface.set_alpha(alpha)
            self.screen.blit(damage_surface, (0, 0))

    def spawn_projectile(self, x, y, vx, vy, damage, source):
        """生成投射物
        Args:
            x, y: 初始位置
            vx, vy: 速度
            damage: 伤害值
            source: 来源('player' or 'enemy')
        """
        projectile = {
            'x': x, 'y': y,
            'vx': vx, 'vy': vy,
            'damage': damage,
            'source': source,
            'radius': 5,  # 投射物大小
            'lifetime': 2.0  # 存活时间
        }
        self.projectiles.append(projectile)
        
    def _update_projectiles(self, dt):
        """更新所有投射物"""
        for projectile in self.projectiles[:]:
            # 更新位置
            projectile['x'] += projectile['vx'] * dt
            projectile['y'] += projectile['vy'] * dt
            projectile['lifetime'] -= dt
            
            # 检查碰撞
            if self.gamemap.is_solid(projectile['x'], projectile['y']):
                self.projectiles.remove(projectile)
                continue
                
            # 检查生命周期
            if projectile['lifetime'] <= 0:
                self.projectiles.remove(projectile)
                continue
                
            # 检查与玩家的碰撞
            if projectile['source'] == 'enemy':
                if self._check_projectile_player_collision(projectile):
                    self.projectiles.remove(projectile)
                    
    def _check_projectile_player_collision(self, projectile):
        """检查投射物是否击中玩家"""
        if pygame.time.get_ticks() / 1000.0 < self.player.invincible_time:
            return False
            
        # 简单的圆形碰撞检测
        dx = projectile['x'] - (self.player.x + self.player.width/2)
        dy = projectile['y'] - (self.player.y + self.player.height/2)
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < projectile['radius'] + self.player.width/2:
            # 击中玩家
            self.player.take_damage(projectile['damage'])
            
            # 计算击退
            knockback_x = dx / dist * 300
            knockback_y = -200
            self.player.vx = knockback_x
            self.player.vy = knockback_y
            
            # 设置无敌时间
            self.player.invincible_time = pygame.time.get_ticks() / 1000.0 + 0.5
            return True
            
        return False


class gamemap:
    """关卡管理器"""

    def __init__(self, game):
        self.game = game
        self.current_level = 0
        self.levels = self._load_levels() or self._create_default_levels()
        self.tile_size = 64
        
        # 计算整个世界的宽度和高度
        self.world_width = len(self.levels[0][0]) * len(self.levels) * self.tile_size
        self.level_width = len(self.levels[0][0]) * self.tile_size
        self.level_height = len(self.levels[0]) * self.tile_size
        
        # 计算每个关卡的起始X坐标
        self.level_start_positions = [
            i * self.level_width for i in range(len(self.levels))
        ]

        # 扩展砖块类型定义
        self.EMPTY = 0
        self.WALL = 1
        self.PLATFORM = 2
        self.SPIKE = 3
        self.ICE = 4        # 冰面，玩家会滑动
        self.BOUNCE = 5     # 弹跳板
        self.LAVA = 6       # 熔岩，致命危险
        self.WATER = 7      # 水面，改变物理特性
        self.GLASS = 8      # 玻璃，可以看到后面
        self.BRICK = 9      # 砖块，可以被破坏
        
        # 更新砖块颜色定义
        self.tile_colors = {
            self.WALL: (100, 100, 120),      # 深灰色墙壁
            self.PLATFORM: (76, 153, 0),      # 青草绿色平台
            self.SPIKE: (204, 0, 0),          # 鲜红色尖刺
            self.ICE: (200, 240, 255),        # 浅蓝色冰面
            self.BOUNCE: (255, 200, 0),       # 橙色弹跳板
            self.LAVA: (255, 100, 0),         # 橙红色熔岩
            self.WATER: (0, 120, 200),        # 深蓝色水面
            self.GLASS: (200, 200, 255, 128), # 半透明玻璃
            self.BRICK: (180, 100, 60),       # 棕色砖块
        }
        
        # 更新边框颜色
        self.tile_border_colors = {
            self.WALL: (80, 80, 100),         # 墙壁边框
            self.PLATFORM: (56, 133, 0),       # 平台边框
            self.SPIKE: (184, 0, 0),           # 尖刺边框
            self.ICE: (180, 220, 255),         # 冰面边框
            self.BOUNCE: (235, 180, 0),        # 弹跳板边框
            self.LAVA: (235, 80, 0),           # 熔岩边框
            self.WATER: (0, 100, 180),         # 水面边框
            self.GLASS: (180, 180, 235, 128),  # 玻璃边框
            self.BRICK: (160, 80, 40),         # 砖块边框
        }
        
        # 更新高光颜色
        self.tile_highlight_colors = {
            self.WALL: (120, 120, 140),       # 墙壁高光
            self.PLATFORM: (96, 173, 20),      # 平台高光
            self.SPIKE: (224, 20, 20),         # 尖刺高光
            self.ICE: (220, 255, 255),         # 冰面高光
            self.BOUNCE: (255, 220, 20),       # 弹跳板高光
            self.LAVA: (255, 120, 20),         # 熔岩高光
            self.WATER: (20, 140, 220),        # 水面高光
            self.GLASS: (220, 220, 255, 128),  # 玻璃高光
            self.BRICK: (200, 120, 80),        # 砖块高光
        }

        # 添加特殊效果配置
        self.tile_effects = {
            self.ICE: {'friction': 0.02},      # 冰面摩擦力
            self.BOUNCE: {'bounce': 1.5},      # 弹跳系数
            self.WATER: {'gravity': 0.5},      # 水中重力
            self.LAVA: {'damage': 100},        # 熔岩伤害
            self.GLASS: {'opacity': 0.5},      # 玻璃透明度
            self.BRICK: {'health': 3},         # 砖块耐久度
        }

        self.spatial_hash = SpatialHash(self.tile_size)
        self._tile_cache = {}
        self._solid_cache = {}

    def _create_default_levels(self):
        """创建默认关卡数据，确保关卡之间可以无缝连"""
        default_levels = [
            [  # 第一关 - 右边界放
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 右边开放
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 右边开放
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            ],
            [  # 第二关 - 两边都开放
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 右边开放
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 右边开放
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            ],
            [  # 第三关 - 左边界开放
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 右边开放
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 右边开放
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            ],
        ]
        return default_levels

    def _load_levels(self):
        """从maps目录加载关卡数据"""
        
        levels = []
        try:
            for i in range(1, 6):  # 加载5个地图
                map_path = os.path.join('maps', f'{i}.json')
                if os.path.exists(map_path):
                    with open(map_path, 'r', encoding='utf-8') as f:
                        map_data = json.load(f)
                        levels.append(map_data['data'])
            return levels if levels else None
        except Exception as e:
            print(f"加载地图文件失败: {e}")
            return None

    def get_current_level_index(self, x):
        """根据x坐标获取当前关卡索引"""
        return int(x // self.level_width)

    def get_tile(self, x, y):
        """获取指定世界坐标的砖块类型(使用缓存)"""
        cache_key = (x, y)
        if cache_key in self._tile_cache:
            return self._tile_cache[cache_key]
            
        result = self._get_tile_uncached(x, y)
        self._tile_cache[cache_key] = result
        return result
        
    def _get_tile_uncached(self, x, y):
        """未缓存的砖块获取逻辑"""
        # 计算关卡索引
        level_index = self.get_current_level_index(x)
        if 0 <= level_index < len(self.levels):
            # 计算在当前关卡中的相对坐标
            local_x = int((x % self.level_width) // self.tile_size)
            local_y = int(y // self.tile_size)
            
            if (0 <= local_y < len(self.levels[level_index]) and 
                0 <= local_x < len(self.levels[level_index][0])):
                return self.levels[level_index][local_y][local_x]
        return self.WALL  # 边界外视为墙

    def render(self, camera_offset=(0, 0)):
        """渲染地图
        Args:
            camera_offset: (camera_x, camera_y) 相机偏移量
        """
        self.render_level(camera_offset)

    def render_level(self, camera_offset=(0, 0)):
        """渲染可见范围内的关卡"""
        screen_width = self.game.screen.get_width()
        screen_height = self.game.screen.get_height()
        camera_x, camera_y = camera_offset
        
        # 增加缓冲区，防止突然的视野变化
        buffer = self.tile_size * 2
        
        # 计算可见区域
        visible_rect = pygame.Rect(
            camera_x - buffer,
            camera_y - buffer,
            screen_width + buffer * 2,
            screen_height + buffer * 2
        )
        
        # 只渲染可见区域内的砖块
        start_level = max(0, self.get_current_level_index(visible_rect.left))
        end_level = min(len(self.levels), 
                       self.get_current_level_index(visible_rect.right) + 1)
        
        # 渲染每个可见的关卡
        for level_index in range(start_level, end_level):
            level_data = self.levels[level_index]
            level_offset_x = level_index * self.level_width
            
            # 计算可见区域的砖块范围
            start_x = max(0, int((camera_x - level_offset_x) // self.tile_size))
            end_x = min(
                len(level_data[0]),
                int((camera_x + screen_width - level_offset_x) // self.tile_size + 1)
            )
            start_y = max(0, int(camera_y // self.tile_size))
            end_y = min(
                len(level_data),
                int((camera_y + screen_height) // self.tile_size + 1)
            )

            # 更新渲染砖块的部分
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    tile = level_data[y][x]
                    if tile != self.EMPTY:
                        screen_x = level_offset_x + x * self.tile_size - camera_x
                        screen_y = y * self.tile_size - camera_y
                        self.render_tile(tile, screen_x, screen_y)

    def render_tile(self, tile, screen_x, screen_y):
        """渲染单个砖块
        Args:
            tile: 砖块类型
            screen_x: 屏幕X坐标
            screen_y: 屏幕Y坐标
        """
        if tile == self.EMPTY:
            return
            
        main_rect = pygame.Rect(
            screen_x, screen_y,
            self.tile_size, self.tile_size
        )
        
        # 特殊砖块的渲染逻辑
        if tile == self.SPIKE:
            # 绘制三角形尖刺
            spike_points = [
                (screen_x + self.tile_size//2, screen_y),  # 顶点
                (screen_x + self.tile_size, screen_y + self.tile_size),  # 右下
                (screen_x, screen_y + self.tile_size)  # 左下
            ]
            pygame.draw.polygon(
                self.game.screen,
                self.tile_colors[tile],
                spike_points
            )
            pygame.draw.polygon(
                self.game.screen,
                self.tile_border_colors[tile],
                spike_points,
                2
            )
            
        elif tile == self.BOUNCE:
            # 绘制弹跳板（梯形）
            bounce_points = [
                (screen_x + 5, screen_y + self.tile_size),  # 左下
                (screen_x + self.tile_size - 5, screen_y + self.tile_size),  # 右下
                (screen_x + self.tile_size - 15, screen_y + 10),  # 右上
                (screen_x + 15, screen_y + 10)  # 左上
            ]
            pygame.draw.polygon(
                self.game.screen,
                self.tile_colors[tile],
                bounce_points
            )
            pygame.draw.polygon(
                self.game.screen,
                self.tile_border_colors[tile],
                bounce_points,
                2
            )
            
        elif tile == self.LAVA:
            # 绘制熔（带波浪效果）
            wave_height = 4
            wave_points = [(screen_x, screen_y + self.tile_size)]
            for i in range(5):
                x = screen_x + (i * self.tile_size // 4)
                y = screen_y + self.tile_size - wave_height * (i % 2)
                wave_points.append((x, y))
            wave_points.append((screen_x + self.tile_size, screen_y + self.tile_size))
            pygame.draw.polygon(
                self.game.screen,
                self.tile_colors[tile],
                wave_points
            )
            
        elif tile == self.WATER:
            # 绘制水面（半透明）
            surface = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            pygame.draw.rect(surface, (*self.tile_colors[tile][:3], 128), 
                           (0, 0, self.tile_size, self.tile_size))
            self.game.screen.blit(surface, main_rect)
            
        elif tile == self.GLASS:
            # 绘制玻璃（半透明带边框）
            surface = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            pygame.draw.rect(surface, self.tile_colors[tile], 
                           (0, 0, self.tile_size, self.tile_size))
            pygame.draw.rect(surface, self.tile_border_colors[tile], 
                           (0, 0, self.tile_size, self.tile_size), 2)
            self.game.screen.blit(surface, main_rect)
            
        elif tile == self.BRICK:
            # 绘制砖块（带纹理）
            self.game.view.draw_rect(self.tile_colors[tile], main_rect)
            # 绘制砖块纹理
            brick_height = self.tile_size // 4
            for i in range(4):
                y = screen_y + i * brick_height
                pygame.draw.line(
                    self.game.screen,
                    self.tile_border_colors[tile],
                    (screen_x, y),
                    (screen_x + self.tile_size, y),
                    1
                )
                if i % 2 == 0:
                    pygame.draw.line(
                        self.game.screen,
                        self.tile_border_colors[tile],
                        (screen_x + self.tile_size//2, y),
                        (screen_x + self.tile_size//2, y + brick_height),
                        1
                    )
            
        else:
            # 默认砖块渲染
            self.game.view.draw_rect(self.tile_colors[tile], main_rect)
            self.game.view.draw_rect(self.tile_border_colors[tile], main_rect, 2)
            
            # 添加高光效果
            highlight_rect = pygame.Rect(
                screen_x + 2,
                screen_y + 2,
                self.tile_size - 4,
                self.tile_size - 4
            )
            self.game.view.draw_rect(self.tile_highlight_colors[tile], highlight_rect)

    def is_solid(self, x, y):
        """检查指定位置是否为实心砖块"""
        tile = self.get_tile(x, y)
        return tile in [self.WALL, self.PLATFORM]

    def is_hazard(self, x, y):
        """检查指位置是否为危险物"""
        return self.get_tile(x, y) == self.SPIKE


if __name__ == "__main__":
    game = Game()
    game.run()

import pygame
from animation import AnimationManager

class Player:
    """玩家类"""
    def __init__(self, gamemap, x, y):
        self.gamemap = gamemap
        # 位置和大小
        self.width = 64
        self.height = 128
        self.x = x
        self.y = y
        
        # 速度和加速度
        self.vx = 0
        self.vy = 0
        self.speed = 400  # 移动速度
        self.jump_force = -650  # 降低初始跳跃力度，使跳跃更自然
        self.gravity = 1500  # 调整重力，使下落感更好
        
        # 状态
        self.on_ground = False
        self.facing_right = True
        self.color = (50, 150, 250)  # 蓝色
        
        # 动画系统
        self.animation_manager = AnimationManager()
        self._load_animations()
        
        # 调整空中控制相关的属性
        self.air_control = 0.6  # 增加空中控制度
        self.air_resistance = 0.5  # 保持现有空气阻力
        self.air_acceleration = 1000  # 增加空中加速度
        self.max_air_speed = 400  # 保持现有最大空中速度
        
        # 新增缓冲跳跃机制
        self.jump_buffer_time = 150  # 跳跃缓冲时间（毫秒）
        self.jump_buffer_timer = 0
        
        # 新增土狼时间（Coyote Time）机制
        self.coyote_time = 100  # 土狼时间（毫秒）
        self.coyote_timer = 0
        self.just_left_ground = False
        
        # 添加行走/跑步速度阈值
        self.walk_speed = 200  # 行走速度阈值
        self.run_speed = 400   # 跑步速度（原speed值）
        self.speed = 0  # 默认使用行走速度
        
        # 跳跃优化参数
        self.jump_cut_threshold = -100  # 跳跃中断阈值
        self.max_jump_hold_time = 100  # 最大跳跃按住时间(毫秒)
        self.jump_hold_timer = 0  # 跳跃按住计时器
        self.is_jumping = False  # 是否正在跳跃
        
        # 添加生命值相关属性
        self.max_health = 100
        self.health = self.max_health
        self.invincible_time = 0  # 无敌时间
        self.invincible_duration = 1.0  # 受伤后的无敌持续时间
        self.health_regen_rate = 1  # 每秒回复的生命值
        self.health_regen_delay = 5.0  # 开始回血前的延迟时间
        self.last_damage_time = 0  # 上次受伤时间
        
    def _load_animations(self):
        """加载所有动画"""
        # 设置动画尺寸为玩家尺寸
        self.animation_manager.set_scale(self.width, self.height)
        
        # 定义动画配置
        animations = {
            'idle': ('idle.png', 0, 1, 64, 128, 150),           # 第一行 - 正面
            'idle_left': ('idle.png', 1, 1, 64, 128, 150),      # 第二行 - 左面
            'idle_right': ('idle.png', 2, 1, 64, 128, 150),     # 第三行 - 右面

            'walk': ('walk.png', 0, 6, 64, 128, 150),           # 第一行 - 正面
            'walk_left': ('walk.png', 1, 6, 64, 128, 150),      # 第二行 - 左面
            'walk_right': ('walk.png', 2, 6, 64, 128, 150),     # 第三行 - 右面
            
            'run': ('run.png', 0, 6, 64, 128, 100),            # 第一行 - 正面
            'run_left': ('run.png', 1, 6, 64, 128, 100),       # 第二行 - 左面
            'run_right': ('run.png', 2, 6, 64, 128, 100),      # 第三行 - 右面
            
            'jump': ('jump.png', 0, 4, 64, 128, 100, False),   # 第一行 - 正面
            'jump_left': ('jump.png', 1, 4, 64, 128, 100, False),  # 第二行 - 左面
            'jump_right': ('jump.png', 2, 4, 64, 128, 100, False), # 第三行 - 右面
            
            'fall': ('fall.png', 0, 2, 64, 128, 150),          # 第一行 - 正面
            'fall_left': ('fall.png', 1, 2, 64, 128, 150),     # 第二行 - 左面
            'fall_right': ('fall.png', 2, 2, 64, 128, 150),    # 第三行 - 右面
        }
        
        # 加载每个动画
        for name, params in animations.items():
            # 解包参数，如果没有指定循环参数，默认为True
            if len(params) == 6:
                file, row, columns, width, height, duration = params
                loop = True
            else:
                file, row, columns, width, height, duration, loop = params
                
            path = f"assets/sprites/{file}"
            try:
                self.animation_manager.load_animation(
                    name, path, row, columns, width, height,
                    frame_duration=duration, loop=loop
                )
            except Exception as e:
                print(f"Failed to load animation {name}: {e}")
        
        # 设置默认动画
        self.animation_manager.play('idle')
        
    def update(self, dt):
        """更新玩家状态"""
        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        
        # 更新土狼时间
        if not self.on_ground:
            if self.just_left_ground:
                self.just_left_ground = False
                self.coyote_timer = current_time
        
        # 优化跳跃处理
        jump_key_pressed = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        
        if jump_key_pressed:
            self.jump_buffer_timer = current_time
            if self.is_jumping:
                # 处理长按跳跃
                if current_time - self.jump_hold_timer < self.max_jump_hold_time:
                    self.vy = min(self.vy, self.jump_force * 0.85)  # 持续施加向上的力
        else:
            # 跳跃中断处理
            if self.is_jumping and self.vy < self.jump_cut_threshold:
                self.vy = self.jump_cut_threshold
            self.is_jumping = False
        
        # 检查是否可以跳跃
        can_jump = self.on_ground or (current_time - self.coyote_timer < self.coyote_time)
        
        # 处理跳跃触发
        if current_time - self.jump_buffer_timer < self.jump_buffer_time and can_jump:
            self.vy = self.jump_force
            self.is_jumping = True
            self.jump_hold_timer = current_time
            self.on_ground = False
            self.jump_buffer_timer = 0
            self.coyote_timer = 0
        
        # 可变跳跃高度
        if not keys[pygame.K_SPACE] and not keys[pygame.K_UP] and not keys[pygame.K_w]:
            if self.vy < 0:
                self.vy *= 0.5  # 松开跳跃键时减小上升速度
        
        # 1. 计算目标速度和方向
        target_vx = 0
        # 根据是否按住Shift键来决定速度
        current_speed = self.run_speed if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else self.walk_speed
        
        # 2. 根据按键设置目标速度和方向
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            target_vx = -current_speed
            if self.on_ground:  # 只在地面上时更新朝向
                self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            target_vx = current_speed
            if self.on_ground:  # 只在地面上时更新朝向
                self.facing_right = True
            
        # 3. 根据是否在地面应用不同的移动逻辑
        if self.on_ground:
            self.vx = target_vx  # 直接设置速度
            self.speed = current_speed  # 记录当前速度类型（走/跑）
            self.last_ground_direction = self.facing_right
        else:
            # 新的空中移动逻辑
            if target_vx != 0:
                # 计算空中加速度
                air_acceleration = self.air_acceleration * (1 if target_vx > 0 else -1)
                # 应用空中控制
                self.vx += air_acceleration * dt * self.air_control
                
                # 限制最大速度
                if abs(self.vx) > self.max_air_speed:
                    self.vx = self.max_air_speed if self.vx > 0 else -self.max_air_speed
                
                # 更新朝向
                self.facing_right = target_vx > 0
            else:
                # 没有输入时应用空气阻力
                self.vx *= self.air_resistance
        
        # 调整下落速度
        if self.vy > 0:
            self.vy += self.gravity * dt * 1.3  # 略微增加下落加速度
        else:
            self.vy += self.gravity * dt * 0.95  # 上升时稍微减小重力
        
        # 限制最大下落速度
        max_fall_speed = 1000
        self.vy = min(self.vy, max_fall_speed)
        
        # 更新位置并处理碰撞
        self._move(dt)
        
        # 更新动画状态
        self._update_animation_state()
        # 动画
        self.animation_manager.update(pygame.time.get_ticks())
        
        # 处理生命值回复
        current_time = pygame.time.get_ticks() / 1000.0
        if (current_time - self.last_damage_time > self.health_regen_delay and 
            self.health < self.max_health):
            self.health = min(self.max_health, 
                            self.health + self.health_regen_rate * dt)
        
    def _update_animation_state(self):
        """更新动画状态"""
        # 1. 空中状态
        if not self.on_ground:
            if self.vy < 0:
                base_anim = 'jump'
            else:
                base_anim = 'fall'
            
            # 根据朝向添加方向后缀
            anim_name = f"{base_anim}_right" if self.facing_right else f"{base_anim}_left"
            self.animation_manager.play(anim_name)
            return

        # 2. 地面状态
        if abs(self.vx) < 1:  # 静止状态
            base_anim = 'idle'
            anim_name = f"{base_anim}_right" if self.facing_right else f"{base_anim}_left"
        else:
            # 根据当前速度和朝向决定动画
            if self.speed == self.run_speed:
                base_anim = 'run'
            else:
                base_anim = 'walk'
            
            anim_name = f"{base_anim}_right" if self.facing_right else f"{base_anim}_left"
        self.animation_manager.play(anim_name)
        
    def _move(self, dt):
        """移动并处理碰撞"""
        # 水平移动
        self.x += self.vx * dt
        self._check_x_collision()
        
        # 垂直移动
        self.y += self.vy * dt
        self._check_y_collision()
    
    def _check_x_collision(self):
        """检查水平方向的碰撞"""
        # 确定检查方向
        if self.vx > 0:
            check_x = self.x + self.width
        else:
            check_x = self.x
            
        # 检查三个点（上中下）
        check_points = [
            (check_x, self.y),  # 上
            (check_x, self.y + self.height / 2),  # 中
            (check_x, self.y + self.height - 1)  # 下
        ]
        
        for px, py in check_points:
            if self.gamemap.is_solid(px, py):
                if self.vx > 0:
                    self.x = (px // self.gamemap.tile_size) * self.gamemap.tile_size - self.width
                else:
                    self.x = (px // self.gamemap.tile_size + 1) * self.gamemap.tile_size
                self.vx = 0
                break
    
    def _check_y_collision(self):
        """检查垂直方向的碰撞"""
        self.on_ground = False
        
        # 确定检查方向
        if self.vy > 0:
            check_y = self.y + self.height
        else:
            check_y = self.y
            
        # 检查三个点（左中右）
        check_points = [
            (self.x, check_y),  # 左
            (self.x + self.width / 2, check_y),  # 中
            (self.x + self.width - 1, check_y)  # 右
        ]
        
        for px, py in check_points:
            # 下落时检查实心块和平台，上升时只检查实心块
            if (self.vy > 0 and self.gamemap.get_tile(px, py) in [self.gamemap.WALL, self.gamemap.PLATFORM]) or \
               (self.vy < 0 and self.gamemap.is_solid(px, py)):
                if self.vy > 0:
                    self.y = (py // self.gamemap.tile_size) * self.gamemap.tile_size - self.height
                    self.on_ground = True
                else:
                    self.y = (py // self.gamemap.tile_size + 1) * self.gamemap.tile_size
                self.vy = 0
                break
    
    def render(self, camera_offset=(0, 0)):
        """渲染玩家"""
        screen_x = self.x - camera_offset[0]
        screen_y = self.y - camera_offset[1]
        
        # 获取当前动画帧
        current_frame = self.animation_manager.get_current_frame()
        if current_frame:
            self.gamemap.game.screen.blit(current_frame, (screen_x, screen_y))
        else:
            # 如果没有动画帧，使用默认的矩形
            player_rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
            self.gamemap.game.view.draw_rect(self.color, player_rect) 
        
    def take_damage(self, amount):
        """受到伤害
        Args:
            amount: 伤害值
        """
        current_time = pygame.time.get_ticks() / 1000.0  # 转换为秒
        
        # 检查是否处于无敌状态
        if current_time < self.invincible_time:
            return
            
        # 应用伤害
        self.health = max(0, self.health - amount)
        
        # 设置无敌时间
        self.invincible_time = current_time + self.invincible_duration
        
        # 记录受伤时间（用于回血计时）
        self.last_damage_time = current_time
        
        # 如果生命值为0，处理死亡
        if self.health <= 0:
            self._handle_death()
            
    def _handle_death(self):
        """处理玩家死亡"""
        # 这里可以添加死亡动画、音效等
        # 重置到最近的检查点或关卡起点
        self.health = self.max_health
        self.x = 100  # 重置位置
        self.y = 300
        

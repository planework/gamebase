import pygame

class Enemy:
    def __init__(self, game_map, x, y):
        self.game_map = game_map
        self.x = x
        self.y = y
        self.width = 40
        self.height = 60
        self.vx = 0
        self.vy = 0
        self.color = (255, 0, 0)  # 红色
        self.on_ground = False
        self.game = game_map.game  # 添加游戏引用
        self.health = 100  # 添加生命值
        
        # 碰撞相关
        self.collision_buffer = 2  # 碰撞检测的缓冲区
        self.collision_points = 3  # 每个方向的检测点数量
        
        # 确保初始位置在地面上
        self._snap_to_ground()
        
    def _snap_to_ground(self):
        """将实体对齐到地面"""
        # 向下检测直到找到地面
        test_y = self.y
        while test_y < self.game_map.level_height:
            if self.game_map.is_solid(self.x + self.width/2, test_y + self.height):
                self.y = test_y
                self.on_ground = True
                return
            test_y += self.game_map.tile_size/2  # 每次检测半个砖块的距离
            
        # 如果没找到地面，至少确保不会超出地图
        self.y = min(self.y, self.game_map.level_height - self.height - self.game_map.tile_size)
        
    def update(self, dt):
        """更新敌人状态"""
        # 应用重力
        if not self.on_ground:
            self.vy += 800 * dt  # 重力加速度
            
        # 限制最大下落速度
        max_fall_speed = 800
        self.vy = min(self.vy, max_fall_speed)
        
        # 分别更新水平和垂直位置，并进行碰撞检测
        self._update_x(dt)
        self._update_y(dt)
        
    def _update_x(self, dt):
        """更新水平位置并处理碰撞"""
        # 保存原始位置
        original_x = self.x
        
        # 更新水平位置
        self.x += self.vx * dt
        
        # 检查水平碰撞
        if self._check_x_collision():
            # 发生碰撞时恢复到原始位置
            self.x = original_x
            self.vx = 0
        
    def _update_y(self, dt):
        """更新垂直位置并处理碰撞"""
        # 保存原始位置
        original_y = self.y
        self.on_ground = False
        
        # 更新垂直位置
        self.y += self.vy * dt
        
        # 检查垂直碰撞
        collision_type = self._check_y_collision()
        if collision_type == 'ceiling':
            self.y = original_y
            self.vy = 0
        elif collision_type == 'ground':
            # 计算确切的地面位置
            self.y = (self.y + self.height) // self.game_map.tile_size * self.game_map.tile_size - self.height
            self.vy = 0
            self.on_ground = True
        
    def _check_x_collision(self):
        """检查水平方向的碰撞
        Returns:
            bool: 是否发生碰撞
        """
        # 确定检查方向
        if self.vx > 0:
            check_x = self.x + self.width + self.collision_buffer
        else:
            check_x = self.x - self.collision_buffer
            
        # 生成检查点
        check_points = []
        for i in range(self.collision_points):
            y_offset = (self.height / (self.collision_points - 1)) * i
            check_points.append((check_x, self.y + y_offset))
        
        # 检查所有点
        for px, py in check_points:
            if self.game_map.is_solid(px, py):
                return True
                
        return False
        
    def _check_y_collision(self):
        """检查垂直方向的碰撞
        Returns:
            str: 碰撞类型 ('ground', 'ceiling', None)
        """
        # 确定检查方向和位置
        if self.vy > 0:  # 下落
            check_y = self.y + self.height + self.collision_buffer
            # 生成底部检查点
            check_points = []
            for i in range(self.collision_points):
                x_offset = (self.width / (self.collision_points - 1)) * i
                check_points.append((self.x + x_offset, check_y))
                
            # 检查是否碰到地面或平台
            for px, py in check_points:
                tile = self.game_map.get_tile(px, py)
                if tile in [self.game_map.WALL, self.game_map.PLATFORM]:
                    return 'ground'
                    
        else:  # 上升
            check_y = self.y - self.collision_buffer
            # 生成顶部检查点
            check_points = []
            for i in range(self.collision_points):
                x_offset = (self.width / (self.collision_points - 1)) * i
                check_points.append((self.x + x_offset, check_y))
                
            # 只检查实心墙
            for px, py in check_points:
                if self.game_map.is_solid(px, py):
                    return 'ceiling'
                    
        return None
        
    def render(self, camera_offset=(0, 0)):
        """渲染敌人"""
        screen_x = int(self.x - camera_offset[0])
        screen_y = int(self.y - camera_offset[1])
        
        # 只在屏幕范围内渲染
        screen_width = self.game.screen.get_width()
        screen_height = self.game.screen.get_height()
        
        if (-self.width <= screen_x <= screen_width and 
            -self.height <= screen_y <= screen_height):
            
            # 绘制敌人主体
            pygame.draw.rect(
                self.game.screen,
                self.color,
                (screen_x, screen_y, self.width, self.height)
            )
            
            # 绘制边框
            pygame.draw.rect(
                self.game.screen,
                (200, 0, 0),  # 深红色边框
                (screen_x, screen_y, self.width, self.height),
                2
            )
            
            # 添加简单的面部特征
            eye_color = (255, 255, 255)  # 白色眼睛
            eye_size = 8
            # 左眼
            pygame.draw.circle(
                self.game.screen,
                eye_color,
                (screen_x + self.width//3, screen_y + self.height//3),
                eye_size
            )
            # 右眼
            pygame.draw.circle(
                self.game.screen,
                eye_color,
                (screen_x + 2*self.width//3, screen_y + self.height//3),
                eye_size
            )
            
            # 渲染AI的叫骂文本
            if hasattr(self, 'ai'):
                self.ai.render(self.game.screen, camera_offset)
    def take_damage(self, amount):
        """受到伤害"""
        self.health -= amount
        if self.health <= 0:
            # 通知游戏移除此敌人
            if self in self.game.enemies:
                self.game.enemies.remove(self)
                self.game.view.remove_from_layer('playground', self) 
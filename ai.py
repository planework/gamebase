import pygame
import random
import math
from enum import Enum
import heapq
from collections import defaultdict
import time

class AIState(Enum):
    """AI状态枚举"""
    IDLE = "idle"           
    PATROL = "patrol"       
    CHASE = "chase"         
    ATTACK = "attack"       
    RETREAT = "retreat"     
    STUNNED = "stunned"     
    SEARCH = "search"       # 新增：搜索状态
    ALERT = "alert"         # 新增：警戒状态

class AStarPathFinding:
    """A*寻路算法实现"""
    def __init__(self, game_map):
        self.game_map = game_map
        self.tile_size = game_map.tile_size
        self.max_iterations = 1000  # 防止无限循环
        
    def find_path(self, start, end):
        """寻找路径
        Args:
            start: (x, y) 起点坐标
            end: (x, y) 终点坐标
        Returns:
            list: 路径点列表
        """
        start_node = (int(start[0] // self.tile_size), 
                     int(start[1] // self.tile_size))
        end_node = (int(end[0] // self.tile_size), 
                   int(end[1] // self.tile_size))
        
        frontier = []
        heapq.heappush(frontier, (0, start_node))
        came_from = {start_node: None}
        cost_so_far = {start_node: 0}
        
        while frontier:
            current = heapq.heappop(frontier)[1]
            
            if current == end_node:
                break
                
            for next_node in self._get_neighbors(current):
                new_cost = cost_so_far[current] + 1
                
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self._heuristic(next_node, end_node)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current
                    
        # 重建路径
        path = []
        current = end_node
        while current != start_node:
            if current not in came_from:
                return []  # 无法找到路径
            path.append((current[0] * self.tile_size + self.tile_size // 2,
                        current[1] * self.tile_size + self.tile_size // 2))
            current = came_from[current]
            
        path.append((start[0], start[1]))
        path.reverse()
        return path
        
    def _get_neighbors(self, node):
        """获取相邻节点"""
        x, y = node
        neighbors = []
        
        # 基本方向
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for dx, dy in directions:
            next_x, next_y = x + dx, y + dy
            if self._is_valid_node((next_x, next_y)):
                neighbors.append((next_x, next_y))
                
        return neighbors
        
    def _is_valid_node(self, node):
        """检查节点是否有效"""
        x, y = node
        # 检查是否在地图范围内
        if x < 0 or y < 0:
            return False
            
        # 获取实际的世界坐标
        world_x = x * self.tile_size
        world_y = y * self.tile_size
        
        # 检查是否是实心砖块
        if self.game_map.is_solid(world_x, world_y):
            return False
            
        # 检查头顶是否有空间（假设实体高度为2个tile）
        if self.game_map.is_solid(world_x, world_y - self.tile_size):
            return False
            
        return True
        
    def _heuristic(self, a, b):
        """启发式函数 - 曼哈顿距离"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

class AIEmotionState:
    def __init__(self):
        self.aggression = 0.5
        self.fear = 0.0
        self.confidence = 0.5
        
    def update(self, dt, combat_info):
        # 根据战斗情况更新情绪
        if combat_info['took_damage']:
            self.fear += 0.2
            self.confidence -= 0.1
        if combat_info['dealt_damage']:
            self.aggression += 0.1
            self.confidence += 0.1
            
        # 情绪衰减
        self.aggression = max(0.5, self.aggression - 0.1 * dt)
        self.fear = max(0, self.fear - 0.1 * dt)
        self.confidence = min(1, max(0, self.confidence))

class AI:
    """AI基类"""
    def __init__(self, entity, game_map):
        # 基础引用
        self.entity = entity          # AI控制的实体
        self.game_map = game_map      # 游戏地图用
        
        # 状态相关
        self.state = AIState.IDLE     # 当前状态
        self.target = None            # 当前目标
        self.state_timer = 0          # 状态计时器
        
        # 移动参数
        self.detection_range = 400    # 增加检测范围 (从300增加到400)
        self.attack_range = 80        # 攻击范围
        self.move_speed = 180         # 增加移动速度 (从150增加到180)
        self.jump_force = -400        # 跳跃力度
        
        # 行为参数
        self.aggression = 0.7         # 攻击性(0-1)
        self.caution = 0.3           # 谨慎性(0-1)
        self.intelligence = 0.5       # 智能程度(0-1)
        
        # 路径寻找
        self.path = []               # 当前路径
        self.path_update_timer = 0   # 路径更新计时器
        self.path_update_interval = 0.2  # 减少路径更新间隔 (从0.3减少到0.2)
        self.path_finding = AStarPathFinding(game_map)
        self.path_progress = 0       # 当前路径进度
        
        # 确保初始化所有必要的属性
        self.attack_cooldown = 0
        self.last_state_change = 0
        self.state_change_cooldown = 0.2  # 减少状态切换冷却 (从0.5减少到0.2)
        self.alert_level = 0
        self.search_timer = 0
        self.last_known_target_pos = None
        self.behavior_weights = {
            'aggression': 0.5,
            'caution': 0.5,
            'intelligence': 0.5,
            'persistence': 0.5
        }
        
        # 移动相关参数
        self.target_vx = 0           # 目标水平速度
        self.acceleration = 1000      # 增加加速度 (从800增加到1000)
        self.deceleration = 1500      # 增加减速度 (从1200增加到1500)
        self.min_jump_height = 32    # 最小跳跃高度
        self.jump_cooldown = 0       # 跳跃冷却
        self.jump_cooldown_time = 1.0  # 跳跃冷却时间
        
        # 添加寻路相关的初始化
        self.path_node_distance = 64   # 路径节点间距
        self.max_path_length = 10      # 最大路径长度
        
        # 添加战斗相关的初始化
        self.attack_damage = 10        # 基础攻击伤害
        self.attack_knockback = 300    # 基础击退力度
        self.attack_cooldown_time = 1.0  # 攻击冷却时间
        
        # 添加搜索相关的初始化
        self.search_radius = 100       # 搜索半径
        self.search_timeout = 5.0      # 搜索超时时间
        
        # 添加状态持续时间
        self.alert_duration = 3.0      # 戒状态持续时间
        self.stunned_duration = 1.0    # 眩晕状态持续时间
        
        # 添加视觉和感知参数
        self.vision_angle = math.pi / 2  # 视野角度 (90度)
        self.vision_distance = 400       # 视野距离
        self.hearing_range = 300         # 听觉范围
        
        # 添加战斗参数
        self.attack_windup = 0.2        # 攻击前摇时间
        self.attack_recovery = 0.3      # 攻击后摇时间
        self.combo_window = 0.8         # 连击窗口时间
        self.combo_count = 0            # 当前连击数
        
        # 添加状态持续时间制
        self.state_durations = {
            AIState.ALERT: 3.0,         # 警戒状态最长持续时间
            AIState.SEARCH: 5.0,        # 搜索状态最长持续时间
            AIState.CHASE: 10.0,        # 追击状态最长持续时间
            AIState.RETREAT: 4.0,       # 撤退状态最长持续时间
        }
        
        # 添加行为阈值
        self.thresholds = {
            'health_retreat': 0.3,      # 生值低于30%时考虑退
            'health_cautious': 0.5,     # 生命值低于50%时更谨慎
            'alert_chase': 70,          # 警戒值高于70时可能追击
            'alert_decay': 5,           # 衰减量
        }
        
        # 添加攻击相关参数
        self.attack_type = random.choice(['melee'] * 8 + ['ranged'] * 2)  # 随机选择攻击类型，低远程攻击的概率(20%)
        self.melee_range = 60  # 近战攻击范围
        self.ranged_range = 200  # 远程攻击范围
        self.attack_range = self.melee_range if self.attack_type == 'melee' else self.ranged_range
        
        # 近战攻击参数
        self.lunge_speed = 400  # 扑击速度
        self.lunge_duration = 0.3  # 扑击持续时间
        self.lunge_cooldown = 1.5  # 扑击冷却时间
        self.is_lunging = False  # 是否正在扑击
        self.lunge_timer = 0  # 扑击计时器
        
        # 远程攻击参数
        self.projectile_speed = 300  # 投射物速度
        self.projectile_cooldown = 2.0  # 射击冷却时间
        self.projectile_damage = 8  # 投射物伤害
        self.max_shots = 3            # 连续射击最大次数
        self.shots_fired = 0          # 当前射击次数
        self.burst_cooldown = 4.0     # 连发冷却时间
        
        # 叫骂相关参数
        self.taunt_cooldown = 0      # 叫骂冷却
        self.taunt_cooldown_time = 2.0  # 减少叫骂冷却时间 (从3.0改为2.0)
        self.taunt_duration = 1.5    # 增加显示持续时间 (从1.0改为1.5)
        self.current_taunt = None    # 当前显示的叫骂文本
        self.taunt_timer = 0         # 叫显示计时器
        self.taunt_offset_y = 0      # 文本上下浮动偏移
        self.taunt_float_speed = 2   # 浮动速度
        
        # 尝试加载中文字体
        try:
            # Windows系统常见中文字体
            font_names = [
                'SimHei',           # 黑体
                'Microsoft YaHei',  # 微软雅黑
                'SimSun',          # 宋体
                'NSimSun',         # 新宋体
                'FangSong',        # 仿宋
                'KaiTi'            # 楷体
            ]
            
            # 尝试加载字体
            self.font = None
            for font_name in font_names:
                try:
                    self.font = pygame.font.SysFont(font_name, 24)  # 增大字号到24
                    test_surface = self.font.render("测试", True, (255, 255, 255))
                    if test_surface.get_width() > 0:  # 验证字是否正确渲染
                        print(f"成功加载字体: {font_name}")
                        break
                except:
                    continue
                
            # 如果没有找到中文字体，使用默认字体
            if self.font is None:
                print("警告：无法加载中文字体，使用默认字体")
                self.font = pygame.font.Font(None, 24)
                
        except Exception as e:
            print(f"字体加载错误: {e}")
            self.font = pygame.font.Font(None, 24)
            
        # 更新叫骂文本内容，添加玩家逃跑相关的叫骂
        self.taunts = {
            'alert': [
                "! 有入侵者！",
                "! 谁在那里？",
                "! 发现目标！",
                "! 站住！别动！"
            ],
            'chase': [
                "-> 别想跑！",
                "-> 抓住你了！",
                "-> 你跑不掉的！",
                "-> 看我追上你！"
            ],
            'attack': [
                "* 看招！",
                "* 吃我一击！",
                "* 拿命来！",
                "* 受死吧！"
            ],
            'retreat': [
                "<- 战略性撤退！",
                "<- 暂时撤退...",
                "<- 我还会回来的！",
                "<- 下次再战！"
            ],
            'search': [
                "? 躲在哪里？",
                "? 出来啊！",
                "? 我知道你在附近...",
                "? 让我找找..."
            ],
            'hit': [
                "x 啊！",
                "x 可恶！",
                "x 你会付出代价！",
                "x 这点伤算什么！"
            ],
            'victory': [
                "v 解决了！",
                "v 胜利！",
                "v 就这点本事？",
                "v 太弱了！"
            ],
            # 新增玩家逃跑相关的叫骂
            'player_flee': [
                "→ 别跑啊，胆小鬼！",
                "→ 哈哈，被吓跑吗？",
                "→ 跑得掉吗？",
                "→ 回来打啊！"
            ],
            'player_hide': [
                "? 躲起来了？懦夫！",
                "? 不敢正面对决吗？",
                "? 就知道躲躲藏藏！",
                "? 出来单挑啊！"
            ],
            'mock_player': [
                "! 就这？",
                "! 太弱了吧！",
                "! 不堪一击！",
                "! 不自量力！"
            ],
            'player_avoid': [
                "→ 怎么，不敢来打吗？",
                "→ 一直躲着算什么英雄！",
                "→ 来啊，别当缩头乌龟！",
                "→ 这就是你的实力？就知道躲！"
            ],
            'player_far': [
                "! 站那么远干什么？",
                "! 有本事近战啊！",
                "! 不敢近身吗？",
                "! 离这么远，怕了？"
            ],
            'challenge': [
                "* 来单挑啊！",
                "* 有种过来打！",
                "* 你就只会躲吗？",
                "* 看来你也就这点胆量！"
            ],
            'combat_end': [
                "→ 算你跑得快！",
                "→ 下次别让我逮到你！",
                "→ 懦夫！别跑！",
                "→ 跑什么跑！"
            ],
            'combat_start': [
                "* 终于敢来了？",
                "* 看来你还有点胆量！",
                "* 这次别想跑！",
                "* 来战个痛快！"
            ]
        }
        
        # 添加避战检测相关参数
        self.player_avoid_timer = 0      # 玩家避战计时器
        self.avoid_threshold = 5.0       # 避战判定阈值（秒）
        self.last_player_interaction = 0  # 上次与玩家交互时间
        
        # 添加脱战相关参数
        self.combat_timer = 0           # 战斗计时器
        self.combat_timeout = 5.0       # 脱战时间阈值
        self.last_combat_time = 0       # 上次战斗时间
        self.in_combat = False          # 是否在战斗中
        
        self.emotion_state = AIEmotionState()
        
        # 添加目标锁定相关参数
        self.target_locked = False        # 是否锁定目标
        self.target_lock_time = 0         # 目标锁定时间
        self.target_lock_duration = 2.0   # 锁定持续时间
        self.lock_break_distance = 500    # 锁定打断距离
        
        # 视觉相关参数调整
        self.vision_angle = math.pi / 2   # 视锥角度(90度)
        self.vision_distance = 400        # 视野距离
        self.peripheral_vision = math.pi * 0.75  # 周边视野(135度)

    def update(self, dt, player_pos):
        """更新AI状态和行为"""
        if self.state == AIState.STUNNED:
            self._update_stunned(dt)
            return
            
        # 更新计时器
        self.state_timer += dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        # 获取感知信息
        perception_info = self._check_perception(player_pos)
        perception_info['player_pos'] = player_pos
        
        # 更新朝向
        self._update_facing_direction(perception_info)
        
        # 状态转换（添加冷却检查）
        current_time = time.time()
        if current_time - self.last_state_change >= self.state_change_cooldown:
            new_state = self._determine_new_state(perception_info)
            if new_state != self.state:
                self._on_state_change(new_state)
                self.state = new_state
                self.last_state_change = current_time
        
        # 更新行为
        self._update_current_state(dt, perception_info)
        
        # 平滑移动
        self._update_movement(dt)
        
        # 更新连击计时器
        if hasattr(self, 'combo_timer'):
            self.combo_timer = max(0, self.combo_timer - dt)
            if self.combo_timer <= 0:
                self.combo_count = 0
        
        # 检查状态超时
        self._check_state_timeout(dt)
        
        # 更新扑击状态
        if self.is_lunging:
            self.lunge_timer -= dt
            if self.lunge_timer <= 0:
                self.is_lunging = False
                self.entity.vx = 0  # 停止扑击移动
        
        # 更新叫骂计时器
        if self.taunt_cooldown > 0:
            self.taunt_cooldown -= dt
        if self.taunt_timer > 0:
            self.taunt_timer -= dt
            if self.taunt_timer <= 0:
                self.current_taunt = None
        
        # 更新战斗状态
        self._update_combat_state(dt, perception_info)
        
        self.emotion_state.update(dt, {
            'took_damage': getattr(self, 'took_damage', False),
            'dealt_damage': getattr(self, 'dealt_damage', False)
        })

    def _update_current_state(self, dt, perception_info):
        """更新当前状态的具体行为"""
        state_updates = {
            AIState.IDLE: self._update_idle,
            AIState.PATROL: self._update_patrol,
            AIState.CHASE: self._update_chase,
            AIState.ATTACK: self._update_attack,
            AIState.RETREAT: self._update_retreat,
            AIState.SEARCH: self._update_search,
            AIState.ALERT: self._update_alert,
            AIState.STUNNED: self._update_stunned
        }
        
        if self.state in state_updates:
            state_updates[self.state](dt, perception_info)

    def _determine_new_state(self, perception_info):
        """确定新状态"""
        current_state = self.state
        can_see_player = perception_info['can_see_player']
        can_sense_player = perception_info['can_sense_player']
        distance = perception_info['distance']
        
        # 优先处理紧急状态
        if self._should_retreat(perception_info):
            return AIState.RETREAT
        
        # 根据当前状态和感知信息决定下一个状态
        if current_state == AIState.IDLE:
            # 从空闲状态更容易进入巡逻状态
            if can_see_player:
                return AIState.CHASE
            elif can_sense_player:
                return AIState.ALERT
            elif random.random() < 0.01:  # 1%的概率开始巡逻
                return AIState.PATROL
                
        elif current_state == AIState.PATROL:
            if can_see_player:
                return AIState.CHASE
            elif can_sense_player:
                return AIState.ALERT
                
        elif current_state == AIState.ALERT:
            if can_see_player:
                if self.behavior_weights['aggression'] > 0.5:
                    return AIState.CHASE
            elif not can_sense_player:
                if self.alert_level < 30:
                    return AIState.PATROL
                    
        elif current_state == AIState.CHASE:
            if not can_see_player:
                if can_sense_player:
                    return AIState.SEARCH
                else:
                    return AIState.PATROL
                
        elif current_state == AIState.SEARCH:
            if can_see_player:
                return AIState.CHASE
            elif self.search_timer > 3.0:
                return AIState.PATROL
                
        # 添加脱战相关的状态转换逻辑
        if not self.in_combat:
            if current_state in [AIState.CHASE, AIState.ATTACK, AIState.SEARCH]:
                return AIState.PATROL
                
        return current_state

    def _check_perception(self, player_pos):
        """检查感知信息"""
        perception_info = {
            'can_see_player': False,
            'distance': float('inf'),
            'player_pos': None,
            'can_sense_player': False,
            'has_line_of_sight': False,  # 新增:是否有直接视线
            'target_locked': False       # 新增:是否锁定目标
        }
        
        if not player_pos:
            return perception_info
        
        # 计算与玩家的距离
        dx = player_pos[0] - self.entity.x
        dy = player_pos[1] - self.entity.y
        distance = math.sqrt(dx * dx + dy * dy)
        perception_info['distance'] = distance
        
        # 检查是否在警戒范围内
        alert_range = self.detection_range * 1.5
        if distance <= alert_range:
            perception_info['can_sense_player'] = True
            
            # 如果在视觉范围内，检查是否有直接视线
            if distance <= self.detection_range:
                # 检查是否在视锥内
                if self._is_in_vision_cone(player_pos):
                    ai_center = (
                        self.entity.x + self.entity.width / 2,
                        self.entity.y + self.entity.height / 2
                    )
                    player_center = (
                        player_pos[0],
                        player_pos[1]
                    )
                    
                    # 检查视线
                    has_los = self._has_line_of_sight(ai_center, player_center)
                    perception_info['has_line_of_sight'] = has_los
                    
                    if has_los:
                        perception_info['can_see_player'] = True
                        perception_info['player_pos'] = player_pos
                        perception_info['direction'] = math.copysign(1, dx)
                        self.last_known_target_pos = player_pos
                        
                        # 锁定目标
                        if not self.target_locked:
                            self.target_locked = True
                            self.target_lock_time = time.time()
                        perception_info['target_locked'] = True
                        
                        # 看到玩家时显著提高警戒等级
                        self.alert_level = min(100, self.alert_level + 50)
                    
        # 如果失去视线但之前已锁定，保持一段时间的锁定
        elif self.target_locked:
            current_time = time.time()
            if current_time - self.target_lock_time < self.target_lock_duration:
                perception_info['target_locked'] = True
                perception_info['can_sense_player'] = True
            else:
                self.target_locked = False
                
        return perception_info

    def _is_in_vision_cone(self, target_pos):
        """检查目标是否在视锥内"""
        # 计算到目标的向量
        dx = target_pos[0] - (self.entity.x + self.entity.width/2)
        dy = target_pos[1] - (self.entity.y + self.entity.height/2)
        
        # 计算角度
        angle = math.atan2(dy, dx)
        
        # 获取AI当前朝向
        facing_angle = 0 if self.entity.vx >= 0 else math.pi
        
        # 计算角度差
        angle_diff = abs(angle - facing_angle)
        angle_diff = min(angle_diff, 2 * math.pi - angle_diff)
        
        # 检查是否在视锥角度内
        return angle_diff <= self.vision_angle / 2

    def _perform_attack(self):
        """执行攻击"""
        if self.attack_cooldown <= 0:
            if self.attack_type == 'melee':
                self._perform_melee_attack()
            else:
                self._perform_ranged_attack()
        
        # 设置攻击冷却
        self.attack_cooldown = self.attack_cooldown_time

    def _perform_melee_attack(self):
        """执行近战扑咬攻击"""
        if not self.is_lunging:
            # 开始扑击
            self.is_lunging = True
            self.lunge_timer = self.lunge_duration
            
            # 计算扑击方向
            player = self._get_player()
            if player:
                dx = player.x - self.entity.x
                dy = player.y - self.entity.y
                dist = math.sqrt(dx * dx + dy * dy)
                
                if dist > 0:
                    # 设置扑击速度
                    self.entity.vx = (dx / dist) * self.lunge_speed
                    self.entity.vy = min(-200, (dy / dist) * self.lunge_speed * 0.5)
                    
    def _perform_ranged_attack(self):
        """执行远程射击攻击"""
        player = self._get_player()
        if not player or not hasattr(self.game_map.game, 'spawn_projectile'):
            return
        
        # 检查是否达到最大射击次数
        if self.shots_fired >= self.max_shots:
            self.attack_cooldown = self.burst_cooldown  # 使用更长的冷却时间
            self.shots_fired = 0
            return
        
        # 计算射击方向
        dx = player.x - self.entity.x
        dy = player.y - self.entity.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 0:
            # 添加一些随机偏移，使射击不么精确
            accuracy = 0.1  # 精确度（越小越准）
            dx = dx / dist + random.uniform(-accuracy, accuracy)
            dy = dy / dist + random.uniform(-accuracy, accuracy)
            
            # 生成投射物
            projectile_x = self.entity.x + self.entity.width/2
            projectile_y = self.entity.y + self.entity.height/2
            
            self.game_map.game.spawn_projectile(
                projectile_x, projectile_y,
                dx * self.projectile_speed,
                dy * self.projectile_speed,
                self.projectile_damage,
                'enemy'
            )
            
            # 增加射击计
            self.shots_fired += 1
            
            # 设置较短的攻击冷却（连发间隔）
            self.attack_cooldown = 0.3

    def _get_attack_rect(self):
        """获取攻击范围矩形"""
        # 根据AI朝向确定攻击范围
        direction = 1 if self.entity.vx >= 0 else -1
        attack_width = 40
        attack_height = self.entity.height  # 使用AI的高度作攻击高度
        
        # 攻击判定框略微偏移，使其更合理
        offset_x = self.entity.width * 0.5 if direction > 0 else -attack_width
        offset_y = 0  # 可以根据需要调整垂直偏移
        
        return pygame.Rect(
            self.entity.x + offset_x,
            self.entity.y + offset_y,
            attack_width,
            attack_height
        )

    def _check_attack_hit(self, attack_rect, target):
        """检查攻击是否命中"""
        # 创建一个稍小的目标碰撞箱，使判定更精确
        target_rect = pygame.Rect(
            target.x + target.width * 0.2,  # 缩小碰撞箱
            target.y + target.height * 0.1,
            target.width * 0.6,
            target.height * 0.8
        )
        return attack_rect.colliderect(target_rect)

    def _should_retreat(self, perception_info):
        """判断是否应该撤退"""
        # 根据生命值和谨慎性判断
        health_ratio = getattr(self.entity, 'health', 100) / 100
        return (health_ratio < 0.3 or  # 生命值于30%
                (health_ratio < 0.5 and  # 生命值低于50%且
                 self.behavior_weights['caution'] > 0.7))  # 谨慎性高

    def set_patrol_points(self, points):
        """设置巡逻点
        Args:
            points: 巡逻点列表，每个点为(x, y)元组
        """
        self.patrol_points = points
        self.current_patrol_index = 0
        
        # 确保个巡逻点都在地面上
        for i, (x, y) in enumerate(self.patrol_points):
            test_y = y
            while test_y < self.game_map.level_height:
                if self.game_map.is_solid(x, test_y + self.entity.height):
                    self.patrol_points[i] = (x, test_y)
                    break
                test_y += self.game_map.tile_size/2

    def _update_idle(self, dt, perception_info):
        """更新空闲状态"""
        # 随机移动
        if self.state_timer > random.uniform(2.0, 4.0):
            self.state_timer = 0
            # 30%概率改变方向
            if random.random() < 0.3:
                self.target_vx = random.choice([-1, 0, 1]) * self.move_speed * 0.3
            
        # 检查前方是否有障碍物
        if self._check_obstacle_ahead():
            self.target_vx *= -1
            
        # 降低警戒等级
        self.alert_level = max(0, self.alert_level - 5 * dt)

    def _update_patrol(self, dt, perception_info):
        """更新巡逻状态"""
        if not hasattr(self, 'patrol_points') or not self.patrol_points:
            self._prepare_patrol()
            return
        
        current_point = self.patrol_points[self.current_patrol_index]
        dx = current_point[0] - self.entity.x
        
        # 添加死区，防止在目标点附近抖动
        if abs(dx) > 20:  # 增加目标点判定距离
            self.target_vx = math.copysign(self.move_speed * 0.6, dx)
        else:
            # 到达当前巡逻点
            self.target_vx = 0
            if self.state_timer >= 0.5:  # 确保在每个点停留一段时间
                self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
                self.state_timer = 0
        
        # 检查前方是否有障碍物
        if self._check_obstacle_ahead():
            if self.entity.on_ground:
                self._try_jump()
            # 如果连续多次检测到障碍物，考虑切换到下一个巡逻点
            if not hasattr(self, 'obstacle_counter'):
                self.obstacle_counter = 0
            self.obstacle_counter += 1
            if self.obstacle_counter > 60:  # 增加阈值，减少切换频率
                self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
                self.obstacle_counter = 0
                self.state_timer = 0
        else:
            self.obstacle_counter = 0
        
        # 缓慢降低警戒等级
        self.alert_level = max(0, self.alert_level - 5 * dt)
        
        # 如果感知到玩家，增加警戒等级
        if perception_info['can_sense_player']:
            self.alert_level = min(100, self.alert_level + 15 * dt)
        
        # 如果不在战斗中，警戒等级下降更快
        if not self.in_combat:
            self.alert_level = max(0, self.alert_level - 10 * dt)

    def _prepare_patrol(self):
        """准备进入巡逻状态"""
        # 生成新的巡逻点
        if not hasattr(self, 'patrol_points') or not self.patrol_points:
            self.patrol_points = self._generate_patrol_points()
        
        # 确保有巡逻点
        if not self.patrol_points:
            base_x = self.entity.x
            self.patrol_points = [
                (base_x - 200, self.entity.y),
                (base_x, self.entity.y),
                (base_x + 200, self.entity.y)
            ]
        
        self.current_patrol_index = 0
        self.obstacle_counter = 0  # 添加障碍计数器
        self.alert_level = max(0, self.alert_level - 30)  # 降低警戒等级

    def _generate_patrol_points(self):
        """生成巡逻路径点"""
        patrol_points = []
        base_x = self.entity.x
        base_y = self.entity.y
        
        # 定义搜索范围
        search_range = [-300, -200, -100, 100, 200, 300]  # 增加搜索范围和密度
        random.shuffle(search_range)  # 随机打乱搜索顺序
        
        for offset in search_range:
            x = base_x + offset
            y = base_y
            
            # 确保点在地图范围内
            if 0 <= x < self.game_map.level_width:
                # 向下寻找可站立的地面
                found_ground = False
                test_y = y
                while test_y < self.game_map.level_height - self.entity.height:
                    # 检查脚下是否是地面
                    foot_pos = test_y + self.entity.height + 1
                    if self.game_map.is_solid(x, foot_pos):
                        # 检查头顶是否有空间
                        head_space = True
                        for check_y in range(int(test_y), int(test_y + self.entity.height)):
                            if self.game_map.is_solid(x, check_y):
                                head_space = False
                                break
                        
                        if head_space:
                            patrol_points.append((x, test_y))
                            found_ground = True
                            break
                    
                    test_y += self.game_map.tile_size/2
                
                if not found_ground:
                    # 如果向下没找到，尝试向找
                    test_y = y
                    while test_y > 0:
                        foot_pos = test_y + self.entity.height + 1
                        if self.game_map.is_solid(x, foot_pos):
                            # 检查头顶否有空间
                            head_space = True
                            for check_y in range(int(test_y), int(test_y + self.entity.height)):
                                if self.game_map.is_solid(x, check_y):
                                    head_space = False
                                    break
                            
                            if head_space:
                                patrol_points.append((x, test_y))
                                break
                        
                        test_y -= self.game_map.tile_size/2
        
        # 如果没有找到任何有效的巡逻点，至少保留当前位置
        if not patrol_points:
            patrol_points.append((base_x, base_y))
        
        # 检查巡逻点之间是否有可通行的路径
        valid_points = [patrol_points[0]]  # 从第一个点开始
        for point in patrol_points[1:]:
            # 使用A*检查是否可以到达该点
            path = self.path_finding.find_path(valid_points[-1], point)
            if path:  # 如果找到路径，则该点有效
                valid_points.append(point)
        
        return valid_points

    def _is_valid_position(self, x, y):
        """检查位置是否有效（可以站立）"""
        # 检查是否在地图范围内
        if not (0 <= x < self.game_map.level_width and 0 <= y < self.game_map.level_height):
            return False
        
        # 检查脚下是否有地面
        foot_pos = y + self.entity.height + 1
        if not self.game_map.is_solid(x, foot_pos):
            return False
        
        # 检查身体位置是否有障碍物
        for check_y in range(int(y), int(y + self.entity.height)):
            if self.game_map.is_solid(x, check_y):
                return False
            
        return True

    def _update_search(self, dt, perception_info):
        """更新搜索状态"""
        self.search_timer += dt
        
        if not self.last_known_target_pos:
            self.state = AIState.PATROL
            return
            
        # 更新路径到最后已知位置
        if not self.path or self.path_progress >= len(self.path):
            self.path = self.path_finding.find_path(
                (self.entity.x, self.entity.y),
                self.last_known_target_pos
            )
            self.path_progress = 0
            
        # 按路径移动
        self._follow_path()
        
        # 搜索超时，返回巡逻
        if self.search_timer > 5.0:
            self.last_known_target_pos = None
            self.state = AIState.PATROL

    def _follow_path(self):
        """跟随路径点"""
        if not self.path or self.path_progress >= len(self.path):
            return
        
        target_point = self.path[min(self.path_progress, len(self.path)-1)]
        dx = target_point[0] - self.entity.x
        dy = target_point[1] - self.entity.y
        
        # 水平移动
        if abs(dx) > 10:
            self.target_vx = math.copysign(self.move_speed, dx)
        else:
            self.target_vx = 0
            self.path_progress += 1
            
        # 处理跳跃
        if self._should_jump(target_point):
            self._try_jump()

    def _has_line_of_sight(self, start, end):
        """检查两点间是否有视线"""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return True
            
        steps = int(distance / 10)  # 每10像素检查一次
        if steps == 0:
            steps = 1
            
        dx /= steps
        dy /= steps
        
        for i in range(steps):
            check_x = start[0] + dx * i
            check_y = start[1] + dy * i
            
            # 检点是否在固体方块
            if self.game_map.is_solid(check_x, check_y):
                return False
                
        return True

    def _get_player(self):
        """获取玩家引用"""
        if hasattr(self.game_map, 'game') and hasattr(self.game_map.game, 'player'):
            return self.game_map.game.player
        return None

    def _update_attack(self, dt, perception_info):
        """更新攻击状态"""
        if not perception_info['can_see_player']:
            # 玩家躲避攻击，触发嘲讽
            if random.random() < 0.25:  # 25%的概率触发叫骂
                self._try_taunt('mock_player')
            self.state = AIState.CHASE
            return
        
        player_pos = perception_info['player_pos']
        dx = player_pos[0] - self.entity.x
        dist = perception_info['distance']
        
        # 根据攻击类型采取不同的行为
        if self.attack_type == 'melee':
            # 近战攻击行为
            if dist <= self.attack_range:
                # 面向玩家
                self.target_vx = math.copysign(self.move_speed * 0.3, dx)
                
                # 执行攻击
                if self.attack_cooldown <= 0 and not self.is_lunging:
                    self._perform_attack()
            else:
                # 如果超出攻击范围，切换回追击状态
                self.state = AIState.CHASE
        else:
            # 远程攻击行为
            optimal_range = self.attack_range * 0.7
            
            if dist < optimal_range:
                # 太近了，后退
                self.target_vx = -math.copysign(self.move_speed * 0.5, dx)
            elif dist > self.attack_range:
                # 太远了，切换回追击状态
                self.state = AIState.CHASE
            else:
                # 保持距离，执行攻击
                self.target_vx = 0
                if self.attack_cooldown <= 0:
                    self._perform_attack()

    def _update_retreat(self, dt, perception_info):
        """更新撤退状态"""
        if perception_info['can_see_player']:
            # 远离玩家
            dx = perception_info['player_pos'][0] - self.entity.x
            self.target_vx = -math.copysign(self.move_speed * 1.2, dx)
            
            # 如果有机会，尝试跳跃逃离
            if self._check_obstacle_ahead() or random.random() < 0.1:
                self._try_jump()
        else:
            # 继续朝当前方向移动一段距离
            if abs(self.target_vx) < self.move_speed:
                self.target_vx = -self.move_speed if random.random() < 0.5 else self.move_speed

    def _update_search(self, dt, perception_info):
        """更新搜索状态"""
        self.search_timer += dt
        
        if not self.last_known_target_pos:
            self.state = AIState.PATROL
            return
            
        # 更新路径到最后已知位置
        if not self.path or self.path_progress >= len(self.path):
            self.path = self.path_finding.find_path(
                (self.entity.x, self.entity.y),
                self.last_known_target_pos
            )
            self.path_progress = 0
            
        # 按路径移动
        self._follow_path()
        
        # 搜索超时，返回巡逻
        if self.search_timer > 5.0:
            self.last_known_target_pos = None
            self.state = AIState.PATROL

    def _update_alert(self, dt, perception_info):
        """更新警戒状态"""
        current_time = time.time()
        
        if perception_info['can_sense_player']:
            if perception_info.get('player_pos'):
                dx = perception_info['player_pos'][0] - self.entity.x
                dist = perception_info['distance']
                
                # 检测玩家是否在观望
                if dist > self.detection_range * 0.6:
                    self.player_avoid_timer += dt
                    if self.player_avoid_timer > self.avoid_threshold:
                        # 玩家在远处观望，发出挑战
                        if random.random() < 0.2 and current_time - self.last_player_interaction > 4.0:
                            self._try_taunt('challenge')
                            self.last_player_interaction = current_time
                            self.player_avoid_timer = 0
                else:
                    self.player_avoid_timer = 0
                
                # 更快的移动速度
                self.target_vx = math.copysign(self.move_speed * 0.5, dx)
                
                # 更积极的跳跃
                if random.random() < 0.05:
                    self._try_jump()
                    
                # 快速增加警戒等级
                self.alert_level = min(100, self.alert_level + 30 * dt)
        else:
            # 快速降低警戒等级
            self.alert_level = max(0, self.alert_level - 35 * dt)
            self.player_avoid_timer = 0  # 重置避战计时器
        
        # 如果在战斗中，保持较高的警戒等级
        if self.in_combat:
            self.alert_level = max(self.alert_level, 50)

    def _prepare_patrol(self):
        """准备进入巡逻状态"""
        if not hasattr(self, 'patrol_points') or not self.patrol_points:
            # 生新的巡逻点
            self.patrol_points = self._generate_patrol_points()
        self.current_patrol_index = 0
        self.state = AIState.PATROL

    def _update_movement(self, dt):
        """平滑移动更新"""
        # 更新跳跃冷却
        if hasattr(self, 'jump_cooldown'):
            self.jump_cooldown = max(0, self.jump_cooldown - dt)
        
        # 添加转向延迟
        if not hasattr(self, 'direction_change_timer'):
            self.direction_change_timer = 0
            self.last_direction = 1 if self.target_vx >= 0 else -1
        
        current_direction = 1 if self.target_vx >= 0 else -1
        
        # 检查是否需要改变方向
        if current_direction != self.last_direction:
            self.direction_change_timer += dt
            # 只有当方向改变计时器超过阈值时才真正改变方向
            if self.direction_change_timer >= 0.3:  # 300ms的转向延迟
                self.last_direction = current_direction
                self.direction_change_timer = 0
            else:
                # 在转向延迟期间保持原来的方向
                self.target_vx = self.move_speed * self.last_direction
        else:
            self.direction_change_timer = 0
        
        # 计算加速度，添加缓冲区
        if abs(self.entity.vx) < abs(self.target_vx) - 10:  # 添加速度缓冲区
            # 加速
            acceleration = self.acceleration * (1 if self.target_vx > 0 else -1)
            self.entity.vx += acceleration * dt
        elif abs(self.entity.vx) > abs(self.target_vx) + 10:  # 添加速度缓冲区
            # 减速
            deceleration = self.deceleration * (-1 if self.entity.vx > 0 else 1)
            self.entity.vx += deceleration * dt
        else:
            # 在缓冲区内保持当前速度
            self.entity.vx = self.target_vx
        
        # 确保实体不会卡在墙里
        if self._check_wall_collision():
            self.entity.vx = 0
            self.target_vx = 0
            self.direction_change_timer = 0  # 重置方向改变计时器

    def _check_wall_collision(self):
        """检查是否撞墙"""
        # 检查方是否有墙
        direction = 1 if self.entity.vx > 0 else -1
        check_points = [
            (self.entity.x + direction * self.entity.width, self.entity.y),
            (self.entity.x + direction * self.entity.width, self.entity.y + self.entity.height/2),
            (self.entity.x + direction * self.entity.width, self.entity.y + self.entity.height)
        ]
        
        return any(self.game_map.is_solid(x, y) for x, y in check_points)

    def _check_obstacle_ahead(self):
        """检前方是否有障碍物"""
        # 确定检查方向
        direction = 1 if self.target_vx > 0 else -1
        check_x = self.entity.x + direction * (self.entity.width + 10)
        
        # 检查多个高度点
        check_points = [
            (check_x, self.entity.y),  # 头部
            (check_x, self.entity.y + self.entity.height * 0.5),  # 中间
            (check_x, self.entity.y + self.entity.height - 1)  # 底部
        ]
        
        # 检查地面是否中断
        ground_check = (
            check_x,
            self.entity.y + self.entity.height + 5
        )
        
        # 如果前方有墙或者地面中断，都视为障碍
        return any(self.game_map.is_solid(px, py) for px, py in check_points) or \
               not self.game_map.is_solid(*ground_check)

    def _try_jump(self):
        """尝试跳"""
        if not self.entity.on_ground:
            return False
        
        # 检查头顶空间
        head_space = not any(self.game_map.is_solid(
            self.entity.x + x,
            self.entity.y - self.min_jump_height
        ) for x in [0, self.entity.width])
        
        if not head_space:
            return False
        
        # 执行跳跃
        self.entity.vy = self.jump_force
        if hasattr(self, 'jump_cooldown_time'):
            self.jump_cooldown = self.jump_cooldown_time
        return True

    def _should_jump(self, target_point):
        """判断是否需要跳跃到目标点"""
        if not self.entity.on_ground or (hasattr(self, 'jump_cooldown') and self.jump_cooldown > 0):
            return False
        
        # 检查是否有障碍物
        has_obstacle = self._check_obstacle_ahead()
        
        # 计算高度差
        dy = target_point[1] - (self.entity.y + self.entity.height)
        
        # 检查头顶空间
        head_space = not any(self.game_map.is_solid(
            self.entity.x + x, 
            self.entity.y - self.min_jump_height
        ) for x in [0, self.entity.width])
        
        # 如果目标点在上方且有足够间，或者前有障碍物且有足够空间
        if head_space and (dy < -self.min_jump_height or has_obstacle):
            # 额外检查：确保不会跳到危险位置
            future_x = self.entity.x + self.target_vx * 0.5  # 预测位置
            if not self.game_map.is_solid(future_x, self.entity.y + self.entity.height + 32):
                return True
        
        return False

    def _on_state_change(self, new_state):
        """状态改变时的处理"""
        old_state = self.state
        self.state_timer = 0
        
        # 根据状态转换类型执行特定行为
        if old_state == AIState.IDLE and new_state == AIState.ALERT:
            # 从空闲到警戒，快速提高警戒等级
            self.alert_level = min(100, self.alert_level + 40)
            
        elif old_state == AIState.CHASE and new_state == AIState.ATTACK:
            # 追击到攻击，重置攻击冷却
            self.attack_cooldown = 0
            
        elif old_state == AIState.ATTACK and new_state == AIState.CHASE:
            # 攻击到追击，给予短暂冷却
            self.attack_cooldown = 0.5
            
        elif new_state == AIState.SEARCH:
            # 进入搜索状态，初始化搜索参数
            self.search_timer = 0
            if not self.last_known_target_pos:
                self.last_known_target_pos = None
                
        elif new_state == AIState.PATROL:
            # 进入巡逻状态，重置巡逻点
            if hasattr(self, 'patrol_points') and self.patrol_points:
                self.current_patrol_index = 0
                
        # 记录状态改变时间
        self.last_state_change = time.time()
        
        # 根据状态转换触发合适的叫骂
        if old_state == AIState.IDLE and new_state == AIState.ALERT:
            self._try_taunt('alert')
        elif old_state == AIState.ALERT and new_state == AIState.CHASE:
            self._try_taunt('chase')
        elif new_state == AIState.ATTACK:
            self._try_taunt('attack')
        elif new_state == AIState.RETREAT:
            self._try_taunt('retreat')
        elif new_state == AIState.SEARCH:
            self._try_taunt('search')

    def render(self, screen, camera_offset=(0, 0)):
        """渲染AI相的视觉效果"""
        # 渲染路径
        if self.path and len(self.path) > 1:
            # 创建路径表面
            path_surface = pygame.Surface(
                (screen.get_width(), screen.get_height()),
                pygame.SRCALPHA
            )
            
            # 绘制路径线
            for i in range(len(self.path) - 1):
                pygame.draw.line(
                    path_surface,
                    (0, 255, 0, 40),  # 半透明绿色
                    (int(self.path[i][0] - camera_offset[0]),
                     int(self.path[i][1] - camera_offset[1])),
                    (int(self.path[i+1][0] - camera_offset[0]),
                     int(self.path[i+1][1] - camera_offset[1])),
                    2  # 线宽
                )
                
                # 在路径点绘制小圆点
                pygame.draw.circle(
                    path_surface,
                    (0, 255, 0, 60),  # 稍微不透明的绿色
                    (int(self.path[i][0] - camera_offset[0]),
                     int(self.path[i][1] - camera_offset[1])),
                    3  # 圆点半径
                )
            
            # 绘制当前目标点（大一点的圆点）
            if self.path_progress < len(self.path):
                target_point = self.path[self.path_progress]
                pygame.draw.circle(
                    path_surface,
                    (255, 255, 0, 80),  # 半透明黄色
                    (int(target_point[0] - camera_offset[0]),
                     int(target_point[1] - camera_offset[1])),
                    5  # 目标点半径
                )
            
            # 将路径表面绘制到屏幕上
            screen.blit(path_surface, (0, 0))
        
        # 渲染感知范围（仅在警戒或搜索状态下）
        if self.state in [AIState.ALERT, AIState.SEARCH, AIState.CHASE]:
            # 创建一个大的透明表面用于渲染感知范围
            vision_surface = pygame.Surface(
                (self.detection_range * 3, self.detection_range * 3), 
                pygame.SRCALPHA
            )
            
            # 渲染听觉范围（外圈）
            pygame.draw.circle(
                vision_surface,
                (100, 100, 255, 15),  # 更透明的蓝色
                (vision_surface.get_width()//2, vision_surface.get_height()//2),
                int(self.detection_range * 1.5)
            )
            
            # 渲染视觉范围（内圈）
            pygame.draw.circle(
                vision_surface,
                (255, 255, 100, 10),  # 更透明的黄色
                (vision_surface.get_width()//2, vision_surface.get_height()//2),
                self.detection_range
            )
            
            # 如果在战斗状态，添加红色警戒光环
            if self.in_combat:
                pygame.draw.circle(
                    vision_surface,
                    (255, 0, 0, 8),  # 非常透明的红色
                    (vision_surface.get_width()//2, vision_surface.get_height()//2),
                    int(self.detection_range * 1.2),
                    2
                )
            
            # 将感知范围绘制到屏幕上
            screen.blit(
                vision_surface,
                (self.entity.x - camera_offset[0] + self.entity.width/2 - vision_surface.get_width()//2,
                 self.entity.y - camera_offset[1] + self.entity.height/2 - vision_surface.get_height()//2)
            )
        
        # 渲染叫骂文本
        if self.current_taunt and self.taunt_timer > 0:
            # 计算透明度
            alpha = int(255 * (self.taunt_timer / self.taunt_duration))
            
            # 计算浮动效果
            self.taunt_offset_y = math.sin(pygame.time.get_ticks() * 0.005) * 5
            
            try:
                # 创建文本表面
                text_surface = self.font.render(self.current_taunt, True, (255, 255, 255))
                text_rect = text_surface.get_rect()
                
                # 创建带透明度的背景
                padding = 10
                background_surface = pygame.Surface(
                    (text_rect.width + padding * 2, text_rect.height + padding * 2),
                    pygame.SRCALPHA
                )
                
                # 根据AI状态选择背景颜色
                if self.state == AIState.ALERT:
                    bg_color = (200, 150, 0, int(alpha * 0.7))  # 警戒状态：橙色
                elif self.state == AIState.CHASE:
                    bg_color = (200, 50, 50, int(alpha * 0.7))  # 击态：红色
                elif self.state == AIState.ATTACK:
                    bg_color = (200, 0, 0, int(alpha * 0.7))    # 攻击状态：深红色
                else:
                    bg_color = (0, 0, 0, int(alpha * 0.7))      # 其他状态：黑色
                
                # 绘制圆��矩形背景
                pygame.draw.rect(
                    background_surface,
                    bg_color,
                    (0, 0, text_rect.width + padding * 2, text_rect.height + padding * 2),
                    border_radius=10
                )
                
                # 计算显示位置
                text_x = self.entity.x - camera_offset[0] - text_rect.width / 2 + self.entity.width / 2
                text_y = self.entity.y - camera_offset[1] - 60 + self.taunt_offset_y
                
                # 绘制背景和文本
                screen.blit(background_surface, (text_x - padding, text_y - padding))
                text_surface.set_alpha(alpha)
                screen.blit(text_surface, (text_x, text_y))
                
            except Exception as e:
                print(f"渲染文本错误: {e}")
        
        # 渲染锁定指示器
        if self.target_locked:
            # 创建锁定标记表面
            lock_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
            
            # 绘制锁定标记
            pygame.draw.circle(
                lock_surface,
                (255, 0, 0, 100),  # 半透明红色
                (15, 15),
                12
            )
            pygame.draw.circle(
                lock_surface,
                (255, 0, 0, 150),  # 较不透明的红色
                (15, 15),
                12,
                2
            )
            
            # 显示在AI头顶
            screen.blit(
                lock_surface,
                (self.entity.x - camera_offset[0] + self.entity.width/2 - 15,
                 self.entity.y - camera_offset[1] - 40)
            )

    def render_debug(self, screen, camera_offset=(0, 0)):
        """渲染调试信息"""
        if not hasattr(self.game_map, 'game') or not self.game_map.game.debug:
            return
        
        # 渲染听觉范围（最大感知范围）
        alert_range = self.detection_range * 1.5
        pygame.draw.circle(
            screen,
            (100, 100, 255, 40),  # 更透明的蓝色
            (int(self.entity.x - camera_offset[0] + self.entity.width/2),
             int(self.entity.y - camera_offset[1] + self.entity.height/2)),
            int(alert_range),
            1
        )
        
        # 渲染视觉范围（锥形区域）
        vision_points = self._get_vision_cone_points(camera_offset)
        if vision_points:
            # 绘制视觉锥形
            pygame.draw.polygon(
                screen,
                (255, 255, 0, 25),  # 更透明的黄色
                vision_points
            )
            # 绘制视觉锥形边界
            pygame.draw.lines(
                screen,
                (255, 255, 0, 40),  # 更透明的黄色边界
                True,  # 闭合多边形
                vision_points,
                1
            )
        
        # 渲染攻击范围
        attack_color = (255, 0, 0, 30) if self.attack_type == 'melee' else (255, 100, 100, 30)
        pygame.draw.circle(
            screen,
            attack_color,
            (int(self.entity.x - camera_offset[0] + self.entity.width/2),
             int(self.entity.y - camera_offset[1] + self.entity.height/2)),
            int(self.attack_range),
            1
        )
        
        # 渲染路径
        if self.path:
            for i in range(len(self.path) - 1):
                pygame.draw.line(
                    screen,
                    (0, 255, 0, 40),  # 更透明的绿色
                    (int(self.path[i][0] - camera_offset[0]),
                     int(self.path[i][1] - camera_offset[1])),
                    (int(self.path[i+1][0] - camera_offset[0]),
                     int(self.path[i+1][1] - camera_offset[1])),
                    1
                )
                
        # 渲染状态文本
        font = pygame.font.Font(None, 24)
        state_text = font.render(
            f"State: {self.state.value}",
            True,
            (255, 255, 255)
        )
        screen.blit(
            state_text,
            (self.entity.x - camera_offset[0] - 30,
             self.entity.y - camera_offset[1] - 40)
        )
        
        # 渲染生命值条
        health_ratio = getattr(self.entity, 'health', 100) / 100
        health_width = 40
        health_height = 4
        pygame.draw.rect(
            screen,
            (255, 0, 0),
            (self.entity.x - camera_offset[0],
             self.entity.y - camera_offset[1] - 10,
             health_width,
             health_height)
        )
        pygame.draw.rect(
            screen,
            (0, 255, 0),
            (self.entity.x - camera_offset[0],
             self.entity.y - camera_offset[1] - 10,
             health_width * health_ratio,
             health_height)
        )
        
        # 渲染叫骂文本
        if self.current_taunt and self.taunt_timer > 0:
            # 计算透明度
            alpha = int(255 * (self.taunt_timer / self.taunt_duration))
            
            # 计算浮动效果
            self.taunt_offset_y = math.sin(pygame.time.get_ticks() * 0.005) * 5
            
            try:
                # 创建文本表面
                text_surface = self.font.render(self.current_taunt, True, (255, 255, 255))
                text_rect = text_surface.get_rect()
                
                # 创建带透明度的背景
                padding = 10
                background_surface = pygame.Surface(
                    (text_rect.width + padding * 2, text_rect.height + padding * 2),
                    pygame.SRCALPHA
                )
                
                # 根据AI状态选择背景颜色
                if self.state == AIState.ALERT:
                    bg_color = (200, 150, 0, int(alpha * 0.7))  # 警戒状态：橙色
                elif self.state == AIState.CHASE:
                    bg_color = (200, 50, 50, int(alpha * 0.7))  # 追击状态：红色
                elif self.state == AIState.ATTACK:
                    bg_color = (200, 0, 0, int(alpha * 0.7))    # 攻击状态：深红色
                else:
                    bg_color = (0, 0, 0, int(alpha * 0.7))      # 其他状态：黑色
                
                # 绘制圆角矩形背景
                pygame.draw.rect(
                    background_surface,
                    bg_color,
                    (0, 0, text_rect.width + padding * 2, text_rect.height + padding * 2),
                    border_radius=10
                )
                
                # 计算显示位置
                text_x = self.entity.x - camera_offset[0] - text_rect.width / 2 + self.entity.width / 2
                text_y = self.entity.y - camera_offset[1] - 60 + self.taunt_offset_y
                
                # 绘制背景和文本
                screen.blit(background_surface, (text_x - padding, text_y - padding))
                text_surface.set_alpha(alpha)
                screen.blit(text_surface, (text_x, text_y))
                
            except Exception as e:
                print(f"渲染文本错误: {e}")

    def _update_chase(self, dt, perception_info):
        """更新追击状态"""
        # 检查是否完全失去目标
        if not perception_info.get('player_pos') and not perception_info['target_locked']:
            if self.last_known_target_pos:
                self.state = AIState.SEARCH
            else:
                self.state = AIState.PATROL
            return
            
        # 获取目标位置(实际位置或最后已知位置)
        target_pos = perception_info.get('player_pos') or self.last_known_target_pos
        if not target_pos:
            return
            
        dx = target_pos[0] - self.entity.x
        dy = target_pos[1] - self.entity.y
        dist = perception_info['distance']
        
        # 根据是否���定采用不同���追击策略
        if perception_info['target_locked'] or perception_info['can_see_player']:
            # 锁定状态: 更积极的追击
            
            # 调整追击速度基于距离
            if dist > self.attack_range * 2:
                # 远距离快速追击
                speed_factor = 1.2
            elif dist > self.attack_range:
                # 中距离正常追击
                speed_factor = 1.0
            else:
                # 接近时减速
                speed_factor = 0.7
                
            # 设置移动方向和速度
            self.target_vx = math.copysign(self.move_speed * speed_factor, dx)
            
            # 处理垂直移动
            if abs(dy) > self.entity.height * 2:  # 如果垂直距离较大
                if dy < 0 and self.entity.on_ground:  # 目标在上方且在地面上
                    self._try_jump()
                elif dy > 0 and not self.game_map.is_solid(self.entity.x, self.entity.y + self.entity.height + 32):
                    # 目标在下方且下方是空的，可以下落
                    pass  # 自然下落
                    
            # 处理障碍物
            if self._check_obstacle_ahead():
                if self.entity.on_ground:
                    self._try_jump()
                elif not self.entity.on_ground and dy > 0:
                    # 如果在空中且目标在下方，尝试贴墙下落
                    self.target_vx *= -0.5
                    
            # 如果距离很近，准备攻击
            if dist <= self.attack_range * 1.2:
                self.state = AIState.ATTACK
                
        else:
            # 非锁定状态: 更谨慎的追击
            # 使用上一次看到玩家的位置
            if self.last_known_target_pos:
                # 更新路径到最后已知位置
                if not self.path or self.path_update_timer <= 0:
                    self.path = self.path_finding.find_path(
                        (self.entity.x, self.entity.y),
                        self.last_known_target_pos
                    )
                    self.path_update_timer = self.path_update_interval
                    self.path_progress = 0
                else:
                    self.path_update_timer -= dt
                    
                # 跟随路径
                if self.path and self.path_progress < len(self.path):
                    current_target = self.path[self.path_progress]
                    dx_path = current_target[0] - self.entity.x
                    
                    # 移动到路径点
                    if abs(dx_path) > 10:
                        self.target_vx = math.copysign(self.move_speed * 0.8, dx_path)
                    else:
                        self.path_progress += 1
                        
                    # 处理跳跃
                    if self._should_jump(current_target):
                        self._try_jump()
                else:
                    # 如果没有路径或已到达终点，切换到搜索状态
                    self.state = AIState.SEARCH

    def _update_attack(self, dt, perception_info):
        """更新攻击状态"""
        if not perception_info['can_see_player']:
            # 玩家躲避攻击，触发嘲讽
            if random.random() < 0.25:  # 25%的概率触发叫骂
                self._try_taunt('mock_player')
            self.state = AIState.CHASE
            return
        
        player_pos = perception_info['player_pos']
        dx = player_pos[0] - self.entity.x
        dist = perception_info['distance']
        
        # 根据攻击类型采取不同的行为
        if self.attack_type == 'melee':
            # 近战攻击行为
            if dist <= self.attack_range:
                # 面向玩家
                self.target_vx = math.copysign(self.move_speed * 0.3, dx)
                
                # 执行攻击
                if self.attack_cooldown <= 0 and not self.is_lunging:
                    self._perform_attack()
            else:
                # 如果超出攻击范围，切换回追击状态
                self.state = AIState.CHASE
        else:
            # 远程攻击行为
            optimal_range = self.attack_range * 0.7
            
            if dist < optimal_range:
                # 太近了，后退
                self.target_vx = -math.copysign(self.move_speed * 0.5, dx)
            elif dist > self.attack_range:
                # 太远了，切换回追击状态
                self.state = AIState.CHASE
            else:
                # 保持距离，执行攻击
                self.target_vx = 0
                if self.attack_cooldown <= 0:
                    self._perform_attack()

    def _update_stunned(self, dt):
        """更新眩晕状态"""
        # 在眩晕状态下停止移动
        self.target_vx = 0
        
        # 眩晕结束后恢复到警戒状态
        if self.state_timer > 1.0:
            self.state = AIState.ALERT
            self.alert_level = 70

    def _check_vision_cone(self, target_pos):
        """检查目标是否在视野锥内
        Args:
            target_pos: (x, y) 目标位置
        Returns:
            bool: 是否在视野内
        """
        # 计算到目标的向量
        dx = target_pos[0] - self.entity.x
        dy = target_pos[1] - self.entity.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # 检距离
        if distance > self.vision_distance:
            return False
        
        # 计算朝向角度（假设右为0度）
        facing_angle = 0 if self.entity.vx >= 0 else math.pi
        
        # 计算到目标的角度
        target_angle = math.atan2(dy, dx)
        
        # 计算角度差
        angle_diff = abs(target_angle - facing_angle)
        angle_diff = min(angle_diff, 2 * math.pi - angle_diff)
        
        # 检查是否在视野角度内
        return angle_diff <= self.vision_angle / 2

    def _check_state_timeout(self, dt):
        """检查状态是否超时"""
        if self.state in self.state_durations:
            max_duration = self.state_durations[self.state]
            if self.state_timer >= max_duration:
                # 状态超时，切换到默认状态
                if self.state == AIState.CHASE:
                    self.state = AIState.SEARCH
                else:
                    self.state = AIState.PATROL
                self.state_timer = 0

    def _try_taunt(self, taunt_type):
        """尝试进行叫骂"""
        if self.taunt_cooldown <= 0 and taunt_type in self.taunts:
            # 根据状态和行为权重选择叫骂概率
            chance = 1.0
            if taunt_type == 'alert':
                chance = 0.7
            elif taunt_type == 'chase':
                chance = self.behavior_weights['aggression']
            elif taunt_type == 'retreat':
                chance = self.behavior_weights['caution']
            
            if random.random() < chance:
                # 随机选择一句叫骂
                self.current_taunt = random.choice(self.taunts[taunt_type])
                self.taunt_timer = self.taunt_duration
                self.taunt_cooldown = self.taunt_cooldown_time

    def take_damage(self, damage):
        """受到伤害时的处理"""
        # 触发受伤叫骂
        self._try_taunt('hit')
        
        # 重置战斗状态
        self.in_combat = True
        self.last_combat_time = time.time()
        self.combat_timer = 0
        
        # 提高警戒等级
        self.alert_level = min(100, self.alert_level + 30)

    def _get_vision_cone_points(self, camera_offset):
        """获取视觉锥形的顶点
        Args:
            camera_offset: (camera_x, camera_y) 相机偏移
        Returns:
            list: 视觉锥形的顶点列表
        """
        # 计算视觉锥形的起点（实体中心）
        center_x = self.entity.x + self.entity.width/2 - camera_offset[0]
        center_y = self.entity.y + self.entity.height/2 - camera_offset[1]
        
        # 根据实体朝向确定基准角度
        base_angle = 0 if self.entity.vx >= 0 else math.pi
        
        # 计算视觉锥形的两个边界角度
        half_angle = self.vision_angle / 2
        angle1 = base_angle - half_angle
        angle2 = base_angle + half_angle
        
        # 计算视觉锥形的顶点
        points = [(center_x, center_y)]  # 起点（实体中心）
        
        # 添加锥形边缘的点
        num_points = 8  # 边缘的点数，增加可以使锥形更平滑
        for i in range(num_points + 1):
            angle = angle1 + (angle2 - angle1) * i / num_points
            x = center_x + math.cos(angle) * self.vision_distance
            y = center_y + math.sin(angle) * self.vision_distance
            points.append((x, y))
        
        return points

    def _update_combat_state(self, dt, perception_info):
        """更新战斗状态"""
        current_time = time.time()
        
        # 检查是否应该进入战斗状态
        if perception_info['can_see_player'] or perception_info['can_sense_player']:
            if not self.in_combat:
                # 进入战斗状态
                self.in_combat = True
                self._try_taunt('combat_start')
            self.last_combat_time = current_time
            self.combat_timer = 0
        else:
            # 更新脱战计时器
            self.combat_timer += dt
            
            # 检查是否应该脱战
            if self.in_combat and self.combat_timer >= self.combat_timeout:
                self._handle_combat_end()

    def _handle_combat_end(self):
        """处理脱战"""
        self.in_combat = False
        self.combat_timer = 0
        self.alert_level = max(0, self.alert_level - 50)  # 大幅降低警戒等级
        
        # 触发脱战叫骂
        self._try_taunt('combat_end')
        
        # 切换到巡逻状态
        self._prepare_patrol()
        self.state = AIState.PATROL

    def _render_debug_info(self, screen, camera_offset):
        """渲染调试信息"""
        # ... 现有的渲染代码 ...
        
        # 添加更多状态信息显示
        debug_info = [
            f"State: {self.state.value}",
            f"Alert: {int(self.alert_level)}",
            f"Combat: {'Yes' if self.in_combat else 'No'}",
            f"Health: {int(getattr(self.entity, 'health', 100))}",
        ]
        
        y_offset = 40
        for info in debug_info:
            text = self.font.render(info, True, (255, 255, 255))
            screen.blit(
                text,
                (self.entity.x - camera_offset[0] - 30,
                 self.entity.y - camera_offset[1] - y_offset)
            )
            y_offset += 20

    def _evaluate_behavior_tree(self, perception_info):
        """评估行为树"""
        class BehaviorNode:
            def evaluate(self, ai, info):
                return False
        
        class HealthCheck(BehaviorNode):
            def evaluate(self, ai, info):
                health_ratio = getattr(ai.entity, 'health', 100) / 100
                return health_ratio < ai.thresholds['health_retreat']
        
        class RangeCheck(BehaviorNode):
            def evaluate(self, ai, info):
                return info['distance'] <= ai.attack_range
        
        # 定义行为节点
        behavior_tree = [
            (HealthCheck(), AIState.RETREAT),
            (RangeCheck(), AIState.ATTACK),
            (lambda: True, AIState.CHASE)  # 默认行为
        ]
        
        # 评估行为树
        for node, state in behavior_tree:
            if node.evaluate(self, perception_info):
                return state
                
        return self.state  # 保持当前状态

    def _smooth_path(self, path):
        """平滑路径，减少锯齿状移动"""
        if len(path) <= 2:
            return path
            
        smoothed = [path[0]]
        current = 0
        
        while current < len(path) - 1:
            # 尝试找到可以直接到达的最远点
            for i in range(len(path) - 1, current, -1):
                if self._has_line_of_sight(path[current], path[i]):
                    smoothed.append(path[i])
                    current = i
                    break
            else:
                current += 1
                smoothed.append(path[current])
        
        return smoothed

    def _update_facing_direction(self, perception_info):
        """更新AI的朝向,使其注视目标"""
        if perception_info['can_see_player'] or perception_info['target_locked']:
            # 获取目标位置
            target_pos = perception_info.get('player_pos') or self.last_known_target_pos
            if target_pos:
                # 计算到目标的向量
                dx = target_pos[0] - self.entity.x
                # 根据目标位置更新朝向,而不是根据移动方向
                self.entity.facing_right = dx > 0
                return True
        return False

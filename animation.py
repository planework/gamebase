import pygame
import os

class Animation:
    def __init__(self, name, frames, frame_duration=100, loop=True):
        """
        初始化动画
        frames: 动画帧列表
        """
        self.name = name
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
        
        self.current_frame = 0
        self.last_update = 0
        self.finished = False
    
    def update(self, current_time):
        if self.finished and not self.loop:
            return
            
        if current_time - self.last_update > self.frame_duration:
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True
            self.last_update = current_time
    
    def get_current_frame(self):
        return self.frames[self.current_frame]
    
    def reset(self):
        self.current_frame = 0
        self.finished = False

class AnimationManager:
    def __init__(self, debug=False):
        self.animations = {}
        self.current_animation = None
        self.scale = (64, 128)
        self.debug = debug
    
    def load_animation(self, name, sprite_sheet_path, row, columns, width, height,  
                      frame_duration=100, loop=True, colorkey=None):
        """
        加载动画
        name: 动画名称
        sprite_sheet_path: 精灵表路径
        row: 要加载的行号
        columns: 列数
        width: 每帧宽度
        height: 每帧高度
        """
        try:
            # 加载精灵表
            sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
            if self.debug:
                print(f"\nLoading animation: {name}")
                print(f"Sprite sheet size: {sprite_sheet.get_size()}")
            
            if colorkey is not None:
                sprite_sheet.set_colorkey(colorkey)
            
            frames = []
            
            # 从指定行加载帧
            for col in range(columns):
                frame = pygame.Surface((width, height), pygame.SRCALPHA)
                src_rect = (col * width, row * height, width, height)
                frame.blit(sprite_sheet, (0, 0), src_rect)
                
                if colorkey is not None:
                    frame.set_colorkey(colorkey)
                
                # 缩放到指定大小
                if (width, height) != self.scale:
                    frame = pygame.transform.scale(frame, self.scale)
                
                frames.append(frame)
                if self.debug:
                    print(f"Frame loaded: {name}, col:{col}, row:{row}, "
                          f"size: {frame.get_size()}")
            
            # 创建动画对象
            self.animations[name] = Animation(name, frames, frame_duration, loop)
            
            # 如果是第一个加载的动画，设为当前动画
            if not self.current_animation:
                self.play(name)
                
            return True
            
        except Exception as e:
            print(f"Error loading animation {name}: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    
    def play(self, animation_name, force_reset=False):
        """
        播放指定动画
        animation_name: 动画名称
        force_reset: 是否强制重置动画状态
        """
        if animation_name not in self.animations:
            print(f"Warning: Animation '{animation_name}' not found!")
            print(f"Available animations: {list(self.animations.keys())}")
            return False
        
        # 如果是新动画或强制重置
        if self.current_animation != self.animations[animation_name] or force_reset:
            self.current_animation = self.animations[animation_name]
            self.current_animation.reset()
        return True
    
    def update(self, current_time):
        """更新当前动画"""
        if self.current_animation:
            self.current_animation.update(current_time)
    
    def get_current_frame(self):
        """获取当前帧"""
        if self.current_animation:
            return self.current_animation.get_current_frame()
        return None
    
    def set_scale(self, width, height):
        """设置动画帧的缩放尺寸"""
        self.scale = (width, height)
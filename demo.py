import pygame
import sys
import random


class Entity(pygame.sprite.Sprite):
    def __init__(self, position, type, image):
        super().__init__()
        self.type = type
        self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect(topleft=position)
        self.mask = pygame.mask.from_surface(self.image)

    def on_collision(self, other):
        """Handle collision with another game entity."""
        pass


class Ground(Entity):
    def __init__(self, position, size, image_path):
        super().__init__(position, "ground", image_path)
        self.rect.size = size
        self.image = pygame.transform.scale(self.image, size)

    def on_collision(self, other):
        """Handle collision with another game entity."""
        print(f"{self.type} collided with {other.type}!")

    def draw(self, surface):
        """Draw the ground on the surface."""
        surface.blit(self.image, self.rect)

class Wall(Entity):
    def __init__(self, position, size, image_path):
        super().__init__(position, "wall", image_path)
        self.rect.size = size
        self.image = pygame.transform.scale(self.image, size)

    def on_collision(self, other):
        if isinstance(other, Player):
            # 检查玩家的底部是否在墙壁顶部之上
            if other.rect.bottom > self.rect.top and other.rect.top < self.rect.bottom:
                # 碰撞在顶部，防止玩家掉落
                other.rect.bottom = self.rect.top  # 将玩家位置调整到墙的顶部
                other.velocity_y = 0  # 重置垂直速度
                other.on_ground = True  # 玩家在地面上

            # 碰撞在底部
            if other.rect.top < self.rect.bottom and other.rect.bottom > self.rect.top:
                if other.rect.bottom > self.rect.top:  # 确保底部碰撞
                    other.rect.bottom = self.rect.top  # 将玩家位置调整到墙的顶部
                    other.velocity_y = 0  # 重置垂直速度
                    other.on_ground = True  # 玩家在地面上

            # 处理玩家在墙壁的左右碰撞
            if other.rect.right > self.rect.left and other.rect.left < self.rect.right:
                if other.rect.centerx < self.rect.centerx:
                    # 碰撞在左侧
                    other.rect.left = self.rect.left - other.rect.width  # 将玩家位置调整到墙的左侧
                else:
                    # 碰撞在右侧
                    other.rect.right = self.rect.right  # 将玩家位置调整到墙的右侧

            # 确保在与墙壁的碰撞后重置玩家的垂直速度
            other.velocity_y = 0

class Player(Entity):
    def __init__(self, position):
        super().__init__(position, "player", "player.png")
        self.speed = 5
        self.jump_strength = 10
        self.gravity = 0.5
        self.velocity_y = 0
        self.on_ground = False

    def update(self):
        self.handle_input()
        self.apply_gravity()

    def handle_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.move(-self.speed, 0)
        if keys[pygame.K_RIGHT]:
            self.move(self.speed, 0)
        if keys[pygame.K_UP] and self.on_ground:
            self.jump()
        if keys[pygame.K_DOWN]:
            self.move(0, self.speed)

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy



    def jump(self):
        self.velocity_y = -self.jump_strength
        self.on_ground = False

    def apply_gravity(self):
        if not self.on_ground:
            self.velocity_y += self.gravity
            self.move(0, self.velocity_y)

    def on_collision(self, other):
        print(f"{self.type} collided with {other.type}!")
        if other.type == "wall":
            
            pass

    def draw(self, surface):
        surface.blit(self.image, self.rect)



class Enemy(Entity):
    def __init__(self, position):
        super().__init__(position, "enemy", "enemy.png")
        self.speed = 2
        self.direction = random.choice([-1, 1])
        self.change_direction_timer = 0

    def update(self):
        """Update enemy state (random movement)."""
        self.change_direction_timer += 1
        if self.change_direction_timer > 60:  # Change direction every 60 frames
            self.direction = random.choice([-1, 1])
            self.change_direction_timer = 0

        self.rect.x += self.speed * self.direction

        # Check boundaries and reverse direction if needed
        if (
            self.rect.x <= 0
            or self.rect.x >= pygame.display.get_surface().get_width() - self.rect.width
        ):
            self.direction *= -1

        self.rect.x = max(
            0,
            min(
                self.rect.x, pygame.display.get_surface().get_width() - self.rect.width
            ),
        )
        self.rect.y = max(
            0,
            min(
                self.rect.y,
                pygame.display.get_surface().get_height() - self.rect.height,
            ),
        )

    def on_collision(self, other):
        """Handle collision with another game entity."""
        print(f"{self.type} collided with {other.type}!")
        if isinstance(other, Player):
            other.rect.x += 10

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        self.clock = pygame.time.Clock()

        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()

        # Create player and other entities
        self.player = Player(position=(100, 100))  # Store player as an instance variable
        ground = Ground((0, 0), (1280, 720), "ground.png")
        self.all_sprites.add(ground)

        # Create walls
        wall_top = Ground((0, 0), (1280, 100), "wall.png")
        wall_bottom = Ground((0, 620), (1280, 100), "wall.png")
        wall_left = Ground((0, 100), (100, 520), "wall.png")
        wall_right = Ground((1180, 100), (100, 520), "wall.png")
        
        self.all_sprites.add(wall_top, wall_bottom, wall_left, wall_right)

        # Add player to all sprites
        self.all_sprites.add(self.player)

        # Adding multiple enemies for a better challenge
        # for _ in range(5):
        #     enemy = Enemy(position=(random.randint(0, 1280), random.randint(0, 500)))
        #     self.all_sprites.add(enemy)
        #     self.enemies.add(enemy)

    def run(self):
        while True:
            self.events()
            self.update()
            self.collisions()
            self.draw()
            self.clock.tick(60)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def update(self):
        self.all_sprites.update()

    def collisions(self):
        """Handle collisions for the player."""
        # Check collisions with enemies
        for enemy in self.enemies:
            if pygame.sprite.collide_mask(self.player, enemy):
                self.handle_collision(self.player, enemy)

        # Check collisions with other sprites
        for sprite in self.all_sprites:
            if isinstance(sprite, Player):
                continue  # Skip player in collision checks
            if pygame.sprite.collide_mask(self.player, sprite):
                self.handle_collision(self.player, sprite)

    def handle_collision(self, player, other):
        """Handle collisions based on entity types."""
        if player.type == "player" and other.type == "enemy":
            player.on_collision(other)
            other.on_collision(player)
        elif player.type == "player" and other.type == "ground":
            player.on_collision(other)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.all_sprites.draw(self.screen)
        pygame.display.flip()


# Entry point for the game
if __name__ == "__main__":
    game = Game()
    game.run()

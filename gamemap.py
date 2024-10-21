import pygame
import os
import json

# Constants
TILE_SIZE = 40
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MAP_WIDTH = 1000  # Tile count in width
MAP_HEIGHT = 200  # Tile count in height
BACKGROUND_COLOR = (0, 0, 0)

class Tile:
    def __init__(self, color=None, image=None, width=TILE_SIZE, height=TILE_SIZE, type="center"):
        self.color = color
        self.image = None
        self.width = max(width, TILE_SIZE)
        self.height = max(height, TILE_SIZE)
        self.type = type
        if image:
            self.load_image(image)

    def load_image(self, image):
        try:
            self.image = pygame.image.load(image)
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except pygame.error as e:
            print(f"Error loading image '{image}': {e}")

    def draw(self, surface, x, y):
        if self.image:
            surface.blit(self.image, (x, y))
        elif self.color:
            pygame.draw.rect(surface, self.color, (x, y, self.width, self.height))

class Map:
    def __init__(self, width, height):
        self.width = max(width, 1)
        self.height = max(height, 1)
        self.map_data = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.background_image = None

    def load_background(self, image):
        try:
            self.background_image = pygame.image.load(image)
            self.background_image = pygame.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error as e:
            print(f"Error loading background image '{image}': {e}")

    def clear_map(self):
        """Clear the map data to reset it before loading new tiles."""
        self.map_data = [[None for _ in range(self.width)] for _ in range(self.height)]

    def set_tile(self, x, y, tile):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.map_data[y][x] = tile

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)  # Clear the main surface
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        
        for y in range(self.height):
            for x in range(self.width):
                tile = self.map_data[y][x]
                if tile:
                    tile.draw(surface, x * TILE_SIZE, y * TILE_SIZE)

class MapLoader:
    def __init__(self, map_name):
        self.map = Map(MAP_WIDTH, MAP_HEIGHT)
        self.map_name = map_name
        self.map_config = self.load_map_config(map_name)
        self.load_assets()

    def load_map_config(self, map_name):
        config_path = os.path.join("assets", f"{map_name}_config.json")
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError as e:
            print(f"Map configuration file not found: {e}")
            return {"background": None, "tiles": []}

    def load_assets(self):
        if 'background' in self.map_config and self.map_config['background']:
            background_path = os.path.join("assets", self.map_config['background'])
            self.map.load_background(background_path)

        tile_data = self.map_config.get('tiles', [])
        self.load_tiles(tile_data)

    def load_tiles(self, tile_data):
        for tile_info in tile_data:
            x, y, image, width, height = tile_info.values()
            tile = Tile(image=os.path.join("assets", image), width=width, height=height)
            self.map.set_tile(x, y, tile)

    def change(self, new_map_name):
        """Change the map to a new one by clearing the old map data and reloading assets."""
        self.map.clear_map()  # Clear the old map data
        self.map_name = new_map_name
        self.map_config = self.load_map_config(new_map_name)
        self.load_assets()

    def draw(self, surface):
        self.map.draw(surface)


class Camera:
    def __init__(self, view_width, view_height):
        self.camera = pygame.Rect(0, 0, view_width, view_height)  # Camera rectangle
        self.view_width = view_width  # Width of the view
        self.view_height = view_height  # Height of the view
        self.map_width = 0  # Total width of the map
        self.map_height = 0  # Total height of the map
        self.padding = 10  # Padding around the center area
        self.fill_color = (255, 255, 255, 200)  # Fill color with 200 alpha for transparency

    def apply(self, entity):
        """Apply the camera offset to an entity's position."""
        return entity.rect.move(-self.camera.topleft)

    def update(self, target):
        """Update the camera position based on the target's position."""
        x = target.rect.centerx - self.camera.width // 2
        y = target.rect.centery - self.camera.height // 2

        # Keep the camera within the bounds of the map
        x = min(0, x)  # Prevent scrolling left past 0
        x = max(-(self.map_width - self.camera.width), x)  # Prevent scrolling right past the map width
        y = min(0, y)  # Prevent scrolling up past 0
        y = max(-(self.map_height - self.camera.height), y)  # Prevent scrolling down past the map height

        self.camera = pygame.Rect(x, y, self.camera.width, self.camera.height)
    def map(self,game_map):
        self.map = game_map
    def set_map_size(self, width, height):
        """Set the size of the map."""
        self.map_width = width
        self.map_height = height

    def get_camera_rect(self):
        """Return the current camera rectangle."""
        return self.camera

    def draw_padding(self, surface):
        """Draw the padding area around the center."""
        # Calculate the area for the padding
        left_area = pygame.Rect(0, 0, self.camera.width, self.camera.height)  # Left area
        right_area = pygame.Rect(0, 0, self.camera.width, self.camera.height)  # Right area

        # Draw padding around the center
        # Top area
        top_area = pygame.Rect(self.camera.x, self.camera.y, self.camera.width, self.padding)
        surface.fill(self.fill_color, top_area)

        # Bottom area
        bottom_area = pygame.Rect(self.camera.x, self.camera.y + self.camera.height - self.padding, self.camera.width, self.padding)
        surface.fill(self.fill_color, bottom_area)

        # Left area
        left_area = pygame.Rect(self.camera.x, self.camera.y, self.padding, self.camera.height)
        surface.fill(self.fill_color, left_area)

        # Right area
        right_area = pygame.Rect(self.camera.x + self.camera.width - self.padding, self.camera.y, self.padding, self.camera.height)
        surface.fill(self.fill_color, right_area)

        # Center area (the area in which the camera can move freely)
        center_area = pygame.Rect(
            self.camera.x + self.padding,
            self.camera.y + self.padding,
            self.camera.width - 2 * self.padding,
            self.camera.height - 2 * self.padding
        )
        return center_area


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tile Map Example")
    clock = pygame.time.Clock()

    map_loader = MapLoader("level1")
    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
    camera.map(map_loader)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    map_loader.change("level1")
                elif event.key == pygame.K_2:
                    map_loader.change("level2")

        screen.fill(BACKGROUND_COLOR)  # Clear screen before drawing the map

        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

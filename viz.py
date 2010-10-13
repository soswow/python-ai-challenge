import pygame

class PlanetWarViz(Debuggable):
    def __init__(self, data=None):
        self.data = data
        self.surface = None
        self.width, self.height = 640, 480
        self.k = None
        self.growth_size_k = 5
        self.border_padding = 30
        self.debug_name = "viz"

    def update_k_and_height(self):
        self.debug("update_k_and_height")
        max_x = max([p.x for p in self.state.planets])
        max_y = max([p.y for p in self.state.planets])
        self.debug("max_x = %d, max_y = %d" % (max_x, max_y))
        self.k = (self.width - self.border_padding) / max_x
        self.debug("k = %.2f" % self.k)
        self.height = max_y * self.k

    def make_surface(self):
        pygame.init()
        width = self.width + self.border_padding
        height = self.height + (self.border_padding * 2)
        self.surface = pygame.display.set_mode((width, height))
        self.surface.fill((255,255,255))
        pygame.display.update()

    def draw_state(self, state=None):
        if state:
            self.state = state
        if not self.k:
            self.update_k_and_height()
        if not self.surface:
            self.make_surface()

        map(self.draw_planet, self.state.planets)

    def input(self, events):
       for event in events:
          if event.type == pygame.QUIT:
             sys.exit(0)

    def draw_planet(self, p):
        pos = (p.x * self.k + self.border_padding, p.y * self.k + self.border_padding)
        rect = pygame.draw.circle(self.surface, (100, 100, 100, 0.5), pos, p.growth_rate * self.growth_size_k)
        pygame.display.update(rect)
  
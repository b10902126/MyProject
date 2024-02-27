import pygame
import sys
import random
from enum import Enum
from collections import namedtuple
import numpy as np

Point = namedtuple('Point', 'x, y')
pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
Pad_color = (128, 128, 128)  
Ball_color = (178, 34, 34)

fps = 30

class Direction(Enum):
    STAY = 0
    LEFT = -1
    RIGHT = 1
    
class PingPong:
    def __init__(self, width=600, height=600):
        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("PingPong Game")
        self.clock = pygame.time.Clock()
        self.max_score = 0
        self.pad_width = 60
        self.pad_height = 12
        self.pad_step = 10
        self.ball_radius = 12
        self.ball_step = 4
        self._reset()
    
    def _reset(self):
        self.score = 0
        self.pad_pos = Point(self.width/2-self.pad_width/2, self.height-self.pad_height-6)
        self.ball_pos = Point(random.randint(0 ,self.width), self.ball_radius)
        self.ball_vx = random.randint(1,3) * self.ball_step * random.choice([1, -1])
        self.ball_vy = random.randint(1,3) * self.ball_step
        self.direction = Direction.STAY
        self._draw()

    def _draw(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, Pad_color, (self.pad_pos.x, self.pad_pos.y, self.pad_width, self.pad_height))
        pygame.draw.circle(self.screen, Ball_color, (int(self.ball_pos.x), int(self.ball_pos.y)), self.ball_radius)

        font = pygame.font.Font(None, 36)
        alpha = pygame.mouse.get_pos()[0] / self.width
        text = font.render(f"Your Score: {self.score}", True, WHITE)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 80))
        self.screen.blit(text, text_rect)
        
        pygame.display.flip()
    
    def _move(self):
        if self.pad_pos.x <= 0 and self.direction == Direction.LEFT:
            self.pad_pos = Point(0, self.pad_pos.y)
        elif self.pad_pos.x >= self.width - self.pad_width and self.direction == Direction.RIGHT:
            self.pad_pos = Point(self.width - self.pad_width, self.pad_pos.y)
        else:
            self.pad_pos = Point(self.pad_pos.x + self.pad_step * self.direction.value, self.pad_pos.y)
        
        if (
            (self.ball_vy > 0) and
            (self.ball_pos.x >= self.pad_pos.x - self.ball_radius) and
            (self.ball_pos.x <= self.pad_pos.x + self.pad_width + self.ball_radius) and
            (self.ball_pos.y + self.ball_radius >= self.pad_pos.y)
        ):
            self.ball_vx = random.randint(1,3) * self.ball_step * random.choice([1, -1])
            self.ball_vy = -random.randint(1,3) * self.ball_step
            self.score += 1
        
        if self.ball_pos.x <= self.ball_radius and self.ball_vx < 0:
            self.ball_vx = -self.ball_vx
        elif self.ball_pos.x >= self.width - self.ball_radius and self.ball_vx > 0:
            self.ball_vx = -self.ball_vx
        
        if self.ball_pos.y <= self.ball_radius and self.ball_vy < 0:
            self.ball_vy = -self.ball_vy

        self.ball_pos = Point(self.ball_pos.x + self.ball_vx, self.ball_pos.y + self.ball_vy)

    def _check_gameover(self):
        if self.ball_pos.y + self.ball_radius >= self.height:
            return True
        else:
            return False
        
    def _end_game_screen(self):
        font = pygame.font.Font(None, 36)
        text = font.render(f"Your Score: {self.score}", True, WHITE)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 80))
        self.screen.blit(text, text_rect)

        font = pygame.font.Font(None, 36)
        text = font.render(f"Max Score: {self.max_score}", True, WHITE)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(text, text_rect)

        play_again_button = pygame.Rect(self.width // 2 - 80, self.height // 2 + 20, 160, 50)
        pygame.draw.rect(self.screen, WHITE, play_again_button)
        play_again_text = font.render("Play Again", True, BLACK)
        self.screen.blit(play_again_text, play_again_button.move(20, 10))

        quit_button = pygame.Rect(self.width // 2 - 80, self.height // 2 + 80, 160, 50)
        pygame.draw.rect(self.screen, WHITE, quit_button)
        quit_text = font.render("Quit", True, BLACK)
        self.screen.blit(quit_text, quit_button.move(50, 10))

        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if play_again_button.collidepoint(mouse_pos):
                        return True  # Play Again
                    elif quit_button.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()

    def play_step(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.direction = Direction.LEFT
                elif event.key == pygame.K_RIGHT:
                    self.direction = Direction.RIGHT
            elif event.type == pygame.KEYUP:
                self.direction = Direction.STAY

        self._move()

        if self.score > self.max_score:
            self.max_score = self.score
        if(self._check_gameover()):
            self._end_game_screen()
            self._reset()
        
        self._draw()
        self.clock.tick(fps)

if __name__ == '__main__':
    game = PingPong()
    while True:
        game.play_step()
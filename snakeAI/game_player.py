import pygame
import sys
import random
from enum import Enum
from collections import namedtuple
import numpy as np

Point = namedtuple('Point', 'x, y')
pygame.init()

BLOCK_SIZE = 15
fps = 10

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG_color = "gray0"
HEAD_color = "chartreuse2"
BODY_color = "chartreuse"
FOOD_color = "firebrick1"

class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4
    STOP = 5

class snakeGameAI:
    def __init__(self, width=600, height=600):
        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.max_score = 0
        self._reset()
    def _reset(self):
        self.frame_iteration = 0
        self.score = 0
        self.snake = [Point(self.width/2, self.height/2)]
        self.direction = Direction.STOP
        self.food = self._spawn()
        self._draw()
    
    def _spawn(self):
        while True:
            x = random.randrange(0,self.width,BLOCK_SIZE)
            y = random.randrange(0,self.height,BLOCK_SIZE)
            if Point(x, y) not in self.snake:
                return Point(x, y)

    def check_ate(self):
        if self.food == self.snake[0]:
            self.snake.append(Point(-BLOCK_SIZE, -BLOCK_SIZE))
            self.food = self._spawn()
            return True
        return False

    def check_collision(self, point=None):
        if point == None:
            point = self.snake[0]
        if (
            point.x < 0
            or point.x >= self.width
            or point.y < 0
            or point.y >= self.height
        ):
            return True
        if point in self.snake[1:]:
            return True
        
        return False
    
    def _move(self, action=None):
        # clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        # idx = clock_wise.index(self.direction)

        # if np.array_equal(action, [1, 0, 0]):
        #     new_direction = clock_wise[idx] # no change
        # elif np.array_equal(action, [0, 1, 0]):
        #     next_idx = (idx + 1) % 4
        #     new_direction = clock_wise[next_idx] # turn right
        # else:  # [0, 0, 1]
        #     next_idx = (idx - 1) % 4
        #     new_direction = clock_wise[next_idx] # turn left

        # self.direction = new_direction

        for i in range(len(self.snake)-1, 0, -1):
            self.snake[i] = self.snake[i-1]
        x = self.snake[0].x
        y = self.snake[0].y
        if self.direction == Direction.UP:
            y -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.RIGHT:
            x += BLOCK_SIZE
        self.snake[0] = Point(x, y)
    
    def change_direction(self, new_direction=None):
        if new_direction == None:
            return
        if len(self.snake) == 1:
            self.direction = new_direction
        elif (
            (self.direction == Direction.RIGHT and new_direction != Direction.LEFT) or
            (self.direction == Direction.LEFT and new_direction != Direction.RIGHT) or
            (self.direction == Direction.UP and new_direction != Direction.DOWN) or
            (self.direction == Direction.DOWN and new_direction != Direction.UP)
        ):
            self.direction = new_direction

    def play_step(self, action='None'):
        self.frame_iteration += 1
        new_direction = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if ( event.key == pygame.K_UP):
                    new_direction = Direction.UP
                elif  ( event.key == pygame.K_DOWN):
                    new_direction = Direction.DOWN
                elif  ( event.key == pygame.K_LEFT):
                    new_direction = Direction.LEFT
                elif  ( event.key == pygame.K_RIGHT):
                    new_direction = Direction.RIGHT

        self.change_direction(new_direction)
        self._move(action)
        if self.check_ate():
            self.score += 10
            if self.score > self.max_score:
                self.max_score = self.score
            self.food = self._spawn()
        if self.check_collision():
            self._end_game_screen()
            self._reset()
        self._draw()
        self.clock.tick(fps)

    def _draw(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, pygame.Color(HEAD_color), (self.snake[0].x, self.snake[0].y, BLOCK_SIZE, BLOCK_SIZE))
        for segment in self.snake[1:]:
            pygame.draw.rect(self.screen, pygame.Color(BODY_color), (segment.x, segment.y, BLOCK_SIZE, BLOCK_SIZE))
        pygame.draw.rect(self.screen, pygame.Color(FOOD_color), (self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))
        pygame.display.flip()

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

if __name__ == '__main__':
    snakeGame = snakeGameAI()
    while True:
        snakeGame.play_step()
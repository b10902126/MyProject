import pygame
import sys
import random
from enum import Enum
from collections import namedtuple
import numpy as np

Point = namedtuple('Point', 'x, y')
pygame.init()

BLOCK_SIZE = 15
fps = 80

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

class snakeGameAI:
    def __init__(self, width=600, height=600):
        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.max_score = 0
        self.reset()
    def reset(self):
        self.frame_iteration = 0
        self.score = 0
        self.snake = [Point(self.width/2, self.height/2)]
        self.direction = random.choice(list(Direction))
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
        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        idx = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):
            new_direction = clock_wise[idx] # no change
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx - 1) % 4
            new_direction = clock_wise[next_idx] # turn left
        else:  # [0, 0, 1]
            next_idx = (idx + 1) % 4
            new_direction = clock_wise[next_idx] # turn right

        self.direction = new_direction

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
    
    def play_step(self, action=None):
        self.frame_iteration += 1
        new_direction = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        self._move(action)
        
        reward = 0
        game_over = False
        if self.check_ate():
            self.score += 1
            reward = 10
            if self.score > self.max_score:
                self.max_score = self.score
            self.food = self._spawn()
        if self.check_collision():
            reward = -10
            game_over = True
        self._draw()
        self.clock.tick(fps)
        return reward, game_over, self.score

    def _draw(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, pygame.Color(HEAD_color), (self.snake[0].x, self.snake[0].y, BLOCK_SIZE, BLOCK_SIZE))
        for segment in self.snake[1:]:
            pygame.draw.rect(self.screen, pygame.Color(BODY_color), (segment.x, segment.y, BLOCK_SIZE, BLOCK_SIZE))
        pygame.draw.rect(self.screen, pygame.Color(FOOD_color), (self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))
        pygame.display.flip()


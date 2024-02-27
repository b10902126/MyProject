import torch
import random
import numpy as np
from collections import deque
from game import snakeGameAI, Direction, Point
from model import Linear_QNet, QTrainer
from plot import plot

BLOCK_SIZE = 15
MAX_MEMORY = 1000000
BATCH_SIZE = 1000

class Agent():
    def __init__(self):
        self.num_games = 0
        self.epsilion = 0
        self.memory = deque(maxlen=MAX_MEMORY)
        self.model = Linear_QNet(11, 256, 3)
        self.trainer = QTrainer(self.model, lr=0.005, gamma=0.85)

    def get_state(self, game):
        # [danger_straight, danger_left, danger_right, 
        # direction_up, direction_down, direction_left, direction_right,
        # food_up, food_down, food_left, food_right]

        head = game.snake[0]
        
        direction_up = game.direction == Direction.UP
        direction_down = game.direction == Direction.DOWN
        direction_left = game.direction == Direction.LEFT
        direction_right = game.direction == Direction.RIGHT

        if(direction_up):
            point_straight = Point(head.x, head.y - BLOCK_SIZE)
            point_left = Point(head.x - BLOCK_SIZE, head.y)
            point_right = Point(head.x + BLOCK_SIZE, head.y)
        elif(direction_down):
            point_straight = Point(head.x, head.y + BLOCK_SIZE)
            point_left = Point(head.x + BLOCK_SIZE, head.y)
            point_right = Point(head.x - BLOCK_SIZE, head.y)
        elif(direction_left):
            point_straight = Point(head.x - BLOCK_SIZE, head.y)
            point_left = Point(head.x, head.y + BLOCK_SIZE)
            point_right = Point(head.x, head.y - BLOCK_SIZE)
        else:
            point_straight = Point(head.x + BLOCK_SIZE, head.y)
            point_left = Point(head.x, head.y - BLOCK_SIZE)
            point_right = Point(head.x, head.y + BLOCK_SIZE)

        state =  [
            game.check_collision(point_straight),
            game.check_collision(point_left),
            game.check_collision(point_right),

            direction_up,
            direction_down,
            direction_left,
            direction_right,

            game.food.y < head.y,
            game.food.y > head.y,
            game.food.x < head.x,
            game.food.x > head.x
        ]

        return np.array(state, dtype=int)
    
    def get_action(self, state):
        # straight = [1, 0, 0], left = [0, 1, 0], right = [0, 0, 1]
        action = [0, 0, 0]
        self.epsilion = 80 - self.num_games
        if random.randint(0,200) < self.epsilion:
            idx = random.randint(0,2)
            action[idx] = 1
        else:
            state0 = torch.tensor(state, dtype = torch.float)
            prediction = self.model(state0)
            idx = torch.argmax(prediction).item()
            action[idx] = 1

        return action

    def remember(self, state, action, reward, new_state, game_over):
        self.memory.append((state, action, reward, new_state, game_over))

    def train_short_memory(self, state, action, reward, new_state, game_over):
        self.trainer.train_step(state, action, reward, new_state, game_over)
    
    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory
        states, actions, rewards, new_states, game_overs = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, new_states, game_overs)

def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    agent = Agent()
    game = snakeGameAI()
    while True:
        old_state = agent.get_state(game)
        action = agent.get_action(old_state)
        reward, game_over, score = game.play_step(action)
        new_state = agent.get_state(game)
        agent.train_short_memory(old_state, action, reward, new_state, game_over)
        agent.remember(old_state, action, reward, new_state, game_over)
        if game_over:
            if score > game.max_score:
                game.max_score = score
            agent.num_games += 1
            game.reset()

            agent.train_long_memory()
            print(f"Game:{agent.num_games}, Score:{score}, Record:{game.max_score}")

            plot_scores.append(score)
            total_score += score
            plot_mean_scores.append(total_score/agent.num_games)
            plot(plot_scores, plot_mean_scores)

if __name__ == '__main__':
    train()
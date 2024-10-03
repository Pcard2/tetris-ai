"""
@author: Viet Nguyen <nhviet1009@gmail.com>
edited by: Pau Cardona
"""
from random import random, randint, sample
import torch
import torch.nn as nn
from src.deep_q_network import DeepQNetwork
from src.tetris import Tetris
from collections import deque

width = 10
height = 20
block_size = 15
batch_size = 512
lr = 1e-3
gamma = 0.99
initial_epsilon = 1
final_epsilon = 1e-3
num_decay_epochs = 2000
num_epochs = 10000 #
save_interval = 1000
replay_memory_size = 30000
log_path = "tensorboard"
saved_path = "trained_models"


def train():
    if torch.cuda.is_available():
        torch.cuda.manual_seed(123)
    else:
        torch.manual_seed(123)
    env = Tetris(width=width, height=height, block_size=block_size)
    model = DeepQNetwork()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    state = env.reset()
    if torch.cuda.is_available():
        model.cuda()
        state = state.cuda()

    replay_memory = deque(maxlen=replay_memory_size)
    epoch = 1
    while epoch < num_epochs:
        next_steps = env.get_next_states()
        # Exploration or exploitation
        epsilon = final_epsilon + (max(num_decay_epochs - epoch, 0) * (
                initial_epsilon - final_epsilon) / num_decay_epochs)
        u = random()
        random_action = u <= epsilon
        next_actions, next_states = zip(*next_steps.items())
        next_states = torch.stack(next_states)
        if torch.cuda.is_available():
            next_states = next_states.cuda()
        model.eval()
        with torch.no_grad():
            predictions = model(next_states)[:, 0]
        model.train()
        if random_action:
            index = randint(0, len(next_steps) - 1)
        else:
            index = torch.argmax(predictions).item()

        next_state = next_states[index, :]
        action = next_actions[index]


        reward, done = env.step(action, epoch)
        env.render(epoch)


        if torch.cuda.is_available():
            next_state = next_state.cuda()
        replay_memory.append([state, reward, next_state, done])
        if done:
            final_score = env.reward
            final_tetrominoes = env.tetrominoes
            final_cleared_lines = env.cleared_lines
            state = env.reset()
            if torch.cuda.is_available():
                state = state.cuda()
        else:
            state = next_state
            continue
        # if len(replay_memory) < replay_memory_size / 10:
        #     continue

        epoch += 1
        batch = sample(replay_memory, min(len(replay_memory), batch_size))
        state_batch, reward_batch, next_state_batch, done_batch = zip(*batch)
        state_batch = torch.stack(tuple(state for state in state_batch))
        reward_batch = torch.tensor(reward_batch, dtype=torch.float32)[:, None]
        next_state_batch = torch.stack(tuple(state for state in next_state_batch))

        if torch.cuda.is_available():
            state_batch = state_batch.cuda()
            reward_batch = reward_batch.cuda()
            next_state_batch = next_state_batch.cuda()

        q_values = model(state_batch)
        model.eval()
        with torch.no_grad():
            next_prediction_batch = model(next_state_batch)
        model.train()

        y_batch = torch.cat(
            tuple(reward if done else reward + gamma * prediction for reward, done, prediction in
                  zip(reward_batch, done_batch, next_prediction_batch)))[:, None]

        optimizer.zero_grad()
        loss = criterion(q_values, y_batch)
        loss.backward()
        optimizer.step()

        print("Epoch: {}/{}, Action: {}, Reward: {}, Tetrominoes {}, Cleared lines: {}".format(
            epoch,
            num_epochs,
            action,
            final_score,
            final_tetrominoes,
            final_cleared_lines))

        if epoch > 0 and epoch % save_interval == 0:
            torch.save(model, "{}/tetris_{}".format(saved_path, epoch))
            env.saveGraph(epoch)


if __name__ == "__main__":
    train()
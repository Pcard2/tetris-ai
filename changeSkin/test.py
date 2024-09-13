"""
@author: Viet Nguyen <nhviet1009@gmail.com>
edited by: Pau Cardona
"""
import torch
from src.tetris import Tetris


width = 10
height = 20
block_size = 15
saved_path = "trained_models"


def test():
    if torch.cuda.is_available():
        torch.cuda.manual_seed(123)
    else:
        torch.manual_seed(123)
    if torch.cuda.is_available():
        model = torch.load("{}/tetris".format(saved_path))
    else:
        model = torch.load("{}/tetris".format(saved_path), map_location=lambda storage, loc: storage)
    model.eval()
    env = Tetris(width=width, height=height, block_size=block_size)
    env.reset()
    if torch.cuda.is_available():
        model.cuda()
    while True:
        next_steps = env.get_next_states()
        next_actions, next_states = zip(*next_steps.items())
        next_states = torch.stack(next_states)
        if torch.cuda.is_available():
            next_states = next_states.cuda()
        predictions = model(next_states)[:, 0]
        index = torch.argmax(predictions).item()
        action = next_actions[index]
        reward, done = env.step(action, 1)
        env.render(1)

        if done:
            if reward >= 0:
                env.uploadStats()
            env.reset()

if __name__ == "__main__":
    test()
import gym
import yaml
import numpy as np

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage
from stable_baselines3.common.evaluation import evaluate_policy

# Import scripts module to register the custom gym environment
import scripts
from scripts.network import NatureCNN


# Load train environment configs
with open('scripts/env_config.yml', 'r') as f:
    env_config = yaml.safe_load(f)

# Load inference configs
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

# Determine input image shape
image_shape = (84,84,1) if config["test_mode"]=="depth" else (84,84,3)

# Create a DummyVecEnv for evaluation
env = DummyVecEnv([lambda: Monitor(
    gym.make(
        "airsim-env-v0",
        ip_address="127.0.0.1",
        image_shape=image_shape,
        env_config=env_config["TrainEnv"],
        input_mode=config["test_mode"]
    )
)])

# Wrap env as VecTransposeImage (Channel last to channel first)
env = VecTransposeImage(env)

policy_kwargs = dict(
    features_extractor_class=NatureCNN
)

print("Loading trained model...")
model = PPO.load("saved_policy/best_model", env=env)

print("Evaluating policy...")
print("="*60)

# Evaluate the policy
mean_reward, std_reward = evaluate_policy(
    model,
    env,
    n_eval_episodes=20,
    deterministic=True
)

print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")
print("="*60)

# Run a few episodes manually to see behavior
print("\nRunning manual evaluation episodes...")
n_episodes = 5
episode_rewards = []

obs = env.reset()
episode_reward = 0
episode_count = 0

for step in range(5000):  # Max steps
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, done, info = env.step(action)
    episode_reward += reward[0]

    if done[0]:
        episode_count += 1
        print(f"Episode {episode_count}: Reward = {episode_reward:.2f}")
        episode_rewards.append(episode_reward)
        episode_reward = 0
        obs = env.reset()

        if episode_count >= n_episodes:
            break

if episode_rewards:
    print("\n" + "="*60)
    print(f"Manual evaluation - Average reward: {np.mean(episode_rewards):.2f} +/- {np.std(episode_rewards):.2f}")
    print(f"Min: {np.min(episode_rewards):.2f}, Max: {np.max(episode_rewards):.2f}")
    print("="*60)

env.close()
print("\nEvaluation complete!")

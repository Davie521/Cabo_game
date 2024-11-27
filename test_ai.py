from train_ai_player import CaboAIPlayer, CaboEnv

def test_trained_ai(model_path="cabo_ai_model.pth"):
    env = CaboEnv()
    ai_player = env.players[0]
    ai_player.load_model(model_path)
    
    # 设置为评估模式（不探索）
    ai_player.epsilon = 0
    
    state = env.reset()
    total_reward = 0
    done = False
    
    while not done:
        action = ai_player.choose_action(state)
        state, reward, done = env.step(action)
        total_reward += reward
    
    print(f"测试游戏结束，总奖励: {total_reward}")

if __name__ == "__main__":
    test_trained_ai() 
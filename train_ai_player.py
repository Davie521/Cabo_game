from game_cabo import Game, Player, Card
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque, namedtuple
import random
import os
import torch.nn.functional as F

Experience = namedtuple('Experience', ('state', 'action', 'reward', 'next_state', 'done'))

class DQN(nn.Module):
    def __init__(self, input_size, output_size):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.ln1 = nn.LayerNorm(128)
        self.fc2 = nn.Linear(128, 128)
        self.ln2 = nn.LayerNorm(128)
        self.fc3 = nn.Linear(128, 64)
        self.ln3 = nn.LayerNorm(64)
        self.fc4 = nn.Linear(64, output_size)
        
        # 初始化权重
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        if x.dim() == 1:
            x = x.unsqueeze(0)
        
        x = F.relu(self.ln1(self.fc1(x)))
        x = F.relu(self.ln2(self.fc2(x)))
        x = F.relu(self.ln3(self.fc3(x)))
        return self.fc4(x)

class CaboAIPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.state_size = 13
        self.action_size = 6
        
        # 增加经验池大小和批量大小
        self.memory = deque(maxlen=200000)
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.9995
        self.learning_rate = 0.0005
        self.batch_size = 256
        self.steps = 0
        self.target_update_freq = 10
        
        # 添加目标网络
        self.model = DQN(self.state_size, self.action_size)
        self.target_model = DQN(self.state_size, self.action_size)
        self.update_target_model()
        
        # 使用 RMSprop 优化器
        self.optimizer = optim.RMSprop(self.model.parameters(), 
                                     lr=self.learning_rate, 
                                     momentum=0.9)

    def update_target_model(self):
        """更新目标网络"""
        self.target_model.load_state_dict(self.model.state_dict())

    def save_model(self, path):
        """保存模型"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, path)

    def load_model(self, path):
        """加载模型"""
        if os.path.exists(path):
            try:
                checkpoint = torch.load(path)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                self.epsilon = checkpoint['epsilon']
            except RuntimeError as e:
                print("警告: 模型结构已更改，将使用新的模型结构开始训练")
                # 如果加载失败，就使用新的模型继续训练
                pass

    def decode_action(self, action_idx):
        """将动作索引解码为具体操作"""
        if action_idx == 0:
            return "cabo"
        elif action_idx == 1:
            return "peek"
        elif action_idx == 2:
            return "swap"
        elif action_idx == 3:
            return "swap_pos_1"
        elif action_idx == 4:
            return "swap_pos_2"
        else:
            return "discard"

    def encode_state(self, game_state):
        """改进状态编码，添加更多信息"""
        state = []
        # 编码自己已知的牌
        known_sum = 0
        known_count = 0
        for i in range(2):
            if i in self.known_cards:
                card = self.known_cards[i]
                state.extend([card.number / 5, 1])
                known_sum += card.number
                known_count += 1
            else:
                state.extend([0, 0])
        
        # 添加平均分信息
        avg_score = known_sum / max(1, known_count)
        state.append(avg_score / 5)
        
        # 编码对手已知的牌
        opp_known_sum = 0
        opp_known_count = 0
        for i in range(2):
            if i in self.known_opponent_cards:
                card = self.known_opponent_cards[i]
                state.extend([card.number / 5, 1])
                opp_known_sum += card.number
                opp_known_count += 1
            else:
                state.extend([0, 0])
        
        # 添加对手平均分信息
        opp_avg_score = opp_known_sum / max(1, opp_known_count)
        state.append(opp_avg_score / 5)
        
        # 编码牌堆和游戏状态信息
        state.extend([
            len(game_state.deck) / 10,  # 牌堆剩余比例
            1 if game_state.cabo_called else 0,
            1 if game_state.cabo_caller == self else 0
        ])
        
        return np.array(state, dtype=np.float32)

    def choose_action(self, state):
        """选择动作（epsilon-greedy策略）"""
        if random.random() < self.epsilon:
            return random.randrange(self.action_size)
        
        with torch.no_grad():
            # 确保state是正确的形状
            if isinstance(state, np.ndarray):
                state = torch.FloatTensor(state)
            state = state.unsqueeze(0)  # 添加batch维度
            q_values = self.model(state)
            return q_values.argmax().item()

    def remember(self, state, action, reward, next_state, done):
        """存储经验"""
        self.memory.append(Experience(state, action, reward, next_state, done))

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        
        experiences = random.sample(self.memory, batch_size)
        states = np.array([exp.state for exp in experiences])
        actions = np.array([exp.action for exp in experiences])
        rewards = np.array([exp.reward for exp in experiences])
        next_states = np.array([exp.next_state for exp in experiences])
        dones = np.array([exp.done for exp in experiences])
        
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions).unsqueeze(1)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)

        current_q = self.model(states).gather(1, actions)
        next_q = self.target_model(next_states).max(1)[0].detach()
        target_q = rewards + (1 - dones) * self.gamma * next_q
        
        loss = F.smooth_l1_loss(current_q.squeeze(), target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()

        self.steps += 1
        if self.steps % self.target_update_freq == 0:
            self.update_target_model()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def decide_peek_initial(self):
        """决定初始要看哪张牌"""
        # 随机选择一张未知的牌
        unknown_positions = [i for i in range(2) if i not in self.known_cards]
        return random.choice(unknown_positions)

class CaboEnv(Game):
    def __init__(self):
        super().__init__()
        self.players = [CaboAIPlayer("AI_1"), CaboAIPlayer("AI_2")]
        self.reset()

    def reset(self):
        """重置游戏环境"""
        self.deck = self.create_deck()
        self.discard_pile = []
        self.current_player = 0
        self.cabo_called = False
        self.cabo_caller = None
        
        # 发牌
        for player in self.players:
            for _ in range(2):
                player.hand.append(self.deck.pop())
        
        # 初始偷看
        for player in self.players:
            pos = random.randint(0, 1)
            player.peek_card(pos)

        return self.get_state()

    def get_state(self):
        """获取当前游戏状态"""
        current_player = self.players[self.current_player]
        return current_player.encode_state(self)

    def step(self, action):
        """执行一步动作"""
        current_player = self.players[self.current_player]
        opponent = self.players[1 - self.current_player]
        
        reward = 0
        done = False
        action_type = current_player.decode_action(action)

        # 基础奖励：根据已知牌的平均分数（缩小尺度）
        known_cards = list(current_player.known_cards.values())
        if known_cards:
            avg_score = sum(card.number for card in known_cards) / len(known_cards)
            reward -= min(1.0, avg_score / 10)  # 限制基础惩罚的大小

        # 执行动作
        if action_type == "cabo":
            if not self.cabo_called:
                self.cabo_called = True
                self.cabo_caller = current_player
                known_sum = sum(card.number for card in current_player.known_cards.values())
                known_count = len(current_player.known_cards)
                if known_count > 0 and (known_sum / known_count) <= 2:
                    reward += 2  # 减小奖励幅度
                else:
                    reward -= 2
            else:
                reward -= 1

        elif action_type == "peek" and self.deck:
            drawn_card = self.deck.pop()
            if drawn_card.skill == "Peek":
                unknown_positions = [i for i in range(2) if i not in current_player.known_opponent_cards]
                if unknown_positions:
                    pos = random.choice(unknown_positions)
                    peeked_card = opponent.hand[pos]
                    current_player.peek_opponent_card(pos, peeked_card)
                    reward += 1
            self.discard_pile.append(drawn_card)

        elif action_type == "swap" and self.deck:
            drawn_card = self.deck.pop()
            if drawn_card.skill == "Swap":
                my_max_card = max(((i, card) for i, card in current_player.known_cards.items()),
                                key=lambda x: x[1].number, default=(None, None))
                opp_min_card = min(((i, card) for i, card in current_player.known_opponent_cards.items()),
                                 key=lambda x: x[1].number, default=(None, None))
                
                if my_max_card[0] is not None and opp_min_card[0] is not None:
                    my_pos, my_card = my_max_card
                    opp_pos, opp_card = opp_min_card
                    current_player.hand[my_pos], opponent.hand[opp_pos] = opponent.hand[opp_pos], current_player.hand[my_pos]
                    reward += 1 if my_card.number > opp_card.number else -1

            self.discard_pile.append(drawn_card)

        elif action_type.startswith("swap_pos") and self.deck:
            drawn_card = self.deck.pop()
            if not drawn_card.skill:
                pos = int(action_type[-1]) - 1
                if pos in current_player.known_cards:
                    old_card = current_player.hand[pos]
                    if drawn_card.number < old_card.number:
                        reward += min(2.0, (old_card.number - drawn_card.number) / 3)  # 限制奖励大小
                    current_player.hand[pos] = drawn_card
                    current_player.known_cards[pos] = drawn_card
                    self.discard_pile.append(old_card)

        # 游戏结束时的奖励
        if not self.deck or (self.cabo_called and self.cabo_caller != current_player):
            done = True
            if self.cabo_called:
                caller_score = self.cabo_caller.total_score()
                other_player = self.players[1 - self.players.index(self.cabo_caller)]
                other_score = other_player.total_score()
                
                if self.cabo_caller == current_player:
                    score_diff = other_score - caller_score
                    if score_diff >= 0:
                        reward += min(5.0, 2.0 + score_diff / 10)  # 限制最大奖励
                    else:
                        reward -= min(5.0, 2.0 + abs(score_diff) / 10)  # 限制最大惩罚

        return self.get_state(), reward, done

def train_ai(save_path="cabo_ai_model.pth", episodes=100000):
    """改进训练过程"""
    env = CaboEnv()
    ai_player = env.players[0]
    opponent = env.players[1]
    
    if os.path.exists(save_path):
        try:
            ai_player.load_model(save_path)
        except:
            os.remove(save_path)
            print("删除旧的模型文件，使用新的模型结构开始训练")
    
    best_reward = float('-inf')
    no_improvement_count = 0
    window_size = 100
    rewards_window = deque(maxlen=window_size)
    
    print(f"开始训练，状态空间大小: {ai_player.state_size}, 动作空间大小: {ai_player.action_size}")
    
    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        
        episode_states = []
        episode_actions = []
        episode_rewards = []
        
        while True:
            action = ai_player.choose_action(state)
            next_state, reward, done = env.step(action)
            
            episode_states.append(state)
            episode_actions.append(action)
            episode_rewards.append(reward)
            
            total_reward += reward
            state = next_state
            
            if done:
                ai_score = ai_player.total_score()
                opp_score = opponent.total_score()
                score_diff = opp_score - ai_score
                
                final_reward = score_diff / 10.0
                
                for t in range(len(episode_rewards)):
                    discount = ai_player.gamma ** (len(episode_rewards) - t - 1)
                    episode_rewards[t] += final_reward * discount
                
                for t in range(len(episode_states)):
                    ai_player.remember(
                        episode_states[t],
                        episode_actions[t],
                        episode_rewards[t],
                        episode_states[t+1] if t+1 < len(episode_states) else next_state,
                        t == len(episode_states)-1
                    )
                break
            
            if len(ai_player.memory) > ai_player.batch_size:
                ai_player.replay(ai_player.batch_size)
        
        rewards_window.append(total_reward)
        avg_reward = sum(rewards_window) / len(rewards_window)
        
        if episode % 100 == 0:
            print(f"Episode: {episode}, Avg Reward: {avg_reward:.2f}, "
                  f"Total Reward: {total_reward:.2f}, Epsilon: {ai_player.epsilon:.3f}, "
                  f"Score Diff: {score_diff}, AI Score: {ai_score}, Opp Score: {opp_score}")
            
            if avg_reward > best_reward:
                best_reward = avg_reward
                ai_player.save_model(save_path)
                no_improvement_count = 0
                print(f"保存新的最佳模型，最佳平均奖励: {best_reward:.2f}")
            else:
                no_improvement_count += 1
            
            if no_improvement_count > 50 and episode > 10000:
                print(f"训练在第{episode}轮后停止，因为{no_improvement_count}次评估没有改善")
                break
    
    return ai_player

if __name__ == "__main__":
    trained_ai = train_ai() 
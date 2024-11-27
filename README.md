# Cabo AI Game

这是一个基于深度强化学习的 Cabo 纸牌游戏 AI 实现。

## 文件结构

### 核心游戏文件
- `game_cabo.py`: 游戏核心逻辑，包含基础的游戏规则、玩家类和卡牌类
- `smart_cabo_players.py`: 简单的规则基础AI实现（不使用深度学习）

### AI 相关文件
- `cabo_ai_player.py`: 深度强化学习AI的主要实现
  - 包含 DQN 网络结构
  - AI 玩家类
  - 训练环境
  - 训练循环
- `train_ai_player.py`: AI训练脚本
- `test_ai.py`: AI模型测试脚本

### 界面相关文件
- `cabo_gui.py`: 基础游戏GUI界面
- `cabo_gui_vs_ai.py`: 人机对战的GUI界面
- `play_with_ai.py`: 命令行版本的人机对战实现

### 配置文件
- `requirements.txt`: 项目依赖包列表

## 如何使用

1. 安装依赖：

```bash
pip install -r
```

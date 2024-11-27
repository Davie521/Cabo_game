from game_cabo import Game, Player, Card
from train_ai_player import CaboAIPlayer
import os

class HumanPlayer(Player):
    def show_hand(self, reveal_all=False):
        cards = []
        for i, card in enumerate(self.hand):
            if i in self.known_cards or reveal_all:
                cards.append(str(card))
            else:
                cards.append("?")
        return cards

class HumanVsAI(Game):
    def __init__(self, ai_model_path):
        super().__init__()
        self.ai_player = CaboAIPlayer("AI玩家")
        if os.path.exists(ai_model_path):
            self.ai_player.load_model(ai_model_path)
            # 设置AI为评估模式
            self.ai_player.epsilon = 0
        self.human_player = HumanPlayer("人类玩家")
        self.players = [self.human_player, self.ai_player]

    def setup_game(self):
        """初始化游戏"""
        # 发牌
        for player in self.players:
            for _ in range(2):
                player.hand.append(self.deck.pop())
        
        # 人类玩家初始偷看
        print(f"\n{self.human_player.name}的回合 - 初始偷看")
        self.show_game_state(0)
        while True:
            try:
                pos = int(input(f"选择要偷看的牌 (1 或 2): ")) - 1
                if pos in [0, 1]:
                    break
                print("请输入1或2")
            except ValueError:
                print("请输入有效的数字")
        card = self.human_player.peek_card(pos)
        print(f"你偷看的牌是: {card}")
        input("\n按Enter继续...")

        # AI玩家初始偷看
        print(f"\n{self.ai_player.name}的回合 - 初始偷看")
        pos = self.ai_player.decide_peek_initial()
        self.ai_player.peek_card(pos)  # AI偷看牌但不显示结果
        print(f"{self.ai_player.name}偷看了第{pos+1}张牌")
        input("\n按Enter继续...")

    def show_game_state(self, player_idx):
        """显示游戏状态"""
        current_player = self.players[player_idx]
        opponent = self.players[1 - player_idx]
        
        print("\n" + "="*50)
        if player_idx == 0:  # 人类玩家视角
            print(f"对手 ({opponent.name}) 的手牌: ['?', '?']")  # 永远显示为未知
            print(f"牌堆剩余: {len(self.deck)} 张")
            print(f"弃牌堆顶: {self.discard_pile[-1] if self.discard_pile else '空'}")
            print(f"你的手牌: {current_player.show_hand()}")
        if self.cabo_called:
            print(f"\n{self.cabo_caller.name}已经呼叫Cabo!")
        print("="*50)

    def play_game(self):
        self.setup_game()
        game_continue = True
        
        while game_continue and self.deck:
            if self.current_player == 0:  # 人类玩家的回合
                game_continue = self.play_human_turn()
            else:  # AI玩家的回合
                game_continue = self.play_ai_turn()
            
            self.current_player = 1 - self.current_player

        # 游戏结束，显示结果
        print("\n" + "="*20 + " 游戏结束 " + "="*20)
        for player in self.players:
            print(f"\n{player.name}的手牌: {player.show_hand(reveal_all=True)}")
            print(f"{player.name}的手牌点数: {player.total_score()}")

        if self.cabo_called:
            caller_score = self.cabo_caller.total_score()
            other_player = self.players[1 - self.players.index(self.cabo_caller)]
            other_score = other_player.total_score()
            
            print(f"\n{self.cabo_caller.name} 呼叫了Cabo!")
            if caller_score <= other_score:
                print(f"{self.cabo_caller.name} 获胜！")
            else:
                print(f"{other_player.name} 获胜！")
        else:
            scores = [(p.total_score(), p) for p in self.players]
            winner = min(scores, key=lambda x: x[0])[1]
            print(f"\n{winner.name} 获胜！")

    def play_human_turn(self):
        """人类玩家的回合"""
        print(f"\n{self.human_player.name}的回合:")
        self.show_game_state(0)

        if not self.cabo_called:
            action = input("\n选择行动:\n1. 摸牌\n2. 呼叫Cabo\n请选择: ")
            if action == "2":
                self.cabo_called = True
                self.cabo_caller = self.human_player
                print(f"\n{self.human_player.name}呼叫了Cabo！")
                return True

        drawn_card = self.deck.pop()
        print(f"\n摸到的牌: {drawn_card}")
        
        if drawn_card.skill:
            choice = input("\n1. 使用技能\n2. 弃掉\n请选择: ")
            if choice == "1":
                if drawn_card.skill == "Peek":
                    pos = int(input("选择要偷看对手的哪张牌 (1 或 2): ")) - 1
                    peeked_card = self.ai_player.hand[pos]
                    self.human_player.peek_opponent_card(pos, peeked_card)
                    print(f"你偷看的对手的牌是: {peeked_card}")
                elif drawn_card.skill == "Swap":
                    my_pos = int(input("选择要交换的自己的牌位置 (1 或 2): ")) - 1
                    opp_pos = int(input("选择要交换的对手的牌位置 (1 或 2): ")) - 1
                    
                    my_card = self.human_player.hand[my_pos]
                    opp_card = self.ai_player.hand[opp_pos]
                    self.human_player.hand[my_pos] = opp_card
                    self.ai_player.hand[opp_pos] = my_card
                    
                    if my_pos in self.human_player.known_cards:
                        self.human_player.known_opponent_cards[opp_pos] = my_card
                        self.human_player.known_cards[my_pos] = opp_card
            self.discard_pile.append(drawn_card)
        else:
            choice = input("\n1. 与手牌交换\n2. 弃掉\n请选择: ")
            if choice == "1":
                pos = int(input("选择要交换的手牌位置 (1 或 2): ")) - 1
                old_card = self.human_player.hand[pos]
                self.human_player.hand[pos] = drawn_card
                self.human_player.known_cards[pos] = drawn_card
                self.discard_pile.append(old_card)
            else:
                self.discard_pile.append(drawn_card)

        if self.cabo_called and self.cabo_caller != self.human_player:
            return False
        return True

    def play_ai_turn(self):
        """AI玩家的回合"""
        # 获取当前状态
        state = self.ai_player.encode_state(self)
        
        # AI选择动作
        action = self.ai_player.choose_action(state)
        action_type = self.ai_player.decode_action(action)
        
        if action_type == "cabo" and not self.cabo_called:
            self.cabo_called = True
            self.cabo_caller = self.ai_player
            print(f"\nAI玩家呼叫了Cabo！")
            input("\n按Enter继续...")
            return True

        drawn_card = self.deck.pop()
        print(f"\n弃牌堆顶: {self.discard_pile[-1] if self.discard_pile else '空'}")
        
        if drawn_card.skill:
            if action_type == "peek":
                unknown_positions = [i for i in range(2) if i not in self.ai_player.known_opponent_cards]
                if unknown_positions:
                    pos = random.choice(unknown_positions)
                    peeked_card = self.human_player.hand[pos]
                    self.ai_player.peek_opponent_card(pos, peeked_card)
                    print(f"AI玩家摸到了 {drawn_card}，偷看了你的第{pos+1}张牌")
            elif action_type == "swap":
                my_max_card = max(((i, card) for i, card in self.ai_player.known_cards.items()),
                                key=lambda x: x[1].number, default=(None, None))
                opp_min_card = min(((i, card) for i, card in self.ai_player.known_opponent_cards.items()),
                                 key=lambda x: x[1].number, default=(None, None))
                
                if my_max_card[0] is not None and opp_min_card[0] is not None:
                    my_pos, my_card = my_max_card
                    opp_pos, opp_card = opp_min_card
                    self.ai_player.hand[my_pos], self.human_player.hand[opp_pos] = self.human_player.hand[opp_pos], self.ai_player.hand[my_pos]
                    print(f"AI玩家摸到了 {drawn_card}，用第{my_pos+1}张牌和你的第{opp_pos+1}张牌交换")
            self.discard_pile.append(drawn_card)
        else:
            if action_type.startswith("swap_pos"):
                pos = int(action_type[-1]) - 1
                old_card = self.ai_player.hand[pos]
                self.ai_player.hand[pos] = drawn_card
                self.ai_player.known_cards[pos] = drawn_card
                self.discard_pile.append(old_card)
                print(f"AI玩家摸到了 {drawn_card}，替换了第{pos+1}号位的牌")
                print(f"弃掉了: {old_card}")
            else:
                self.discard_pile.append(drawn_card)
                print(f"AI玩家摸到了 {drawn_card} 并弃掉了")

        print(f"弃牌堆顶: {self.discard_pile[-1]}")
        input("\n按Enter继续...")
        
        if self.cabo_called and self.cabo_caller != self.ai_player:
            return False
        return True

if __name__ == "__main__":
    game = HumanVsAI("cabo_ai_model.pth")
    game.play_game() 
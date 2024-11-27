import random
import os

class Card:
    def __init__(self, number, skill=None):
        self.number = number
        self.skill = skill  # 'Peek' 或 'Swap'

    def __str__(self):
        return f"{self.number}{'(' + self.skill + ')' if self.skill else ''}"

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.known_cards = {}  # 记录自己已知的牌
        self.known_opponent_cards = {}  # 记录已知的对手牌
        self.called_cabo = False

    def peek_card(self, position):
        if 0 <= position < len(self.hand):
            self.known_cards[position] = self.hand[position]
            return self.hand[position]
        return None

    def peek_opponent_card(self, position, opponent_card):
        self.known_opponent_cards[position] = opponent_card
        return opponent_card

    def show_hand(self, reveal_all=False):
        cards = []
        for i, card in enumerate(self.hand):
            if i in self.known_cards or reveal_all:
                cards.append(str(card))
            else:
                cards.append("?")
        return cards

    def show_opponent_cards(self):
        # 返回已知的对手牌信息
        return self.known_opponent_cards

    def total_score(self):
        return sum(card.number for card in self.hand)

class Game:
    def __init__(self):
        self.deck = self.create_deck()
        self.players = [Player("玩家A"), Player("玩家B")]
        self.discard_pile = []
        self.current_player = 0
        self.cabo_called = False
        self.cabo_caller = None

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def create_deck(self):
        deck = []
        # 添加数字牌 (1-5各两张)
        for num in range(1, 5):  # 1-4的数字牌
            for _ in range(2):
                deck.append(Card(num))
        # 添加特殊的5号牌（技能牌）
        deck.append(Card(5, 'Peek'))  # 偷看对手的牌
        deck.append(Card(5, 'Swap'))  # 与对手交换牌
        random.shuffle(deck)
        return deck

    def setup_game(self):
        # 发牌
        for player in self.players:
            for _ in range(2):
                player.hand.append(self.deck.pop())
        
        # 初始偷看
        for i, player in enumerate(self.players):
            self.clear_screen()
            print(f"\n{player.name}的回合 - 初始偷看")
            self.show_game_state(i)
            while True:
                try:
                    pos = int(input(f"{player.name}选择要偷看的牌 (1 或 2): ")) - 1
                    if pos in [0, 1]:
                        break
                    print("请输入1或2")
                except ValueError:
                    print("请输入有效的数字")
            card = player.peek_card(pos)
            print(f"你偷看的牌是: {card}")
            input("\n按Enter继续...")

    def show_game_state(self, player_idx):
        current_player = self.players[player_idx]
        opponent = self.players[1 - player_idx]
        
        print("\n" + "="*50)
        print(f"对手 ({opponent.name}) 的手牌: ", end="")
        # 显示对手的手牌，如果有已知的牌就显示出来
        opponent_cards = []
        for i in range(len(opponent.hand)):
            if i in current_player.known_opponent_cards:
                opponent_cards.append(str(current_player.known_opponent_cards[i]))
            else:
                opponent_cards.append("?")
        print(opponent_cards)
        
        print(f"牌堆剩余: {len(self.deck)} 张")
        print(f"弃牌堆顶: {self.discard_pile[-1] if self.discard_pile else '空'}")
        print(f"你的手牌 ({current_player.name}): {current_player.show_hand()}")
        if self.cabo_called:
            print(f"\n{self.cabo_caller.name}已经呼叫Cabo!")
        print("="*50)

    def get_valid_input(self, prompt, valid_options):
        while True:
            choice = input(prompt)
            if choice in valid_options:
                return choice
            print(f"请输入有效选项: {', '.join(valid_options)}")

    def play_turn(self, player_idx):
        current_player = self.players[player_idx]
        opponent = self.players[1 - player_idx]
        self.clear_screen()
        print(f"\n{current_player.name}的回合:")
        self.show_game_state(player_idx)

        # 选择主要动作：摸牌或呼叫Cabo
        if not self.cabo_called:
            main_action = self.get_valid_input("\n选择行动:\n1. 摸牌\n2. 呼叫Cabo\n请选择: ", ["1", "2"])
            if main_action == "2":
                self.cabo_called = True
                self.cabo_caller = current_player
                print(f"\n{current_player.name}呼叫了Cabo！")
                input("\n按Enter继续...")
                return True  # 继续游戏，让对手还有一次机会
        else:
            main_action = "1"  # 如果已经有人呼叫了Cabo，只能摸牌

        # 摸牌
        drawn_card = self.deck.pop() if self.deck else None
        if not drawn_card:
            print("牌堆已空，游戏结束！")
            return False

        print(f"\n摸到的牌: {drawn_card}")
        
        # 处理摸到的牌
        if drawn_card.skill:
            choice = self.get_valid_input("\n1. 使用技能\n2. 弃掉\n请选择: ", ["1", "2"])
            if choice == "1":
                if drawn_card.skill == "Peek":
                    pos = int(self.get_valid_input("选择要偷看对手的哪张牌 (1 或 2): ", ["1", "2"])) - 1
                    peeked_card = opponent.hand[pos]
                    current_player.peek_opponent_card(pos, peeked_card)
                    print(f"你偷看的对手的牌是: {peeked_card}")
                    input("\n按Enter继续...")
                elif drawn_card.skill == "Swap":
                    my_pos = int(self.get_valid_input("选择要交换的自己的牌位置 (1 或 2): ", ["1", "2"])) - 1
                    opp_pos = int(self.get_valid_input("选择要交换的对手的牌位置 (1 或 2): ", ["1", "2"])) - 1
                    
                    # 交换牌
                    my_card = current_player.hand[my_pos]
                    opp_card = opponent.hand[opp_pos]
                    current_player.hand[my_pos] = opp_card
                    opponent.hand[opp_pos] = my_card
                    
                    # 更新双方的已知牌信息
                    # 如果当前玩家知道自己的牌，交换后仍然知道这张牌（现在在对手那里）
                    if my_pos in current_player.known_cards:
                        current_player.known_opponent_cards[opp_pos] = my_card
                        del current_player.known_cards[my_pos]
                    
                    # 如果对手知道自己的牌，交换后仍然知道这张牌（现在在当前玩家那里）
                    if opp_pos in opponent.known_cards:
                        opponent.known_opponent_cards[my_pos] = opp_card
                        del opponent.known_cards[opp_pos]
                    
                    print("交换完成！")
                    input("\n按Enter继续...")
            self.discard_pile.append(drawn_card)
        else:
            # 普通牌的操作
            choice = self.get_valid_input("\n1. 与手牌交换\n2. 弃掉\n请选择: ", ["1", "2"])
            if choice == "1":
                pos = int(self.get_valid_input("选择要交换的手牌位置 (1 或 2): ", ["1", "2"])) - 1
                old_card = current_player.hand[pos]
                current_player.hand[pos] = drawn_card
                current_player.known_cards[pos] = drawn_card
                self.discard_pile.append(old_card)
                print("交换完成！")
            else:
                self.discard_pile.append(drawn_card)
                print("已弃掉摸到的牌")

        # 更新显示
        self.clear_screen()
        self.show_game_state(player_idx)
        
        # 回合结束提示
        print(f"\n{current_player.name}的回合结束")
        input("\n按Enter继续...")

        # 如果已经有人叫了Cabo，并且对手也完成了最后一回合，游戏结束
        if self.cabo_called and self.cabo_caller != current_player:
            return False

        return True

    def play_game(self):
        self.setup_game()
        game_continue = True
        
        while game_continue and self.deck:
            game_continue = self.play_turn(self.current_player)
            self.current_player = 1 - self.current_player

        # 游戏结束，显示结果
        self.clear_screen()
        print("\n" + "="*20 + " 游戏结束 " + "="*20)
        for player in self.players:
            print(f"\n{player.name}的手牌: {player.show_hand(reveal_all=True)}")
            print(f"{player.name}的手牌点数: {player.total_score()}")

        # 判断胜负和计算最终得分
        if self.cabo_called:
            caller_score = self.cabo_caller.total_score()
            other_player = self.players[1 - self.players.index(self.cabo_caller)]
            other_score = other_player.total_score()
            
            print("\n" + "="*20 + " 最终结果 " + "="*20)
            print(f"\n{self.cabo_caller.name} 呼叫了Cabo!")
            if caller_score <= other_score:
                print(f"{self.cabo_caller.name} 是分数最低的")
                final_caller_score = 0
                final_other_score = other_score
            else:
                print(f"{self.cabo_caller.name} 不是分数最低的")
                final_caller_score = caller_score + 5
                final_other_score = other_score
            
            print(f"\n{self.cabo_caller.name} 最终得分: {final_caller_score}")
            print(f"{other_player.name} 最终得分: {final_other_score}")
        else:
            # 如果是因为牌堆空了而结束
            print("\n" + "="*20 + " 最终结果 " + "="*20)
            print("\n没有人呼叫Cabo，游戏因牌堆耗尽而结束")
            for player in self.players:
                print(f"{player.name} 最终得分: {player.total_score()}")

if __name__ == "__main__":
    game = Game()
    game.play_game() 
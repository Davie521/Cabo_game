from game_cabo import Game, Player, Card
import random

class SmartPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.memory = {}  # 记录所有已知的牌信息，包括弃牌堆

    def decide_peek_initial(self):
        """决定初始要看哪张牌"""
        # 随机选择一张未知的牌
        unknown_positions = [i for i in range(2) if i not in self.known_cards]
        return random.choice(unknown_positions)

    def should_call_cabo(self):
        """决定是否要叫Cabo"""
        # 计算已知牌的总分
        known_sum = 0
        known_count = 0
        for pos, card in self.known_cards.items():
            known_sum += card.number
            known_count += 1
        
        # 如果已知牌的平均分小于等于2，而且至少知道一张牌，就叫Cabo
        if known_count > 0 and (known_sum / known_count) <= 2:
            return True
        return False

    def decide_swap_with_opponent(self, my_known_cards, opponent_known_cards):
        """决定是否要和对手交换牌"""
        # 如果知道自己有一张大牌（4或5），而且知道对手有小牌，就交换
        my_max_pos = None
        my_max_val = -1
        for pos, card in my_known_cards.items():
            if card.number > my_max_val:
                my_max_val = card.number
                my_max_pos = pos

        opp_min_pos = None
        opp_min_val = 6
        for pos, card in opponent_known_cards.items():
            if card.number < opp_min_val:
                opp_min_val = card.number
                opp_min_pos = pos

        if my_max_val >= 4 and opp_min_val <= 2:
            return (my_max_pos, opp_min_pos)
        return None

    def decide_action_for_drawn_card(self, drawn_card, my_known_cards):
        """决定如何处理摸到的牌"""
        if drawn_card.skill:
            return "use" if drawn_card.skill in ["Peek", "Swap"] else "discard"
        
        # 如果摸到的普通牌比已知的某张牌小，就交换
        for pos, card in my_known_cards.items():
            if drawn_card.number < card.number:
                return ("swap", pos)
        return "discard"

class SmartGame(Game):
    def __init__(self):
        self.deck = self.create_deck()
        self.players = [SmartPlayer("智能玩家A"), SmartPlayer("智能玩家B")]
        self.discard_pile = []
        self.current_player = 0
        self.cabo_called = False
        self.cabo_caller = None

    def setup_game(self):
        # 发牌
        for player in self.players:
            for _ in range(2):
                player.hand.append(self.deck.pop())
        
        # AI自主决定初始偷看
        for i, player in enumerate(self.players):
            pos = player.decide_peek_initial()
            card = player.peek_card(pos)
            print(f"{player.name}偷看了第{pos+1}张牌: {card}")

    def play_turn(self, player_idx):
        current_player = self.players[player_idx]
        opponent = self.players[1 - player_idx]

        # AI决策是否叫Cabo
        if not self.cabo_called and current_player.should_call_cabo():
            self.cabo_called = True
            self.cabo_caller = current_player
            print(f"{current_player.name}呼叫了Cabo!")
            return True

        # 摸牌
        drawn_card = self.deck.pop() if self.deck else None
        if not drawn_card:
            return False

        print(f"\n{current_player.name} <- {drawn_card}", end=" ")

        # 处理摸到的牌
        if drawn_card.skill:
            action = current_player.decide_action_for_drawn_card(drawn_card, current_player.known_cards)
            if action == "use":
                if drawn_card.skill == "Peek":
                    unknown_positions = [i for i in range(2) if i not in current_player.known_opponent_cards]
                    if unknown_positions:
                        pos = random.choice(unknown_positions)
                        peeked_card = opponent.hand[pos]
                        current_player.peek_opponent_card(pos, peeked_card)
                        print(f"[偷看对手第{pos+1}张牌]")
                
                elif drawn_card.skill == "Swap":
                    swap_decision = current_player.decide_swap_with_opponent(
                        current_player.known_cards,
                        current_player.known_opponent_cards
                    )
                    if swap_decision:
                        my_pos, opp_pos = swap_decision
                        my_card = current_player.hand[my_pos]
                        opp_card = opponent.hand[opp_pos]
                        current_player.hand[my_pos] = opp_card
                        opponent.hand[opp_pos] = my_card
                        print(f"[交换{my_pos+1}号牌与对手{opp_pos+1}号牌]")
            self.discard_pile.append(drawn_card)
        else:
            action = current_player.decide_action_for_drawn_card(drawn_card, current_player.known_cards)
            if isinstance(action, tuple) and action[0] == "swap":
                pos = action[1]
                old_card = current_player.hand[pos]
                current_player.hand[pos] = drawn_card
                current_player.known_cards[pos] = drawn_card
                self.discard_pile.append(old_card)
                print(f"[替换{pos+1}号牌]")
            else:
                self.discard_pile.append(drawn_card)
                print("[弃牌]")

        if self.cabo_called and self.cabo_caller != current_player:
            return False

        return True

if __name__ == "__main__":
    game = SmartGame()
    game.play_game() 
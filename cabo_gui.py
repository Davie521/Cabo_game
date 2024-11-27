import tkinter as tk
from tkinter import ttk, messagebox
from game_cabo import CaboGame, Player, Card, Deck

class PlayerWindow:
    def __init__(self, player_name, game, is_main=False):
        self.window = tk.Tk() if is_main else tk.Toplevel()
        self.window.title(f"Cabo 游戏 - {player_name}")
        self.player_name = player_name
        self.game = game
        self.drawn_card = None
        self.setup_gui()
        
        # 设置窗口位置
        if player_name == "玩家A":
            self.window.geometry("+100+100")
        else:
            self.window.geometry("+800+100")

    def setup_gui(self):
        # 主框架
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 对手区域
        self.opponent_frame = ttk.LabelFrame(self.main_frame, 
            text=f"对手的手牌", padding="5")
        self.opponent_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.opponent_cards = []
        for i in range(2):
            btn = ttk.Button(self.opponent_frame, text="?", width=10)
            btn.grid(row=0, column=i, padx=5)
            self.opponent_cards.append(btn)

        # 中间区域
        self.middle_frame = ttk.Frame(self.main_frame, padding="5")
        self.middle_frame.grid(row=1, column=0, columnspan=2, pady=20)
        
        self.deck_label = ttk.Label(self.middle_frame, text="牌堆")
        self.deck_label.grid(row=0, column=0, padx=20)
        
        self.discard_label = ttk.Label(self.middle_frame, text="弃牌堆")
        self.discard_label.grid(row=0, column=1, padx=20)

        # 玩家区域
        self.player_frame = ttk.LabelFrame(self.main_frame, 
            text=f"{self.player_name}的手牌", padding="5")
        self.player_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.player_cards = []
        for i in range(2):
            btn = ttk.Button(self.player_frame, text="?", width=10,
                           command=lambda pos=i: self.handle_card_click(pos))
            btn.grid(row=0, column=i, padx=5)
            self.player_cards.append(btn)

        # 操作按钮
        self.action_frame = ttk.Frame(self.main_frame, padding="5")
        self.action_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.draw_btn = ttk.Button(self.action_frame, text="摸牌", 
                                 command=self.draw_card)
        self.draw_btn.grid(row=0, column=0, padx=5)

        self.discard_btn = ttk.Button(self.action_frame, text="弃牌", 
                                    command=self.discard_drawn_card)
        self.discard_btn.grid(row=0, column=1, padx=5)
        
        self.cabo_btn = ttk.Button(self.action_frame, text="呼叫Cabo", 
                                 command=self.call_cabo)
        self.cabo_btn.grid(row=0, column=2, padx=5)

        # 回合提示标签
        self.turn_label = ttk.Label(self.main_frame, text="")
        self.turn_label.grid(row=4, column=0, columnspan=2, pady=5)

        # 初始禁用部分按钮
        self.discard_btn.state(['disabled'])

    def update_display(self):
        player_idx = 0 if self.player_name == "玩家A" else 1
        current_player = self.game.players[player_idx]
        opponent = self.game.players[1 - player_idx]

        # 更新手牌显示
        for i, card in enumerate(current_player.hand):
            if i in current_player.peeked:
                self.player_cards[i]['text'] = str(card)
            else:
                self.player_cards[i]['text'] = "?"

        # 更新对手手牌
        for i, card in enumerate(opponent.hand):
            self.opponent_cards[i]['text'] = "?"

        # 更新牌堆信息
        self.deck_label['text'] = f"牌堆\n({len(self.game.deck.cards)}张)"
        
        # 更新弃牌堆信息
        discard_top = self.game.discard_pile[-1] if self.game.discard_pile else "空"
        self.discard_label['text'] = f"弃牌堆\n{discard_top}"

        # 更新回合提示
        is_my_turn = self.game.current_player_idx == player_idx
        self.turn_label['text'] = "现在是你的回合！" if is_my_turn else "等待对手行动..."
        
        # 更新按钮状态
        if is_my_turn and not self.drawn_card:
            self.draw_btn.state(['!disabled'])
        else:
            self.draw_btn.state(['disabled'])

    def draw_card(self):
        player_idx = 0 if self.player_name == "玩家A" else 1
        if self.game.current_player_idx == player_idx:
            self.drawn_card = self.game.deck.draw_card()
            if self.drawn_card:
                messagebox.showinfo("摸牌", f"你摸到了: {self.drawn_card}\n点击你的手牌可以与摸到的牌交换，或点击弃牌按钮直接弃掉")
                self.draw_btn.state(['disabled'])
                self.discard_btn.state(['!disabled'])
            else:
                messagebox.showinfo("游戏结束", "牌堆已空！")
                self.game.end_game()

    def discard_drawn_card(self):
        if self.drawn_card:
            self.game.discard_pile.append(self.drawn_card)
            self.drawn_card = None
            self.discard_btn.state(['disabled'])
            self.game.current_player_idx = 1 - self.game.current_player_idx
            self.update_display()

    def handle_card_click(self, position):
        player_idx = 0 if self.player_name == "玩家A" else 1
        current_player = self.game.players[player_idx]
        
        if self.drawn_card and self.drawn_card.skill:
            if self.drawn_card.skill == 'Peek':
                current_player.peek_card(position)
                self.discard_drawn_card()
            elif self.drawn_card.skill == 'Swap':
                # TODO: 实现交换逻辑
                pass
        elif self.drawn_card:  # 普通牌的交换逻辑
            # 保存被替换的牌
            replaced_card = current_player.hand[position]
            # 用摸到的牌替换选中的手牌
            current_player.hand[position] = self.drawn_card
            # 将被替换的牌放入弃牌堆
            self.game.discard_pile.append(replaced_card)
            # 清空摸到的牌
            self.drawn_card = None
            # 更新按钮状态
            self.discard_btn.state(['disabled'])
            # 切换玩家
            self.game.current_player_idx = 1 - self.game.current_player_idx
            # 更新显示
            self.update_display()
            messagebox.showinfo("交换完成", "已将摸到的牌与手牌交换")

    def call_cabo(self):
        if messagebox.askyesno("确认", "确定要呼叫Cabo吗？"):
            self.game.end_game()
            self.show_game_result()

    def show_game_result(self):
        result = "游戏结束！\n"
        for player in self.game.players:
            result += f"{player.name}的手牌: {player.show_hand(reveal_all=True)}\n"
            result += f"总分: {player.total_score()}\n"
        messagebox.showinfo("游戏结果", result)
        self.window.quit()

class CaboGUI:
    def __init__(self):
        self.game = CaboGame()
        self.game.setup_game()
        
        # 创建两个玩家窗口
        self.window_a = PlayerWindow("玩家A", self.game, is_main=True)
        self.window_b = PlayerWindow("玩家B", self.game)
        
        # 初始偷看牌的设置
        self.setup_initial_peek()
        
        # 定期更新显示
        self.update_displays()
        
    def setup_initial_peek(self):
        """设置初始偷看牌"""
        def on_peek_a():
            pos = messagebox.askquestion("选择位置", 
                "是否查看第一张牌？\n选择'是'查看第一张，选择'否'查看第二张")
            peek_pos = 0 if pos == 'yes' else 1
            self.game.players[0].peek_card(peek_pos)
            self.window_a.update_display()
            
        def on_peek_b():
            pos = messagebox.askquestion("选择位置", 
                "是否查看第一张牌？\n选择'是'查看第一张，选择'否'查看第二张")
            peek_pos = 0 if pos == 'yes' else 1
            self.game.players[1].peek_card(peek_pos)
            self.window_b.update_display()
            
        messagebox.showinfo("玩家A", "玩家A请选择要偷看的牌")
        on_peek_a()
        messagebox.showinfo("玩家B", "玩家B请选择要偷看的牌")
        on_peek_b()

    def update_displays(self):
        """定期更新两个窗口的显示"""
        self.window_a.update_display()
        self.window_b.update_display()
        self.window_a.window.after(1000, self.update_displays)

if __name__ == "__main__":
    app = CaboGUI()
    app.window_a.window.mainloop() 
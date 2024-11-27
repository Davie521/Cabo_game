calculateFinalScore() {
    // 找到呼叫卡波的玩家
    const callingPlayer = this.players.find(p => p.calledCapo);
    
    // 计算所有玩家的当前分数
    const scores = this.players.map(player => {
        const currentScore = player.calculateScore();
        const cardsSum = player.cards.reduce((sum, card) => sum + card.value, 0);
        
        if (player === callingPlayer) {
            // 检查呼叫卡波的玩家是否分数最少
            const isLowest = this.players.every(p => 
                p === player || p.calculateScore() >= currentScore
            );
            
            // 如果是最低分，只加两张牌的和；否则加5分和两张牌的和
            return currentScore + cardsSum + (isLowest ? 0 : 5);
        } else {
            // 其他玩家加两张牌的和
            return currentScore + cardsSum;
        }
    });

    // 更新玩家分数
    this.players.forEach((player, index) => {
        player.score = scores[index];
    });
} 
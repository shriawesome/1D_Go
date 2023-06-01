import numpy as np
class Alak:
    def __init__(self, verbose=False):
        self.verbose = verbose
    
    def init_board(self):
        self.board = np.array(['x','x','x','x','x','_','_','_','_','o','o','o','o','o'])
    
    def print_board(self):
        print(f"Board : {' '.join(self.board)}")
        print(f"        {' '.join(map(str,list(range(10))+['A','B','C','D']))}")
        
    
    def suicide_move(self, pick, attack):
        l, r = attack-1, attack+1
        lb, rb = False, False
        while l >= 0:
            if self.board[l]!=self.board[pick] and self.board[l]!='_':
                lb = True
                break
            elif self.board[l] == '_':
                return (False,)
            elif pick == l:
                return (False,)
            l -= 1
        while r <= len(self.board)-1:
            if self.board[r]!=self.board[pick] and self.board[r]!='_':
                rb = True
                break
            elif self.board[r] == '_':
                return (False,)
            r -= 1

        if lb and rb:
            return (True, l, r)

        return (False,)
    
    def is_kill(self, pick, attack):
        l, r = attack-1, attack+1
        count_l = count_r = 0
        lb = rb = False
        while l>=0:
            if l == pick:
                lb = True
                l = attack
                break
            elif l!=pick and self.board[l]==self.board[pick]:
                lb = True
                break
            elif self.board[l]=='_':
                break
            count_l+=1
            l-=1

        while r<=len(self.board)-1:
            if r == pick:
                rb = True
                r = attack
                break
            elif r!=pick and self.board[r]==self.board[pick]:
                rb = True
                break
            elif self.board[r]=='_':
                break
            count_r+=1
            r += 1

        if not rb and not lb:
            return (False,)
        elif lb and rb:
            return (True, l, r) if count_l>0 or count_r>0 else (False,)
        elif lb:
            return (True, l, attack) if abs(l-attack)>1 else (False,)
        elif rb:
            return (True, attack, r) if abs(r-attack)>1 else (False,)
    
    def tentative_move(self, pick, attack, encoding):
        new_board = self.board.copy()
        new_board[pick], new_board[attack] = '_', self.board[pick]
        # Check for kill and update accordingly
        kill = self.is_kill(pick, attack)
        if kill[0]:
            l, r = kill[1:]
            new_board[l+1:r]='_'
        new_board[pick], new_board[attack] = '_',self.board[pick]
        x = np.array(np.hstack([self.board, new_board]))
        x[x=='x']=encoding[0]
        x[x=='o']=encoding[1]
        x[x=='_']=encoding[2]
        x = x.astype(float)
        x[x==2]=-1
        return x.reshape(1,-1)
        
    
    def get_model_move(self, model, sym, encoding,threshold=0.8):
        select_pos = np.where(self.board==sym)[0]
        target_pos = np.where(self.board=='_')[0]
        #print(select_pos, target_pos)
        preds=[]
        f_pick, f_attack=0,0
        max_prob = -100
        moves, move=[],[]
        x_test = np.zeros((1,28))
        for pick in select_pos:
            for attack in target_pos:
                kill = self.is_kill(pick, attack)
                if kill[0] or not self.suicide_move(pick, attack)[0]:
                    x_pred = self.tentative_move(pick, attack, encoding)
                    x_test = np.vstack([x_test, x_pred])
                    moves.append((pick, attack))
        x_test = x_test[1:]
        y_pred = model.predict(x_test, verbose=0)
        move_idxs = np.argmax(y_pred, axis=0)
        kill_idx=5
        for i in range(len(move_idxs)-1,-1,-1):
            curr_move_idx = move_idxs[i]
            curr_prob = y_pred[curr_move_idx, kill_idx]
            if curr_prob >= threshold:
                return moves[curr_move_idx]
            if curr_prob>max_prob:
                max_prob = curr_prob
                move = moves[curr_move_idx]
            kill_idx-=1
        return move
                        
        
    def choose_pos(self, symb,interact=False, model=None, allow_suicide=False, encoding=None):
        selec_pos = np.where(self.board==symb)[0]
        # Randomly select a position
        # Your position
        if model:
            pick_pos, attack_pos = self.get_model_move(model, symb, encoding)
            kill = self.is_kill(pick_pos, attack_pos)
            
        else:
            pick_pos = np.random.choice(selec_pos)
            # To play interactively
            if interact:
                print(f'Available pos : {selec_pos}')
                pick_pos = int(input('Select the pos : '))
                while pick_pos not in selec_pos:
                    pick_pos = int(input('Select the pos : '))
            # Target postiion
            target_pos = np.where(self.board=='_')[0]
            attack_pos = np.random.choice(target_pos)
            if interact:
                print(f'Attack pos : {target_pos}')
                attack_pos = int(input('Select the attack pos : '))
                while attack_pos not in target_pos:
                    attack_pos = int(input('Select the attack pos : '))
            # Check for the kill
            kill = self.is_kill(pick_pos, attack_pos)
            if not kill[0] and not allow_suicide:
                while self.suicide_move(pick_pos, attack_pos)[0]:
                    if self.verbose or interact:
                        print(f'{self.map_pos.get(pick_pos, pick_pos)}=>{self.map_pos.get(attack_pos, attack_pos)} is a Suicide Move!!! Select again')
                    if not interact:
                        # Pick Your and target position again
                        pick_pos = np.random.choice(selec_pos)
                        attack_pos = np.random.choice(target_pos)
                    else:
                        # Your position
                        print(f'Available pos : {selec_pos}')
                        pick_pos = int(input('Select the pos : '))
                        while pick_pos not in selec_pos:
                            pick_pos = int(input('Select the pos : '))
                        # Target position
                        print(f'Attack pos : {target_pos}')
                        attack_pos = int(input('Select the attack pos : '))
                        while attack_pos not in target_pos:
                            attack_pos = int(input('Select the attack pos : '))
                    # Again check for the kill
                    kill = self.is_kill(pick_pos, attack_pos)
                    if kill[0]:
                        break
                    
        return pick_pos, attack_pos, kill
                
        
    def play_side(self, symb, interact, model, allow_suicide, encoding):
        # Play the game
        if self.verbose:
            print(f'{symb} : Making a move')
        # Choose pos
        pick_pos, attack_pos, kill = self.choose_pos(symb, interact, model=model,allow_suicide=allow_suicide, encoding=encoding)
        # update the board
        if kill[0]:
            l, r = kill[1:]
            count_kill = np.where(self.board[l+1:r]=="o")[0].shape[0] if symb=='x' else np.where(self.board[l+1:r]=="x")[0].shape[0]
            self.board[l+1:r]='_'
            self.board[pick_pos], self.board[attack_pos] = '_',symb
            if self.verbose:
                print(f'Move {self.map_pos.get(pick_pos, pick_pos)}=>{self.map_pos.get(attack_pos, attack_pos)} was a good move!!!')
                print(f'Kills :{count_kill}')
        elif allow_suicide and self.suicide_move(pick_pos, attack_pos)[0]:
            # Update the board
            _,l,r = self.suicide_move(pick_pos, attack_pos)
            self.board[l+1:r]='_'
            self.board[pick_pos]='_'
            if self.verbose:
                print(f'You played a suicide move removing pieces between {l}, {r}')
            count_kill = -1
        else:
            self.board[pick_pos], self.board[attack_pos] = '_',symb
            count_kill = 0
        if self.verbose:
            print(f"Moving {self.map_pos.get(pick_pos, pick_pos)}=>{self.map_pos.get(attack_pos,attack_pos)}")
            self.print_board()
            
        return count_kill
        
    def game_end(self):
        # Check for the end game
        count_x, count_o = len(np.where(self.board=='x')[0]), len(np.where(self.board=='o')[0])
        if count_x <= 1 or count_o <= 1:
            if self.verbose:
                print('\n\nGame Ended!')
                print('x wins!!!\n\n') if count_x>count_o else print('o wins!!!\n\n')
            return [True, 'x', self.rounds_] if count_x>count_o else [True, 'o', self.rounds_]
        return [False,]
    
        
    def play(self, interact=(False, False) ,model=(None, None), allow_suicide=(False, False), save_data=(False, False)):
        self.init_board()
        # Print the initial Board setup
        if self.verbose:
            self.print_board()
        # Keep count of the rounds
        self.rounds_ = 0
        # Maps indexes greater than 9 to alphabets
        self.map_pos={10:'A', 11:'B', 12:'C', 13:'D'}
        # Saving the data
        data_x = np.zeros((1,29)) if save_data[0] else None
        data_y = np.zeros((1,29)) if save_data[1] else None
        while True:
            # Save initial state
            prev_board = self.board.copy()
            
            # play side 'x' and updates the board
            kills = self.play_side('x', interact[0], model[0], allow_suicide[0],encoding=[1,2,0])
            # Save the data
            if save_data[0] and (kills>0 or self.rounds_ % 5 == 0):
                kills = 0 if kills<0 else kills 
                cur_data = np.hstack([prev_board, self.board,[kills]])
                data_x = np.vstack([data_x, cur_data])
            prev_board = self.board.copy()
            # Check if the game ended
            game_status = self.game_end()
            if game_status[0]:
                if data_x is not None:
                    game_status.append(data_x[1:])
                else:
                    game_status.append([])
                if data_y is not None:
                    game_status.append(data_y[1:])
                else:
                    game_status.append([])
                return game_status[1:]
            
            # play side 'o' and updates the board
            kills = self.play_side('o', interact[1], model[1], allow_suicide[1],encoding=[2,1,0])
            # Save the data
            if save_data[1] and (kills>0 or self.rounds_ % 5 == 0):
                kills = 0 if kills<0 else kills
                cur_data = np.hstack([prev_board, self.board, [kills]])
                data_y = np.vstack([data_y, cur_data])
            prev_board = self.board.copy()
            self.rounds_+=1
            if self.verbose:
                print(f'\nRound: {self.rounds_} Completed!!!\n')
            # Check if the game ended
            game_status = self.game_end()
            if game_status[0]:
                if data_x is not None:
                    game_status.append(data_x[1:])
                else:
                    game_status.append([])
                if data_y is not None:
                    game_status.append(data_y[1:])
                else:
                    game_status.append([])
                return game_status[1:]
                
    def check_cases(self, board, side, pos):
        pick, attack = pos
        self.board = np.array(board)
        # update pick temporarily
        self.board[pick], self.board[attack] = side, '_'

        # Check for the kill and if not kill check for the suicide move
        kill = self.is_kill(pick, attack)
        if kill[0]:
            l, r = kill[1:]
            self.board[l+1:r]='_'
            self.board[pick], self.board[attack] = '_',side
        elif self.suicide_move(pick, attack)[0]:
            self.board[pick]='_'

        return self.board 
                
                
            
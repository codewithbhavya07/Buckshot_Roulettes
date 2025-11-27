import random

# Item effects
ITEMS = {
    'Magnifying Glass': 'Reveal the next shell (live or blank).',
    'Beer': 'Eject the current shell without firing.',
    'Hand Saw': 'If the next shot is live, deal double damage.',
    'Cigarette': 'Recover 1 health (max 3).',
    'Handcuffs': "Skip the opponent's next turn."
}

def hearts(health):
    return '❤️' * max(0, health) #max(0, health) prevents negative repetition

class Player:
    def __init__(self, name):
        self.name = name
        self.health = 3
        self.items = []
        self.skip_turn = False #if True, player's next turn will be skipped (used by Handcuffs).
        self.hand_saw_active = False #whether the Hand Saw effect is active (next live shot deals double damage).

    def is_alive(self):
        return self.health > 0 #Returns True if the player has positive health.

    def take_damage(self, damage=1): #Subtracts damage (default 1) from health. Ensures health doesn’t go below 0.
        self.health -= damage
        if self.health < 0:
            self.health = 0

    def heal(self): #Restores 1 health if health is below the max (3). No return; used by Cigarette item.
        if self.health < 3:
            self.health += 1

    def add_item(self, item): #Appends an item (string) to the items list.
        self.items.append(item)

    def use_item_by_name(self, item_name, game):
        """
        Use item by name if present. Returns True if used, False if not present.
        """
        if item_name not in self.items:
            return False
        idx = self.items.index(item_name) # idx is short name for index
        return self.use_item(idx, game)

    def use_item(self, item_index, game):
        # Pop and execute the item. Return True if used.
        item = self.items.pop(item_index)
        print(f"{self.name} uses {item}!")
        if item == 'Magnifying Glass': 
            if game.shells:
                shell = game.shells[0]
                print(f"The next shell is {'live' if shell == 1 else 'blank'}.")
            else:
                print("No shells left!")
        elif item == 'Beer':
            if game.shells:
                ejected = game.shells.pop(0)
                print(f"Ejected shell was {'live' if ejected == 1 else 'blank'}.")
            else:
                print("No shells left!")
        elif item == 'Hand Saw':
            self.hand_saw_active = True
            print("Hand Saw activated! Next live shot will deal double damage.")
        elif item == 'Cigarette':
            self.heal()
            print(f"{self.name} recovers 1 health. Health: {hearts(self.health)}")
        elif item == 'Handcuffs':
            opponent = game.dealer if self == game.player else game.player
            opponent.skip_turn = True
            print(f"{opponent.name}'s next turn is skipped!")
        return True

class Dealer(Player):
    def __init__(self):
        super().__init__("Dealer")
        self.knows_next = None

    def ai_decide(self, game):
        """
        Decide a single action to perform this turn.
        Possible returns:
          - ('use_item', item_name)
          - 'shoot_self'
          - 'shoot_dealer'  (meaning shoot the player)
        Dealer will not be forced to end their turn by using an item — the caller controls turn progression.
        """
        # Reset knowledge if no shells
        if not game.shells:
            self.knows_next = None

        # Priority rules
        if self.knows_next is None and 'Magnifying Glass' in self.items and game.shells:
            return ('use_item', 'Magnifying Glass')

        if self.health < 3 and 'Cigarette' in self.items:
            return ('use_item', 'Cigarette')

        if self.knows_next is not None:
            if self.knows_next == 1:  # live next
                if 'Hand Saw' in self.items and not self.hand_saw_active:
                    return ('use_item', 'Hand Saw')
                return 'shoot_dealer'
            else:
                return 'shoot_self'

        if 'Beer' in self.items and game.shells and random.random() < 0.18:
            return ('use_item', 'Beer')

        if 'Handcuffs' in self.items and random.random() < 0.25:
            return ('use_item', 'Handcuffs')

        if self.health == 1 and random.random() < 0.30:
            return 'shoot_self'

        return 'shoot_self' if random.random() < 0.55 else 'shoot_dealer'

class Game:
    def __init__(self):
        self.player = Player("You")
        self.dealer = Dealer()
        self.shells = []
        self.round = 1
        self.turn = 'player'  # 'player' or 'dealer'

    def load_shells(self):
        if self.round == 1:
            num_shells = 4
            live = 2
        elif self.round == 2:
            num_shells = 6
            live = 3
        else:  # Round 3+
            num_shells = 8
            live = 5
        blanks = num_shells - live
        self.shells = [1] * live + [0] * blanks
        random.shuffle(self.shells)
        print(f"Round {self.round}: Loaded {num_shells} shells ({live} live, {blanks} blank).")

    def assign_items(self):
        item_list = list(ITEMS.keys())
        # Clear previous items for fairness
        self.player.items = []
        self.dealer.items = []
        if self.round == 1:
            num_items = 0
        elif self.round == 2:
            num_items = 1
        else:
            num_items = 2
        for _ in range(num_items):
            self.player.add_item(random.choice(item_list))
            self.dealer.add_item(random.choice(item_list))
        print(f"You got items: {self.player.items}")
        print(f"Dealer got items: {self.dealer.items}")

    def shoot(self, shooter, target):
        if not self.shells:
            print("No shells left!")
            return
        shell = self.shells.pop(0)
        damage = 1
        if shooter.hand_saw_active and shell == 1:
            damage = 2
            shooter.hand_saw_active = False
        if shell == 1:
            target.take_damage(damage)
            print(f"Live shell! {target.name} takes {damage} damage. Health: {hearts(target.health)}")
            # After a live hit, switch turn
            self.switch_turn()
        else:
            print("Blank shell! No damage.")
            # Shooting self with blank keeps turn (explicit message)
            if target == shooter:
                print("Blank — shooter keeps the gun.")
                # keep turn
            else:
                self.switch_turn()

    def switch_turn(self):
        self.turn = 'dealer' if self.turn == 'player' else 'player'

    def play_turn(self):
        current = self.player if self.turn == 'player' else self.dealer

        if current.skip_turn:
            print(f"{current.name}'s turn is skipped due to Handcuffs!")
            current.skip_turn = False
            self.switch_turn()
            return

        # PLAYER TURN
        if current == self.player:
            print(f"\nYour turn. Health: {hearts(self.player.health)} | Dealer Health: {hearts(self.dealer.health)}")
            print(f"Shells left: {len(self.shells)}")
            if self.player.items:
                print("Your items:")
                for i, item in enumerate(self.player.items):
                    print(f"{i+1}. {item}: {ITEMS[item]}")
                choice = input("Choose: 1. Use item  2. Shoot self  3. Shoot dealer\n").strip()
                if choice == '1' and self.player.items:
                    try:
                        item_choice = int(input("Choose item number: ")) - 1
                    except ValueError:
                        print("Invalid input. Please enter a number.")
                        # do NOT change turn on invalid input; let player act again
                        return
                    if 0 <= item_choice < len(self.player.items):
                        # Player uses item, but TURN REMAINS THE SAME (per your rule)
                        self.player.use_item(item_choice, self)
                        # Note: do NOT call self.switch_turn() here
                    else:
                        print("Invalid choice.")
                elif choice == '2':
                    self.shoot(self.player, self.player)
                elif choice == '3':
                    self.shoot(self.player, self.dealer)
                else:
                    print("Invalid choice.")
            else:
                # No items
                choice = input("Choose: 1. Shoot self  2. Shoot dealer\n").strip()
                if choice == '1':
                    self.shoot(self.player, self.player)
                elif choice == '2':
                    self.shoot(self.player, self.dealer)
                else:
                    print("Invalid choice.")

        # DEALER TURN
        else:
            print(f"\nDealer's turn. Health: {hearts(self.dealer.health)} | Your Health: {hearts(self.player.health)}")
            decision = self.dealer.ai_decide(self)

            # If dealer decided to use an item, execute it and DO NOT automatically end dealer's turn
            if isinstance(decision, tuple) and decision[0] == 'use_item':
                item_name = decision[1]
                used = self.dealer.use_item_by_name(item_name, self)
                if used and item_name == 'Magnifying Glass':
                    self.dealer.knows_next = self.shells[0] if self.shells else None
                # IMPORTANT: do NOT switch turn here — dealer keeps the turn after using an item
                # This allows dealer to act again (use another item or decide to shoot)
            elif decision == 'shoot_self':
                print("Dealer shoots themselves.")
                self.shoot(self.dealer, self.dealer)
            elif decision == 'shoot_dealer':
                print("Dealer shoots you.")
                self.shoot(self.dealer, self.player)
            else:
                # Fallback: random shot
                if random.random() < 0.5:
                    print("Dealer (fallback) shoots themselves.")
                    self.shoot(self.dealer, self.dealer)
                else:
                    print("Dealer (fallback) shoots you.")
                    self.shoot(self.dealer, self.player)

        print("\n" + "="*50 + "\n")  # Separator after each turn

    def play_round(self):
        # Reset per-round state
        self.turn = 'player'  # player starts every round
        self.dealer.knows_next = None
        self.player.hand_saw_active = False
        self.dealer.hand_saw_active = False

        print(f"\nStarting Round {self.round}!")
        self.load_shells()
        self.assign_items()
        while self.shells and self.player.is_alive() and self.dealer.is_alive():
            self.play_turn()

        if not self.player.is_alive():
            print("You lose!")
            return False
        elif not self.dealer.is_alive():
            print("You win!")
            return False
        else:
            print("Round over, both alive. Next round!")
            self.round += 1
            return True

    def play_game(self):
        print("Welcome to Buckshot Roulette!")
        print("You vs Dealer. Survive the shots!")
        while self.player.is_alive() and self.dealer.is_alive():
            if not self.play_round():
                break
        print("Game Over.")

if __name__ == "__main__":
    game = Game()
    game.play_game()

# Final this code no bugs


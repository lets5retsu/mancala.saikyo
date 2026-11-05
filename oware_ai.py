"""
Oware (Abapa-style) starter engine and search CPU.

Assumed rules:
- 2 players, 6 pits each, 4 seeds per pit at the start.
- Sow counter-clockwise through all 12 pits, skipping the starting pit
  when a move contains more than one full circuit.
- Capture 2 or 3 seeds from the opponent's side, moving backwards from
  the last pit; continue while the next pit also contains 2 or 3.
- A grand slam (capturing every seed on the opponent's side) is forbidden.
- If the opponent's side is empty, a move must feed it if possible.
- If a player cannot make a legal move, the game ends and the player
  who still has seeds collects the remaining seeds.
- 25 seeds wins; 24-24 is a draw. Repetition is treated as a draw
  in the search path.

This is a playable/searchable baseline, not a claim of solved optimal play.
"""

from dataclasses import dataclass
from math import inf
from typing import List, Optional, Tuple, Dict

Move = int  # pit index 0..5, relative to the player to move


@dataclass(frozen=True)
class State:
    board: Tuple[int, ...]   # pits 0..5 = P0, 6..11 = P1
    scores: Tuple[int, int]  # captured seeds
    turn: int                 # 0 or 1


def initial_state(seeds_per_pit: int = 4) -> State:
    return State((seeds_per_pit,) * 12, (0, 0), 0)


def side_indices(player: int) -> range:
    return range(0, 6) if player == 0 else range(6, 12)


def opponent(player: int) -> int:
    return 1 - player


def side_seed_count(board: Tuple[int, ...], player: int) -> int:
    return sum(board[i] for i in side_indices(player))


def _sow(board: Tuple[int, ...], player: int, pit: int):
    """Return board after sowing and the absolute index of the last seed."""
    b = list(board)
    start = (0 if player == 0 else 6) + pit
    seeds = b[start]
    if seeds <= 0:
        raise ValueError("Cannot play an empty pit")
    b[start] = 0
    pos = start
    while seeds:
        pos = (pos + 1) % 12
        if pos == start:
            continue
        b[pos] += 1
        seeds -= 1
    return b, pos


def apply_move(state: State, move: Move) -> State:
    if move not in legal_moves(state):
        raise ValueError(f"Illegal move: {move}")
    player = state.turn
    start = (0 if player == 0 else 6) + move
    b, last = _sow(state.board, player, move)
    gained = 0

    # Capture backwards only while landing on the opponent's side.
    if (6 <= last <= 11 if player == 0 else 0 <= last <= 5):
        opp_before_capture = sum(b[i] for i in side_indices(1 - player))
        captured_pits = []
        pos = last
        while (6 <= pos <= 11 if player == 0 else 0 <= pos <= 5) and b[pos] in (2, 3):
            captured_pits.append(pos)
            pos = (pos - 1) % 12
        possible = sum(b[i] for i in captured_pits)
        # Grand slam is forbidden: do not capture if it takes all opposing seeds.
        if possible < opp_before_capture:
            for i in captured_pits:
                gained += b[i]
                b[i] = 0

    scores = list(state.scores)
    scores[player] += gained
    return State(tuple(b), tuple(scores), 1 - player)


def _raw_moves(state: State) -> List[Move]:
    base = 0 if state.turn == 0 else 6
    return [i for i in range(6) if state.board[base + i] > 0]


def legal_moves(state: State) -> List[Move]:
    moves = _raw_moves(state)
    if not moves:
        return []

    # Feeding rule: if the opponent has no seeds, prefer/require a move
    # that leaves at least one seed on their side after sowing/capturing.
    other = 1 - state.turn
    if side_seed_count(state.board, other) == 0:
        feeding = []
        for move in moves:
            nxt = _apply_unchecked(state, move)
            if side_seed_count(nxt.board, other) > 0:
                feeding.append(move)
        # If no move can feed the empty side, the game ends: no legal move.
        return feeding
    return moves


def _apply_unchecked(state: State, move: Move) -> State:
    """Internal move application; avoids legal_moves recursion."""
    player = state.turn
    b, last = _sow(state.board, player, move)
    gained = 0
    is_opponent_pit = (6 <= last <= 11) if player == 0 else (0 <= last <= 5)
    if is_opponent_pit:
        opp_total = sum(b[i] for i in side_indices(1 - player))
        captured = []
        pos = last
        while ((6 <= pos <= 11) if player == 0 else (0 <= pos <= 5)) and b[pos] in (2, 3):
            captured.append(pos)
            pos = (pos - 1) % 12
        amount = sum(b[i] for i in captured)
        if amount < opp_total:  # no grand slam
            for i in captured:
                gained += b[i]
                b[i] = 0
    scores = list(state.scores)
    scores[player] += gained
    return State(tuple(b), tuple(scores), 1 - player)


def is_terminal(state: State) -> bool:
    if state.scores[0] >= 25 or state.scores[1] >= 25:
        return True
    return len(legal_moves(state)) == 0


def final_state(state: State) -> State:
    """Collect remaining seeds if the game has ended."""
    if not is_terminal(state):
        return state
    # Reaching 25 ends the game immediately; do not sweep the board.
    if state.scores[0] >= 25 or state.scores[1] >= 25:
        return state
    scores = list(state.scores)
    # If play stops because no legal move exists, award the remaining
    # seeds to the player who owns each side.
    remaining0 = sum(state.board[0:6])
    remaining1 = sum(state.board[6:12])
    scores[0] += remaining0
    scores[1] += remaining1
    return State((0,) * 12, tuple(scores), state.turn)


def outcome(state: State) -> str:
    end = final_state(state)
    if end.scores[0] > end.scores[1]:
        return "Player 0 wins"
    if end.scores[1] > end.scores[0]:
        return "Player 1 wins"
    return "Draw"


def evaluate(state: State, root: int) -> float:
    """Heuristic evaluation from root player's perspective."""
    if is_terminal(state):
        end = final_state(state)
        return (end.scores[root] - end.scores[1 - root]) * 10000

    score_diff = state.scores[root] - state.scores[1 - root]
    own = side_seed_count(state.board, root)
    opp = side_seed_count(state.board, 1 - root)
    # Small positional terms; terminal score remains dominant.
    mobility = len(legal_moves(state)) if state.turn == root else 0
    return score_diff * 120 + (own - opp) * 1.5 + mobility * 0.2


def position_key(state: State):
    return state.board, state.scores, state.turn


def choose_move(state: State, max_depth: int = 8) -> Optional[Move]:
    """
    Iterative-deepening alpha-beta CPU.
    Increase max_depth for stronger but slower play.
    """
    moves = legal_moves(state)
    if not moves:
        return None
    root = state.turn
    best_move = moves[0]

    # Move ordering: test each move and prioritize immediate score gains.
    def ordered_moves(s: State):
        scored = []
        for m in legal_moves(s):
            nxt = _apply_unchecked(s, m)
            gain = nxt.scores[s.turn] - s.scores[s.turn]
            scored.append((gain, m))
        return [m for _, m in sorted(scored, reverse=True)]

    for depth in range(1, max_depth + 1):
        alpha, beta = -inf, inf
        current_best = best_move
        best_value = -inf
        for move in ordered_moves(state):
            child = _apply_unchecked(state, move)
            value = _alphabeta(child, depth - 1, alpha, beta, root, -1, {}, 0)
            if value > best_value:
                best_value, current_best = value, move
            alpha = max(alpha, best_value)
        best_move = current_best
    return best_move


def _alphabeta(state: State, depth: int, alpha: float, beta: float,
               root: int, _unused: int, path: Dict[tuple, int], ply: int) -> float:
    if is_terminal(state):
        end = final_state(state)
        return (end.scores[root] - end.scores[1 - root]) * 10000
    if depth <= 0:
        return evaluate(state, root)

    key = position_key(state)
    count = path.get(key, 0)
    if count >= 2:
        return evaluate(state, root) * 0.25  # discourage cycling; approximate draw

    path[key] = count + 1
    maximizing = state.turn == root
    moves = legal_moves(state)

    def order(m):
        nxt = _apply_unchecked(state, m)
        return nxt.scores[state.turn] - state.scores[state.turn]

    moves.sort(key=order, reverse=True)
    if maximizing:
        value = -inf
        for move in moves:
            child = _apply_unchecked(state, move)
            value = max(value, _alphabeta(child, depth - 1, alpha, beta,
                                          root, 0, path, ply + 1))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = inf
        for move in moves:
            child = _apply_unchecked(state, move)
            value = min(value, _alphabeta(child, depth - 1, alpha, beta,
                                          root, 0, path, ply + 1))
            beta = min(beta, value)
            if alpha >= beta:
                break
    if count:
        path[key] = count
    else:
        path.pop(key, None)
    return value


def print_board(state: State) -> None:
    b = state.board
    print("          Opponent (P1)" if state.turn == 0 else "          Opponent (P0)")
    print("       ", " ".join(f"{b[i]:2d}" for i in range(11, 5, -1)))
    print(f"Score P1: {state.scores[1]:2d}", " " * 14, f"Score P0: {state.scores[0]:2d}")
    print("       ", " ".join(f"{b[i]:2d}" for i in range(0, 6)))
    print("          You (P0)" if state.turn == 0 else "          You (P1)")
    print("Pit numbers:  1  2  3  4  5  6")


def play_human_vs_cpu(depth: int = 8, human_player: int = 0) -> None:
    state = initial_state(4)
    while not is_terminal(state):
        print_board(state)
        moves = legal_moves(state)
        if state.turn == human_player:
            print("Legal pits:", [m + 1 for m in moves])
            try:
                move = int(input("Choose a pit (1-6): ")) - 1
            except (ValueError, EOFError):
                print("Please enter a number from 1 to 6.")
                continue
            if move not in moves:
                print("That move is not legal.")
                continue
        else:
            move = choose_move(state, depth)
            print(f"CPU chooses pit {move + 1}")
        state = apply_move(state, move)

    end = final_state(state)
    print_board(end)
    print("Final score:", end.scores, "-", outcome(state))


if __name__ == "__main__":
    print("Oware CPU baseline. Human = Player 0, CPU = Player 1.")
    play_human_vs_cpu(depth=8, human_player=0)

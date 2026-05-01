"""
Wumpus World Environment and Knowledge-Based Agent
"""

import random
from logic_engine import KnowledgeBase


def get_adjacent(r, c, rows, cols):
    adj = []
    if r > 0:         adj.append((r-1, c))
    if r < rows - 1:  adj.append((r+1, c))
    if c > 0:         adj.append((r, c-1))
    if c < cols - 1:  adj.append((r, c+1))
    return adj


def cell_id(r, c):
    return f"{r}_{c}"


class WumpusWorld:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.pits = set()
        self.wumpus = None
        self.gold = None
        self._generate()

    def _generate(self):
        all_cells = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if not (r == 0 and c == 0)]

        # Pits (~15% chance each non-start cell)
        for r, c in all_cells:
            if random.random() < 0.15:
                self.pits.add(cell_id(r, c))

        # Wumpus: random non-start, non-pit cell
        safe_cells = [(r, c) for r, c in all_cells if cell_id(r, c) not in self.pits]
        if safe_cells:
            wr, wc = random.choice(safe_cells)
            self.wumpus = (wr, wc)
            safe_cells.remove((wr, wc))

        # Gold: random remaining safe cell
        if safe_cells:
            self.gold = random.choice(safe_cells)

    def compute_percepts(self, r, c):
        adj = get_adjacent(r, c, self.rows, self.cols)
        breeze  = any(cell_id(ar, ac) in self.pits for ar, ac in adj)
        stench  = self.wumpus is not None and any(
            (ar, ac) == self.wumpus for ar, ac in adj)
        glitter = self.gold is not None and self.gold == (r, c)
        in_pit  = cell_id(r, c) in self.pits
        wumpus_here = self.wumpus is not None and self.wumpus == (r, c)
        return {
            "breeze": breeze,
            "stench": stench,
            "glitter": glitter,
            "in_pit": in_pit,
            "wumpus_here": wumpus_here
        }

    def to_dict(self, reveal=False):
        return {
            "rows": self.rows,
            "cols": self.cols,
            "pits": list(self.pits) if reveal else [],
            "wumpus": list(self.wumpus) if (reveal and self.wumpus) else None,
            "gold": list(self.gold) if (reveal and self.gold) else None,
        }


class Agent:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.r = 0
        self.c = 0
        self.visited = set()
        self.cell_status = {cell_id(0, 0): "safe"}
        self.kb = KnowledgeBase(rows, cols)
        self.path = [(0, 0)]
        self.alive = True
        self.won = False
        self.stuck = False
        self.current_percepts = "None"
        self.agent_log = ["🤖 Agent spawned at [0,0]. Exploration started."]
        self.step_count = 0

    def step(self, world):
        if not self.alive or self.won or self.stuck:
            return self._state(world)

        self.step_count += 1
        percepts = world.compute_percepts(self.r, self.c)

        # Check death
        if percepts["in_pit"]:
            self.alive = False
            self.agent_log.append(f"💀 Fell into a pit at [{self.r},{self.c}]!")
            return self._state(world, reveal=True)

        if percepts["wumpus_here"]:
            self.alive = False
            self.agent_log.append(f"💀 Eaten by the Wumpus at [{self.r},{self.c}]!")
            return self._state(world, reveal=True)

        if percepts["glitter"]:
            self.won = True
            self.agent_log.append(f"🏆 Gold grabbed at [{self.r},{self.c}]! Mission complete!")
            return self._state(world, reveal=True)

        # Tell KB
        adj = get_adjacent(self.r, self.c, self.rows, self.cols)
        self.kb.tell_percepts(self.r, self.c, percepts, adj)

        # Mark visited and safe
        self.visited.add(cell_id(self.r, self.c))
        self.cell_status[cell_id(self.r, self.c)] = "safe"

        # Build percept string
        perc_list = []
        if percepts["breeze"]:  perc_list.append("Breeze")
        if percepts["stench"]:  perc_list.append("Stench")
        if percepts["glitter"]: perc_list.append("Glitter")
        self.current_percepts = ", ".join(perc_list) if perc_list else "None"

        # Frontier: unvisited adjacent
        frontier = [(ar, ac) for ar, ac in adj if cell_id(ar, ac) not in self.visited]

        best_next = None
        for ar, ac in frontier:
            cid = cell_id(ar, ac)
            if self.cell_status.get(cid) == "safe":
                best_next = (ar, ac)
                break
            result = self.kb.ask_safe(ar, ac)
            if result["safe"]:
                self.cell_status[cid] = "safe"
                if best_next is None:
                    best_next = (ar, ac)
            else:
                if not result["pit_safe"] and not result["wump_safe"]:
                    self.cell_status[cid] = "danger"
                else:
                    self.cell_status[cid] = "unknown"

        # Backtrack if no safe frontier
        if best_next is None:
            visited_adj = [(ar, ac) for ar, ac in adj if cell_id(ar, ac) in self.visited]
            if visited_adj:
                best_next = visited_adj[0]
            else:
                self.stuck = True
                self.agent_log.append(f"🔒 Agent stuck at [{self.r},{self.c}] — no safe moves.")
                return self._state(world)

        nr, nc = best_next
        self.agent_log.append(
            f"Step {self.step_count}: [{self.r},{self.c}] percepts=[{self.current_percepts}] "
            f"→ moving to [{nr},{nc}] | KB inferences: {self.kb.total_inferences}"
        )
        self.r, self.c = nr, nc
        self.path.append((nr, nc))
        return self._state(world)

    def _state(self, world, reveal=False):
        reveal_now = reveal or not self.alive or self.won
        return {
            "agent": {
                "r": self.r,
                "c": self.c,
                "alive": self.alive,
                "won": self.won,
                "stuck": self.stuck,
                "step_count": self.step_count,
                "current_percepts": self.current_percepts,
                "path": self.path,
                "cell_status": self.cell_status,
                "visited": list(self.visited),
                "agent_log": self.agent_log[-50:],
            },
            "kb": self.kb.to_dict(),
            "world": world.to_dict(reveal=reveal_now),
        }

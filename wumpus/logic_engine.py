"""
Propositional Logic Resolution Engine
Implements CNF conversion, TELL/ASK KB, and Resolution Refutation
for the Wumpus World Knowledge-Based Agent.
"""

from itertools import combinations


# ─────────────────────────────────────────────
#  LITERAL & CLAUSE UTILITIES
# ─────────────────────────────────────────────

def make_lit(name, negated=False):
    return {"name": name, "negated": negated}

def lit_str(lit):
    return ("¬" if lit["negated"] else "") + lit["name"]

def negate_lit(lit):
    return {"name": lit["name"], "negated": not lit["negated"]}

def clause_str(clause):
    if not clause:
        return "⊥"
    return " ∨ ".join(lit_str(l) for l in clause)

def clause_key(clause):
    return ",".join(sorted(lit_str(l) for l in clause))

def clauses_equal(c1, c2):
    return clause_key(c1) == clause_key(c2)

def is_tautology(clause):
    names = {}
    for lit in clause:
        if lit["name"] in names:
            if names[lit["name"]] != lit["negated"]:
                return True
        else:
            names[lit["name"]] = lit["negated"]
    return False


# ─────────────────────────────────────────────
#  RESOLUTION
# ─────────────────────────────────────────────

def resolve_clauses(c1, c2, lit_name):
    """Try resolving c1 and c2 on lit_name. Returns resolvent or None."""
    pos_in_c1 = any(l["name"] == lit_name and not l["negated"] for l in c1)
    neg_in_c1 = any(l["name"] == lit_name and l["negated"] for l in c1)
    pos_in_c2 = any(l["name"] == lit_name and not l["negated"] for l in c2)
    neg_in_c2 = any(l["name"] == lit_name and l["negated"] for l in c2)

    if not ((pos_in_c1 and neg_in_c2) or (neg_in_c1 and pos_in_c2)):
        return None

    seen = set()
    merged = []
    for lit in c1 + c2:
        if lit["name"] == lit_name:
            continue
        key = lit_str(lit)
        if key not in seen:
            seen.add(key)
            merged.append(lit)

    if is_tautology(merged):
        return None

    return merged


def resolution_refutation(kb_clauses, query_clauses, max_iter=500):
    """
    Prove KB |= alpha by showing KB ∪ {¬alpha} is unsatisfiable.
    query_clauses = CNF of the NEGATED goal.
    Returns dict: {proved, steps, inference_count}
    """
    clauses = [list(c) for c in kb_clauses] + [list(c) for c in query_clauses]
    clause_set = set(clause_key(c) for c in clauses)
    steps = []
    inference_count = 0

    for _ in range(max_iter):
        new_clauses = []
        pairs = list(combinations(range(len(clauses)), 2))

        for i, j in pairs:
            c1, c2 = clauses[i], clauses[j]
            lit_names = set(l["name"] for l in c1 + c2)

            for name in lit_names:
                resolvent = resolve_clauses(c1, c2, name)
                if resolvent is None:
                    continue

                inference_count += 1
                step = {
                    "c1": clause_str(c1),
                    "c2": clause_str(c2),
                    "on": name,
                    "result": clause_str(resolvent)
                }
                steps.append(step)

                if len(resolvent) == 0:
                    return {"proved": True, "steps": steps, "inference_count": inference_count}

                key = clause_key(resolvent)
                if key not in clause_set:
                    clause_set.add(key)
                    new_clauses.append(resolvent)

        if not new_clauses:
            return {"proved": False, "steps": steps, "inference_count": inference_count}

        clauses.extend(new_clauses)

    return {"proved": False, "steps": steps, "inference_count": inference_count}


# ─────────────────────────────────────────────
#  CNF RULE BUILDERS
# ─────────────────────────────────────────────

def breeze_rule_cnf(b_name, pit_names):
    """B ⟺ (P1 ∨ P2 ∨ ...) in CNF"""
    clauses = []
    # ¬B ∨ P1 ∨ P2 ∨ ...
    clauses.append([make_lit(b_name, True)] + [make_lit(p) for p in pit_names])
    # For each Pi: ¬Pi ∨ B
    for p in pit_names:
        clauses.append([make_lit(p, True), make_lit(b_name)])
    return clauses

def stench_rule_cnf(s_name, wumpus_names):
    """S ⟺ (W1 ∨ W2 ∨ ...) in CNF"""
    clauses = []
    clauses.append([make_lit(s_name, True)] + [make_lit(w) for w in wumpus_names])
    for w in wumpus_names:
        clauses.append([make_lit(w, True), make_lit(s_name)])
    return clauses


# ─────────────────────────────────────────────
#  KNOWLEDGE BASE
# ─────────────────────────────────────────────

class KnowledgeBase:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.clauses = []
        self.clause_keys = set()
        self.total_inferences = 0
        self.log = []

        # Start cell [0,0] is always safe
        self._tell([make_lit(f"P_0_0", True)])
        self._tell([make_lit(f"W_0_0", True)])

    def _tell(self, clause):
        key = clause_key(clause)
        if key not in self.clause_keys:
            self.clause_keys.add(key)
            self.clauses.append(clause)

    def tell_percepts(self, r, c, percepts, adj_cells):
        b_name = f"B_{r}_{c}"
        s_name = f"S_{r}_{c}"
        adj_pit_names  = [f"P_{ar}_{ac}" for ar, ac in adj_cells]
        adj_wump_names = [f"W_{ar}_{ac}" for ar, ac in adj_cells]

        # Assert breeze fact
        if percepts["breeze"]:
            self._tell([make_lit(b_name)])
            self.log.append(f"TELL: {b_name} (breeze at [{r},{c}])")
        else:
            self._tell([make_lit(b_name, True)])
            self.log.append(f"TELL: ¬{b_name} (no breeze at [{r},{c}])")
            for ar, ac in adj_cells:
                self._tell([make_lit(f"P_{ar}_{ac}", True)])
                self.log.append(f"TELL: ¬P_{ar}_{ac} → safe from pit")

        # Assert stench fact
        if percepts["stench"]:
            self._tell([make_lit(s_name)])
            self.log.append(f"TELL: {s_name} (stench at [{r},{c}])")
        else:
            self._tell([make_lit(s_name, True)])
            self.log.append(f"TELL: ¬{s_name} (no stench at [{r},{c}])")
            for ar, ac in adj_cells:
                self._tell([make_lit(f"W_{ar}_{ac}", True)])
                self.log.append(f"TELL: ¬W_{ar}_{ac} → safe from wumpus")

        # Add biconditional rules in CNF
        if adj_pit_names:
            for clause in breeze_rule_cnf(b_name, adj_pit_names):
                self._tell(clause)
        if adj_wump_names:
            for clause in stench_rule_cnf(s_name, adj_wump_names):
                self._tell(clause)

    def ask_safe(self, r, c):
        """Ask if cell [r,c] is safe. Uses resolution refutation."""
        # Prove ¬P_r_c: assume P_r_c, find contradiction
        pit_result = resolution_refutation(
            self.clauses, [[make_lit(f"P_{r}_{c}")]]
        )
        # Prove ¬W_r_c: assume W_r_c, find contradiction
        wump_result = resolution_refutation(
            self.clauses, [[make_lit(f"W_{r}_{c}")]]
        )

        inferences = pit_result["inference_count"] + wump_result["inference_count"]
        self.total_inferences += inferences

        pit_safe  = pit_result["proved"]
        wump_safe = wump_result["proved"]

        self.log.append(
            f"ASK [{r},{c}]: Pit={'SAFE' if pit_safe else 'UNKNOWN'} "
            f"Wumpus={'SAFE' if wump_safe else 'UNKNOWN'} "
            f"({inferences} inferences)"
        )

        return {
            "safe": pit_safe and wump_safe,
            "pit_safe": pit_safe,
            "wump_safe": wump_safe,
            "pit_steps": pit_result["steps"],
            "wump_steps": wump_result["steps"],
            "inferences": inferences
        }

    def to_dict(self):
        return {
            "clauses": [clause_str(c) for c in self.clauses],
            "total_inferences": self.total_inferences,
            "log": self.log[-60:]  # last 60 entries
        }

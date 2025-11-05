from dataclasses import dataclass

@dataclass(frozen=True)
class Triple:
    s: str
    p: str
    o: str

class GraphBuffer:
    def __init__(self):
        self.triples = []

    def add(self, s, p, o):
        self.triples.append(Triple(s, p, o))

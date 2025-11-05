from .evaluator import eval_value
from .ids import NodeFactory

class RuleExecutor:
    def __init__(self, mapping):
        self.mapping = mapping
        self.ids = NodeFactory(mapping.id_subject_template)

    def applies(self, rule, row):
        return all(col in row for col in rule.when_columns)

    def run_rule(self, rule, row, row_idx, graph):
        subj = self.ids.subject(rule.subject, row, row_idx)
        for p, o in rule.triples:
            p_eval = eval_value(p, row, self.mapping.prefixes) if isinstance(p, dict) else p
            o_eval = eval_value(o, row, self.mapping.prefixes) if isinstance(o, dict) else o
            graph.add(subj, p_eval, o_eval)

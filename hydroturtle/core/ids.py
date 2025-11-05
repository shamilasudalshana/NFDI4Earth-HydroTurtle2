class NodeFactory:
    def __init__(self, default_subject_template: str):
        self.default_tpl = default_subject_template

    def subject(self, tpl: str | None, row: dict, row_index: int):
        template = tpl or self.default_tpl
        return template.format(rowIndex=row_index, **row)

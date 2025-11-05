def _pretty_bnode(o: str, indent: str = "\t") -> str:
    core = o.strip()
    if not (core.startswith("[") and core.endswith("]")):
        return o
    inner = core[1:-1].strip()
    parts = [p.strip() for p in inner.split(" ; ")] if inner else []
    lines = []
    for idx, part in enumerate(parts):
        # swap "rdf:type " → "a " inside bnodes for readability
        if part.startswith("rdf:type "):
            part = "a " + part[len("rdf:type "):]
        suffix = " ;" if idx < len(parts) - 1 else ""
        lines.append(indent + part + suffix)
    return "[\n" + "\n".join(lines) + "\n]"

def _p_shorthand(p: str) -> str:
    return "a" if p == "rdf:type" else p

def write_turtle(triples_by_subject, prefixes, path):
    with open(path, "w", encoding="utf-8") as out:
        for k, v in prefixes.items():
            out.write(f"@prefix {k}: <{v}> .\n")
        out.write("\n")
        for s, pos in triples_by_subject.items():
            out.write(f"{s} ")
            for j, (p, o) in enumerate(pos):
                p_fmt = _p_shorthand(p)
                o_fmt = _pretty_bnode(o)
                end = " .\n" if j == len(pos)-1 else " ;\n\t"
                out.write(f"{p_fmt} {o_fmt}{end}")

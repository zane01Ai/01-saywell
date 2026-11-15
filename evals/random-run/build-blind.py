"""Build anonymous A/B pairs from two locally supplied output files."""

import argparse
import json
import random
import re
from pathlib import Path


def parse(path):
    parts = re.split(r"^## 【S(\d+)】[ \t]*$", Path(path).read_text(encoding="utf-8"), flags=re.M)
    records = {}
    for index in range(1, len(parts), 2):
        sample_id = f"{int(parts[index]):02d}"
        body = parts[index + 1].strip()
        if sample_id in records:
            raise ValueError(f"duplicate sample ID: {sample_id}")
        if not body:
            raise ValueError(f"empty sample: {sample_id}")
        records[sample_id] = body
    if not records:
        raise ValueError("no samples found; expected headings such as ## 【S01】")
    return records


def build(a_path, b_path, seed):
    a, b = parse(a_path), parse(b_path)
    if a.keys() != b.keys():
        raise ValueError(f"unpaired IDs: only A={sorted(a.keys() - b.keys())}, only B={sorted(b.keys() - a.keys())}")
    rng = random.Random(seed)
    sections, answers = [], {}
    for sample_id in sorted(a, key=int):
        pair = [("A", a[sample_id]), ("B", b[sample_id])]
        rng.shuffle(pair)
        sections.append(f"### 第 {int(sample_id)} 组\n\n**甲**\n\n{pair[0][1]}\n\n**乙**\n\n{pair[1][1]}")
        answers[sample_id] = {"甲": pair[0][0], "乙": pair[1][0]}
    return "\n\n---\n\n".join(sections) + "\n", answers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a", type=Path, required=True, help="outputs with Skill")
    parser.add_argument("--b", type=Path, required=True, help="outputs without Skill")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261113)
    args = parser.parse_args()
    try:
        body, answers = build(args.a, args.b, args.seed)
        outputs = [args.out_dir / "blind-package.md", args.out_dir / "answer-key.json"]
        if any(path.exists() for path in outputs):
            raise ValueError("output files already exist; choose another --out-dir")
        args.out_dir.mkdir(parents=True, exist_ok=True)
        outputs[0].write_text(body, encoding="utf-8")
        outputs[1].write_text(json.dumps(answers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Wrote {len(answers)} pairs to {args.out_dir}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""多宿主 Skill 校验：只查硬性要求，不限制扩展字段。"""
import re, sys, pathlib, yaml

def check(root):
    root = pathlib.Path(root)
    p = root / "SKILL.md"
    problems, notes = [], []

    if not p.exists():
        return ["SKILL.md 不存在"], []
    text = p.read_text()

    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return ["frontmatter 格式不对"], []
    try:
        fm = yaml.safe_load(m.group(1))
    except Exception as e:
        return [f"YAML 解析失败: {e}"], []
    if not isinstance(fm, dict):
        return ["frontmatter 不是字典"], []

    # 硬性字段
    for k in ("name", "description"):
        if not fm.get(k):
            problems.append(f"缺少 {k}")
    name = str(fm.get("name", ""))
    if name and not re.match(r"^[a-z0-9-]+$", name):
        problems.append(f"name 需小写字母数字连字符: {name}")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        problems.append("name 首尾不能是连字符，也不能连续")

    # 展示用字段：有就检查类型
    for k in ("display_name", "display_name_en", "description_zh", "description_en", "version", "license", "visibility"):
        if k in fm and not isinstance(fm[k], (str, int, float)):
            problems.append(f"{k} 类型异常")

    # 版本：顶层或 metadata 至少有一处
    ver = fm.get("version") or (fm.get("metadata") or {}).get("version")
    if not ver:
        problems.append("缺少版本号（version 或 metadata.version）")

    # WorkBuddy 市场的必填项（缺失只提示，不阻断其他宿主）
    wb_required = ("display_name", "display_name_en", "description_zh", "description_en", "author")
    missing_wb = [k for k in wb_required if not fm.get(k)]
    if missing_wb:
        notes.append(f"WorkBuddy 市场必填项缺失: {', '.join(missing_wb)}")

    # 引用的 references 是否存在
    for ref in re.findall(r"\]\((references/[^)#]+)", text):
        if not (root / ref).exists():
            problems.append(f"引用文件不存在: {ref}")

    # 扩展字段提示（不影响通过）
    extra = set(fm) - {"name","description","license","allowed-tools","metadata",
                       "display_name","display_name_en","description_zh","description_en",
                       "version","visibility","author","examples_zh","examples_en"}
    if extra:
        notes.append(f"未识别的扩展字段: {', '.join(sorted(extra))}")

    return problems, notes

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    problems, notes = check(target)
    if problems:
        print("失败:")
        for x in problems: print("  ✗", x)
        sys.exit(1)
    print("通过（多宿主宽松校验）")
    for n in notes: print("  提示:", n)

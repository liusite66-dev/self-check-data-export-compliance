#!/usr/bin/env python3
"""数据出境合规路径自检 self-check.

根据决策树判定中国数据出境适用路径，输出路径判定、决策路径追溯与资料清单。
本工具为自检辅助，不构成法律意见，最终以监管口径为准。
"""
import argparse
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DISCLAIMER = "本报告为自检辅助，不构成法律意见，最终以监管口径为准。"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(inp, rules):
    """遍历决策树，返回 (path, trace)。trace 为命中的规则节点序列。"""
    thresholds = rules["thresholds"]
    trace = []
    for node in rules["decision_tree"]:
        nid = node["node_id"]
        field = node.get("condition_field")
        # 兜底节点(无 condition_field 且非 match_value 型)：直接命中
        if field is None and "match_value" not in node and "threshold_key" not in node:
            trace.append({"node_id": nid, "description": node["description"],
                          "evaluated": "reached_fallback", "matched": True,
                          "reason": node["on_match"]["reason"]})
            return node["on_match"]["path"], trace

        matched = False
        detail = ""
        if "threshold_key" in node:
            value = inp.get(field, 0) or 0
            thr = thresholds[node["threshold_key"]]
            op = node.get("operator", ">=")
            if op == ">=":
                matched = value >= thr
            detail = "%s=%s %s 阈值%s" % (field, value, op, thr)
        elif "match_value" in node:
            value = inp.get(field, False)
            matched = value == node["match_value"]
            detail = "%s=%s (期望 %s)" % (field, value, node["match_value"])

        trace.append({"node_id": nid, "description": node["description"],
                      "evaluated": detail, "matched": matched,
                      "reason": node["on_match"]["reason"] if matched else ""})
        if matched:
            return node["on_match"]["path"], trace
    # 理论不可达；保底
    return "scc_or_certification", trace


def build_result(inp, rules, materials):
    path, trace = evaluate(inp, rules)
    mat = materials["paths"][path]
    return {
        "rules_version": rules["version"],
        "rules_updated_date": rules["updated_date"],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input": inp,
        "applicable_path": path,
        "path_name": mat["path_name"],
        "authority": mat["authority"],
        "time_limit": mat["time_limit"],
        "material_list": mat["materials"],
        "decision_trace": trace,
        "disclaimer": DISCLAIMER,
    }


def to_markdown(res):
    lines = []
    lines.append("# 数据出境合规路径自检报告")
    lines.append("")
    lines.append("- 生成时间：%s" % res["generated_at"])
    lines.append("- 规则版本：%s（更新日期 %s）" % (res["rules_version"], res["rules_updated_date"]))
    lines.append("")
    lines.append("## 一、判定结论")
    lines.append("")
    lines.append("**适用路径：%s（%s）**" % (res["path_name"], res["applicable_path"]))
    lines.append("")
    lines.append("- 受理/主管部门：%s" % res["authority"])
    lines.append("- 时限提示：%s" % res["time_limit"])
    lines.append("")
    lines.append("## 二、决策路径追溯")
    lines.append("")
    for i, node in enumerate(res["decision_trace"], 1):
        flag = "命中" if node["matched"] else "未命中"
        lines.append("%d. [%s] %s —— %s（判定：%s）" %
                     (i, node["node_id"], node["description"], node["evaluated"], flag))
        if node["matched"] and node["reason"]:
            lines.append("   - 依据：%s" % node["reason"])
    lines.append("")
    lines.append("## 三、所需资料清单")
    lines.append("")
    for m in res["material_list"]:
        lines.append("- [ ] %s" % m)
    lines.append("")
    lines.append("## 四、免责声明")
    lines.append("")
    lines.append("> %s" % res["disclaimer"])
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="数据出境合规路径自检")
    ap.add_argument("--input", required=True, help="输入 JSON 文件路径")
    ap.add_argument("--output", help="输出 Markdown 报告路径")
    ap.add_argument("--json-output", help="输出判定 JSON 路径(可选)")
    args = ap.parse_args()

    inp = load_json(args.input)
    rules = load_json(os.path.join(DATA_DIR, "rules.json"))
    materials = load_json(os.path.join(DATA_DIR, "material_lists.json"))
    res = build_result(inp, rules, materials)
    md = to_markdown(res)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    if not args.output and not args.json_output:
        print(md)
    else:
        print("判定路径：%s -> %s" % (res["applicable_path"], res["path_name"]))
        if args.output:
            print("Markdown 报告已写入：%s" % args.output)
        if args.json_output:
            print("JSON 已写入：%s" % args.json_output)
    return res


if __name__ == "__main__":
    main()

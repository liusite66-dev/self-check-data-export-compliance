#!/usr/bin/env python3
"""self-check-data-export-compliance 测试。构造多组输入，断言判定路径与追溯正确。"""
import json
import os
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
import self_check  # noqa: E402

DATA_DIR = os.path.join(BASE_DIR, "data")
RULES = self_check.load_json(os.path.join(DATA_DIR, "rules.json"))
MATERIALS = self_check.load_json(os.path.join(DATA_DIR, "material_lists.json"))


def run_case(name, inp, expected_path, expected_node):
    res = self_check.build_result(inp, RULES, MATERIALS)
    ok = res["applicable_path"] == expected_path
    hit_node = next((n["node_id"] for n in res["decision_trace"] if n["matched"]), None)
    ok = ok and hit_node == expected_node
    ok = ok and len(res["decision_trace"]) > 0
    ok = ok and len(res["material_list"]) > 0
    status = "PASS" if ok else "FAIL"
    print("[%s] %s -> path=%s(expect %s) hit=%s(expect %s)" %
          (status, name, res["applicable_path"], expected_path, hit_node, expected_node))
    return ok


def base(**kw):
    d = {
        "is_critical_information_infrastructure": False,
        "important_data_involved": False,
        "personal_info_count_annual": 0,
        "sensitive_personal_info_count": 0,
        "data_processor_type": "一般处理者",
        "scenario": "对外提供",
        "exemption_applicable": False,
    }
    d.update(kw)
    return d


def main():
    results = []
    results.append(run_case("CIIO", base(is_critical_information_infrastructure=True),
                             "security_assessment", "N1_CIIO"))
    results.append(run_case("重要数据", base(important_data_involved=True),
                             "security_assessment", "N2_IMPORTANT_DATA"))
    results.append(run_case("个人信息超100万", base(personal_info_count_annual=1200000),
                             "security_assessment", "N3_PI_COUNT"))
    results.append(run_case("敏感信息超1万", base(sensitive_personal_info_count=15000),
                             "security_assessment", "N4_SPI_COUNT"))
    results.append(run_case("豁免情形", base(personal_info_count_annual=50000, exemption_applicable=True),
                             "exemption", "N5_EXEMPTION"))
    results.append(run_case("未超阈值-SCC", base(personal_info_count_annual=300000, sensitive_personal_info_count=2000),
                             "scc_or_certification", "N6_SCC_OR_CERT"))

    # 校验配置版本字段
    cfg_ok = "version" in RULES and "updated_date" in RULES and "version" in MATERIALS
    print("[%s] 配置含 version/updated_date" % ("PASS" if cfg_ok else "FAIL"))
    results.append(cfg_ok)

    # 校验 Markdown 输出与 CLI 落盘
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "r.md")
        res = self_check.build_result(base(is_critical_information_infrastructure=True), RULES, MATERIALS)
        md = self_check.to_markdown(res)
        with open(out, "w", encoding="utf-8") as f:
            f.write(md)
        md_ok = "决策路径追溯" in md and "免责声明" in md and os.path.getsize(out) > 0
    print("[%s] Markdown 报告生成含追溯与免责声明" % ("PASS" if md_ok else "FAIL"))
    results.append(md_ok)

    total, passed = len(results), sum(1 for r in results if r)
    print("\n汇总：%d/%d PASS" % (passed, total))
    if passed == total:
        print("ALL PASS")
        sys.exit(0)
    else:
        print("SOME FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()

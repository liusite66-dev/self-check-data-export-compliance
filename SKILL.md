---
name: self-check-data-export-compliance
description: 数据出境合规路径自检。用决策树判定中国数据出境应走哪条合规路径（数据出境安全评估申报 / 个人信息出境标准合同SCC备案 / 个人信息保护认证 / 豁免），输出路径判定、决策路径逐步追溯、对应资料清单与时限提示。USE WHEN 用户需要判断“数据/个人信息出境要不要做安全评估、走标准合同还是认证、能不能豁免”“跨境传输个人信息合规路径”“数据出境走哪条路”“CIIO/重要数据/超百万人个人信息出境怎么办”“跨国集团内数据共享合规自检”等场景。边界：仅做规则化路径自检与资料清单生成，不出具法律意见、不替代律师与监管审查；阈值为示例口径，需按最新法规核对；不处理具体合同起草、不做PIA报告撰写。
activation: /self-check-data-export-compliance
license: MIT
metadata:
  author: liusite66-dev
  version: 1.0.0
  created: 2026-08-31
provenance:
  maintainer: liusite66-dev
  source_references: user-provided skill package
---

# 数据出境合规路径自检 (self-check-data-export-compliance)

用外置的、带版本号的决策树规则判定中国数据出境适用的合规路径，并输出可追溯的判定过程与资料清单。

## 判定逻辑（决策树，规则见 data/rules.json）
按顺序评估，命中即返回：
1. N1 是否 CIIO → 安全评估
2. N2 是否涉重要数据 → 安全评估
3. N3 年度累计提供个人信息 ≥ 100万人 → 安全评估
4. N4 累计提供敏感个人信息 ≥ 1万人 → 安全评估
5. N5 是否符合豁免情形 → 豁免
6. N6 兜底 → 标准合同备案 / 个人信息保护认证

阈值与分支全部外置在 `data/rules.json`（含 `version`/`updated_date`），资料清单外置在 `data/material_lists.json`，法规变化时只改配置不改代码。

## 输入 (JSON)
```json
{
  "is_critical_information_infrastructure": false,
  "important_data_involved": false,
  "personal_info_count_annual": 300000,
  "sensitive_personal_info_count": 2000,
  "data_processor_type": "一般处理者",
  "scenario": "跨国集团内共享",
  "exemption_applicable": false
}
```

## 输出
- 判定 JSON：适用路径、受理部门、时限、资料清单、`decision_trace`（命中的规则节点序列，含每个节点的取值与阈值比较）。
- Markdown 报告：判定结论 + 决策路径逐步说明 + 资料清单勾选表 + 时限提示 + 免责声明。

## 命令示例
```bash
# 生成 Markdown 报告
python3 scripts/self_check.py --input examples/sample_input.json --output examples/report.md

# 同时导出判定 JSON
python3 scripts/self_check.py --input examples/sample_input.json \
  --output examples/report.md --json-output examples/report.json

# 直接打印到终端
python3 scripts/self_check.py --input examples/sample_input.json
```

## 测试
```bash
python3 tests/run_test.py   # 覆盖 CIIO/重要数据/超阈值/豁免/未超阈值，打印 PASS/FAIL
```

## 免责声明
本 Skill 为自检辅助，不构成法律意见，最终以监管口径为准。阈值为示例口径，请按最新法规核对。

## Gotchas

- 阈值和豁免规则会随法规与监管口径变化，运行前应更新规则文件并核验版本。
- 自检路径不证明跨境传输已经获得授权、完成 PIA 或满足数据主体告知同意要求。

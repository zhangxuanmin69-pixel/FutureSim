# ContextBundle 校验脚本

对 A 提供的 ContextBundle 做候选 Schema 校验、语义检查与"预测输入 / 回测结果分离"检查。

## 运行（克隆仓库后）

```bash
cd scripts/validation
npm install
node validate.mjs
```

- 退出码 `0` = 全部通过，`1` = 存在失败。
- 默认校验仓库内提交的 `frontend/public/futuresim-data/context_bundle_20_real.json`（20 份）。
- 可追加校验仓库外的文件（json 数组 / 单对象 / jsonl）：

```bash
node validate.mjs D:/FutureSim_tmp/day1_intake/data/context_bundle_20_real.jsonl
```

## 文件位置约定

| 内容 | 位置 | 说明 |
|---|---|---|
| 候选 Schema（唯一权威副本） | `contracts/context_bundle.proposed.schema.json` | `1.0.0-draft`，待 B 确认后冻结；前后端不得各自另存版本 |
| 预测输入（ContextBundle） | `frontend/public/futuresim-data/context_bundle_20_real.json` | 不含任何未来标签 |
| 回测结果（含 actual_label） | `frontend/public/futuresim-data/backtest_metrics.json`、`backtest_predictions.csv` | 仅用于历史回测展示，禁止作为预测/仿真输入 |

## 检查项

1. **Schema**：JSON Schema draft 2020-12（ajv + ajv-formats），`additionalProperties: false`。
2. **语义**：`target_definition = next7_views_sum > last7_views_sum`；`horizon_days = 7`；history 固定 28 天；目标窗口 = cutoff+1 ~ cutoff+7；`available_at` / `published_at` 必须为 null（不得补造）。
3. **分离**：history 观测日不得晚于 `cutoff_date`；bundle 与 history 中不得出现 `actual_label`、`next7_views_sum` 等标签字段；回测标签只存在于 backtest_* 文件。

## 依赖说明

`node_modules` 由根 `.gitignore` 排除，不入库；`package.json` 锁定 ajv 依赖，任何成员 `npm install` 后可复现校验。
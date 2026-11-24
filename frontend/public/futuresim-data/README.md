# FutureSim 演示数据来源与许可

本目录为成员 A 提供、成员 C 原样引入的真实数据样本（未修改数值、未补造缺失字段）。

## 数据来源
- **来源**：Wikimedia Analytics (Pageviews) API，`https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/...`
- **项目**：`en.wikipedia.org`｜访问方式 `all-access`｜代理 `user`｜粒度 `daily`
- **官方文档**：https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/examples/page-metrics.html
- **访问政策**：https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html
- **数据集**：`futuresim-wikipedia-pageviews-v0.1`，sha256 `ed87341cd1b5148bd9ec35c5d2738e877f7490340193300ab951a9cf947314e1`
- 每份 ContextBundle 的 `provenance` 字段记录了来源、文档链接与抓取时间（`fetched_at_utc`）。

## 许可
- **数据**：Wikimedia Analytics API 提供的数据采用 **CC0 1.0 通用公共领域贡献声明**（官方 Access policy 原文：“Data provided by the API is available under the CC0 1.0 license”）。据此可自由复制与再分发，本目录保留来源署名以便追溯。
- **使用条款**：调用该 API 须遵守 Wikimedia Terms of Use 与 User-Agent 政策（由 A 的数据管线负责）。
- **代码**：本仓库代码遵循根目录 `LICENSE`（AGPL-3.0，继承自 MiroFish）；数据许可与代码许可相互独立。
- 说明：`available_at` / `published_at` 为 `null` 表示原始发布/可得时间未知，**不得人为补造**；`fetched_at_utc` 仅为抓取时间。

## 文件说明
| 文件 | 内容 | 用途 |
|---|---|---|
| `context_bundle_20_real.json` | 20 份 ContextBundle（5 topic × 4 个月初 cutoff），28 天历史，**不含未来标签** | 预测输入 / 实验绑定 |
| `backtest_metrics.json` | 255 条历史回测的总体指标（2025-01-01 ~ 2025-12-17） | 仅历史回测页展示 |
| `backtest_predictions.csv` | 逐条历史回测预测，**含 `actual_label`** | 仅历史回测页展示，严禁进入预测/仿真输入 |

回测文件为 A 的模型输出（历史回放，非实时预测）；前端展示时明确标注“历史/非实时”。
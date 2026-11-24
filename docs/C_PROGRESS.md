# 成员 C 开发进度（Web 前端与 API Gateway 系统集成）

> 新任务开始前先读仓库根目录 `AGENTS.md`（项目背景/分工/接口约定/限制/路径），再读本文档，并确认当前分支为 `feature/web`。

## 项目背景及 C 的职责
- **项目**：FutureSim V0.1 MVP，基于 MiroFish（群体智能引擎，AGPL-3.0）二次开发，五天交付可运行 MVP，优先功能、不过度设计。
- **预测目标（固定）**：`next7_views_sum > last7_views_sum`（未来 7 天浏览量总和是否高于过去 7 天），数据为 Wikipedia 每日页面浏览量。
- **分工**：A 负责数据管线、训练与回测；B 负责仿真核心；**C（本人）负责 Web 前端与 API Gateway 系统集成**。
- **仓库**：https://github.com/zhangxuanmin69-pixel/FutureSim.git ｜ 本地：`D:\FutureSim` ｜ 分支：`feature/web`
- **纪律**：不修改 A/B 核心代码；不大规模重构 MiroFish；不动 main；不擅自 commit/push；不提交压缩包/密钥/依赖目录/临时文件；`available_at`/`published_at` 为 null 不得补造；不编造预测/仿真结果。

## 实际目录结构（C 相关部分）
```
D:\FutureSim\
├── contracts\
│   └── context_bundle.proposed.schema.json   # A 候选 Schema 唯一权威副本（1.0.0-draft）
├── docs\
│   └── C_PROGRESS.md                         # 本文档
├── scripts\validation\
│   ├── validate.mjs                          # Schema + 语义 + 分离检查脚本
│   ├── package.json / package-lock.json      # ajv 依赖（node_modules 不入库）
│   └── README.md                             # 运行说明
├── frontend\
│   ├── public\futuresim-data\
│   │   ├── context_bundle_20_real.json       # 预测输入（20 份，无未来标签）
│   │   ├── backtest_metrics.json             # 回测结果（仅回测页展示）
│   │   └── backtest_predictions.csv          # 回测逐条预测（含 actual_label）
│   └── src\
│       ├── api\futuresim.js                  # 统一类型(JSDoc) + 常量 + 数据访问层
│       ├── router\index.js                   # 新增 /futuresim 嵌套路由
│       └── views\futuresim\                  # Layout + 5 页面 + futuresim.css
├── backend\
│   ├── futuresim_gateway\                    # FutureSim API Gateway 独立模块（成员 C）
│   │   ├── routes.py                         # /api/v1 七个接口，统一错误/状态
│   │   ├── providers.py                      # ForecastProvider / SimulationProvider 适配层
│   │   ├── storage.py                        # JSON 持久化（线程锁+原子写）
│   │   └── validation.py                     # 服务端 ContextBundle 校验（无第三方依赖）
│   ├── run_futuresim.py                      # 轻量启动入口（无需 LLM/Zep 密钥）
│   ├── data\futuresim\experiments.json       # 运行时数据（.gitignore data/ 排除，不入库）
│   └── app\__init__.py                       # 仅增量注册 futuresim 蓝图（+3 行）
└── (其余 MiroFish 原有结构未动)

仓库外（D 盘临时区，不入库）：
D:\FutureSim_tmp\{day1_intake, validator, npm-cache, shots, build_final.log}
```

## A 的接口约定（候选 Schema，draft）
- 权威文件：`contracts/context_bundle.proposed.schema.json`，`schema_version = 1.0.0-draft`，**待 B 确认后冻结，当前不冻结**。前后端不得各自另存版本。
- ContextBundle 必填字段：`schema_version, experiment_id, dataset_version, dataset_sha256, topic, metric(daily_pageviews), unit(views), cutoff_date, cutoff_time, cutoff_granularity(day), cutoff_semantics(historical_observation_date_inclusive), horizon_days(7), target_start, target_end, target_definition, history(28天), provenance`；`additionalProperties: false`。
- history 点：`timestamp`（观测日 00:00Z，非发布时间）、`value`（int ≥ 0）、`source`、`available_at = null`、`published_at = null`。
- provenance：`project, source, source_documentation, fetched_at_utc`（API 抓取时间，不可替代 available_at）、`record_available_at_verified = false`、`published_at_provided = false`、`note`。
- 数据集：futuresim-wikipedia-pageviews-v0.1，5 topic（Artificial_intelligence / Bitcoin / ChatGPT / Nvidia / Tesla,_Inc.），sha256 `ed87341c…7314e1`，来源 Wikimedia Pageviews API（en.wikipedia.org，all-access，user，daily）。

## B 尚未确认的接口
1. **Schema 冻结**：1.0.0-draft 候选版待 B 确认（尤其 cutoff 语义与 null 时间戳约定）。
2. **仿真接口**：Agent 仿真的启动/状态/结果接口未定义，仿真页当前显示"等待仿真模块接入"。
3. **API Gateway 对接**：创建实验、预测结果、仿真结果的后端路由与请求/响应格式待 A/B 提供，当前页面为框架占位。

## Day 1 已完成功能
1. 环境：克隆 + feature/web 分支；项目迁移至 D:\FutureSim（完整性/fsck/远程验证通过）；依赖与缓存均在 D 盘。
2. 数据接收：`contracts(1).zip` / `data(1).zip` 解压至仓库外 `D:\FutureSim_tmp\day1_intake`，5 个重点文件齐全，无缺失、无编造。
3. 前端五页面（复用 MiroFish Vue3+Vite，原有路由未动）：
   | 路径 | 页面 | 状态 |
   |---|---|---|
   | /futuresim → /futuresim/experiments | 实验列表 | 20 条真实数据 |
   | /futuresim/create | 创建实验 | 参数组装预览；提交提示待 Gateway 接入 |
   | /futuresim/prediction/:experimentId? | 预测结果 | Bundle 详情 + 28 天浏览量图；预测区等待 A 接入 |
   | /futuresim/simulation/:experimentId? | Agent 仿真 | 等待 B 接入，不编造结果 |
   | /futuresim/backtest | 历史回测 | 255 条真实预测 + 双模型指标，topic 过滤 |
4. 收尾：建立 `contracts/` 权威 Schema；校验脚本入库 `scripts/validation/`（克隆后可复现）；移除 public 下 Schema 重复副本（与原件逐字节一致后删除）。

## 测试结果
- **Schema 校验**：仓库脚本 `node scripts/validation/validate.mjs` → 20/20 通过，退出码 0；追加 intake jsonl + single 共 41 份全部通过。
- **语义检查**：target_definition / horizon=7 / 28 天 history / 目标窗口=cutoff+1..+7 / null 时间戳 / experiment_id 唯一，全部通过。
- **分离检查（预测输入 vs 回测结果）**：
  - 脚本断言：history 观测日 ≤ cutoff_date；bundle/history 无 actual_label、next7_views_sum 等标签字段；Schema additionalProperties=false 兜底 → 通过。
  - 静态检查：`fetchBacktest*` 仅被 BacktestHistory.vue（展示页）引用；预测/仿真/创建/列表页仅消费 `fetchContextBundles` → 未来标签不会进入预测或仿真输入。
- **构建**：`npm run build` 实际退出码 **0**（704 模块，~3s；chunk>500kB 警告为 MiroFish 原有）。
- **浏览器实测**：6 路由正常，MiroFish 首页无回归（截图 `D:\FutureSim_tmp\shots\`）。
- **已修复 bug**：CSV 引号字段 `"Tesla,_Inc."` 含逗号导致解析错位 → 引号感知 splitCsvLine，复测无 NaN。
- **敏感信息扫描**：17 个待提交文件无密钥/口令/token 模式；跟踪文件中无 .env/zip/node_modules/dist。
- **数据许可**：代码遵循仓库 AGPL-3.0；浏览量数据来自 Wikimedia Pageviews API（Wikimedia 分析数据按 CC0 提供），来源与抓取时间已在 provenance 与 dataset_manifest 中记录。

## Day 2 已完成功能（2026-11-24）

### API Gateway（backend/futuresim_gateway，独立模块）
| 接口 | 状态 | 说明 |
|---|---|---|
| GET /api/v1/health | ✅ | 服务状态、Schema 版本/draft 状态、Bundle 加载数、Provider 状态 |
| GET /api/v1/experiments | ✅ | 用户实验列表，支持 ?topic= 过滤 |
| POST /api/v1/experiments | ✅ | {topic, cutoff_date} → 生成 fs-exp-xxxxxxxx，绑定真实 Bundle；400/422 校验 |
| GET /api/v1/experiments/{id} | ✅ | 实验记录 + 完整 ContextBundle |
| POST /api/v1/experiments/{id}/run | ✅ | created/failed/completed → running → completed/failed；409 防重复运行 |
| GET /api/v1/experiments/{id}/results | ✅ | forecast（标记 historical_backtest / is_realtime:false）+ simulation(not_connected) |
| GET /api/v1/experiments/{id}/events | ✅ | 真实运行事件流（Gateway 自身事件，非仿真事件） |

- 统一错误结构 `{"error":{"code","message"}}`；状态机 created→running→completed|failed。
- 持久化：`backend/data/futuresim/experiments.json`（线程锁 + 原子写，重启不丢失，已实测）。
- 主应用工厂 `app/__init__.py` 仅增量注册蓝图；完整 MiroFish 后端与轻量入口共用同一模块。

### Provider 适配层
- **ForecastProvider**：服务端读取 A 的 20 份真实 JSON 样本并逐份校验（0 失败）；A 的 export_context 入库后仅需替换数据来源。已保存回测预测按 (topic, cutoff) 精确匹配，**标记 historical_backtest、is_realtime:false，不含 actual_label**；无匹配则 unavailable，不编造。
- **SimulationProvider**：预留 `run_simulation(context_bundle, config)` 接入位；B 未接入返回 not_connected，simulation_signal=null，不伪造事件；不阻塞预测/回测。

### 前端接入（复用 Day 1 页面）
- 实验列表：我的实验（API）与 A 历史样本（20 份，明确标注非用户实验）严格分区；加载/空/失败+重试/刷新。
- 创建实验：真实 POST，成功跳转详情页；可用 cutoff 快捷链接；服务端错误原样展示。
- 预测结果：双模式（fs-exp-* 走 API；wiki-* 为历史样本视图）；运行按钮 + 1.5s 状态轮询；真实 28 天历史图表；保存预测双模型概率表（标注非实时）；事件表；刷新后状态从后端恢复。
- Agent 仿真：显示服务端 not_connected 状态，不编造结果。
- 历史回测页：不变（255 条真实回测，明确标注历史）。

### 启动命令
```bash
# 后端 Gateway（轻量，无需密钥；venv 在 D 盘）
D:\FutureSim_tmp\venv-futuresim\Scripts\python.exe D:\FutureSim\backend\run_futuresim.py   # 端口 5001
# 前端
cd D:\FutureSim\frontend && npm run dev    # 端口 3000，/api 代理到 5001
# 完整 MiroFish 后端（需 .env 密钥与完整依赖，未启动）
cd backend && uv run python run.py
```

## Day 2 测试结果
- 前后端同时启动 ✅（3000 + 5001）。
- 接口测试 ✅：创建/查询/运行/结果/事件/列表过滤；非法日期 400、未知 topic 422、缺失数据 422（含可用 cutoff 提示）、不存在 404、重复运行 409。
- 20 份 ContextBundle：服务端校验 0 失败 + ajv 脚本复验 20/20（退出码 0）。
- 未来信息隔离 ✅：validation.py 断言 history ≤ cutoff、无标签字段；results 不含 actual_label；回测数据仅回测页消费。
- 重启恢复 ✅：后端重启后实验记录/状态/事件完整；页面刷新后状态恢复。
- UI 端到端 ✅：创建 Nvidia 2025-10-01 → 运行 → 已完成 → 保存预测 46.18%/50.38%（标注非实时）→ 事件流 → 刷新恢复；错误态（不存在实验、缺失数据）展示+重试正常。
- `npm run build` 退出码 **0**（3.17s）。
- MiroFish 回归 ✅：首页正常渲染，FutureSim 入口在；原有路由未动。

## Day 2 第二轮增量（2026-11-24，幂等性 + 轮询退避 + 回归验证）

### 代码改动（仅 C 范围内）
| 文件 | 改动 |
|---|---|
| `backend/futuresim_gateway/storage.py` | 新增 `begin_run()`：锁内原子占用运行权，返回 missing/running/completed/started，杜绝并发重复执行 |
| `backend/futuresim_gateway/routes.py` | `POST /run` 改用 `begin_run`；**completed 重复运行返回 200 + `idempotent:true`，不重复执行、不追加事件、不改 completed_at**；running 仍 409；failed 可重试。新增 `register_error_handlers(app)`：路由级 404/405 由 app 抛出，蓝图 errorhandler 捕获不到，改为应用级注册且**仅接管 `/api/v1` 前缀**（不影响 MiroFish 其他路由） |
| `backend/futuresim_gateway/__init__.py` | 导出 `register_error_handlers` |
| `backend/run_futuresim.py` | 调用 `register_error_handlers` |
| `backend/app/__init__.py` | 同上（MiroFish 核心累计仅 +5 行蓝图注册） |
| `frontend/src/views/futuresim/PredictionResult.vue` | 轮询由 `setInterval(1500)` 改为 **2.5s `setTimeout` 递归**；失败**指数退避 5→10→20→30s（上限 30s）**，连续 5 次失败停止并显示「重试轮询」按钮；页面加载/刷新时若 status=running **自动续轮询**；重复运行显示幂等提示 |
| `scripts/tests/gateway_api_test.py`（新增） | 31 项接口测试，仅标准库，`python scripts/tests/gateway_api_test.py`，退出码 0=全通过 |

### 本轮测试结果（全部实测）
- **接口测试 31/31 通过，退出码 0**：health/创建/列表/topic 过滤/详情/运行/结果/事件；幂等（事件数 5→5 不变、completed_at 不变）；**6 并发重复运行只执行一次**（响应 `[200,200,409,409,409,409]`，run_started 事件 1 条）；无匹配回测 forecast=null/unavailable；400/422/404/405 错误码与统一结构。
- **持久化**：Gateway 重启前后 7 条实验记录（id/status/completed_at）**完全一致**。
- **未来信息隔离**：详情与 results 全量扫描无 `actual_label/label/next7_views_sum/...`；history 观测日 ≤ cutoff；`available_at/published_at` 保持 null。
- **Schema 校验**：`node scripts/validation/validate.mjs` → 20/20，退出码 0。
- **构建**：`npm run build` 退出码 **0**（3.00s；chunk>500kB 为 MiroFish 原有警告）。
- **浏览器端到端**（DOM 实测，隐藏视口下截图不可用）：
  - 列表：我的实验 10 条（API）与 A 历史样本 20 条分区显示，无 wiki-* 混入实验表。
  - 创建：Tesla,_Inc. + 2025-10-01 快捷链接 → 提交 → 跳转 `fs-exp-c1c98f9d`（已创建）。
  - 运行：→ 已完成，保存预测 historical_rate 46.18% / logistic_regression 49.47%，明确标注「非实时预测」；仿真区显示 not_connected。
  - 重复运行：页面提示「该实验已完成，重复运行返回既有结果（幂等，未重复执行）」，表格行数 7→7 不变。
  - 刷新恢复：状态/预测/事件从后端完整恢复。
  - **轮询节奏**：running 状态下实测请求间隔 ≈3.0s（设定 2.5s，隐藏标签页定时器对齐到秒；符合 2–3s 要求）。
  - **失败退避**：停掉 Gateway 后实测提示序列 5.0s→10.0s→20.0s→30.0s，第 5 次失败后「已停止」；重启 Gateway 后点「重试轮询」恢复正常轮询。
  - 历史样本视图（wiki-nvidia-2025-10-01）：28 根柱状图、无运行按钮、无标签泄露；回测页 255 条、无 NaN；错误态（不存在实验）展示服务端消息 + 重试。
  - MiroFish 首页无回归，FutureSim 入口在。
- **测试夹具已清理**：为验证轮询曾临时写入 `fs-exp-polltest`（status=running）记录，测后已从存储删除并重启，当前 11 条实验均为真实操作产生。
- **敏感信息扫描**：新增/改动文件 0 命中。

### 本轮启动/复现命令
```bash
# Gateway（venv 在 D 盘，无需密钥）
D:\FutureSim_tmp\venv-futuresim\Scripts\python.exe D:\FutureSim\backend\run_futuresim.py
# 接口测试（Gateway 启动后）
D:\FutureSim_tmp\venv-futuresim\Scripts\python.exe D:\FutureSim\scripts\tests\gateway_api_test.py
```

## Day 2 验收与提交前检查（版本保存，2026-11-24）

### 状态契约核对（completed vs succeeded）
- 全仓检索：**没有任何 FutureSim 设计文档/契约使用 `succeeded`**；`succeeded` 仅出现在 MiroFish 自身的 Zep 图谱构建域（`backend/app/services/graph_builder.py`、`backend/app/api/graph.py`、`backend/tests/test_zep_cloud_contracts.py`），属另一种资源，与实验状态无关。
- FutureSim 前后端一致使用 `created / running / completed / failed`（`routes.py`、`ExperimentList.vue`、`PredictionResult.vue`）；MiroFish 原有 `SimulationRunView.vue` 亦用 `completed`。**结论：无契约冲突，不改名、不触碰 A/B 代码。**

### 提交范围与排除项
- 入库 30 个文件：Gateway 模块 5 + 启动入口 1 + 主工厂增量 1、前端页面 7 + API 层 1 + 路由 1 + 首页入口 1、真实数据 3 + 数据署名 README 1、contracts Schema 1、校验脚本 4、接口测试 1、文档 2、`.gitignore` 1。
- 已确认被忽略且**未入库**：`backend/data/`（含真实实验记录 experiments.json，**保留未删除**）、`__pycache__/`、`frontend/dist/`、`frontend/node_modules/`、`scripts/validation/node_modules/`、`contracts(1).zip`、`data(1).zip`、`.env*`、`*.log`。venv 与 npm/uv 缓存位于仓库外 `D:\FutureSim_tmp\`。
- 敏感信息扫描：待提交文件 0 命中（仅出现环境变量名，无任何密钥值）。

### 数据许可与来源
- 核实 Wikimedia Analytics API 官方 Access policy 原文：“Data provided by the API is available under the **CC0 1.0** license”。
- 新增 `frontend/public/futuresim-data/README.md`：来源 API/项目/参数、官方文档与访问政策链接、dataset 版本与 sha256、各文件用途、CC0 数据许可与 AGPL-3.0 代码许可区分、null 时间戳不得补造、回测文件含标签仅限回测页。

### 提交前复跑（全部通过）
| 项目 | 结果 |
|---|---|
| `scripts/tests/gateway_api_test.py` | 31/31，退出码 **0** |
| `scripts/validation/validate.mjs` | 20/20，退出码 **0** |
| `npm run build` | 704 模块，3.95s，退出码 **0** |

## 遗留问题
1. **回测 cutoff 网格与样本不重合**：回测 CSV 为周网格（2025-01-01 起每 7 天），20 份 Bundle 的月初 cutoff 中仅 2025-10-01 命中；其余运行结果为 forecast unavailable（诚实展示，不编造）。需 A 确认是否补充对应 cutoff 的回测。
2. 完整 MiroFish 后端未启动（需 LLM_API_KEY/ZEP_API_KEY 与 camel-oasis 等重依赖）；轻量 Gateway 不提供 MiroFish 原有 /api/graph|simulation|report 路由，首页历史项目组件仍报网络错误（原有行为）。
3. B 仿真接口未定义（SimulationProvider 已预留）；Schema 仍 draft 待 B 确认。
4. chunk>500kB 构建警告（MiroFish 原有）。
5. 会话默认工作目录需用户在 Qoder 界面「打开文件夹」选择 D:\FutureSim；助手命令均以绝对路径在 D:\FutureSim 执行。
6. Day 1 + Day 2（含第二轮增量）全部改动仍未 commit（等待人工批准）。
7. 运行目前是同步执行（毫秒级完成），前端轮询与退避路径已用临时 running 记录实测，但真实长耗时运行需等 B 仿真接入后才会出现。
8. 隐藏浏览器标签页会把定时器对齐到整秒，实测轮询间隔 3.0s（设定 2.5s）；前台标签页应为 2.5s。

## Day 3 开发计划（待人工批准后开展）
1. 与 B 确认 Schema 冻结与仿真接口定义，接入 SimulationProvider。
2. 与 A 确认 export_context 入库与回测 cutoff 补齐，替换 ForecastProvider 数据来源。
3. 仿真状态流/事件流前端展示；视需要配置完整 MiroFish 后端（密钥向用户索取）。

## 变更日志
- 2026-11-24 Day 1 开发：环境迁移 + 数据校验 + 前端五页面框架 + 构建/路由验证。
- 2026-11-24 Day 1 收尾：contracts/ 权威 Schema、scripts/validation 入库、分离检查、完整提交前检查（build 退出码 0、敏感扫描通过）；待人工批准提交。
- 2026-11-24 Day 2：API Gateway 七接口 + JSON 持久化 + Forecast/Simulation Provider + 前端全面接入；接口/UI/重启/隔离/构建测试全部通过；未 commit。
- 2026-11-24 Day 2 第二轮：运行幂等（原子占用 + completed 直接返回）、应用级 404/405 统一错误、前端 2.5s 轮询 + 指数退避 + 刷新续轮询、新增 scripts/tests/gateway_api_test.py（31/31 通过）；构建/Schema/浏览器回归全通过；未 commit。
# FutureSim — Agent 项目记忆（跨任务共享）

> 任何 Agent 开始本项目工作前：**先读本文件，再读 `docs/C_PROGRESS.md`（详细进度），并确认 Git 分支为 `feature/web`。**
> 本文件与进度文档足以让新 Agent 继续开发，无须历史对话记录。

## 项目背景与目标
- **FutureSim V0.1 MVP**：基于开源项目 MiroFish（群体智能引擎，AGPL-3.0）二次开发，**五天交付可运行 MVP**，优先功能、不过度设计、不做无关重构。
- **预测目标（固定，不得更改）**：`next7_views_sum > last7_views_sum` —— 未来 7 天 Wikipedia 页面浏览量总和是否高于过去 7 天。
- 仓库：https://github.com/zhangxuanmin69-pixel/FutureSim.git ｜ 本地：`D:\FutureSim`（C 盘空间不足，一切项目文件/依赖/缓存放 D 盘）。

## 团队分工
| 成员 | 职责 | 边界 |
|---|---|---|
| A | 数据管线、训练与回测 | **不得修改其代码**；数据/Schema 由其提供 |
| B | 仿真核心（MiroFish Agent 仿真） | **不得修改其代码**；仿真接口未定义 |
| C（本 Agent 角色） | Web 前端 + API Gateway 系统集成 | 负责 frontend 与 backend/futuresim_gateway |

## 技术栈
- 前端：Vue 3 + Vite 7 + vue-router 4（JavaScript，无 TS；类型用 JSDoc），端口 3000，`/api` 代理到 5001。
- 后端：Flask（MiroFish 原有，重依赖 camel-oasis/zep，需 LLM/Zep 密钥）；**FutureSim Gateway 为独立模块**，仅依赖 flask/flask-cors/python-dotenv，无需密钥。
- 校验：Node ajv（draft 2020-12）；服务端 Python 无依赖等价校验。
- 持久化：JSON 文件 + 线程锁 + 原子写（无数据库）。

## 分支与 Git 规则
- 开发分支 **`feature/web`**（远程原有）；**禁止修改 main**；远程另有 feature/forecast、feature/simulation。
- **未经人工批准不得 commit/push**（当前 Day 1+Day 2 全部改动未提交，等待验收）。
- 不提交：压缩包（*.zip 已 ignore）、密钥/.env、node_modules、dist、缓存、临时文件、运行时数据（backend/data/ 被 `data/` 规则 ignore）。

## 接口约定
### ContextBundle（A 提供，候选 Schema）
- **唯一权威副本：`contracts/context_bundle.proposed.schema.json`**，版本 `1.0.0-draft`，**待 B 确认后才冻结，不得擅自冻结或另存版本**。
- 必填字段：schema_version, experiment_id, dataset_version, dataset_sha256, topic, metric(daily_pageviews), unit(views), cutoff_date, cutoff_time, cutoff_granularity(day), cutoff_semantics(historical_observation_date_inclusive), horizon_days(7), target_start, target_end, target_definition, history(28 天), provenance；additionalProperties:false。
- history 点：timestamp(观测日 00:00Z)、value(int≥0)、source、**available_at=null、published_at=null（不得补造）**。
- 目标窗口 = cutoff+1 ~ cutoff+7；history 末日 = cutoff_date。
- 数据集：futuresim-wikipedia-pageviews-v0.1，5 topic（Artificial_intelligence/Bitcoin/ChatGPT/Nvidia/Tesla,_Inc.），每 topic 4 个月初 cutoff（2025-09/10/11/12-01）。

### API Gateway（已实现，/api/v1）
GET /health、GET /experiments(?topic=)、POST /experiments({topic,cutoff_date})、GET /experiments/{id}、POST /experiments/{id}/run、GET /experiments/{id}/results、GET /experiments/{id}/events。
- 统一错误：`{"error":{"code","message"}}`（404/405 由 `register_error_handlers(app)` 在应用级接管，仅 `/api/v1` 前缀）；状态机：created→running→completed|failed。
- **状态词约定**：FutureSim 实验统一用 `completed`（前后端一致）。仓库中出现的 `succeeded` 只属于 MiroFish 自身的 Zep 图谱构建任务（`backend/app/services/graph_builder.py`、`app/api/graph.py`），与实验状态无关，**不得混用或改名**。
- **运行幂等**：`store.begin_run()` 锁内原子占用；completed 重复 POST /run 返回 200 + `idempotent:true`（不重复执行/不追加事件），running 返回 409，failed 可重试。
- 前端状态轮询：2.5s 递归 setTimeout，失败指数退避 5→10→20→30s，连续 5 次失败停止并提供重试；刷新时 status=running 自动续轮询。
- 实验 id 形如 `fs-exp-xxxxxxxx`；A 的历史样本 id 形如 `wiki-<topic>-<cutoff>`，**历史样本不是用户实验，不得混入实验列表**。
- 预测输出仅来自**已保存历史回测**（source=historical_backtest、is_realtime:false），无匹配则 unavailable，**不编造实时预测**。
- 仿真：SimulationProvider 预留 `run_simulation(context_bundle, config)`；B 未接入返回 not_connected、simulation_signal=null，**不伪造仿真事件**，不阻塞预测/回测。

### 数据纪律（红线）
- **严禁未来标签进入预测/仿真输入**：ContextBundle 无 actual_label 等字段；history ≤ cutoff；回测标签只存在于 backtest_* 文件且仅回测页展示。
- 不编造任何数据/预测/仿真结果；缺失即如实报告。
- **数据许可**：Wikimedia Analytics API 数据为 **CC0 1.0**；来源/抓取时间见各 bundle 的 provenance 与 `frontend/public/futuresim-data/README.md`；代码为 AGPL-3.0（根 LICENSE）。

## 开发限制
- 不修改 A/B 核心代码；不大规模重构 MiroFish（对 app/__init__.py 仅增量注册蓝图）。
- 不引入不必要的复杂架构；不擅自冻结跨组接口。
- 不记录/提交 API Key 等敏感信息；完整 MiroFish 后端所需密钥向用户索取，不编造。

## 重要文件路径
| 路径 | 说明 |
|---|---|
| `docs/C_PROGRESS.md` | **详细进度/测试/计划（每次任务后更新）** |
| `contracts/context_bundle.proposed.schema.json` | 候选 Schema 权威副本 |
| `backend/futuresim_gateway/` | Gateway：routes/providers/storage/validation |
| `backend/run_futuresim.py` | 轻量启动入口（端口 5001） |
| `backend/data/futuresim/experiments.json` | 运行时持久化（不入库） |
| `frontend/src/api/futuresim.js` | 前端统一类型(JSDoc)+常量+数据访问层 |
| `frontend/src/views/futuresim/` | 5 页面 + Layout + 共享 css |
| `frontend/src/router/index.js` | /futuresim 嵌套路由 |
| `frontend/public/futuresim-data/` | A 的真实数据（20 Bundle + 回测指标/明细） |
| `scripts/validation/` | ajv 校验脚本 + 运行说明（克隆后可复现） |
| `scripts/tests/gateway_api_test.py` | Gateway 接口测试 31 项（仅标准库，退出码 0=通过） |
| `D:\FutureSim_tmp\`（仓库外） | day1_intake 解压资料 / venv-futuresim / npm-cache / uv-cache / shots |

## 启动与验证命令
```bash
# Gateway（venv 在 D 盘，无需密钥）
D:\FutureSim_tmp\venv-futuresim\Scripts\python.exe D:\FutureSim\backend\run_futuresim.py
# 前端
cd D:\FutureSim\frontend && npm run dev        # http://localhost:3000/futuresim
# 构建（须退出码 0）
cd D:\FutureSim\frontend && npm run build
# Schema 校验（须退出码 0）
cd D:\FutureSim\scripts\validation && npm install && node validate.mjs
# 接口测试（Gateway 启动后，须退出码 0）
D:\FutureSim_tmp\venv-futuresim\Scripts\python.exe D:\FutureSim\scripts\tests\gateway_api_test.py
```

## 已知关键事实
- 回测 CSV 为周网格（2025-01-01 起每 7 天），与样本月初 cutoff **仅 2025-10-01 重合**；演示保存预测请用 10-01。
- 完整 MiroFish 后端（run.py）需 LLM_API_KEY/ZEP_API_KEY 与重依赖，当前未启动；首页历史项目组件报网络错误属原有行为。
- 会话默认工作目录可能不在 D:\FutureSim：所有项目命令用绝对路径定位 `D:\FutureSim` 执行。
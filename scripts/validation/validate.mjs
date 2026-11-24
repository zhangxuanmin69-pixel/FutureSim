/**
 * FutureSim ContextBundle 校验（可复现，克隆仓库后即可运行）
 *
 * 用法：
 *   cd scripts/validation && npm install && node validate.mjs [额外的bundle文件.json或.jsonl ...]
 *
 * 默认校验对象（仓库内提交的文件）：
 *   - Schema：contracts/context_bundle.proposed.schema.json（唯一权威副本，draft）
 *   - 数据：frontend/public/futuresim-data/context_bundle_20_real.json
 *
 * 检查内容：
 *   1. JSON Schema（draft 2020-12）逐条校验
 *   2. 语义检查：target_definition / horizon / 28 天 history / 目标窗口 / null 时间戳
 *   3. 分离检查：禁止未来标签进入 ContextBundle（history 不得晚于 cutoff，
 *      不得出现 actual_label / next7 等标签字段；回测结果只存在于 backtest_* 文件）
 *
 * 退出码：0 = 全部通过；1 = 存在失败。
 */
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import Ajv2020 from 'ajv/dist/2020.js'
import addFormats from 'ajv-formats'

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
const schemaPath = resolve(repoRoot, 'contracts/context_bundle.proposed.schema.json')
const defaultData = resolve(repoRoot, 'frontend/public/futuresim-data/context_bundle_20_real.json')

const schema = JSON.parse(readFileSync(schemaPath, 'utf8'))
const ajv = new Ajv2020({ allErrors: true, strict: false })
addFormats(ajv)
const validate = ajv.compile(schema)

const LABEL_KEYS = ['actual_label', 'label', 'next7_views_sum', 'future_views', 'target_label', 'y_true']

function loadBundles(path) {
  const text = readFileSync(path, 'utf8').trim()
  if (path.endsWith('.jsonl')) return text.split(/\r?\n/).map(l => JSON.parse(l))
  const parsed = JSON.parse(text)
  return Array.isArray(parsed) ? parsed : [parsed]
}

function checkBundle(b) {
  const issues = []
  const schemaOk = validate(b)
  if (!schemaOk) issues.push(...validate.errors.map(e => `schema: ${e.instancePath || '/'} ${e.message}`))

  if (b.target_definition !== 'next7_views_sum > last7_views_sum') issues.push('target_definition 不符')
  if (b.horizon_days !== 7) issues.push('horizon_days != 7')
  if (b.history?.length !== 28) issues.push(`history 长度 ${b.history?.length} != 28`)
  if (b.history?.some(h => h.available_at !== null)) issues.push('available_at 非 null（不得补造）')
  if (b.history?.some(h => h.published_at !== null)) issues.push('published_at 非 null（不得补造）')

  const cutoff = new Date(b.cutoff_date + 'T00:00:00Z')
  const plus = d => new Date(cutoff.getTime() + d * 86400000).toISOString().slice(0, 10)
  if (b.target_start !== plus(1)) issues.push(`target_start ${b.target_start} != cutoff+1`)
  if (b.target_end !== plus(7)) issues.push(`target_end ${b.target_end} != cutoff+7`)

  // 分离检查：预测输入不得包含未来信息
  for (const h of b.history ?? []) {
    if (h.timestamp?.slice(0, 10) > b.cutoff_date) issues.push(`history 含 cutoff 之后的观测 ${h.timestamp}`)
    for (const k of LABEL_KEYS) if (k in h) issues.push(`history 含标签字段 ${k}`)
  }
  for (const k of LABEL_KEYS) if (k in b) issues.push(`bundle 含标签字段 ${k}`)
  const lastDay = b.history?.[b.history.length - 1]?.timestamp?.slice(0, 10)
  if (lastDay !== b.cutoff_date) issues.push(`history 末日 ${lastDay} != cutoff_date`)

  return { experiment_id: b.experiment_id, ok: issues.length === 0, issues }
}

const files = [defaultData, ...process.argv.slice(2).map(p => resolve(p))]
let failed = 0
let total = 0
const allIds = new Set()

for (const file of files) {
  const bundles = loadBundles(file)
  const results = bundles.map(checkBundle)
  const pass = results.filter(r => r.ok).length
  total += results.length
  failed += results.length - pass
  for (const b of bundles) allIds.add(b.experiment_id)
  console.log(`\n[${file}]`)
  console.log(`  数量: ${bundles.length}  通过: ${pass}  失败: ${results.length - pass}`)
  for (const r of results.filter(r => !r.ok)) console.log(`  FAIL ${r.experiment_id}: ${r.issues.join('; ')}`)
}

console.log(`\nSchema: ${schema.$id} (${schema.properties.schema_version.const})`)
console.log(`总计: ${total} 份，失败 ${failed} 份，唯一 experiment_id ${allIds.size} 个`)
console.log(failed === 0 ? 'RESULT: PASS' : 'RESULT: FAIL')
process.exit(failed === 0 ? 0 : 1)
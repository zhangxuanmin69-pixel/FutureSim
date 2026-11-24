/**
 * FutureSim 统一数据类型与数据访问层（成员 C / Day 1）
 * 字段定义以 A 的候选 Schema 为准：contracts/context_bundle.proposed.schema.json（仓库根目录，唯一权威副本）
 * Schema 版本 1.0.0-draft，待 B 确认后冻结。
 */

export const SCHEMA_VERSION = '1.0.0-draft'
export const TARGET_DEFINITION = 'next7_views_sum > last7_views_sum'
export const HORIZON_DAYS = 7
export const HISTORY_DAYS = 28

/**
 * @typedef {Object} HistoryPoint
 * @property {string} timestamp 观测日 00:00Z（ISO date-time），非发布时间
 * @property {number} value 当日浏览量（整数，>= 0）
 * @property {string} source
 * @property {string|null} available_at 未经核实的时间戳一律为 null，不得补造
 * @property {string|null} published_at 源未提供发布时间时为 null，不得补造
 */

/**
 * @typedef {Object} Provenance
 * @property {string} project
 * @property {string} source
 * @property {string} source_documentation
 * @property {string} fetched_at_utc API 抓取时间，不可替代 available_at
 * @property {boolean} record_available_at_verified
 * @property {boolean} published_at_provided
 * @property {string} note
 */

/**
 * @typedef {Object} ContextBundle
 * @property {string} schema_version
 * @property {string} experiment_id
 * @property {string} dataset_version
 * @property {string} dataset_sha256
 * @property {string} topic
 * @property {string} metric 'daily_pageviews'
 * @property {string} unit 'views'
 * @property {string} cutoff_date
 * @property {string} cutoff_time
 * @property {string} cutoff_granularity 'day'
 * @property {string} cutoff_semantics 'historical_observation_date_inclusive'
 * @property {number} horizon_days 7
 * @property {string} target_start
 * @property {string} target_end
 * @property {string} target_definition 'next7_views_sum > last7_views_sum'
 * @property {HistoryPoint[]} history 28 天
 * @property {Provenance} provenance
 */

/**
 * @typedef {Object} BacktestPrediction
 * @property {string} topic
 * @property {string} cutoff_date
 * @property {string} target_end
 * @property {number} actual_label
 * @property {number} historical_rate_probability
 * @property {number} logistic_probability
 * @property {number} training_samples
 */

/**
 * @typedef {Object} BacktestMetrics
 * @property {number} n_predictions
 * @property {string} date_min
 * @property {string} date_max
 * @property {Object<string, {accuracy: number, brier_score: number}>} model_scores
 */

const DATA_BASE = '/futuresim-data'
const API_BASE = '/api/v1'

async function gatewayFetch(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options)
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const msg = data?.error?.message ?? `HTTP ${res.status}`
    const err = new Error(msg)
    err.code = data?.error?.code ?? 'HTTP_ERROR'
    throw err
  }
  return data
}

export function fetchHealth() {
  return gatewayFetch('/health')
}

export function listExperiments(topic) {
  return gatewayFetch(`/experiments${topic ? `?topic=${encodeURIComponent(topic)}` : ''}`)
}

export function createExperiment(payload) {
  return gatewayFetch('/experiments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export function getExperiment(id) {
  return gatewayFetch(`/experiments/${encodeURIComponent(id)}`)
}

export function runExperiment(id) {
  return gatewayFetch(`/experiments/${encodeURIComponent(id)}/run`, { method: 'POST' })
}

export function getResults(id) {
  return gatewayFetch(`/experiments/${encodeURIComponent(id)}/results`)
}

export function getEvents(id) {
  return gatewayFetch(`/experiments/${encodeURIComponent(id)}/events`)
}

/** @returns {Promise<ContextBundle[]>} */
export async function fetchContextBundles() {
  const res = await fetch(`${DATA_BASE}/context_bundle_20_real.json`)
  if (!res.ok) throw new Error(`加载 ContextBundle 失败: HTTP ${res.status}`)
  return res.json()
}

/** @returns {Promise<BacktestMetrics>} */
export async function fetchBacktestMetrics() {
  const res = await fetch(`${DATA_BASE}/backtest_metrics.json`)
  if (!res.ok) throw new Error(`加载回测指标失败: HTTP ${res.status}`)
  return res.json()
}

function splitCsvLine(line) {
  const cells = []
  let cur = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (inQuotes) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          cur += '"'
          i++
        } else {
          inQuotes = false
        }
      } else {
        cur += ch
      }
    } else if (ch === '"') {
      inQuotes = true
    } else if (ch === ',') {
      cells.push(cur)
      cur = ''
    } else {
      cur += ch
    }
  }
  cells.push(cur)
  return cells
}

/** @returns {Promise<BacktestPrediction[]>} */
export async function fetchBacktestPredictions() {
  const res = await fetch(`${DATA_BASE}/backtest_predictions.csv`)
  if (!res.ok) throw new Error(`加载回测预测失败: HTTP ${res.status}`)
  const text = (await res.text()).replace(/^﻿/, '')
  const [header, ...lines] = text.trim().split(/\r?\n/)
  const cols = splitCsvLine(header)
  return lines.map(line => {
    const cells = splitCsvLine(line)
    const row = Object.fromEntries(cols.map((c, i) => [c, cells[i]]))
    return {
      ...row,
      actual_label: Number(row.actual_label),
      historical_rate_probability: Number(row.historical_rate_probability),
      logistic_probability: Number(row.logistic_probability),
      training_samples: Number(row.training_samples)
    }
  })
}
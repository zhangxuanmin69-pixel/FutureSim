<template>
  <div>
    <h1 class="fs-title">预测结果</h1>
    <p class="fs-sub">
      <router-link to="/futuresim/experiments">← 返回实验列表</router-link>
    </p>

    <div v-if="loading" class="fs-muted">加载中…</div>
    <div v-else-if="error" class="fs-error">
      {{ error }}
      <button class="fs-btn" style="margin-left: 12px" @click="loadAll">重试</button>
    </div>

    <template v-else-if="!bundle">
      <p class="fs-sub">请选择一个实验或历史样本：</p>
      <ul>
        <li v-for="b in bundles" :key="b.experiment_id" style="margin-bottom: 6px">
          <router-link :to="`/futuresim/prediction/${b.experiment_id}`" class="fs-mono">
            {{ b.experiment_id }}
          </router-link>
        </li>
      </ul>
    </template>

    <template v-else>
      <!-- 实验模式：状态与运行 -->
      <div v-if="isExperiment" class="fs-card">
        <h2>实验状态（{{ experimentId }}）</h2>
        <dl class="fs-kv">
          <dt>status</dt><dd>{{ statusText(exp.status) }}</dd>
          <dt>topic / cutoff_date</dt><dd>{{ exp.topic }} / {{ exp.cutoff_date }}</dd>
          <dt>创建时间</dt><dd>{{ exp.created_at }}</dd>
          <dt>完成时间</dt><dd>{{ exp.completed_at ?? '—' }}</dd>
        </dl>
        <button class="fs-btn" style="margin-top: 12px" :disabled="exp.status === 'running'" @click="run">
          {{ exp.status === 'running' ? '运行中（轮询状态）…' : '运行实验' }}
        </button>
        <div v-if="runError" class="fs-error" style="margin-top: 12px">{{ runError }}</div>
        <div v-if="runNotice" class="fs-muted" style="margin-top: 12px">{{ runNotice }}</div>
        <div v-if="pollNotice" class="fs-error" style="margin-top: 12px">
          {{ pollNotice }}
          <button class="fs-btn" style="margin-left: 12px" @click="startPolling">重试轮询</button>
        </div>
      </div>

      <div class="fs-card">
        <h2>ContextBundle（{{ bundle.experiment_id }}）<span v-if="!isExperiment" class="fs-muted">　历史样本</span></h2>
        <dl class="fs-kv">
          <dt>schema_version</dt><dd>{{ bundle.schema_version }}</dd>
          <dt>dataset_version</dt><dd>{{ bundle.dataset_version }}</dd>
          <dt>dataset_sha256</dt><dd>{{ bundle.dataset_sha256 }}</dd>
          <dt>topic</dt><dd>{{ bundle.topic }}</dd>
          <dt>cutoff_date / cutoff_time</dt><dd>{{ bundle.cutoff_date }} / {{ bundle.cutoff_time }}</dd>
          <dt>horizon_days</dt><dd>{{ bundle.horizon_days }}</dd>
          <dt>target_definition</dt><dd>{{ bundle.target_definition }}</dd>
          <dt>目标窗口</dt><dd>{{ bundle.target_start }} ~ {{ bundle.target_end }}</dd>
          <dt>history</dt><dd>{{ bundle.history.length }} 天（available_at / published_at 均为 null）</dd>
          <dt>provenance.source</dt><dd>{{ bundle.provenance.source }}</dd>
          <dt>fetched_at_utc</dt><dd>{{ bundle.provenance.fetched_at_utc }}</dd>
        </dl>
      </div>

      <div class="fs-card">
        <h2>过去 28 天浏览量（{{ bundle.unit }}）</h2>
        <div class="fs-bars">
          <div
            v-for="h in bundle.history"
            :key="h.timestamp"
            class="fs-bar"
            :style="{ height: barHeight(h.value) }"
            :title="`${h.timestamp.slice(0, 10)}: ${h.value}`"
          ></div>
        </div>
        <div class="fs-muted" style="margin-top: 6px; font-size: 12px">
          {{ bundle.history[0].timestamp.slice(0, 10) }} ~ {{ bundle.history[bundle.history.length - 1].timestamp.slice(0, 10) }}
          ｜ 最近 7 天总和：{{ last7Sum.toLocaleString() }}
        </div>
      </div>

      <div class="fs-card">
        <h2>预测（next7_views_sum &gt; last7_views_sum）</h2>
        <template v-if="isExperiment">
          <div v-if="exp.status === 'created'" class="fs-pending">尚未运行，点击上方"运行实验"。</div>
          <div v-else-if="results?.forecast" class="fs-notice" style="margin-top: 0">
            数据来源：已保存的历史回测结果（{{ results.forecast.source }}），<b>非实时预测</b>。
            训练样本 {{ results.forecast.training_samples }} 条，目标窗口至 {{ results.forecast.target_end }}。
          </div>
          <table v-if="results?.forecast" class="fs-table" style="margin-top: 12px">
            <thead><tr><th>模型</th><th>P(next7 &gt; last7)</th></tr></thead>
            <tbody>
              <tr v-for="(m, name) in results.forecast.models" :key="name">
                <td class="fs-mono">{{ name }}</td>
                <td>{{ (m.probability * 100).toFixed(2) }}%</td>
              </tr>
            </tbody>
          </table>
          <div v-else-if="exp.status === 'completed'" class="fs-pending">
            该 topic/cutoff 无已保存的回测预测（回测 cutoff 网格与样本 cutoff 不重合），不编造数值。
          </div>
          <div v-else-if="exp.status === 'failed'" class="fs-error">运行失败，请查看事件后重试。</div>
        </template>
        <div v-else class="fs-pending">历史样本视图。创建并运行实验后可查看已保存预测；实时预测待 A 经 API Gateway 接入。</div>
      </div>

      <div v-if="isExperiment" class="fs-card">
        <h2>仿真</h2>
        <div class="fs-pending">{{ results?.simulation?.message ?? '等待仿真模块接入（B）' }}</div>
      </div>

      <div v-if="isExperiment && events.length" class="fs-card">
        <h2>运行事件</h2>
        <table class="fs-table">
          <thead><tr><th>时间 (UTC)</th><th>类型</th><th>详情</th></tr></thead>
          <tbody>
            <tr v-for="(ev, i) in events" :key="i">
              <td class="fs-mono">{{ ev.ts.slice(0, 19) }}</td>
              <td class="fs-mono">{{ ev.type }}</td>
              <td>{{ ev.detail }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  fetchContextBundles, getExperiment, getResults, getEvents, runExperiment
} from '@/api/futuresim'

const route = useRoute()
const bundles = ref([])
const loading = ref(true)
const error = ref('')
const runError = ref('')

const exp = ref(null)
const results = ref(null)
const events = ref([])
const pollNotice = ref('')
const runNotice = ref('')
let pollTimer = null
let pollFailures = 0

const POLL_BASE_MS = 2500
const POLL_MAX_MS = 30000
const POLL_MAX_FAILURES = 5

const experimentId = computed(() => route.params.experimentId ?? '')
const isExperiment = computed(() => experimentId.value.startsWith('fs-exp-'))
const bundle = computed(() =>
  isExperiment.value ? exp.value?.context_bundle : bundles.value.find(b => b.experiment_id === experimentId.value)
)
const last7Sum = computed(() =>
  bundle.value ? bundle.value.history.slice(-7).reduce((s, h) => s + h.value, 0) : 0
)
const maxValue = computed(() =>
  bundle.value ? Math.max(...bundle.value.history.map(h => h.value)) : 1
)

const STATUS_TEXT = { created: '已创建', running: '运行中', completed: '已完成', failed: '失败' }
function statusText(s) {
  return STATUS_TEXT[s] ?? s
}
function barHeight(v) {
  return `${Math.max(4, Math.round((v / maxValue.value) * 100))}%`
}

function stopPolling() {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
  pollFailures = 0
}

function schedulePoll(delay) {
  pollTimer = setTimeout(pollOnce, delay)
}

function startPolling() {
  stopPolling()
  pollNotice.value = ''
  schedulePoll(POLL_BASE_MS)
}

async function pollOnce() {
  pollTimer = null
  try {
    const e = await getExperiment(experimentId.value)
    exp.value = e
    pollFailures = 0
    pollNotice.value = ''
    if (e.status === 'running') {
      schedulePoll(POLL_BASE_MS)
    } else {
      await loadAll()
    }
  } catch (e) {
    pollFailures += 1
    if (pollFailures >= POLL_MAX_FAILURES) {
      pollNotice.value = `状态轮询连续失败 ${pollFailures} 次，已停止：${e.message}`
      return
    }
    const delay = Math.min(POLL_BASE_MS * 2 ** pollFailures, POLL_MAX_MS)
    pollNotice.value = `状态轮询失败（${e.message}），第 ${pollFailures} 次退避，${(delay / 1000).toFixed(1)}s 后重试`
    schedulePoll(delay)
  }
}

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    if (isExperiment.value) {
      const [e, r, ev] = await Promise.all([
        getExperiment(experimentId.value),
        getResults(experimentId.value),
        getEvents(experimentId.value)
      ])
      exp.value = e
      results.value = r
      events.value = ev.events
      if (e.status === 'running') startPolling()
    } else {
      bundles.value = await fetchContextBundles()
    }
  } catch (e) {
    error.value = `加载失败：${e.message}`
  } finally {
    loading.value = false
  }
}

async function run() {
  runError.value = ''
  runNotice.value = ''
  try {
    const e = await runExperiment(experimentId.value)
    exp.value = e
    if (e.idempotent) {
      runNotice.value = '该实验已完成，重复运行返回既有结果（幂等，未重复执行）。'
    }
    if (e.status === 'running') {
      startPolling()
    } else {
      await loadAll()
    }
  } catch (e) {
    runError.value = `运行失败：${e.message}`
  }
}

watch(experimentId, () => {
  stopPolling()
  pollNotice.value = ''
  runNotice.value = ''
  exp.value = null
  results.value = null
  events.value = []
  loadAll()
})

onMounted(loadAll)
onUnmounted(stopPolling)
</script>

<style scoped>
@import './futuresim.css';
.fs-bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 120px;
  border-bottom: 1px solid #000;
}
.fs-bar {
  flex: 1;
  background: #000;
  min-width: 6px;
}
.fs-bar:hover {
  background: #ff6600;
}
</style>
<template>
  <div>
    <h1 class="fs-title">历史回测</h1>
    <p class="fs-sub">
      数据源：A 提供的真实回测结果（backtest_metrics.json / backtest_predictions.csv），非实时计算。
    </p>

    <div v-if="error" class="fs-error">{{ error }}</div>
    <div v-else-if="loading" class="fs-muted">加载中…</div>

    <template v-else>
      <div class="fs-card">
        <h2>总体指标（{{ metrics.n_predictions }} 条预测，{{ metrics.date_min }} ~ {{ metrics.date_max }}）</h2>
        <table class="fs-table">
          <thead>
            <tr><th>模型</th><th>Accuracy</th><th>Brier Score</th></tr>
          </thead>
          <tbody>
            <tr v-for="(score, name) in metrics.model_scores" :key="name">
              <td class="fs-mono">{{ name }}</td>
              <td>{{ (score.accuracy * 100).toFixed(2) }}%</td>
              <td>{{ score.brier_score.toFixed(6) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="fs-card">
        <h2>逐条预测（共 {{ predictions.length }} 条，显示前 {{ shown.length }} 条）</h2>
        <div class="fs-field">
          <label>按 topic 过滤</label>
          <select v-model="topicFilter">
            <option value="">全部</option>
            <option v-for="t in topicOptions" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        <table class="fs-table">
          <thead>
            <tr>
              <th>topic</th>
              <th>cutoff_date</th>
              <th>target_end</th>
              <th>actual_label</th>
              <th>historical_rate P</th>
              <th>logistic P</th>
              <th>训练样本</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(p, i) in shown" :key="i">
              <td>{{ p.topic }}</td>
              <td>{{ p.cutoff_date }}</td>
              <td>{{ p.target_end }}</td>
              <td>{{ p.actual_label }}</td>
              <td>{{ p.historical_rate_probability.toFixed(4) }}</td>
              <td>{{ p.logistic_probability.toFixed(4) }}</td>
              <td>{{ p.training_samples }}</td>
            </tr>
          </tbody>
        </table>
        <button v-if="filtered.length > limit" class="fs-btn" style="margin-top: 12px" @click="limit += 50">
          显示更多
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchBacktestMetrics, fetchBacktestPredictions } from '@/api/futuresim'

const metrics = ref(null)
const predictions = ref([])
const loading = ref(true)
const error = ref('')
const topicFilter = ref('')
const limit = ref(50)

const topicOptions = computed(() => [...new Set(predictions.value.map(p => p.topic))])
const filtered = computed(() =>
  topicFilter.value ? predictions.value.filter(p => p.topic === topicFilter.value) : predictions.value
)
const shown = computed(() => filtered.value.slice(0, limit.value))

onMounted(async () => {
  try {
    ;[metrics.value, predictions.value] = await Promise.all([
      fetchBacktestMetrics(),
      fetchBacktestPredictions()
    ])
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
@import './futuresim.css';
</style>
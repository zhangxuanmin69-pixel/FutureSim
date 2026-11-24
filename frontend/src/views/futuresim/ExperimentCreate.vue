<template>
  <div>
    <h1 class="fs-title">创建实验</h1>
    <p class="fs-sub">
      预测目标固定为 next7_views_sum &gt; last7_views_sum（未来 7 天浏览量总和是否高于过去 7 天）。
      字段定义遵循 A 的候选 Schema {{ SCHEMA_VERSION }}。创建后可在详情页运行。
    </p>

    <div class="fs-card">
      <h2>实验参数</h2>
      <div class="fs-field">
        <label>topic（Wikipedia 条目）</label>
        <select v-model="form.topic">
          <option v-for="t in topics" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
      <div class="fs-field">
        <label>cutoff_date（观测截止日，含当日）</label>
        <input type="date" v-model="form.cutoff_date" />
        <div v-if="availableCutoffs.length" class="fs-muted" style="margin-top: 4px; font-size: 12px">
          该 topic 可用 cutoff：
          <a v-for="c in availableCutoffs" :key="c" href="#" style="margin-right: 8px"
             @click.prevent="form.cutoff_date = c">{{ c }}</a>
        </div>
      </div>
      <div class="fs-field">
        <label>horizon_days</label>
        <input :value="HORIZON_DAYS" disabled />
      </div>
      <div class="fs-field">
        <label>target_definition</label>
        <input :value="TARGET_DEFINITION" disabled style="min-width: 360px" />
      </div>
      <button class="fs-btn" :disabled="submitting" @click="submit">
        {{ submitting ? '创建中…' : '创建实验' }}
      </button>
      <div v-if="error" class="fs-error" style="margin-top: 14px">{{ error }}</div>
    </div>

    <div class="fs-card">
      <h2>预览（按候选 Schema 组装，available_at / published_at 保持 null）</h2>
      <pre class="fs-mono" style="font-size: 12px; white-space: pre-wrap">{{ preview }}</pre>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  SCHEMA_VERSION, TARGET_DEFINITION, HORIZON_DAYS,
  fetchContextBundles, createExperiment
} from '@/api/futuresim'

const router = useRouter()
const topics = ['Artificial_intelligence', 'Bitcoin', 'ChatGPT', 'Nvidia', 'Tesla,_Inc.']
const form = reactive({ topic: topics[0], cutoff_date: '' })
const submitting = ref(false)
const error = ref('')
const bundles = ref([])

const availableCutoffs = computed(() =>
  [...new Set(bundles.value.filter(b => b.topic === form.topic).map(b => b.cutoff_date))].sort()
)

const preview = computed(() => {
  if (!form.cutoff_date) return '请选择 cutoff_date'
  const cutoff = new Date(form.cutoff_date + 'T00:00:00Z')
  const plus = d => new Date(cutoff.getTime() + d * 86400000).toISOString().slice(0, 10)
  return JSON.stringify(
    {
      schema_version: SCHEMA_VERSION,
      topic: form.topic,
      metric: 'daily_pageviews',
      unit: 'views',
      cutoff_date: form.cutoff_date,
      cutoff_time: form.cutoff_date,
      cutoff_granularity: 'day',
      cutoff_semantics: 'historical_observation_date_inclusive',
      horizon_days: HORIZON_DAYS,
      target_start: plus(1),
      target_end: plus(7),
      target_definition: TARGET_DEFINITION,
      history: '28 天历史，由 A 的数据管线提供（available_at / published_at 为 null）',
      provenance: '由 A 的数据管线提供'
    },
    null,
    2
  )
})

async function submit() {
  error.value = ''
  if (!form.cutoff_date) {
    error.value = '请先选择 cutoff_date。'
    return
  }
  submitting.value = true
  try {
    const record = await createExperiment({ topic: form.topic, cutoff_date: form.cutoff_date })
    router.push(`/futuresim/prediction/${record.experiment_id}`)
  } catch (e) {
    error.value = `创建失败：${e.message}`
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    bundles.value = await fetchContextBundles()
  } catch {
    bundles.value = []
  }
})
</script>

<style scoped>
@import './futuresim.css';
</style>
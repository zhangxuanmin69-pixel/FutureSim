<template>
  <div>
    <h1 class="fs-title">实验列表</h1>

    <div class="fs-card">
      <h2>我的实验（API Gateway）</h2>
      <div v-if="expLoading" class="fs-muted">加载中…</div>
      <div v-else-if="expError" class="fs-error">
        {{ expError }}
        <button class="fs-btn" style="margin-left: 12px" @click="loadExperiments">重试</button>
      </div>
      <div v-else-if="experiments.length === 0" class="fs-muted">
        暂无实验。<router-link to="/futuresim/create">创建第一个实验</router-link>
      </div>
      <table v-else class="fs-table">
        <thead>
          <tr>
            <th>experiment_id</th>
            <th>topic</th>
            <th>cutoff_date</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in experiments" :key="e.experiment_id">
            <td class="fs-mono">{{ e.experiment_id }}</td>
            <td>{{ e.topic }}</td>
            <td>{{ e.cutoff_date }}</td>
            <td>{{ statusText(e.status) }}</td>
            <td class="fs-mono">{{ e.created_at?.slice(0, 19).replace('T', ' ') }}</td>
            <td>
              <router-link :to="`/futuresim/prediction/${e.experiment_id}`">详情/运行</router-link>
              ·
              <router-link :to="`/futuresim/simulation/${e.experiment_id}`">仿真</router-link>
            </td>
          </tr>
        </tbody>
      </table>
      <button v-if="!expLoading" class="fs-btn" style="margin-top: 12px" @click="loadExperiments">刷新</button>
    </div>

    <div class="fs-card">
      <h2>A 的历史样本（{{ bundles.length }} 份 ContextBundle，非用户实验）</h2>
      <p class="fs-sub">
        数据源：{{ datasetVersion }}。这些是 A 提供的真实历史样本，仅用于查看与创建实验时选择参数，
        不会出现在"我的实验"中。预测目标：未来 7 天浏览量总和是否高于过去 7 天。
      </p>
      <div v-if="error" class="fs-error">{{ error }}</div>
      <div v-else-if="loading" class="fs-muted">加载中…</div>
      <table v-else class="fs-table">
        <thead>
          <tr>
            <th>experiment_id</th>
            <th>topic</th>
            <th>cutoff_date</th>
            <th>目标窗口</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in bundles" :key="b.experiment_id">
            <td class="fs-mono">{{ b.experiment_id }}</td>
            <td>{{ b.topic }}</td>
            <td>{{ b.cutoff_date }}</td>
            <td>{{ b.target_start }} ~ {{ b.target_end }}</td>
            <td>
              <router-link :to="`/futuresim/prediction/${b.experiment_id}`">查看样本</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchContextBundles, listExperiments } from '@/api/futuresim'

const bundles = ref([])
const loading = ref(true)
const error = ref('')
const datasetVersion = ref('')

const experiments = ref([])
const expLoading = ref(true)
const expError = ref('')

const STATUS_TEXT = { created: '已创建', running: '运行中', completed: '已完成', failed: '失败' }
function statusText(s) {
  return STATUS_TEXT[s] ?? s
}

async function loadExperiments() {
  expLoading.value = true
  expError.value = ''
  try {
    const data = await listExperiments()
    experiments.value = data.experiments
  } catch (e) {
    expError.value = `实验列表加载失败：${e.message}`
  } finally {
    expLoading.value = false
  }
}

onMounted(async () => {
  loadExperiments()
  try {
    bundles.value = await fetchContextBundles()
    datasetVersion.value = bundles.value[0]?.dataset_version ?? ''
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
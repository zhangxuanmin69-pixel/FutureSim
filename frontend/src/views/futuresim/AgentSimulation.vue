<template>
  <div>
    <h1 class="fs-title">Agent 仿真</h1>
    <p class="fs-sub">
      基于群体智能 Agent 对目标事件进行仿真推演，输出与统计预测互为参照。
    </p>

    <div v-if="experimentId" class="fs-card">
      <h2>当前实验</h2>
      <p class="fs-mono">{{ experimentId }}</p>
    </div>
    <div v-else class="fs-card">
      <h2>选择实验</h2>
      <p class="fs-sub">从 <router-link to="/futuresim/experiments">实验列表</router-link> 进入，或选择：</p>
      <ul>
        <li v-for="b in bundles" :key="b.experiment_id" style="margin-bottom: 6px">
          <router-link :to="`/futuresim/simulation/${b.experiment_id}`" class="fs-mono">
            {{ b.experiment_id }}
          </router-link>
        </li>
      </ul>
    </div>

    <div class="fs-card">
      <h2>仿真运行</h2>
      <div class="fs-pending">{{ simulationMessage }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchContextBundles, getResults } from '@/api/futuresim'

const route = useRoute()
const bundles = ref([])
const serverMessage = ref('')
const experimentId = computed(() => route.params.experimentId ?? '')
const simulationMessage = computed(() =>
  serverMessage.value || '等待仿真模块接入（B 尚未完成接口对接，不展示任何仿真结果）'
)

onMounted(async () => {
  try {
    bundles.value = await fetchContextBundles()
  } catch {
    bundles.value = []
  }
  if (experimentId.value.startsWith('fs-exp-')) {
    try {
      const r = await getResults(experimentId.value)
      serverMessage.value = r.simulation?.message ?? ''
    } catch {
      serverMessage.value = ''
    }
  }
})
</script>

<style scoped>
@import './futuresim.css';
</style>
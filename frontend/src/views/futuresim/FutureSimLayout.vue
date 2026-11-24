<template>
  <div class="fs-shell">
    <nav class="fs-nav">
      <router-link to="/futuresim" class="fs-brand">FUTURESIM <span class="fs-ver">V0.1</span></router-link>
      <div class="fs-links">
        <router-link to="/futuresim/experiments">实验列表</router-link>
        <router-link to="/futuresim/create">创建实验</router-link>
        <router-link to="/futuresim/prediction">预测结果</router-link>
        <router-link to="/futuresim/simulation">Agent 仿真</router-link>
        <router-link to="/futuresim/backtest">历史回测</router-link>
      </div>
      <router-link to="/" class="fs-back">← MiroFish</router-link>
    </nav>
    <main class="fs-main">
      <router-view />
    </main>
    <footer class="fs-footer">
      预测目标：next7_views_sum &gt; last7_views_sum ｜ Schema {{ SCHEMA_VERSION }}（候选版，待 B 确认冻结）
    </footer>
  </div>
</template>

<script setup>
import { SCHEMA_VERSION } from '@/api/futuresim'
</script>

<style scoped>
.fs-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  color: #000000;
}
.fs-nav {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 24px;
  height: 56px;
  border-bottom: 2px solid #000;
}
.fs-brand {
  font-weight: 700;
  font-size: 18px;
  color: #000;
  text-decoration: none;
  letter-spacing: 1px;
}
.fs-ver {
  font-size: 11px;
  border: 1px solid #000;
  padding: 1px 5px;
  vertical-align: middle;
}
.fs-links {
  display: flex;
  gap: 4px;
  flex: 1;
}
.fs-links a {
  color: #000;
  text-decoration: none;
  padding: 6px 12px;
  font-size: 14px;
  border: 1px solid transparent;
  white-space: nowrap;
}
.fs-links a:hover {
  border-color: #000;
}
.fs-links a.router-link-active {
  background: #000;
  color: #fff;
}
.fs-back {
  color: #666;
  text-decoration: none;
  font-size: 13px;
}
.fs-back:hover {
  color: #000;
}
.fs-main {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
}
.fs-footer {
  padding: 12px 24px;
  border-top: 1px solid #ddd;
  font-size: 12px;
  color: #666;
}
</style>
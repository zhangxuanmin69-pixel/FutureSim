import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Process from '../views/MainView.vue'
import SimulationView from '../views/SimulationView.vue'
import SimulationRunView from '../views/SimulationRunView.vue'
import ReportView from '../views/ReportView.vue'
import InteractionView from '../views/InteractionView.vue'
import FutureSimLayout from '../views/futuresim/FutureSimLayout.vue'
import FsExperimentList from '../views/futuresim/ExperimentList.vue'
import FsExperimentCreate from '../views/futuresim/ExperimentCreate.vue'
import FsPredictionResult from '../views/futuresim/PredictionResult.vue'
import FsAgentSimulation from '../views/futuresim/AgentSimulation.vue'
import FsBacktestHistory from '../views/futuresim/BacktestHistory.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: Process,
    props: true
  },
  {
    path: '/simulation/:simulationId',
    name: 'Simulation',
    component: SimulationView,
    props: true
  },
  {
    path: '/simulation/:simulationId/start',
    name: 'SimulationRun',
    component: SimulationRunView,
    props: true
  },
  {
    path: '/report/:reportId',
    name: 'Report',
    component: ReportView,
    props: true
  },
  {
    path: '/interaction/:reportId',
    name: 'Interaction',
    component: InteractionView,
    props: true
  },
  {
    path: '/futuresim',
    component: FutureSimLayout,
    children: [
      { path: '', redirect: '/futuresim/experiments' },
      { path: 'experiments', name: 'FsExperiments', component: FsExperimentList },
      { path: 'create', name: 'FsCreate', component: FsExperimentCreate },
      { path: 'prediction/:experimentId?', name: 'FsPrediction', component: FsPredictionResult },
      { path: 'simulation/:experimentId?', name: 'FsSimulation', component: FsAgentSimulation },
      { path: 'backtest', name: 'FsBacktest', component: FsBacktestHistory }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

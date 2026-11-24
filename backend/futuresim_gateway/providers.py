"""
Provider 适配层：
- ForecastProvider：读取 A 的真实 ContextBundle 样本与已保存回测结果（标记为历史，非实时预测）。
  A 的 export_context 进入团队仓库后，仅需替换本模块的数据来源。
- SimulationProvider：B 的 run_simulation(context_bundle, config) 预留接入位。
  B 未接入前返回 not_connected，不伪造事件与 simulation_signal。
"""
import csv
import json
from pathlib import Path

from .validation import validate_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / 'frontend' / 'public' / 'futuresim-data'
SCHEMA_VERSION = '1.0.0-draft'


class ForecastProvider:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = Path(data_dir)
        self.bundles = {}
        self.index = {}
        self.load_errors = []
        self._load()

    def _load(self):
        path = self.data_dir / 'context_bundle_20_real.json'
        if not path.exists():
            self.load_errors.append(f'数据文件缺失: {path}')
            return
        for b in json.loads(path.read_text(encoding='utf-8')):
            issues = validate_bundle(b)
            if issues:
                self.load_errors.append(f"{b.get('experiment_id', '?')}: {'; '.join(issues)}")
                continue
            self.bundles[b['experiment_id']] = b
            self.index[(b['topic'], b['cutoff_date'])] = b['experiment_id']

    @property
    def topics(self):
        return sorted({b['topic'] for b in self.bundles.values()})

    def cutoffs_for_topic(self, topic):
        return sorted(b['cutoff_date'] for b in self.bundles.values() if b['topic'] == topic)

    def find_bundle(self, topic, cutoff_date):
        bid = self.index.get((topic, cutoff_date))
        return self.bundles.get(bid) if bid else None

    def saved_prediction(self, topic, cutoff_date):
        """已保存的历史回测预测；不含 actual_label（未来标签不进入预测输出）。"""
        path = self.data_dir / 'backtest_predictions.csv'
        if not path.exists():
            return None
        with path.open(encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                if row['topic'] == topic and row['cutoff_date'] == cutoff_date:
                    return {
                        'source': 'historical_backtest',
                        'is_realtime': False,
                        'note': '已保存的历史回测结果，非实时预测',
                        'topic': topic,
                        'cutoff_date': cutoff_date,
                        'target_end': row['target_end'],
                        'target_definition': 'next7_views_sum > last7_views_sum',
                        'models': {
                            'historical_rate': {'probability': float(row['historical_rate_probability'])},
                            'logistic_regression': {'probability': float(row['logistic_probability'])},
                        },
                        'training_samples': int(row['training_samples']),
                    }
        return None


class SimulationProvider:
    """B 的仿真核心预留接入位。接入后在此调用 run_simulation(context_bundle, config)。"""

    status = 'not_connected'

    def run_simulation(self, context_bundle, config):
        return {
            'status': 'not_connected',
            'message': 'B 的仿真模块尚未接入，不产生仿真事件与 simulation_signal',
            'simulation_signal': None,
        }
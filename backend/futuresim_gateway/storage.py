"""
轻量本地持久化：JSON 文件 + 线程锁 + 原子写。
存储位置 backend/data/futuresim/（被根 .gitignore 的 data/ 规则排除，不入库）。
后端重启后实验记录与事件不丢失。
"""
import json
import os
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_PATH = REPO_ROOT / 'backend' / 'data' / 'futuresim' / 'experiments.json'


class ExperimentStore:
    def __init__(self, path=STORE_PATH):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.experiments = {}
        self._load()

    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding='utf-8'))
            self.experiments = {e['experiment_id']: e for e in data.get('experiments', [])}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(
            json.dumps({'experiments': list(self.experiments.values())}, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        os.replace(tmp, self.path)

    def list(self, topic=None):
        items = sorted(self.experiments.values(), key=lambda e: e['created_at'], reverse=True)
        if topic:
            items = [e for e in items if e['topic'] == topic]
        return items

    def get(self, experiment_id):
        return self.experiments.get(experiment_id)

    def create(self, record):
        with self.lock:
            self.experiments[record['experiment_id']] = record
            self._save()
        return record

    def update(self, record):
        with self.lock:
            self.experiments[record['experiment_id']] = record
            self._save()
        return record

    def begin_run(self, experiment_id):
        """原子占用运行权，避免并发重复运行。

        返回 (record, state)，state ∈ missing / running / completed / started。
        completed 表示已运行过，调用方应直接返回既有结果（幂等，不重复执行）。
        """
        with self.lock:
            record = self.experiments.get(experiment_id)
            if record is None:
                return None, 'missing'
            if record['status'] in ('running', 'completed'):
                return record, record['status']
            record['status'] = 'running'
            self._save()
            return record, 'started'
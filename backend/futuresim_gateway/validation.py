"""
ContextBundle 服务端校验（无第三方依赖）
规则镜像 contracts/context_bundle.proposed.schema.json（1.0.0-draft，候选版）。
权威校验仍以 scripts/validation/validate.mjs（ajv）为准，本模块做等价检查。
"""
import re
from datetime import date, datetime

REQUIRED = [
    'schema_version', 'experiment_id', 'dataset_version', 'dataset_sha256', 'topic',
    'metric', 'unit', 'cutoff_date', 'cutoff_time', 'cutoff_granularity',
    'cutoff_semantics', 'horizon_days', 'target_start', 'target_end',
    'target_definition', 'history', 'provenance',
]
HISTORY_REQUIRED = ['timestamp', 'value', 'source', 'available_at', 'published_at']
PROVENANCE_REQUIRED = [
    'project', 'source', 'source_documentation', 'fetched_at_utc',
    'record_available_at_verified', 'published_at_provided', 'note',
]
LABEL_KEYS = {'actual_label', 'label', 'next7_views_sum', 'future_views', 'target_label', 'y_true'}
SHA_RE = re.compile(r'^[0-9a-f]{64}$')


def _is_date(s):
    if not isinstance(s, str):
        return False
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def _is_datetime(s):
    if not isinstance(s, str):
        return False
    try:
        datetime.fromisoformat(s.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def validate_bundle(b):
    """返回问题列表；空列表 = 通过。"""
    issues = []
    if not isinstance(b, dict):
        return ['bundle 不是对象']
    for k in REQUIRED:
        if k not in b:
            issues.append(f'缺少字段 {k}')
    if issues:
        return issues
    extra = set(b) - set(REQUIRED)
    if extra:
        issues.append(f'多余字段 {sorted(extra)}')
    if b['schema_version'] != '1.0.0-draft':
        issues.append('schema_version 不符')
    if b['metric'] != 'daily_pageviews' or b['unit'] != 'views':
        issues.append('metric/unit 不符')
    if not SHA_RE.match(str(b['dataset_sha256'])):
        issues.append('dataset_sha256 格式不符')
    for k in ('experiment_id', 'dataset_version', 'topic'):
        if not isinstance(b[k], str) or not b[k]:
            issues.append(f'{k} 需为非空字符串')
    for k in ('cutoff_date', 'cutoff_time', 'target_start', 'target_end'):
        if not _is_date(b[k]):
            issues.append(f'{k} 需为日期')
    if b['cutoff_granularity'] != 'day':
        issues.append('cutoff_granularity 不符')
    if b['cutoff_semantics'] != 'historical_observation_date_inclusive':
        issues.append('cutoff_semantics 不符')
    if b['horizon_days'] != 7:
        issues.append('horizon_days 必须为 7')
    if b['target_definition'] != 'next7_views_sum > last7_views_sum':
        issues.append('target_definition 不符')

    h = b['history']
    if not isinstance(h, list) or len(h) != 28:
        issues.append('history 必须为 28 天数组')
    else:
        for i, p in enumerate(h):
            if not isinstance(p, dict):
                issues.append(f'history[{i}] 不是对象')
                continue
            for k in HISTORY_REQUIRED:
                if k not in p:
                    issues.append(f'history[{i}] 缺少 {k}')
            if set(p) - set(HISTORY_REQUIRED):
                issues.append(f'history[{i}] 含多余字段')
            if not _is_datetime(p.get('timestamp')):
                issues.append(f'history[{i}].timestamp 需为 date-time')
            v = p.get('value')
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                issues.append(f'history[{i}].value 需为 >=0 整数')
            if not isinstance(p.get('source'), str) or not p.get('source'):
                issues.append(f'history[{i}].source 需为非空字符串')
            for k in ('available_at', 'published_at'):
                val = p.get(k)
                if val is not None and not _is_datetime(val):
                    issues.append(f'history[{i}].{k} 需为 null 或 date-time')
            # 未来信息隔离
            if isinstance(p.get('timestamp'), str) and p['timestamp'][:10] > b['cutoff_date']:
                issues.append(f'history[{i}] 含 cutoff 之后的观测')
            if LABEL_KEYS & set(p):
                issues.append(f'history[{i}] 含标签字段')
    if LABEL_KEYS & set(b):
        issues.append('bundle 含标签字段')

    prov = b['provenance']
    if not isinstance(prov, dict):
        issues.append('provenance 不是对象')
    else:
        for k in PROVENANCE_REQUIRED:
            if k not in prov:
                issues.append(f'provenance 缺少 {k}')
        if set(prov) - set(PROVENANCE_REQUIRED):
            issues.append('provenance 含多余字段')
        if prov.get('record_available_at_verified') is not False:
            issues.append('record_available_at_verified 必须为 false')
        if prov.get('published_at_provided') is not False:
            issues.append('published_at_provided 必须为 false')
        if not _is_datetime(prov.get('fetched_at_utc')):
            issues.append('fetched_at_utc 需为 date-time')
    return issues
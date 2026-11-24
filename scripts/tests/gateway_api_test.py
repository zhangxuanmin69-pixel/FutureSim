"""FutureSim API Gateway 接口测试（无第三方依赖，仅标准库）。

前置：Gateway 已启动（默认 http://127.0.0.1:5001）。
运行：python scripts/tests/gateway_api_test.py [--base-url http://127.0.0.1:5001]
退出码 0 = 全部通过。测试会创建真实实验记录（写入 backend/data/futuresim/，不入库）。
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

LABEL_KEYS = {'actual_label', 'label', 'next7_views_sum', 'future_views', 'target_label', 'y_true'}

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))
    print(f'{"PASS" if ok else "FAIL"}  {name}' + (f'  | {detail}' if detail else ''))


def call(base, method, path, body=None):
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    if data is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8')
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {'raw': raw}


def has_label(obj):
    if isinstance(obj, dict):
        return any(k in LABEL_KEYS for k in obj) or any(has_label(v) for v in obj.values())
    if isinstance(obj, list):
        return any(has_label(v) for v in obj)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-url', default='http://127.0.0.1:5001')
    base = ap.parse_args().base_url.rstrip('/')
    api = base + '/api/v1'

    s, health = call(api, 'GET', '/health')
    check('health 200 且 20 份 Bundle 无加载错误',
          s == 200 and health.get('bundles_loaded') == 20 and not health.get('bundle_load_errors'),
          f'status={s} bundles={health.get("bundles_loaded")}')
    check('health 标注 Schema draft 与仿真未接入',
          health.get('schema_version') == '1.0.0-draft' and health.get('simulation_provider') == 'not_connected')

    s, exp = call(api, 'POST', '/experiments', {'topic': 'Nvidia', 'cutoff_date': '2025-10-01'})
    eid = exp.get('experiment_id', '')
    check('创建实验 201 且 id 形如 fs-exp-*', s == 201 and eid.startswith('fs-exp-'), f'{s} {eid}')
    check('创建后状态 created', exp.get('status') == 'created')

    s, lst = call(api, 'GET', '/experiments')
    ids = [e['experiment_id'] for e in lst.get('experiments', [])]
    check('列表包含新实验且不含历史样本 id',
          s == 200 and eid in ids and not any(i.startswith('wiki-') for i in ids), f'count={lst.get("count")}')
    s, filtered = call(api, 'GET', '/experiments?topic=Nvidia')
    check('topic 过滤生效', s == 200 and all(e['topic'] == 'Nvidia' for e in filtered['experiments']) and eid in
          [e['experiment_id'] for e in filtered['experiments']])

    s, detail = call(api, 'GET', f'/experiments/{eid}')
    bundle = detail.get('context_bundle') or {}
    check('详情返回完整 ContextBundle', s == 200 and len(bundle.get('history', [])) == 28, f'status={s}')
    check('Bundle 时间戳 null 未被补造',
          all(h['available_at'] is None and h['published_at'] is None for h in bundle.get('history', [])))
    check('预测输入无未来标签', not has_label(detail))
    check('history 观测日 <= cutoff',
          max(h['timestamp'][:10] for h in bundle.get('history', [{'timestamp': ''}])) <= bundle.get('cutoff_date', ''))

    s, run1 = call(api, 'POST', f'/experiments/{eid}/run')
    check('运行完成 completed', s == 200 and run1.get('status') == 'completed', f'status={s}')
    s, res = call(api, 'GET', f'/experiments/{eid}/results')
    fc = res.get('forecast') or {}
    check('预测来自已保存历史回测且非实时',
          res.get('forecast_status') == 'saved_result' and fc.get('source') == 'historical_backtest'
          and fc.get('is_realtime') is False)
    check('预测结果不含 actual_label', not has_label(res))
    sim = res.get('simulation') or {}
    check('仿真未接入返回 not_connected 且 signal=null',
          sim.get('status') == 'not_connected' and sim.get('simulation_signal') is None)

    s, ev = call(api, 'GET', f'/experiments/{eid}/events')
    types = [e['type'] for e in ev.get('events', [])]
    check('事件流含创建/运行/预测/完成',
          {'experiment_created', 'run_started', 'forecast_loaded', 'run_completed'} <= set(types), str(types))
    events_before = len(types)
    completed_before = run1.get('completed_at')

    s, run2 = call(api, 'POST', f'/experiments/{eid}/run')
    s2, ev2 = call(api, 'GET', f'/experiments/{eid}/events')
    check('重复运行幂等：200 + idempotent 标记', s == 200 and run2.get('idempotent') is True, f'status={s}')
    check('重复运行不追加事件、不改完成时间',
          len(ev2['events']) == events_before and run2.get('completed_at') == completed_before,
          f'events {events_before}->{len(ev2["events"])}')

    s, exp2 = call(api, 'POST', '/experiments', {'topic': 'Bitcoin', 'cutoff_date': '2025-10-01'})
    eid2 = exp2['experiment_id']
    with ThreadPoolExecutor(max_workers=6) as pool:
        concurrent = list(pool.map(lambda _: call(api, 'POST', f'/experiments/{eid2}/run'), range(6)))
    codes = sorted(c for c, _ in concurrent)
    executed = sum(1 for c, b in concurrent if c == 200 and not b.get('idempotent'))
    _, ev3 = call(api, 'GET', f'/experiments/{eid2}/events')
    started = sum(1 for e in ev3['events'] if e['type'] == 'run_started')
    check('并发重复运行只执行一次', executed == 1 and started == 1, f'codes={codes} executed={executed} run_started={started}')
    check('并发响应仅 200/409', set(codes) <= {200, 409}, str(codes))

    s, exp3 = call(api, 'POST', '/experiments', {'topic': 'ChatGPT', 'cutoff_date': '2025-09-01'})
    eid3 = exp3['experiment_id']
    call(api, 'POST', f'/experiments/{eid3}/run')
    _, res3 = call(api, 'GET', f'/experiments/{eid3}/results')
    check('无匹配回测时 forecast=null / unavailable（不编造）',
          res3['forecast'] is None and res3['forecast_status'] == 'unavailable')

    err_cases = [
        ('非法日期 400', 'POST', '/experiments', {'topic': 'Nvidia', 'cutoff_date': '2025-13-99'}, 400, 'INVALID_PARAM'),
        ('缺少 topic 400', 'POST', '/experiments', {'cutoff_date': '2025-10-01'}, 400, 'INVALID_PARAM'),
        ('非 JSON 对象 400', 'POST', '/experiments', ['x'], 400, 'INVALID_BODY'),
        ('未知 topic 422', 'POST', '/experiments', {'topic': 'NoSuchTopic', 'cutoff_date': '2025-10-01'}, 422, 'UNKNOWN_TOPIC'),
        ('缺失 Bundle 422', 'POST', '/experiments', {'topic': 'Nvidia', 'cutoff_date': '2025-10-02'}, 422, 'MISSING_DATA'),
        ('详情不存在 404', 'GET', '/experiments/fs-exp-deadbeef', None, 404, 'NOT_FOUND'),
        ('运行不存在 404', 'POST', '/experiments/fs-exp-deadbeef/run', None, 404, 'NOT_FOUND'),
        ('结果不存在 404', 'GET', '/experiments/fs-exp-deadbeef/results', None, 404, 'NOT_FOUND'),
        ('事件不存在 404', 'GET', '/experiments/fs-exp-deadbeef/events', None, 404, 'NOT_FOUND'),
    ]
    for name, method, path, body, want_status, want_code in err_cases:
        s, b = call(api, method, path, body)
        got = (b.get('error') or {}).get('code')
        check(name, s == want_status and got == want_code, f'status={s} code={got}')

    s, b = call(api, 'DELETE', f'/experiments/{eid}')
    check('不支持方法 405 统一错误', s == 405 and (b.get('error') or {}).get('code') == 'METHOD_NOT_ALLOWED', f'status={s}')

    s, lst = call(api, 'GET', '/experiments')
    check('新建实验均已持久化到列表', all(i in [e['experiment_id'] for e in lst['experiments']] for i in (eid, eid2, eid3)))

    failed = [n for n, ok, _ in results if not ok]
    print(f'\n合计 {len(results)} 项，通过 {len(results) - len(failed)}，失败 {len(failed)}')
    if failed:
        print('失败项: ' + '; '.join(failed))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
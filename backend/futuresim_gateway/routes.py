"""
FutureSim API Gateway 路由（/api/v1）
统一错误结构: {"error": {"code": str, "message": str}}
运行状态: created -> running -> completed | failed
"""
import uuid
from datetime import date, datetime, timezone

from flask import Blueprint, jsonify, request

from .providers import ForecastProvider, SimulationProvider, SCHEMA_VERSION
from .storage import ExperimentStore

futuresim_bp = Blueprint('futuresim', __name__)

forecast_provider = ForecastProvider()
simulation_provider = SimulationProvider()
store = ExperimentStore()

STATUSES = ('created', 'running', 'completed', 'failed')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _err(code, message, http):
    return jsonify({'error': {'code': code, 'message': message}}), http


def _event(record, type_, detail):
    record['events'].append({'ts': _now(), 'type': type_, 'detail': detail})


def _public(record):
    """对外视图：事件单独走 /events 接口。"""
    return {k: v for k, v in record.items() if k != 'events'}


@futuresim_bp.errorhandler(404)
def _not_found(_):
    return _err('NOT_FOUND', '资源不存在', 404)


@futuresim_bp.errorhandler(405)
def _method_not_allowed(_):
    return _err('METHOD_NOT_ALLOWED', '请求方法不支持', 405)


def register_error_handlers(app):
    """路由级 404/405 由 app 抛出，蓝图 errorhandler 捕获不到；此处仅接管 /api/v1 前缀。"""
    @app.errorhandler(404)
    def _app_not_found(exc):
        if request.path.startswith('/api/v1'):
            return _err('NOT_FOUND', '资源不存在', 404)
        return exc.get_response()

    @app.errorhandler(405)
    def _app_method_not_allowed(exc):
        if request.path.startswith('/api/v1'):
            return _err('METHOD_NOT_ALLOWED', '请求方法不支持', 405)
        return exc.get_response()


@futuresim_bp.get('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'futuresim-gateway',
        'schema_version': SCHEMA_VERSION,
        'schema_state': 'draft（待 B 确认冻结）',
        'bundles_loaded': len(forecast_provider.bundles),
        'bundle_load_errors': forecast_provider.load_errors,
        'experiments_count': len(store.experiments),
        'forecast_provider': 'real_json_samples',
        'simulation_provider': simulation_provider.status,
    })


@futuresim_bp.get('/experiments')
def list_experiments():
    topic = request.args.get('topic') or None
    items = [_public(e) for e in store.list(topic)]
    return jsonify({'experiments': items, 'count': len(items)})


@futuresim_bp.post('/experiments')
def create_experiment():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _err('INVALID_BODY', '请求体必须为 JSON 对象', 400)
    topic = body.get('topic')
    cutoff = body.get('cutoff_date')
    if not isinstance(topic, str) or not topic:
        return _err('INVALID_PARAM', 'topic 必须为非空字符串', 400)
    if not isinstance(cutoff, str):
        return _err('INVALID_PARAM', 'cutoff_date 必须为 ISO 日期字符串', 400)
    try:
        date.fromisoformat(cutoff)
    except ValueError:
        return _err('INVALID_PARAM', f'cutoff_date 格式非法: {cutoff}', 400)
    if topic not in forecast_provider.topics:
        return _err('UNKNOWN_TOPIC', f'topic 不在数据集中，可选: {forecast_provider.topics}', 422)
    bundle = forecast_provider.find_bundle(topic, cutoff)
    if bundle is None:
        return _err(
            'MISSING_DATA',
            f'缺少 {topic} 在 {cutoff} 的 ContextBundle，可用 cutoff: {forecast_provider.cutoffs_for_topic(topic)}',
            422,
        )
    record = {
        'experiment_id': 'fs-exp-' + uuid.uuid4().hex[:8],
        'topic': topic,
        'cutoff_date': cutoff,
        'bundle_experiment_id': bundle['experiment_id'],
        'schema_version': bundle['schema_version'],
        'dataset_version': bundle['dataset_version'],
        'horizon_days': 7,
        'target_definition': 'next7_views_sum > last7_views_sum',
        'status': 'created',
        'created_at': _now(),
        'forecast': None,
        'simulation': {'status': simulation_provider.status},
        'events': [],
    }
    _event(record, 'experiment_created', f'绑定 ContextBundle {bundle["experiment_id"]}')
    store.create(record)
    return jsonify(_public(record)), 201


@futuresim_bp.get('/experiments/<experiment_id>')
def get_experiment(experiment_id):
    record = store.get(experiment_id)
    if record is None:
        return _err('NOT_FOUND', f'实验不存在: {experiment_id}', 404)
    bundle = forecast_provider.bundles.get(record['bundle_experiment_id'])
    return jsonify({**_public(record), 'context_bundle': bundle})


@futuresim_bp.post('/experiments/<experiment_id>/run')
def run_experiment(experiment_id):
    record, state = store.begin_run(experiment_id)
    if state == 'missing':
        return _err('NOT_FOUND', f'实验不存在: {experiment_id}', 404)
    if state == 'running':
        return _err('ALREADY_RUNNING', '实验正在运行', 409)
    if state == 'completed':
        # 幂等：已完成的实验重复运行直接返回既有结果，不重复执行、不追加事件
        return jsonify({**_public(record), 'idempotent': True})
    _event(record, 'run_started', '开始运行')
    store.update(record)
    try:
        prediction = forecast_provider.saved_prediction(record['topic'], record['cutoff_date'])
        if prediction is not None:
            record['forecast'] = prediction
            _event(record, 'forecast_loaded', '已加载保存的历史回测预测（非实时）')
        else:
            record['forecast'] = None
            _event(record, 'forecast_unavailable', '该 topic/cutoff 无已保存预测，不编造数值')
        bundle = forecast_provider.bundles.get(record['bundle_experiment_id'])
        record['simulation'] = simulation_provider.run_simulation(bundle, {})
        _event(record, 'simulation_not_connected', 'B 仿真模块未接入，跳过仿真')
        record['status'] = 'completed'
        record['completed_at'] = _now()
        _event(record, 'run_completed', '运行完成（预测=历史回测保存值；仿真=未接入）')
    except Exception as exc:
        record['status'] = 'failed'
        _event(record, 'run_failed', str(exc))
    store.update(record)
    return jsonify(_public(record))


@futuresim_bp.get('/experiments/<experiment_id>/results')
def get_results(experiment_id):
    record = store.get(experiment_id)
    if record is None:
        return _err('NOT_FOUND', f'实验不存在: {experiment_id}', 404)
    return jsonify({
        'experiment_id': experiment_id,
        'status': record['status'],
        'forecast': record['forecast'],
        'forecast_status': 'saved_result' if record['forecast'] else 'unavailable',
        'simulation': record['simulation'],
    })


@futuresim_bp.get('/experiments/<experiment_id>/events')
def get_events(experiment_id):
    record = store.get(experiment_id)
    if record is None:
        return _err('NOT_FOUND', f'实验不存在: {experiment_id}', 404)
    return jsonify({'experiment_id': experiment_id, 'events': record['events']})
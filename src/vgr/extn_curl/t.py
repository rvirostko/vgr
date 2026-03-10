"""
Handlers for Http statements
"""

from typing import Any
from urllib.parse import (
    urlparse,
    parse_qs,
    urlunparse,
)

from lark import Tree

from .curl_data import (
    HttpData,
    Setting,
)

from .curl_session import (
    HttpSessionManager,
    HttpSession
)

from ..app_exceptions import VgrRuntimeError
from ..builtins import (
    bound_ops,
    default_to,
    poly_bool,
    poly_clamp,
    poly_isempty,
    poly_strip,
    poly_type,
    poly_isnumber,
    poly_number,
    poly_isstr,
    strip_nulls,
)

from ..data_dict import DataDictionary
from ..exec_context import ExecContext
from ..evaluate import (
#    _var_name_path,
    do_set,
#    get_writable_var_path,
)

_ALLOWABLE_METHODS = { 'Get', 'Post', 'Put', 'Patch', 'Delete', 'Head' }
_ALLOWABLE_AUTHS = {'Basic', 'Digest'}
_HTTP_VERSIONS = {'1': '1.0', '1.0': '1.0', '1.1': '1.1', '2': '2', '2.0': '2'}
_VALID_SCHEMES = {'http', 'https'}

_CONSTANTS = [
    # content types
    (("type", "json"),          "application/json"),
    (("type", "form"),          "application/x-www-form-urlencoded"),
    (("type", "text"),          "text/plain"),
    (("type", "html"),          "text/html"),
    (("type", "xml"),           "text/xml"),
    (("type", "binary"),        "application/octet-stream"),
    (("type", "multipart"),     "multipart/form-data"),

    # common header names
    (("header", "content_type"),        "Content-Type"),
    (("header", "accept"),              "Accept"),
    (("header", "authorization"),       "Authorization"),
    (("header", "user_agent"),          "User-Agent"),
    (("header", "cache_control"),       "Cache-Control"),
    (("header", "accept_encoding"),     "Accept-Encoding"),
    (("header", "content_encoding"),    "Content-Encoding"),
    (("header", "content_length"),      "Content-Length"),
    (("header", "location"),            "Location"),
    (("header", "x_request_id"),        "X-Request-Id"),

    # auth schemes
    (("auth", "basic"),     "basic"),
    (("auth", "digest"),    "digest"),

    # http versions
    (("version", "http1"),  "1.0"),
    (("version", "http11"), "1.1"),
    (("version", "http2"),  "2"),

    # status codes
    (("status", "ok"),                  200),
    (("status", "created"),             201),
    (("status", "accepted"),            202),
    (("status", "no_content"),          204),
    (("status", "moved"),               301),
    (("status", "found"),               302),
    (("status", "not_modified"),        304),
    (("status", "bad_request"),         400),
    (("status", "unauthorized"),        401),
    (("status", "forbidden"),           403),
    (("status", "not_found"),           404),
    (("status", "method_not_allowed"),  405),
    (("status", "conflict"),            409),
    (("status", "unprocessable"),       422),
    (("status", "too_many_requests"),   429),
    (("status", "server_error"),        500),
    (("status", "bad_gateway"),         502),
    (("status", "unavailable"),         503),
    (("status", "gateway_timeout"),     504),

    # retryable status codes
    (("retryable",),    [429, 500, 502, 503, 504]),
]

_HTTP_PREFIX = 'http'
_DEFAULT_GIVING_PATH = (_HTTP_PREFIX, 'result')

_SESSIONS = HttpSessionManager()

def http_initialize(dd: DataDictionary) -> None:
    dd.add_immutable_prefix(_HTTP_PREFIX)
    for path, value in _CONSTANTS:
        dd.set_var(value, _HTTP_PREFIX, *path)
    dd.set_var(None, *_DEFAULT_GIVING_PATH)

@bound_ops("Http Connect")
def execute_connect(ctx: ExecContext, statement: Tree) -> None:
    data = HttpData()
    _handle_url(ctx, statement.children[0], data, name='Connect URL')
    _normalize_base_url(ctx, data)
    for child in statement.children[1:]:
        _dispatch_option(ctx, child, data)
    if HttpData.is_missing(data.connection_name):
        raise VgrRuntimeError(HttpData.tree_for(data.connection_name, statement), ValueError('Missing connection name'))
    _SESSIONS.connect(data)

@bound_ops("Http Disconnect")
def execute_disconnect(ctx: ExecContext, statement: Tree) -> None:
    data = HttpData()
    _handle_connection_name(ctx, statement.children[0], data)
    try:
        _SESSIONS.disconnect(data.connection_name.value)
    finally:
        do_set(ctx, None, *_DEFAULT_GIVING_PATH)

@bound_ops("Http Request")
def execute_request(ctx: ExecContext, statement: Tree) -> None:
    data = HttpData()
    # First position arg is the method
    method_arg = statement.children[0]
    data.method = Setting(_handle_constrained_opt(ctx, method_arg, 'hmethod_', 'Method', _ALLOWABLE_METHODS).upper(), method_arg)
    # Second positional arg is the URL (full or fragment)
    _handle_url(ctx, statement.children[1], data, name='Request URL')
    # Rest of args are optional
    for child in statement.children[2:]:
        _dispatch_option(ctx, child, data)
    if HttpData.is_missing(data.connection_name):
        # if no "Using <name>" then this is a stand alone session
        _normalize_base_url(ctx, data)
        # TODO
    else:
        name = data.connection_name.value
        session = _SESSIONS.get_session(name)
        if not session:
            raise VgrRuntimeError(data.connection_name.tree, ValueError(f'Session {name!r} not found'))
        # TODO check for conflicts session.data
        data.url = Setting(_combine_url(ctx, session.data, data), data.url.tree)
        result = session.execute(data)
        print("!!", result)
    # TODO: handle Giving via ctx

def _combine_url(_ctx: ExecContext, session_data: HttpData, request_data: HttpData) -> str:
    """
    Combine session base URL with request URL.
    If request URL contains scheme/host they must match the base — error if not.
    Path is combined: leading slash replaces base path, no leading slash appends.
    Query params are extracted into request_data.parameters — handled via normal merge.
    Fragment is discarded with warning.
    Returns the combined URL string (no query string — params passed separately to httpx).
    """
    base    = urlparse(session_data.url.value)
    request = urlparse(request_data.url.value)
    # if scheme present in request, must match base
    if request.scheme and request.scheme != base.scheme:
        raise VgrRuntimeError(
            request_data.url.tree,
            ValueError(f'Request scheme {request.scheme!r} does not match session scheme {base.scheme!r}')
        )
    # if host present in request, must match base
    if request.netloc and request.netloc.lower() != base.netloc.lower():
        raise VgrRuntimeError(
            request_data.url.tree,
            ValueError(f'Request host {request.netloc!r} does not match session host {base.netloc!r}')
        )
# TODO
#    if request.fragment:
#        ctx.warn(request_data.url.tree, f'Request URL fragment {request.fragment!r} ignored')
    # extract query params into request parameters — explicit Parameter clauses override
    if request.query:
        for key, values in parse_qs(request.query, keep_blank_values=True).items():
            request_data.parameters.setdefault(key, values[-1])
    # combine paths — leading slash replaces, no leading slash appends
    path = request.path or ''
    combined_path = path if path.startswith('/') else base.path + path
    return urlunparse((base.scheme, base.netloc, combined_path, '', '', ''))

def _check_for_duplicate(existing: Setting, incoming: Tree, name: str) -> None:
    if existing is not None and existing.value is not None:
        raise VgrRuntimeError(incoming, ValueError(f'{name} previously set'), )

def _check_str(value: Any, expr: Tree, name: str, allow_none: bool = False) -> str:
    if value is None or (isinstance(value, str) and poly_isempty(value)):
        if allow_none: return None
        raise VgrRuntimeError(expr, ValueError(f'{name} cannot be None or blank'))
    if not isinstance(value, str):
        raise VgrRuntimeError(expr, TypeError(f'{name} must be a string; found {poly_type(value)!r}'))
    return poly_strip(value)

def _resolve_str(ctx: ExecContext, opt: Tree, name: str, allow_none: bool = False) -> str:
    expr = opt.children[0]
    rc = ctx.eval_expr_or_const(expr)
    return _check_str(rc, expr, name, allow_none)

def _resolve_opt_str(ctx: ExecContext, opt: Tree, name: str) -> str:
    return _resolve_str(ctx, opt, name, True)

def _resolve_bool(ctx: ExecContext, opt: Tree, name: str) -> bool:
    if not opt.children: return True
    expr = opt.children[0]
    rc = ctx.eval_expr_or_const(expr)
    if isinstance(rc, (dict, list)):
        raise VgrRuntimeError(expr, TypeError(f'{name} must be a boolean; found {poly_type(rc)!r}'))
    return None if rc is None or (isinstance(rc, str) and poly_isempty(rc)) else poly_bool(rc)

def _to_number(expr: Tree, name: str, value: any) -> Any:
    if not poly_isnumber(value):
        if poly_isstr(value):
            try:
                value = poly_number(value)
            except ValueError as e:
                raise VgrRuntimeError(expr, e) from e
        else:
            raise VgrRuntimeError(expr, TypeError(f'{name} must be numeric; found {poly_type(value)!r}'))
    return value

def _resolve_timeout(ctx: ExecContext, opt: Tree, name: str) -> Setting:
    expr = opt.children[0]
    value = ctx.eval_expr(expr)
    if value is not None:
        value = poly_clamp(_to_number(expr, name, value), 0, 300) # zero (default) to 5 minutes
    return Setting(value, opt)

def _handle_url(ctx: ExecContext, expr: Tree, data: HttpData, name: str = 'URL') -> None:
    rc = ctx.eval_expr(expr)
    if rc is None or not isinstance(rc, str) or poly_isempty(rc):
        raise VgrRuntimeError(expr, ValueError(f'{name} is required and cannot be blank'))
    data.url = Setting(poly_strip(rc), expr)

def _normalize_base_url(ctx: ExecContext, data: HttpData) -> None:
    parsed = urlparse(data.url.value)
    scheme = parsed.scheme.strip().lower()
    if scheme not in _VALID_SCHEMES:
        raise VgrRuntimeError(data.url.tree, ValueError(f'URL scheme must be http or https; found {scheme!r}'))
    host = parsed.netloc.strip().lower()
    if not host:
        raise VgrRuntimeError(data.url.tree, ValueError(f'URL must include a host; got {data.url.value!r}'))
    if parsed.fragment:
        ctx.print_verbose(f'URL fragment {parsed.fragment!r} ignored')
    if parsed.query:
        for key, values in parse_qs(parsed.query, keep_blank_values=True).items():
            data.parameters[key] = values[-1]  # last value wins
    path = (parsed.path or '/').rstrip('/') + '/'
    port = f':{parsed.port}' if parsed.port else ''
    data.url = Setting(f'{scheme}://{host}{port}{path}', data.url.tree)

def _handle_connection_name(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    # NB: opt can be either an option (connect and request)
    #     or a child of the statement (disconnect)
    value = _check_str(ctx.eval_expr_or_const(opt), opt, 'Connection name')
    _check_for_duplicate(data.connection_name, opt, 'Connection name')
    data.connection_name = Setting(value, opt)

def _handle_verify_ssl(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    value = _resolve_bool(ctx, opt, 'Verify SSL')
    _check_for_duplicate(data.verify_ssl, opt, 'Verify SSL')
    data.verify_ssl = Setting(value, opt)

def _handle_ca_cert(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    value = _resolve_opt_str(ctx, opt, 'CA Certificate')
    _check_for_duplicate(data.ca_cert, opt, 'CA Certificate')
    data.ca_cert = Setting(value, opt)

def _handle_connect_timeout(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.connect_timeout, opt, 'Connect Timeout')
    data.connect_timeout = _resolve_timeout(ctx, opt, 'Connect Timeout')

def _handle_timeout(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.timeout, opt, 'Timeout')
    data.timeout = _resolve_timeout(ctx, opt, 'Timeout')

def _handle_read_timeout(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.read_timeout, opt, 'Read Timeout')
    data.read_timeout = _resolve_timeout(ctx, opt, 'Read Timeout')

def _handle_write_timeout(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.write_timeout, opt, 'Write Timeout')
    data.write_timeout = _resolve_timeout(ctx, opt, 'Write Timeout')

def _handle_http_version(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.http_version, opt, 'HTTP Version')
    expr = opt.children[0]
    rc = ctx.eval_expr(expr)
    canonical = _HTTP_VERSIONS.get(poly_strip(str(rc))) if rc is not None else None
    # Had something, but can't be made canonical version
    if rc is not None and canonical is None:
        raise VgrRuntimeError(expr, ValueError(f'Invalid HTTP Version {rc!r}'))
    data.http_version = Setting(canonical, opt)

def _handle_user(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.user, opt, 'User')
    value = _resolve_opt_str(ctx, opt, 'User')
    data.user = Setting(value, opt)

def _handle_password(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.password, opt, 'Password')
    value = _resolve_opt_str(ctx, opt, 'Password')
    data.password = Setting(value, opt)

def _handle_authentication(ctx: ExecContext, node: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.authentication, node, 'Authentication')
    opt = node.children[0]
    data.authentication = Setting(_handle_constrained_opt(ctx, opt, 'hauth_', 'Authentication', _ALLOWABLE_AUTHS).lower(), opt)

def _handle_constrained_opt(ctx: ExecContext, opt: Tree, prefix: str, name: str, allowable_values) -> str:
    key = opt.data.removeprefix(prefix)
    if key == 'dynamic':
        # expression used for value
        value = _resolve_str(ctx, opt, name)
    else:
        # Simple keyword specified
        value = key
    if value.capitalize() not in allowable_values:
        raise VgrRuntimeError(opt, ValueError(f'{name} must be one of {", ".join(allowable_values)}; got {value!r}'))
    return value

def _handle_follow_redirects(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    value = _resolve_bool(ctx, opt, 'Follow Redirects')
    _check_for_duplicate(data.follow_redirects, opt, 'Follow Redirects')
    data.follow_redirects = Setting(value, opt)

def _handle_max_redirects(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.max_redirects, opt, 'Maximum Redirects')
    expr = opt.children[0]
    value = ctx.eval_expr_or_const(expr)
    if value is not None:
        value = poly_clamp(int(_to_number(expr, 'Maximum Redirects', value)), 0, 99)
    data.max_redirects = Setting(value, opt)

def _handle_kv_option(ctx: ExecContext, opt: Tree, data: dict, name: str, separator: str) -> None:
    expr = opt.children[0]
    value = ctx.eval_expr(expr)
    if value is not None:
        if isinstance(value, dict):
            for k, v in value.items(): _update_dict(data, str(k), str(default_to(v, '')))
        elif isinstance(value, list):
            for item in strip_nulls(value): _extract_kv_entry(data, str(item), separator)
        elif isinstance(value, (str, int, float, bool)):
            _extract_kv_entry(data, str(value), separator)
        else:
            raise VgrRuntimeError(expr, TypeError(f'Type {poly_type(value)!r} unsupported for {name}'))

def _extract_kv_entry(target: dict, value: str, separator: str) -> None:
    if poly_isempty(value): return
    parts = value.split(separator, 1)
    _update_dict(target, poly_strip(parts[0]), parts[1] if len(parts) == 2 else '')

def _update_dict(target: dict, k: str, v:str) -> None:
    if poly_isempty(k): return
    target[k] = default_to(v, '')

def _handle_headers(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _handle_kv_option(ctx, opt, data.headers, 'Headers', ':')

def _handle_parameters(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _handle_kv_option(ctx, opt, data.parameters, 'Parameters', '=')

def _handle_body(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    pass  # TODO: body + As type-driven rules

def _handle_giving(ctx: ExecContext, opt: Tree, data: HttpData) -> None:
    _check_for_duplicate(data.giving, opt, 'Giving')
    data.giving = opt

# ---------------------------------------------------------------------------
# Option dispatch table
# ---------------------------------------------------------------------------

_OPTION_HANDLERS = {
    'hopt_authentication':   _handle_authentication,
    'hopt_body':             _handle_body,
    'hopt_ca_cert':          _handle_ca_cert,
    'hopt_connect_timeout':  _handle_connect_timeout,
    'hopt_connection_name':  lambda ctx, opt, data: _handle_connection_name(ctx, opt.children[0], data),
    'hopt_follow_redirects': _handle_follow_redirects,
    'hopt_giving':           _handle_giving,
    'hopt_headers':          _handle_headers,
    'hopt_http_version':     _handle_http_version,
    'hopt_max_redirects':    _handle_max_redirects,
    'hopt_parameters':       _handle_parameters,
    'hopt_password':         _handle_password,
    'hopt_read_timeout':     _handle_read_timeout,
    'hopt_timeout':          _handle_timeout,
    'hopt_user':             _handle_user,
    'hopt_verify_ssl':       _handle_verify_ssl,
    'hopt_write_timeout':    _handle_write_timeout,
}

def _dispatch_option(ctx: ExecContext, node: Tree, data: HttpData) -> None:
    opt_key = node.data
    handler = _OPTION_HANDLERS.get(opt_key)
    if handler is None: raise VgrRuntimeError(node, ValueError(f'Option {opt_key!r} not handled')) # SNO
    handler(ctx, node, data)

# ---------------------------------------------------------------------------
# Phase 2 — cross-field validation
# ---------------------------------------------------------------------------

def _validate_merged(ctx: ExecContext, statement: Tree, data: HttpData) -> None:
    """
    Post-merge cross-field validation.
    Called after connect session defaults and action overrides are combined.
    Errors here point to the statement as a whole — no single option to blame.
    """
    has_user = data.user is not None and data.user.value is not None
    has_pass = data.password is not None and data.password.value is not None
    has_auth = data.authentication is not None and data.authentication.value is not None
    if has_user or has_pass or has_auth:
        if not has_user:
            raise VgrRuntimeError(statement, ValueError('Authentication incomplete: User not provided'))
        if not has_pass:
            raise VgrRuntimeError(statement, ValueError('Authentication incomplete: Password not provided'))

# ---------------------------------------------------------------------------
# Merge — combine session (connect) defaults with request overrides
# ---------------------------------------------------------------------------
def _merge(session: HttpData, request: HttpData) -> HttpData:
    def _pick(vrequest: Setting, vsession: Setting) -> Setting:
        return vsession if vrequest.is_missing() else vrequest

    # URL needs to be a smarter merge
    return HttpData(
        # TODO wrong: url needs to be an intelligent merge
        url              = _pick(request.url, session.url),
        verify_ssl       = _pick(request.verify_ssl, session.verify_ssl),
        ca_cert          = _pick(request.ca_cert, session.ca_cert),
        connect_timeout  = _pick(request.connect_timeout, session.connect_timeout),
        http_version     = _pick(request.http_version, session.http_version),
        user             = _pick(request.user, session.user),
        password         = _pick(request.password, session.password),
        authentication   = _pick(request.authentication, session.authentication),
        timeout          = _pick(request.timeout, session.timeout),
        read_timeout     = _pick(request.read_timeout, session.read_timeout),
        write_timeout    = _pick(request.write_timeout, session.write_timeout),
        follow_redirects = _pick(request.follow_redirects, session.follow_redirects),
        max_redirects    = _pick(request.max_redirects, session.max_redirects),
        headers          = {**session.headers, **request.headers},
        parameters       = {**session.parameters, **request.parameters},
        connection_name  = request.connection_name,
        body             = request.body,
    )

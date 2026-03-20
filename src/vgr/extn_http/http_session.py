"""
The underlying session and session manager for Http statements
"""

from typing import Optional, Dict
import json
import logging
import ssl

import httpx

from .http_data import (
    HttpData,
)

_LOG = logging.getLogger(__name__)

class HttpSession:

    def __init__(self, data: HttpData) -> None:
        self.data   = data
        self.client = self._build_client()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def execute(self, request_data: HttpData) -> httpx.Response:
        """
        Execute an HTTP request from a parsed request HttpData.
        httpx merges request-level headers, params, auth and timeout
        with session-level values automatically — no manual merge needed.
        Single auto-reconnect on stale connection.
        Unrecoverable errors propagate to the handler for DSL failure normalization.
        """
        method = request_data.method.value
        url = request_data.url.value
        self._info(method, ' ', url)
        kwargs = self._build_request_kwargs(request_data)
        try:
            try:
                return self._build_result(request_data, self.client.request(method, url, **kwargs))
            except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
                self._warn(f"Connection stale during {method} request to {url}: {e}; reconnecting")
                self._reconnect()
                return self._build_result(request_data, self.client.request(method, url, **kwargs))
        except httpx.TransportError as e:
                return self._build_result(request_data, None, e)

    def _build_request_kwargs(self, data: HttpData) -> dict:
        """
        Build per-request kwargs for client.request().
        Only non-None values are included — session-level values
        already on the client are left to httpx's own merge logic.
        """
        kwargs = {}
        if data.parameters: kwargs['params'] = data.parameters
        auth = self._build_auth(data)
        if auth is not None: kwargs['auth'] = auth
        timeout = self._build_request_timeout(data)
        if timeout is not None: kwargs['timeout'] = timeout
        if data.follow_redirects is not None: kwargs['follow_redirects'] = data.follow_redirects.value
        if data.max_redirects is not None: kwargs['max_redirects'] = data.max_redirects.value
        # body handled separately — type-driven content-type rules apply
        if not HttpData.is_missing(data.body):
            kwargs.update(self._build_body(data))
        # headers last because building the body can change things
        if data.headers: kwargs['headers'] = data.headers
        return kwargs

    def _build_body(self, data: HttpData) -> dict:
        if HttpData.is_missing(data.body): return {}
        content_type = self._parse_content_type(data.get_content_type())
        is_json = 'json' in content_type
        charset = content_type[2]
        value = data.body.value
        if isinstance(value, (dict, list)) and content_type is None:
            # RFC 8259 mandates UTF-8 on the wire
            data.set_content_type('application/json; charset=utf-8')
            self._info('Setting Content-Type to ', data.get_content_type())
            is_json = True
        if is_json:
            return { 'content': json.dumps(value, indent=None, allow_nan=False).encode('utf-8', errors="replace")}
        # Any other Content-Type is treated as string-ish
        if value is None: return {}
        # Do a more complicated stringification for these
        if isinstance(value, (dict, list)):
            value = json.dumps(value, indent=None, allow_nan=False)
        else:
            value = str(value)
        # Encode using the given (or default) characterset
        return { 'content': value.encode(charset, errors="replace") }

    def _parse_content_type(self, content_type: str) -> tuple[str, str, str]:
        charset = 'utf-8'
        if not content_type: return ('', '', charset)
        parts = content_type.split(';')
        mime  = parts[0].strip().lower()
        mime_parts = mime.split('/', 1)
        if len(mime_parts) != 2: return ('', '', charset)
        mime_type, mime_subtype = mime_parts[0].strip(), mime_parts[1].strip()
        for param in parts[1:]:
            key, _, val = param.strip().partition('=')
            if key.strip().lower() == 'charset':
                charset = val.strip().lower()
                break
        return (mime_type, mime_subtype, charset)

    def close(self) -> None:
        self._info('Closing session to ', self.data.url.value)
        try:
            self.client.close()
        except httpx.TransportError as e:
            self._warn(repr(e))
        finally:
            self.client = None

    def _build_result(self, data: HttpData, response: httpx.Response, failure: Exception=None) -> dict:
        """
        Normalize an httpx Response into the DSL result structure.
        reason is present only when something went wrong — None means clean.
        On transport failure, data fields are omitted — None derefs are safe in DSL.
        """
        if response is None:
            return {
                "method": data.method.value,
                "url":    data.url.value,
                "reason": str(failure) if failure else "Unknown transport failure",
            }
        content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
        body = self._decode_body(response, content_type)
        result = {
            "response":     body,
            "url":          data.url.value,
            "method":       data.method.value,
            "status_code":  response.status_code,
            "headers":      {key.title() : value for key, value in response.headers.items()}
        }
        if not response.is_success:
            result["reason"] = response.reason_phrase
        return result

    def _decode_body(self, response: httpx.Response, content_type: str) -> tuple[str, any]:
        """
        Decode response body into a DSL-compatible type.
        json    → dict or list
        text/*  → str
        other   → hex string of raw bytes (DSL hex routines handle further processing)
        Falls back gracefully — JSON parse failure drops to text,
        text decode failure drops to hex.
        CSV, XML, and other structured formats are left as text for DSL routines to parse.
        """
        if "json" in content_type:
            try:
                return response.json()
            except (ValueError, httpx.DecodingError) as e:
                self._warn(repr(e))
        if content_type.startswith("text/"):
            try:
                return response.text
            except (UnicodeDecodeError, httpx.DecodingError) as e:
                self._warn(repr(e))
        return response.content.hex()

    def _reconnect(self) -> None:
        self._warn('Reconnecting to ', self.data.url.value)
        self.close()
        self.client = self._build_client()

    def _build_client(self) -> httpx.Client:
        kwargs = {'base_url': self.data.url.value}
        if self.data.headers: kwargs['headers'] = self.data.headers
        if self.data.parameters: kwargs['params'] = self.data.parameters
        kwargs['verify'] = self._build_ssl_context()
        auth = self._build_auth(self.data)
        if auth is not None: kwargs['auth'] = auth
        if self.data.follow_redirects is not None: kwargs['follow_redirects'] = self.data.follow_redirects.value
        if self.data.max_redirects is not None: kwargs['max_redirects'] = self.data.max_redirects.value
        timeout = self._build_timeout()
        if timeout is not None: kwargs['timeout'] = timeout
        kwargs.update(self._build_http_version())
        self._info('Connecting to ', self.data.url.value)
        return httpx.Client(**kwargs)

    def _build_timeout(self) -> httpx.Timeout:
        total   = self.data.timeout.value         if self.data.timeout         else None
        connect = self.data.connect_timeout.value if self.data.connect_timeout else total
        read    = self.data.read_timeout.value    if self.data.read_timeout    else total
        write   = self.data.write_timeout.value   if self.data.write_timeout   else total
        return None if all(v is None for v in (total, connect, read, write)) else \
               httpx.Timeout(timeout=total, connect=connect, read=read, write=write)

    def _build_request_timeout(self, data: HttpData) -> httpx.Timeout:
        total = data.timeout.value         if data.timeout         else None
        read  = data.read_timeout.value    if data.read_timeout    else total
        write = data.write_timeout.value   if data.write_timeout   else total
        return None if all(v is None for v in (total, read, write)) else \
            httpx.Timeout(timeout=total, read=read, write=write)

    def _build_ssl_context(self) -> ssl.SSLContext:
        """
        Build SSL verification argument for httpx.Client.
        CA cert present  → SSLContext with in-memory PEM loaded
        verify_ssl False → False
        otherwise        → True (httpx default)
        """
        if not HttpData.is_missing(self.data.ca_cert):
            context = ssl.create_default_context()
            context.load_verify_locations(cadata=self.data.ca_cert.value)
            return context
        return self.data.verify_ssl.value if self.data.verify_ssl is not None else True

    def _build_auth(self, data: HttpData):
        """
        Build request-level auth from action HttpData.
        Same logic as session-level auth construction.
        Returns None if neither user nor password is set — session auth applies.
        """
        if HttpData.is_missing(data.user) and HttpData.is_missing(data.password):
            return None
        user = data.user.value     if not HttpData.is_missing(data.user)     else ''
        pwd  = data.password.value if not HttpData.is_missing(data.password) else ''
        return httpx.DigestAuth(user, pwd) if (
            not HttpData.is_missing(data.authentication) and
            data.authentication.value == 'digest'
        ) else httpx.BasicAuth(user, pwd)

    def _build_http_version(self) -> dict:
        """
        Derive http1/http2 kwargs from http_version Setting.
        Returns empty dict when unset — httpx defaults apply (http1=True, http2=False).
        """
        if not HttpData.is_missing(self.data.http_version):
            v = self.data.http_version.value
            if v in ('1.0', '1.1'): return {'http1': True,  'http2': False}
            if v == '2':             return {'http1': False, 'http2': True}
        return {}

    @staticmethod
    def _error(*args) -> None:
        _LOG.error(''.join(str(arg) for arg in args))

    @staticmethod
    def _warn(*args) -> None:
        if _LOG.isEnabledFor(logging.WARNING):
            _LOG.warning(''.join(str(arg) for arg in args))

    @staticmethod
    def _info(*args) -> None:
        if _LOG.isEnabledFor(logging.INFO):
            _LOG.info(''.join(str(arg) for arg in args))

    @staticmethod
    def _debug(*args) -> None:
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug(''.join(str(arg) for arg in args))


class HttpSessionManager:

    def __init__(self):
        self._sessions: Dict[str, HttpSession] = {}

    def connect(self, data: HttpData) -> HttpSession:
        """Create and store a session under the given name."""
        name = self._normalize_name(data.connection_name.value)
        # if we had one previously, close it
        self.disconnect(name)
        session = HttpSession(data)
        self._sessions[name] = session
        return session

    def disconnect(self, name: str) -> None:
        """Remove a named session. No error if it does not exist."""
        name = self._normalize_name(name)
        if name in self._sessions:
            self._sessions.pop(name).close()

    def get_session(self, name: str) -> HttpSession:
        """Return the session for the given name."""
        return self._sessions.get(self._normalize_name(name), None)

    def _normalize_name(self, name: Optional[str]) -> str:
        if not name or name.isspace() == '':
            raise ValueError('Missing name for Http session')
        return name.strip()

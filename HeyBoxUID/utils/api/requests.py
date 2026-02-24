import uuid
import logging
from typing import Any, Dict, Optional
from typing_extensions import Self

import httpx

from .utils import XhhUtil

try:
    from gsuid_core.logger import logger  # type: ignore
except ImportError:
    logger = logging.getLogger("xhh")

headers = {
    "User-Agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36 ApiMaxJia/1.0",
    "referer": "http://api.maxjia.com/",
    "host": "api.xiaoheihe.cn",
    "connection": "Keep-Alive",
    "accept-encoding": "gzip",
    "content-type": "application/json; charset=UTF-8",
}


class XhhRequest:
    """
    HTTP 请求基类

    子类通过继承获得：
      - self.client       异步 HTTP 客户端（httpx.AsyncClient）
      - _get_request()    裸 GET（不签名）
      - _post_request()   裸 POST（不签名）
      - _signed_get()     带签名 GET（对外 API 统一走这里）
      - _signed_post()    带签名 POST

    不直接实例化，由 XhhApi 继承使用。
    """

    # 子类可覆盖，指向不同环境的 base_url
    BASE_URL: str = "https://api.xiaoheihe.cn"

    def __init__(
        self,
        heybox_id: str,
        pkey: str,
        x_xhh_tokenid: str,
        # imei: str = "9243b67a1d97e2a1",
        # device_info: str = "V2171A",
        nonce: str = uuid.uuid4().hex,
        os_type: str = "web",
        x_os_type: str = "Windows",
        x_app: str = "heybox_website",
        x_client_type: str = "web",
        # os_version: str = "11",
        version: str = "999.0.3",
        # app_version: str = "1.3.339",
        # build: str = "892",
        # dw: str = "480",
        # channel: str = "heybox",
        # x_app: str = "heybox",
    ):
        self.heybox_id = heybox_id
        self.pkey = pkey
        self.x_xhh_tokenid = x_xhh_tokenid
        # self.imei = imei
        self.os_type = os_type
        # self.os_version = os_version
        self.version = version
        # self.app_version = app_version
        self.nonce = nonce
        # self.device_info = device_info
        self.x_os_type = x_os_type
        # self.build = build
        # self.dw = dw
        # self.channel = channel
        self.x_app = x_app
        self.x_client_type = x_client_type

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30,
            cookies=self.client.cookies,
        )

    # ── 生命周期 ────────────────────────────────────────────────────────────

    async def close(self) -> None:
        """关闭 HTTP 连接池"""
        await self.client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    # ── 签名参数构造 ────────────────────────────────────────────────────────

    def _build_params(
        self,
        path: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        为指定 path 生成带签名的公共 Query 参数

        Args:
            path:  API 路径，如 "/bbs/app/feeds/news"
            extra: 需要追加的业务参数

        Returns:
            包含 heybox_id / imei / os_type / os_version /
            version / _time / hkey 及 extra 的完整参数字典
        """
        return XhhUtil.build_common_params(
            path=path,
            heybox_id=self.heybox_id,
            # imei=self.imei,
            version=self.version,
            os_type=self.os_type,
            # os_version=self.os_version,
            # app_version=self.app_version,
            extra=extra,
            nonce=self.nonce,
            # device_info=self.device_info,
            x_os_type=self.x_os_type,
            # build=self.build,
            # dw=self.dw,
            # channel=self.channel,
            x_app=self.x_app,
        )

    # ── 裸请求（不签名）────────────────────────────────────────────────────

    async def _get_request(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = headers,
    ) -> dict:
        """
        发送 GET 请求，返回解析后的 JSON dict。

        不会自动注入签名参数，适用于无需鉴权的接口
        或已由调用方手动构造完整 params 的场景。

        Args:
            path:    请求路径（相对于 BASE_URL）
            params:  Query 参数
            headers: 请求头；为 None 时使用子类的 DEFAULT_HEADERS

        Returns:
            响应 JSON dict；请求失败时返回 {"status": "error", "message": "..."}
        """
        try:
            # cookies = {"pkey": self.pkey, "x_xhh_tokenid": self.x_xhh_tokenid}
            # logger.info(f"[XHH] GET {path} params={params} headers={headers} cookies={cookies}")
            resp = await self.client.get(
                path,
                params=params,
                headers=headers,
                # cookies={"pkey": self.pkey, "x_xhh_tokenid": self.x_xhh_tokenid},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"[XHH] GET {path} HTTP错误: {e.response.status_code}")
            return {"status": "error", "message": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.exception(f"[XHH] GET {path} 请求失败: {e}")
            return {"status": "error", "message": str(e)}

    async def _post_request(
        self,
        path: str,
        form_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = headers,
    ) -> dict:
        """
        发送 POST 请求，返回解析后的 JSON dict。

        Args:
            path:      请求路径
            form_data: 表单 body（application/x-www-form-urlencoded）
            params:    Query 参数
            headers:   请求头

        Returns:
            响应 JSON dict；请求失败时返回 {"status": "error", "message": "..."}
        """
        try:
            resp = await self.client.post(
                path,
                data=form_data,
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"[XHH] POST {path} HTTP错误: {e.response.status_code}")
            return {"status": "error", "message": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.exception(f"[XHH] POST {path} 请求失败: {e}")
            return {"status": "error", "message": str(e)}

    # ── 签名请求（业务层统一入口）──────────────────────────────────────────

    async def _signed_get(
        self,
        path: str,
        extra_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = headers,
    ) -> dict:
        """
        带自动签名的 GET 请求。

        自动调用 _build_params() 注入 hkey / _time 等公共参数，
        XhhApi 中的所有业务方法统一通过此接口发起请求。

        Args:
            path:         API 路径
            extra_params: 业务专属参数（如 app_id / limit / offset 等）
            headers:      自定义请求头；为 None 时使用 DEFAULT_HEADERS

        Returns:
            响应 JSON dict
        """
        params = self._build_params(path, extra_params)
        return await self._get_request(path, params=params, headers=headers)

    async def _signed_post(
        self,
        path: str,
        form_data: Optional[Dict[str, Any]] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = headers,
    ) -> dict:
        """
        带自动签名的 POST 请求。

        Args:
            path:         API 路径
            form_data:    POST 表单 body
            extra_params: 附加到 Query 的业务参数
            headers:      自定义请求头

        Returns:
            响应 JSON dict
        """
        params = self._build_params(path, extra_params)
        return await self._post_request(path, form_data=form_data, params=params, headers=headers)

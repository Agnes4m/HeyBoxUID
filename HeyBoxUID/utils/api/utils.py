import time
import uuid
import hashlib
import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlparse

# ── 全局常量 ────────────────────────────────────────────────────────────────

BASE_URL = "https://api.xiaoheihe.cn"

API_CONSTANTS: Dict[str, Any] = {
    # 用户 & 账号
    "USER_INFO": "/account/app/account/info/",
    "USER_PROFILE": "/account/app/account/profile/",
    "NOTIFICATION_LIST": "/account/app/notification/list/",
    # 资讯 & 社区
    "FEEDS_NEWS": "/bbs/app/feeds/news",
    "FEEDS_HOT": "/bbs/app/feeds/hot",
    "POST_DETAIL": "/bbs/app/post/info/",
    "POST_COMMENT": "/bbs/app/post/comment/list/",
    "SEARCH_POSTS": "/bbs/app/search/post/",
    # 游戏数据
    "GAME_INFO": "/game/app/link/info/",
    "GAME_LOWEST_PRICE": "/game/app/lowest_price/",
    "GAME_SEARCH": "/game/app/search/",
    "GAME_ACHIEVEMENT": "/game/app/achievement/",
    "GAME_LIBRARY": "/game/app/library/",
    "GAME_WISH": "/game/app/wish_list/",
    "GAME_RANK": "/game/app/rank/",
    # 商店
    "STORE_HOME": "/store/app/index/",
    "STORE_SALE": "/store/app/sale/",
    # 通用请求头
    "REQUEST_HEADERS_BASE": {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.91 Mobile Safari/537.36"
        ),
        "Referer": "http://api.maxjia.com/",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
    },
}

# ── 枚举值映射 ──────────────────────────────────────────────────────────────

# 游戏评测评分区间
REVIEW_SCORE_MAP = {
    (90, 100): "好评如潮",
    (80, 90): "特别好评",
    (70, 80): "多半好评",
    (40, 70): "褒贬不一",
    (20, 40): "多半差评",
    (0, 20): "差评如潮",
}

# 游戏平台 ID
PLATFORM_MAP = {
    1: "Steam",
    2: "PS",
    3: "Xbox",
    4: "Nintendo",
    5: "iOS",
    6: "Android",
    7: "Epic",
}


class XhhUtil:
    """小黑盒专用工具方法（全部为静态方法，无需实例化）"""

    # ── 核心签名 ────────────────────────────────────────────────────────────

    @staticmethod
    def _md5(data: str) -> str:
        """计算字符串 MD5 十六进制摘要"""
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    @staticmethod
    def gen_hkey(path: str, timestamp: Optional[int] = None) -> tuple[str, int]:
        """
        生成小黑盒 API 请求的 hkey 签名

        算法（逆向还原）：
          raw   = path + "/bfhdkud_time=" + timestamp
          step1 = MD5(raw)
          step2 = step1.replace('a', 'app').replace('0', 'app')
          hkey  = MD5(step2)[:10]

        Args:
            path:      API 路径，如 "/bbs/app/feeds/news"
            timestamp: Unix 时间戳（秒），None 则自动取当前时间

        Returns:
            (hkey, timestamp) 元组
        """
        if timestamp is None:
            timestamp = int(time.time())

        # 若传入完整 URL，提取 path 部分
        if path.startswith("http"):
            path = urlparse(path).path.rstrip("/")

        raw = f"{path}/bfhdkud_time={timestamp}"
        step1 = XhhUtil._md5(raw)
        step2 = step1.replace("a", "app").replace("0", "app")
        hkey = XhhUtil._md5(step2)[:10].upper()
        return hkey, timestamp

    # ── 参数构造 ────────────────────────────────────────────────────────────

    @staticmethod
    def build_common_params(
        path: str,
        heybox_id: str,
        x_client_type: str = "web",
        version: str = "999.0.3",
        # imei: str = "9243b67a1d97e2a1",
        # device_info: str = "V2171A",
        os_type: str = "web",
        # os_version: str = "9",
        # app_version: str = "1.3.339",
        nonce: str = uuid.uuid4().hex,
        extra: Optional[Dict[str, Any]] = None,
        x_os_type: str = "Windows",
        # build: str = "892",
        # dw: str = "480",
        # channel: str = "heybox",
        x_app: str = "heybox",
    ) -> Dict[str, Any]:
        """
        构造每次请求都需要附带的公共 Query 参数（含自动签名）

        Args:
            path:        API 路径
            heybox_id:   用户 heybox_id
            imei:        设备 IMEI（任意15位字符串即可）
            os_type:     操作系统类型
            os_version:  操作系统版本
            app_version: App 版本号
            extra:       额外附加参数
            nonce:       随机数（任意32位字符串即可）

        Returns:
            完整参数字典
        """
        hkey, ts = XhhUtil.gen_hkey(path)
        params: Dict[str, Any] = {
            "heybox_id": heybox_id,
            # "imei": imei,
            "os_type": os_type,
            "x_client_type": x_client_type,
            "version": version,
            # "os_version": os_version,
            # "version": app_version,
            "_time": ts,
            "hkey": hkey,
            "nonce": nonce,
            # "device_info": device_info,
            "x_os_type": x_os_type,
            # "build": build,
            # "dw": dw,
            # "channel": channel,
            "x_app": x_app,
        }
        if extra:
            params.update(extra)
        return params

    # ── 响应解析 ────────────────────────────────────────────────────────────

    @staticmethod
    def parse_response(
        data: dict,
        status_key: str = "status",
        ok_value: Any = "ok",
        data_key: str = "data",
    ) -> Dict[str, Any]:
        """
        解析小黑盒 API 标准响应格式

        小黑盒正常响应结构：
          {"status": "ok", "data": {...}, ...}

        Args:
            data:       原始响应 dict
            status_key: 状态字段名（默认 "status"）
            ok_value:   成功时的状态值（默认 "ok"）
            data_key:   数据字段名（默认 "data"）

        Returns:
            {"status": bool, "message": str, "data": dict}
        """
        if data.get(status_key) == ok_value:
            return {
                "status": True,
                "message": "获取成功",
                "data": data.get(data_key, {}),
            }
        msg = data.get("message", data.get("msg", f"请求失败: {data.get(status_key)}"))
        return {
            "status": False,
            "message": str(msg),
            "data": {},
        }

    # ── 格式转换 ────────────────────────────────────────────────────────────

    @staticmethod
    def get_review_label(score: int) -> str:
        """将评分（0-100）转换为可读评价标签"""
        for (lo, hi), label in REVIEW_SCORE_MAP.items():
            if lo <= score < hi:
                return label
        return f"未知评分({score})"

    @staticmethod
    def get_platform_name(platform_id: int) -> str:
        """平台 ID 转可读名称"""
        return PLATFORM_MAP.get(platform_id, f"未知平台({platform_id})")

    @staticmethod
    def trans_num_easy_for_read(num: int | str) -> str:
        """数字简化显示（K/M 单位）"""
        if isinstance(num, str):
            try:
                num = int(num)
            except ValueError:
                return num
        if num < 1000:
            return str(num)
        elif num < 1_000_000:
            return f"{num / 1000:.1f}K"
        else:
            return f"{num / 1_000_000:.1f}M"

    @staticmethod
    def timestamp_to_readable(timestamp: int) -> str:
        """Unix 时间戳 → 可读时间字符串（如 "2025-01-21 14:30:00"）"""
        try:
            return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "未知时间"

    @staticmethod
    def price_fen_to_yuan(price_fen: int | str) -> str:
        """将分转换为元字符串（如 1999 → "¥19.99"）"""
        if isinstance(price_fen, str):
            price_fen = int(price_fen)
        if price_fen == 0:
            return "免费"
        return f"¥{price_fen / 100:.2f}"

    @staticmethod
    def get_micro_time() -> int:
        """获取微秒级时间戳（与参考项目一致）"""
        return int(time.time() * 1_000_000)

    @staticmethod
    def safe_get(d: dict, *keys: str, default: Any = None) -> Any:
        """安全多级取值，键不存在时返回 default"""
        cur = d
        for k in keys:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(k, default)
            if cur is None:
                return default
        return cur


if __name__ == "__main__":
    # 快速验证签名生成
    hkey, ts = XhhUtil.gen_hkey("/bbs/app/feeds/news")
    print(f"hkey  : {hkey}  (应为10位: {'✓' if len(hkey) == 10 else '✗'})")
    print(f"_time : {ts}")
    print(f"price : {XhhUtil.price_fen_to_yuan(4999)}")
    print(f"score : {XhhUtil.get_review_label(85)}")

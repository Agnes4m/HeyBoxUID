from typing import Any, Dict, Optional

from .utils import XhhUtil
from .requests import XhhRequest


class ApiPath:
    """所有接口的路径常量（相对于 BASE_URL）"""

    # ── 用户 & 账号 ──────────────────────────────────────────────────────
    USER_INFO = "/account/app/account/info/"
    USER_PROFILE = "/account/app/account/profile/"
    NOTIFICATION_LIST = "/account/app/notification/list/"

    # ── 资讯 & 社区 ──────────────────────────────────────────────────────
    FEEDS_NEWS = "/bbs/app/feeds/news"
    FEEDS_HOT = "/bbs/app/feeds/hot"
    POST_DETAIL = "/bbs/app/post/info/"
    POST_COMMENT = "/bbs/app/post/comment/list/"
    SEARCH_POSTS = "/bbs/app/search/post/"

    # ── 游戏数据 ─────────────────────────────────────────────────────────
    GAME_INFO = "/game/app/link/info/"
    GAME_LOWEST_PRICE = "/game/app/lowest_price/"
    GAME_SEARCH = "/game/app/search/"
    GAME_ACHIEVEMENT = "/game/app/achievement/"
    GAME_LIBRARY = "/game/app/library/"
    GAME_WISH = "/game/app/wish_list/"
    GAME_RANK = "/game/app/rank/"

    # ── 商店 ─────────────────────────────────────────────────────────────
    STORE_HOME = "/store/app/index/"
    STORE_SALE = "/store/app/sale/"

    # ── 签到 & 任务 ──────────────────────────────────────────────────────
    TASK_STATS = "/task/stats/"  # 签到 + 任务完成状态（GET）
    TASK_LIST = "/task/list/"  # 任务列表（GET）


class ApiHeader:
    """请求头预设"""

    # 通用 JSON 请求头（大多数 GET 接口使用）
    DEFAULT: Dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.91 Mobile Safari/537.36"
        ),
        "Referer": "http://api.maxjia.com/",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
    }

    # 表单 POST 请求头
    FORM: Dict[str, str] = {
        **DEFAULT,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # 带平台标识的请求头（某些接口需要）
    PLATFORM: Dict[str, str] = {
        **DEFAULT,
        "platform": "android",
    }


class XhhApi(XhhRequest):
    """
    小黑盒业务 API 客户端

    继承 XhhRequest 获得 HTTP 收发能力，
    在此基础上实现各业务接口的参数构造、请求发起与响应解析。

    用法::

        # 推荐：async context manager，自动关闭连接
        async with XhhApi(heybox_id="12345678", pkey="your_pkey") as api:
            news = await api.get_news()
            game = await api.get_game_info(730)

        # 或手动管理：
        api = XhhApi(heybox_id="...", pkey="...")
        news = await api.get_news()
        await api.close()
    """

    # 覆盖基类 BASE_URL（此处与默认值相同，便于测试时切换环境）
    BASE_URL = "https://api.xiaoheihe.cn"

    async def get_user_info(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取用户主页基础信息

        Args:
            user_id: 目标用户 ID；为 None 时返回当前登录账号自身信息

        Returns::

            {
                "status": True,
                "message": "获取成功",
                "data": {
                    "heybox_id":  "12345678",
                    "nick_name":  "玩家昵称",
                    "avatar":     "https://...",
                    "level":      10,
                    "exp":        2500,
                    ...
                }
            }
        """
        extra: Dict[str, Any] = {}
        if user_id:
            extra["link_id"] = user_id

        raw = await self._signed_get(
            ApiPath.USER_INFO,
            extra_params=extra,
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户详细资料（关注数、粉丝数、游戏数等）

        Args:
            user_id: 目标用户 heybox_id（必填）

        Returns::

            {
                "status": True,
                "data": {
                    "follow_count":    100,
                    "follower_count":  200,
                    "game_count":       50,
                    ...
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.USER_PROFILE,
            extra_params={"link_id": user_id},
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def get_notifications(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取当前账号的通知消息列表

        Args:
            limit:  每页数量（默认 20）
            offset: 分页偏移

        Returns::

            {
                "status": True,
                "data": {
                    "total": 50,
                    "list":  [ {"type": "like", "content": "...", ...}, ... ]
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.NOTIFICATION_LIST,
            extra_params={"limit": limit, "offset": offset},
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    # ══════════════════════════════════════════════════════════════════
    #  资讯 & 社区
    # ══════════════════════════════════════════════════════════════════

    async def get_news(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取首页资讯信息流

        Args:
            limit:  每页数量
            offset: 分页偏移

        Returns::

            {
                "status": True,
                "data": {
                    "list": [
                        {
                            "post_id":  "abc123",
                            "title":    "资讯标题",
                            "summary":  "摘要...",
                            "cover":    "https://...",
                            "view_num": 1234,
                            ...
                        },
                        ...
                    ]
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.FEEDS_NEWS,
            extra_params={"limit": limit, "offset": offset},
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def get_hot_posts(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取热门帖子列表

        Args:
            limit:  每页数量
            offset: 分页偏移

        Returns::

            {"status": True, "data": {"list": [...]}}
        """
        raw = await self._signed_get(
            ApiPath.FEEDS_HOT,
            extra_params={"limit": limit, "offset": offset},
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def get_post_detail(self, post_id: str) -> Dict[str, Any]:
        """
        获取帖子详情

        Args:
            post_id: 帖子 ID

        Returns::

            {
                "status": True,
                "data": {
                    "post_id":     "abc123",
                    "title":       "帖子标题",
                    "content":     "正文内容...",
                    "like_num":    88,
                    "comment_num": 12,
                    "author":      {"nick_name": "...", ...},
                    ...
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.POST_DETAIL,
            extra_params={"post_id": post_id},
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def get_post_comments(
        self,
        post_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取帖子评论列表

        Args:
            post_id: 帖子 ID
            limit:   每页数量
            offset:  分页偏移

        Returns::

            {"status": True, "data": {"total": 30, "list": [{"content": "...", "user": {...}}, ...]}}
        """
        raw = await self._signed_get(
            ApiPath.POST_COMMENT,
            extra_params={"post_id": post_id, "limit": limit, "offset": offset},
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def search_posts(
        self,
        keyword: str,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        搜索帖子

        Args:
            keyword: 搜索关键词
            limit:   每页数量
            offset:  分页偏移

        Returns::

            {"status": True, "data": {"list": [...]}}
        """
        raw = await self._signed_get(
            ApiPath.SEARCH_POSTS,
            extra_params={"keyword": keyword, "limit": limit, "offset": offset},
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    # ══════════════════════════════════════════════════════════════════
    #  游戏数据
    # ══════════════════════════════════════════════════════════════════

    async def get_game_info(self, app_id: int) -> Dict[str, Any]:
        """
        获取游戏详情（使用 Steam AppID）

        Args:
            app_id: Steam AppID，如 730（CS2）、1245620（Elden Ring）

        Returns::

            {
                "status": True,
                "data": {
                    "app_id":       730,
                    "name":         "Counter-Strike 2",
                    "description":  "...",
                    "cover":        "https://...",
                    "review_score": 85,
                    "review_label": "特别好评",   ← 附加字段
                    "tags":         ["FPS", "多人"],
                    ...
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.GAME_INFO,
            extra_params={"app_id": app_id},
            headers=ApiHeader.DEFAULT,
        )
        result = XhhUtil.parse_response(raw)

        # 附加可读评分标签
        if result["status"] and isinstance(result["data"], dict):
            score = result["data"].get("review_score", 0)
            result["data"]["review_label"] = XhhUtil.get_review_label(score)

        return result

    async def get_game_lowest_price(self, app_id: int) -> Dict[str, Any]:
        """
        获取游戏史低价格

        Args:
            app_id: Steam AppID

        Returns::

            {
                "status": True,
                "data": {
                    "lowest_price":        999,
                    "lowest_price_label":  "¥9.99",   ← 附加字段
                    "lowest_price_date":   "2023-06-22",
                    "current_price":       1999,
                    "current_price_label": "¥19.99",  ← 附加字段
                    "discount":            50,
                    ...
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.GAME_LOWEST_PRICE,
            extra_params={"app_id": app_id},
            headers=ApiHeader.DEFAULT,
        )
        result = XhhUtil.parse_response(raw)

        # 附加可读价格标签
        if result["status"] and isinstance(result["data"], dict):
            d = result["data"]
            if "lowest_price" in d:
                d["lowest_price_label"] = XhhUtil.price_fen_to_yuan(d["lowest_price"])
            if "current_price" in d:
                d["current_price_label"] = XhhUtil.price_fen_to_yuan(d["current_price"])

        return result

    async def search_game(
        self,
        keyword: str,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        搜索游戏

        Args:
            keyword: 关键词，如 "赛博朋克 2077"
            limit:   每页数量
            offset:  分页偏移

        Returns::

            {
                "status": True,
                "data": {
                    "total": 3,
                    "list": [
                        {"app_id": 1091500, "name": "Cyberpunk 2077", ...},
                        ...
                    ]
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.GAME_SEARCH,
            extra_params={"keyword": keyword, "limit": limit, "offset": offset},
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def get_game_achievement(self, app_id: int) -> Dict[str, Any]:
        """
        获取当前账号在指定游戏的成就完成情况

        Args:
            app_id: Steam AppID

        Returns::

            {
                "status": True,
                "data": {
                    "total":    50,
                    "achieved": 30,
                    "progress": "60.0%",   ← 附加字段
                    "list": [
                        {"name": "第一滴血", "achieved": True, ...},
                        ...
                    ]
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.GAME_ACHIEVEMENT,
            extra_params={"app_id": app_id},
            headers=ApiHeader.DEFAULT,
        )
        result = XhhUtil.parse_response(raw)

        # 附加完成进度百分比
        if result["status"] and isinstance(result["data"], dict):
            d = result["data"]
            total = d.get("total", 0)
            achieved = d.get("achieved", 0)
            d["progress"] = f"{achieved / total * 100:.1f}%" if total > 0 else "0.0%"

        return result

    async def get_game_library(
        self,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取用户游戏库列表

        Args:
            user_id: 目标用户 ID；为 None 时查询自身
            limit:   每页数量
            offset:  分页偏移

        Returns::

            {
                "status": True,
                "data": {
                    "total": 100,
                    "list":  [{"app_id": 730, "name": "CS2", "play_time": 1200, ...}, ...]
                }
            }
        """
        extra: Dict[str, Any] = {"limit": limit, "offset": offset}
        if user_id:
            extra["link_id"] = user_id

        raw = await self._signed_get(
            ApiPath.GAME_LIBRARY,
            extra_params=extra,
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def get_game_wish(
        self,
        user_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取用户愿望单列表

        Args:
            user_id: 目标用户 ID；为 None 时查询自身
            limit:   每页数量
            offset:  分页偏移

        Returns::

            {
                "status": True,
                "data": {
                    "total": 10,
                    "list":  [{"app_id": 1172620, "name": "Apex Legends", ...}, ...]
                }
            }
        """
        extra: Dict[str, Any] = {"limit": limit, "offset": offset}
        if user_id:
            extra["link_id"] = user_id

        raw = await self._signed_get(
            ApiPath.GAME_WISH,
            extra_params=extra,
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def get_game_rank(
        self,
        rank_type: str = "hot",
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取游戏排行榜

        Args:
            rank_type: 榜单类型，如 "hot"（热度）/ "new"（新品）/ "sale"（促销）
            limit:     每页数量
            offset:    分页偏移

        Returns::

            {
                "status": True,
                "data": {
                    "list": [{"rank": 1, "app_id": 730, "name": "CS2", ...}, ...]
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.GAME_RANK,
            extra_params={"type": rank_type, "limit": limit, "offset": offset},
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    # ══════════════════════════════════════════════════════════════════
    #  商店
    # ══════════════════════════════════════════════════════════════════

    async def get_store_home(self) -> Dict[str, Any]:
        """
        获取商店首页推荐内容（特惠 / 新品 / 热销等）

        Returns::

            {
                "status": True,
                "data": {
                    "banner":    [...],
                    "hot_sale":  [...],
                    "new_games": [...],
                    ...
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.STORE_HOME,
            headers=ApiHeader.DEFAULT,
        )
        return XhhUtil.parse_response(raw)

    async def get_store_sale(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        获取商店促销游戏列表

        Args:
            limit:  每页数量
            offset: 分页偏移

        Returns::

            {
                "status": True,
                "data": {
                    "total": 120,
                    "list": [
                        {
                            "app_id":               1091500,
                            "name":                 "Cyberpunk 2077",
                            "discount":             50,
                            "current_price":        9999,
                            "current_price_label":  "¥99.99",   ← 附加字段
                            "original_price":       19999,
                            "original_price_label": "¥199.99",  ← 附加字段
                            "sale_end_time":        "2025-02-28 08:00:00",
                            ...
                        },
                        ...
                    ]
                }
            }
        """
        raw = await self._signed_get(
            ApiPath.STORE_SALE,
            extra_params={"limit": limit, "offset": offset},
            headers=ApiHeader.DEFAULT,
        )
        result = XhhUtil.parse_response(raw)

        # 批量附加可读价格标签 & 时间格式转换
        if result["status"] and isinstance(result["data"], dict):
            for item in result["data"].get("list", []):
                if "current_price" in item:
                    item["current_price_label"] = XhhUtil.price_fen_to_yuan(item["current_price"])
                if "original_price" in item:
                    item["original_price_label"] = XhhUtil.price_fen_to_yuan(item["original_price"])
                if isinstance(item.get("sale_end_time"), int):
                    item["sale_end_time"] = XhhUtil.timestamp_to_readable(item["sale_end_time"])

        return result

    # ══════════════════════════════════════════════════════════════════
    #  签到 & 任务
    # ══════════════════════════════════════════════════════════════════

    async def get_task_stats(self) -> Dict[str, Any]:
        """
        查询签到 & 任务完成状态（不执行签到，只读取）。

        Returns::

            {
                "status": True,
                "data": {
                    "sign_in": True,  # 今日是否已签到
                    "sign_in_streak": 7,  # 连续签到天数
                    "coin": 100,  # 今日获得/可获得盒币
                    "exp": 120,  # 当前经验值
                    "max_exp": 200,  # 升级所需经验
                    "share": False,  # 今日是否完成分享任务
                    "like": False,  # 今日是否完成点赞任务
                },
            }
        """
        raw = await self._signed_get(
            ApiPath.TASK_STATS,
            headers=ApiHeader.DEFAULT,
        )
        return _parse_task_stats(raw)

    async def checkin(self) -> Dict[str, Any]:
        """
        执行每日签到。

        小黑盒签到通过 GET /task/stats/ 触发，
        服务端以首次访问即签到的方式处理。

        Returns::

            {
                "status":  True,
                "message": "签到成功！获得盒币 +100",
                "data": {
                    "sign_in":        True,
                    "sign_in_streak": 8,
                    "coin":           100,
                    "exp":            125,
                    "max_exp":        200,
                    "share":          False,
                    "like":           False,
                }
            }
            或已签到时 status=False, message="今日已签到"
        """
        raw = await self._signed_get(
            ApiPath.TASK_STATS,
            headers=ApiHeader.DEFAULT,
        )
        return _parse_task_stats(raw, is_checkin_call=True)


# ════════════════════════════════════════════════════════════════════════
#  任务状态解析（模块级辅助，不依赖实例）
# ════════════════════════════════════════════════════════════════════════


def _parse_task_stats(raw: dict, is_checkin_call: bool = False) -> Dict[str, Any]:
    """
    解析 /task/stats/ 的原始响应。

    response 结构（基于逆向社区文档）：
    {
        "status": "ok",
        "data": {
            "sign_in":        1 or 0,     # 是否已签到
            "sign_in_streak": 7,          # 连续签到天数
            "coin":           100,        # 今日签到盒币奖励
            "exp":            120,        # 当前经验
            "max_exp":        200,        # 升级所需经验
            "task1":          1 or 0,     # 分享任务
            "task2":          1 or 0,     # 点赞任务
        }
    }
    """
    if raw.get("status") != "ok":
        msg = raw.get("message", raw.get("msg", "请求失败，请检查 pkey 是否过期"))
        return {"status": False, "message": str(msg), "data": {}}

    d = raw.get("data", {})
    signed = bool(d.get("sign_in", 0))
    streak = int(d.get("sign_in_streak", 0))
    coin = int(d.get("coin", 0))
    exp = int(d.get("exp", 0))
    max_exp = int(d.get("max_exp", 0))
    task_share = bool(d.get("task1", 0))
    task_like = bool(d.get("task2", 0))

    parsed_data = {
        "sign_in": signed,
        "sign_in_streak": streak,
        "coin": coin,
        "exp": exp,
        "max_exp": max_exp,
        "share": task_share,
        "like": task_like,
    }

    if is_checkin_call:
        if signed:
            return {
                "status": True,
                "message": f"签到成功！盒币 +{coin}，连续签到 {streak} 天",
                "data": parsed_data,
            }
        else:
            return {
                "status": False,
                "message": "今日已签到",
                "data": parsed_data,
            }

    return {"status": True, "message": "ok", "data": parsed_data}

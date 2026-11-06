"""
小黑盒签到业务层

负责：
  - 从数据库取凭据，构造 XhhApi 实例
  - 调用签到 / 任务查询接口
  - 格式化结果为可直接发送的消息字符串

供 __init__.py 的命令处理器调用。
"""

from typing import Optional

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.api.api import XhhApi
from ..utils.database.models import XHHBind, XHHUser

MSG_PREFIX = "[XHH]"


async def _get_api(qq_id: str, bot_id: str) -> Optional[XhhApi]:
    """
    根据 QQ 号从数据库查询凭据，返回可用的 XhhApi 实例。
    凭据缺失时返回 None（调用方负责发送错误提示）。
    """
    heybox_id = await XHHBind.get_uid_by_game(qq_id, bot_id)
    if not heybox_id:
        return None

    user_info = await XHHUser.select_data(qq_id)
    if not user_info:
        return None

    pkey = getattr(user_info, "pkey", "")
    if not pkey:
        return None

    x_xhh_tokenid = getattr(user_info, "stoken", "")
    return XhhApi(heybox_id=heybox_id, pkey=pkey, x_xhh_tokenid=x_xhh_tokenid)


def _fmt_checkin_msg(data: dict, nick: str = "") -> str:
    """将签到结果 data 格式化为可读消息。"""
    streak = data.get("sign_in_streak", 0)
    coin = data.get("coin", 0)
    exp = data.get("exp", 0)
    max_exp = data.get("max_exp", 0)
    share = "✅" if data.get("share") else "❌"
    like = "✅" if data.get("like") else "❌"

    name_line = f"账号：{nick}\n" if nick else ""
    exp_bar = f"{exp}/{max_exp}" if max_exp else str(exp)

    return (
        f"{name_line}"
        f"📅 连续签到：{streak} 天\n"
        f"🪙 盒币奖励：+{coin}\n"
        f"⭐ 当前经验：{exp_bar}\n"
        f"─────────────\n"
        f"📤 分享任务：{share}\n"
        f"👍 点赞任务：{like}"
    )


def _fmt_stats_msg(data: dict, nick: str = "") -> str:
    """将任务状态 data 格式化为可读消息（用于查询，不强调签到结果）。"""
    signed = "✅ 已签到" if data.get("sign_in") else "❌ 未签到"
    streak = data.get("sign_in_streak", 0)
    coin = data.get("coin", 0)
    exp = data.get("exp", 0)
    max_exp = data.get("max_exp", 0)
    share = "✅" if data.get("share") else "❌"
    like = "✅" if data.get("like") else "❌"

    name_line = f"账号：{nick}\n" if nick else ""
    exp_bar = f"{exp}/{max_exp}" if max_exp else str(exp)

    return (
        f"{name_line}"
        f"📋 今日签到：{signed}\n"
        f"📅 连续签到：{streak} 天\n"
        f"🪙 签到盒币：{coin}\n"
        f"⭐ 当前经验：{exp_bar}\n"
        f"─────────────\n"
        f"📤 分享任务：{share}\n"
        f"👍 点赞任务：{like}"
    )


async def do_checkin(bot: Bot, ev: Event) -> None:
    """
    执行签到并向用户发送结果。

    流程：
      1. 查数据库取 heybox_id + pkey
      2. 调用 XhhApi.checkin()
      3. 格式化结果并发送
    """
    qq_id = ev.user_id
    logger.info(f"{MSG_PREFIX} [签到] QQ={qq_id}")

    api = await _get_api(qq_id, ev.bot_id)
    if api is None:
        await bot.send(f"{MSG_PREFIX} 未找到登录凭据，请先使用「添加ck」完成绑定！")
        return

    async with api:
        result = await api.checkin()
    if not result["status"]:
        # 今日已签到或请求失败
        msg = result.get("message", "签到失败")
        data = result.get("data", {})

        if data:
            # 已签到：同样展示当前状态
            await bot.send(f"{MSG_PREFIX} {msg}\n\n" + _fmt_stats_msg(data))
        else:
            await bot.send(f"{MSG_PREFIX} {msg}")
        return

    data = result.get("data", {})
    await bot.send(f"{MSG_PREFIX} 签到成功！\n\n" + _fmt_checkin_msg(data))


async def query_task_stats(bot: Bot, ev: Event) -> None:
    """
    查询今日签到 & 任务状态（不执行签到）并发送。
    """
    qq_id = ev.user_id
    logger.info(f"{MSG_PREFIX} [查询任务状态] QQ={qq_id}")

    api = await _get_api(qq_id, ev.bot_id)
    if api is None:
        await bot.send(f"{MSG_PREFIX} 未找到登录凭据，请先使用「添加ck」完成绑定！")
        return

    async with api:
        result = await api.get_task_stats()

    if not result["status"]:
        await bot.send(f"{MSG_PREFIX} 查询失败：{result.get('message', '未知错误')}")
        return

    data = result.get("data", {})
    await bot.send(f"{MSG_PREFIX} 今日任务状态\n\n" + _fmt_stats_msg(data))


async def do_all_checkin(bot: Bot, ev: Event) -> None:
    """
    对当前 QQ 号下绑定的「所有」heybox_id 依次执行签到。
    多账号场景使用。
    """
    qq_id = ev.user_id
    bot_id = ev.bot_id
    logger.info(f"{MSG_PREFIX} [全部签到] QQ={qq_id}")

    uid_list = await XHHBind.get_uid_list_by_game(qq_id, bot_id)
    if not uid_list:
        await bot.send(f"{MSG_PREFIX} 你尚未绑定任何 heybox_id！")
        return

    lines = [f"{MSG_PREFIX} 全部账号签到结果：\n"]

    for heybox_id in uid_list:
        # 每个账号单独查询凭据
        user_info = await XHHUser.select_data_by_uid(heybox_id)
        pkey = getattr(user_info, "pkey", "") if user_info else ""
        x_xhh_tokenid = await XHHUser.get_user_stoken_by_uid(heybox_id)

        if not pkey or not x_xhh_tokenid:
            lines.append(f"· {heybox_id}：❌ 无凭据，请重新添加ck")
            continue

        try:
            async with XhhApi(
                heybox_id=heybox_id, pkey=pkey, x_xhh_tokenid=x_xhh_tokenid
            ) as api:
                result = await api.checkin()

            if result["status"]:
                data = result.get("data", {})
                coin = data.get("coin", 0)
                streak = data.get("sign_in_streak", 0)
                lines.append(f"· {heybox_id}：✅ 签到成功  盒币+{coin}  连签{streak}天")
            else:
                msg = result.get("message", "失败")
                lines.append(f"· {heybox_id}：⚠️ {msg}")

        except Exception as e:
            logger.exception(f"{MSG_PREFIX} 账号 {heybox_id} 签到异常: {e}")
            lines.append(f"· {heybox_id}：❌ 签到异常，请查看日志")

    await bot.send("\n".join(lines))

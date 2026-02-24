from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .sign import do_checkin, do_all_checkin

MSG_PREFIX = "[XHH]"

xhh_user = SV("小黑盒签到")


def parse_xhh_credential(text: str) -> dict:
    """
    解析用户粘贴的小黑盒凭据文本，提取 heybox_id 与 pkey。

    支持两种格式：

    格式一（推荐）：
        heybox_id=12345678
        pkey=abcdef1234567890...

    格式二（抓包工具复制的 Cookie 字符串）：
        heybox_id=12345678; pkey=abcdef...; other=val
    """
    heybox_id = ""
    pkey = ""

    segments: list[str] = []
    for line in text.splitlines():
        segments.extend(part.strip() for part in line.split(";") if part.strip())

    for seg in segments:
        if "=" not in seg:
            continue
        key, _, value = seg.partition("=")
        key = key.strip().lower()
        value = value.strip()

        if key == "heybox_id":
            heybox_id = value
        elif key == "pkey":
            pkey = value

    return {"heybox_id": heybox_id, "pkey": pkey}


def _missing_fields(credential: dict) -> list[str]:
    """返回凭据字典中值为空的字段名列表"""
    return [k for k, v in credential.items() if not v]


@xhh_user.on_command(
    keyword=("签到"),
    block=True,
)
async def cmd_checkin(bot: Bot, ev: Event):
    """
    执行今日签到，获得盒币和经验。

    用法：
        xhh签到

    须先通过「添加ck」绑定登录凭据。
    """
    logger.info(f"{MSG_PREFIX} [命令] xhh签到  QQ={ev.user_id}")
    await do_checkin(bot, ev)


@xhh_user.on_command(
    keyword=("全签", "全部签到"),
    block=True,
)
async def cmd_all_checkin(bot: Bot, ev: Event):
    """
    对当前 QQ 号绑定的所有 heybox_id 依次签到（多账号使用）。

    用法：
        xhh全签
    """
    logger.info(f"{MSG_PREFIX} [命令] xhh全签  QQ={ev.user_id}")
    await do_all_checkin(bot, ev)

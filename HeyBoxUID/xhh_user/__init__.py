from typing import cast

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.utils.message import send_diff_msg

from .utils import _missing_fields, parse_xhh_credential
from ..utils.models import UserData
from ..utils.database.models import XHHBind, XHHUser

MSG_PREFIX = "[XHH]"

xhh_user = SV("小黑盒绑定")


@xhh_user.on_command(
    keyword=("绑定", "切换", "删除"),
    block=True,
)
async def manage_uid(bot: Bot, ev: Event):
    """
    绑定 / 切换 / 删除小黑盒 heybox_id。

    用法：
        绑定 <heybox_id>   将指定 ID 写入当前 QQ 号
        切换 <heybox_id>   切换到已绑定的另一个 ID
        删除               删除当前正在使用的 ID
    """
    qid = ev.user_id
    uid = ev.text.strip()

    if "绑定" in ev.command:
        logger.info(f"{MSG_PREFIX} [绑定 heybox_id]  QQ={qid}  UID={uid}")

        if not uid:
            return await bot.send(f"{MSG_PREFIX} 请在命令后附上你的 heybox_id，例如：绑定 12345678")

        data = await XHHBind.insert_uid(qid, ev.bot_id, uid, is_digit=False)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f"{MSG_PREFIX} 绑定 heybox_id {uid} 成功！",
                -1: f"{MSG_PREFIX} heybox_id {uid} 格式不正确！",
                -2: f"{MSG_PREFIX} heybox_id {uid} 已经绑定过了！",
                -3: f"{MSG_PREFIX} 输入格式有误，请直接在命令后跟上数字 ID！",
            },
        )

    elif "切换" in ev.command:
        logger.info(f"{MSG_PREFIX} [切换 heybox_id]  QQ={qid}  UID={uid}")

        retcode = await XHHBind.switch_uid_by_game(qid, ev.bot_id, uid)

        if retcode == 0:
            await bot.send(f"{MSG_PREFIX} 切换到 heybox_id {uid} 成功！")
        elif retcode == -3:
            now_uid = await XHHBind.get_uid_by_game(qid, ev.bot_id)
            if now_uid:
                await bot.send(
                    f"{MSG_PREFIX} 你目前只绑定了一个 heybox_id（{now_uid}），无法切换！\n"
                    f"请先使用「绑定 <heybox_id>」添加更多 ID。"
                )
            else:
                await bot.send(f"{MSG_PREFIX} 你尚未绑定任何 heybox_id，无法切换！")
        else:
            await bot.send(f"{MSG_PREFIX} 未找到 heybox_id {uid}，请先绑定后再切换。")

    elif "删除" in ev.command:
        logger.info(f"{MSG_PREFIX} [删除 heybox_id]  QQ={qid}")

        now_uid = await XHHBind.get_uid_by_game(qid, ev.bot_id)
        if now_uid is None:
            return await bot.send(f"{MSG_PREFIX} 你尚未绑定任何 heybox_id，无需删除！")

        data = await XHHBind.delete_uid(qid, ev.bot_id, now_uid)
        await send_diff_msg(
            bot,
            data,
            {
                0: f"{MSG_PREFIX} 已删除 heybox_id {now_uid}！",
                -1: f"{MSG_PREFIX} heybox_id {now_uid} 不在绑定列表中，删除失败！",
            },
        )


# ════════════════════════════════════════════════════════════════════════
#  凭据（pkey）导入 / 删除
# ════════════════════════════════════════════════════════════════════════


@xhh_user.on_command(
    keyword=("添加ck", "添加cookie", "添加Cookie"),
    block=True,
)
async def add_ck(bot: Bot, ev: Event):
    """
    添加小黑盒登录凭据（heybox_id + pkey）。
    """
    logger.info(f"{MSG_PREFIX} [添加 Cookie]  QQ={ev.user_id}")

    credential = parse_xhh_credential(ev.text.strip())
    missing = _missing_fields(credential)

    if missing:
        return await bot.send(
            f"{MSG_PREFIX} 凭据不完整，缺少：{'、'.join(missing)}\n\n"
            f"请按以下格式发送：\n"
            f"添加ck\n"
            f"heybox_id=你的ID\n"
            f"pkey=你的pkey值"
        )

    heybox_id = credential["heybox_id"]
    pkey = credential["pkey"]
    x_xhh_tokenid = credential["x_xhh_tokenid"]

    logger.info(f"{MSG_PREFIX} 凭据解析成功  heybox_id={heybox_id}  pkey={'*' * 8}")

    user_data = cast(
        UserData,
        {
            "user_id": ev.user_id,
            "group_id": ev.group_id,
            "uid": heybox_id,
            "pkey": pkey,
            "x_xhh_tokenid": x_xhh_tokenid,
        },
    )

    await XHHUser.insert_user(bot.bot_id, user_data)
    # 同步写入绑定表，确保 heybox_id 与 pkey 统一
    await XHHBind.insert_uid(ev.user_id, ev.bot_id, heybox_id, is_digit=False)

    await bot.send(f"{MSG_PREFIX} 凭据添加成功！\nheybox_id：{heybox_id}\n发送「我的信息」可查看当前绑定状态。")


@xhh_user.on_command(
    keyword=("导出ck", "导出"),
    block=True,
)
async def export_ck(bot: Bot, ev: Event):
    """
    导出当前账号的登录凭据（仅限私聊）。

    导出的 heybox_id 和 pkey 可直接粘贴到「添加ck」命令中重新导入。
    """
    logger.info(f"{MSG_PREFIX} [导出凭据]  QQ={ev.user_id}")

    if ev.group_id is not None:
        return await bot.send(f"{MSG_PREFIX} 凭据含敏感信息，请在【私聊】中使用该命令！")

    qid = ev.user_id
    uid = await XHHBind.get_uid_by_game(qid, ev.bot_id)
    user_info = await XHHUser.select_data_by_uid(bot.bot_id, uid)

    if user_info is None:
        return await bot.send(f"{MSG_PREFIX} 你尚未添加任何凭据，无法导出！")

    heybox_id = getattr(user_info, "heybox_id", "")
    pkey = getattr(user_info, "pkey", "")

    if not pkey:
        return await bot.send(f"{MSG_PREFIX} 凭据不完整，请重新「添加ck」！")

    await bot.send(f"{MSG_PREFIX} 你的登录凭据（请勿泄露给他人）：\n\nheybox_id={heybox_id}\npkey={pkey}")

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
    x_xhh_tokenid = ""

    segments: list[str] = []
    for line in text.splitlines():
        segments.extend(part.strip() for part in line.split(";") if part.strip())

    for seg in segments:
        if "=" not in seg:
            continue
        key, _, value = seg.partition("=")
        key = key.strip().lower()
        value = value.strip()

        # 同时兼容 App 端（heybox_id / pkey）
        # 和浏览器端（user_heybox_id / user_pkey）
        if key in ("heybox_id", "user_heybox_id"):
            if not heybox_id:  # 优先保留先出现的值
                heybox_id = value
        elif key in ("pkey", "user_pkey"):
            if not pkey:
                pkey = value
        elif key in ("x_xhh_tokenid", "user_x_xhh_tokenid"):
            if not x_xhh_tokenid:
                x_xhh_tokenid = value

    return {"heybox_id": heybox_id, "pkey": pkey, "x_xhh_tokenid": x_xhh_tokenid}


def _missing_fields(credential: dict) -> list[str]:
    """返回凭据字典中值为空的字段名列表"""
    return [k for k, v in credential.items() if not v]

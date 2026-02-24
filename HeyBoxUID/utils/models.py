from typing import TypedDict


class UserData(TypedDict):
    user_id: str
    group_id: int
    uid: str
    pkey: str
    x_xhh_tokenid: str


class BindData(TypedDict):
    user_id: str
    bot_id: str
    uid: str

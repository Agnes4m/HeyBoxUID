from typing import Optional

from sqlmodel import Field
from fastapi_amis_admin.amis.components import PageSchema

from gsuid_core.bot import Event
from gsuid_core.webconsole import site
from gsuid_core.webconsole.mount_app import GsAdminModel
from gsuid_core.utils.database.base_models import Bind, User

from ..models import UserData

# exec_list.append('ALTER TABLE DFUser ADD COLUMN latest_record TEXT DEFAULT ""')


class XHHBind(Bind, table=True):
    uid: Optional[str] = Field(default=None, title="小黑盒uid")

    @classmethod
    async def insert_user(cls, ev: Event, bot_id: str, data: UserData):
        return await cls.insert_data(
            user_id=ev.user_id,
            bot_id=bot_id,
        )


class XHHUser(User, table=True):
    uid: str = Field(default="", title="小黑盒uid")
    pkey: str = Field(default="", title="小黑盒pkey")

    @classmethod
    async def insert_user(cls, bot_id: str, data: UserData):
        return await cls.insert_data(
            user_id=data["qq_id"],
            bot_id=bot_id,
        )


@site.register_admin
class DFBindadmin(GsAdminModel):
    pk_name = "id"
    page_schema = PageSchema(
        label="小黑盒绑定管理",
        icon="fa fa-users",
    )  # type: ignore

    # 配置管理模型
    model = XHHBind


@site.register_admin
class DFUseradmin(GsAdminModel):
    pk_name = "id"
    page_schema = PageSchema(
        label="小黑盒用户管理",
        icon="fa fa-users",
    )  # type: ignore

    # 配置管理模型
    model = XHHUser

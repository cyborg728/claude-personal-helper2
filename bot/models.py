from sqlmodel import Field, SQLModel


class AllowedUser(SQLModel, table=True):
    __tablename__ = "allowed_users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)


class TranslateWhitelistUser(SQLModel, table=True):
    __tablename__ = "translate_whitelist"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)


class UserSettings(SQLModel, table=True):
    __tablename__ = "user_settings"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(unique=True, index=True)
    language_code: str = Field(default="en")
    translation_enabled: bool = Field(default=True)

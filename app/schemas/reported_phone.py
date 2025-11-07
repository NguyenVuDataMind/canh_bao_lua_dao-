from pydantic import BaseModel, ConfigDict


class ReportedPhoneCreate(BaseModel):
    value: str


class ReportedPhoneUpdate(ReportedPhoneCreate):
    pass


class ReportedPhone(ReportedPhoneCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, ConfigDict
from typing import Literal, Union, List, Optional

class EventBase(BaseModel):
    date: str
    title: str
    subtitle: str
    distance: float = 0.0
    heart_rate: float = 0.0
    calories: float = 0.0
    time: str

class MatchEvent(EventBase):
    entry_type: Literal["past_matches", "upcoming_matches"]
    match_id: str

class TrainingEvent(EventBase):
    entry_type: Literal["training"]
    activity_id: str

Event = Union[MatchEvent, TrainingEvent]

class AIAnalysisResponse(BaseModel):
    summary: str

class ChartDataset(BaseModel):
    label: str
    data: List[float]
    borderColor: str
    backgroundColor: str
    fill: bool
    yAxisID: str
    tension: float
    pointRadius: int

class ChartDetails(BaseModel):
    labels: List[str]
    datasets: List[ChartDataset]

class ChartResponseItem(BaseModel):
    title: str
    chart: ChartDetails

class SettingsInput(BaseModel):
    pzpn_email: Optional[str] = None
    pzpn_password: Optional[str] = None
    garmin_email: Optional[str] = None
    garmin_password: Optional[str] = None
    openai_api_key: Optional[str] = None
    surname_name: Optional[str] = None
    model_config = ConfigDict(extra='forbid')
    



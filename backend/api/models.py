from pydantic import BaseModel
from typing import Literal, Union, List

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


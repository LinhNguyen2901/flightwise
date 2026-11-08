from pydantic import BaseModel


class Counts(BaseModel):
    scheduled_count: int
    cancelled_count: int
    diverted_count: int
    cancellation_eligible_count: int
    arrival_eligible_count: int
    late_count: int
    excluded_arrival_count: int
    invalid_time_count: int
    unmapped_count: int
    late_rate: float | None
    cancellation_rate: float | None


class AirportRow(Counts):
    origin_id: int
    origin_code: str
    name: str
    region: str
    latitude: float
    longitude: float


class ContextRow(Counts):
    carrier: str
    weekday: int
    hour: int


class ContextResponse(BaseModel):
    period: str
    version: str
    origin_id: int | None
    origin_code: str | None
    totals: Counts
    rows: list[ContextRow]


class AirportHourRow(BaseModel):
    origin_id: int
    scheduled_count: int
    cancelled_count: int
    diverted_count: int
    cancellation_eligible_count: int
    arrival_eligible_count: int
    late_count: int
    excluded_arrival_count: int
    invalid_time_count: int
    unmapped_count: int


class AirportHourFrame(BaseModel):
    hour: int
    rows: list[AirportHourRow]


class AirportHourResponse(BaseModel):
    period: str
    version: str
    frames: list[AirportHourFrame]


class MetadataResponse(BaseModel):
    period: str
    version: str
    origin_scope: str
    metric_rule: str
    origins: int
    cube_rows: int
    totals: Counts
    exclusions: dict[str, int]
    carrier_names: dict[str, str]
    source_hashes: dict[str, str]


class HealthResponse(BaseModel):
    status: str
    version: str

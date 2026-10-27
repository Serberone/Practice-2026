from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float] = [0.0, 0.0]  # [longitude, latitude]

class StationBase(BaseModel):
    name: str
    city: str
    type: str  # "AIRPORT" | "BUS_STATION"
    code: str
    yandex_code: Optional[str] = None
    location: Optional[GeoPoint] = None
    is_active: bool = True

class StationInDB(StationBase):
    id: str = Field(default_factory=lambda: str(ObjectId()))

class CarrierBase(BaseModel):
    name: str
    short_name: str
    transport_type: str  # "AIR" | "BUS"
    phone: Optional[str] = None
    inn: Optional[str] = None

class CarrierInDB(CarrierBase):
    id: str = Field(default_factory=lambda: str(ObjectId()))

class UserBase(BaseModel):
    username: str
    role: str  # "DISPATCHER" | "ADMIN"
    full_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmbeddedCarrier(BaseModel):
    id: Optional[str] = None
    name: str
    phone: Optional[str] = None

class StationSummary(BaseModel):
    station_id: Optional[str] = None
    city: str
    name: str

class EmbeddedRoute(BaseModel):
    origin: StationSummary
    destination: StationSummary

class EmbeddedSchedule(BaseModel):
    departure_planned: datetime
    arrival_planned: datetime
    departure_estimated: Optional[datetime] = None
    arrival_estimated: Optional[datetime] = None

class EmbeddedWeatherImpact(BaseModel):
    has_impact: bool = False
    phenomenon: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EmbeddedDisplayFlags(BaseModel):
    is_hidden: bool = False
    requires_dispatcher_review: bool = False
    manual_override: bool = False

class TripBase(BaseModel):
    trip_number: str
    transport_type: str  # "PLANE" | "BUS"
    carrier: EmbeddedCarrier
    route: EmbeddedRoute
    schedule: EmbeddedSchedule
    status: str = "SCHEDULED"  # SCHEDULED, DELAYED, BOARDING, CANCELLED, ARRIVED, DEPARTED
    gate_or_platform: Optional[str] = None
    weather_factor: EmbeddedWeatherImpact = Field(default_factory=EmbeddedWeatherImpact)
    display_flags: EmbeddedDisplayFlags = Field(default_factory=EmbeddedDisplayFlags)
    source: str = "YANDEX_RASP"
    last_synced_at: datetime = Field(default_factory=datetime.utcnow)

class TripInDB(TripBase):
    id: str = Field(default_factory=lambda: str(ObjectId()))

class WeatherMetrics(BaseModel):
    temperature_c: float
    wind_speed_ms: float
    wind_gust_ms: Optional[float] = 0.0
    visibility_meters: int
    phenomena: str  # "метель", "ясно", "гололёд", "сильный снегопад"
    humidity_percent: Optional[int] = None
    pressure_hpa: Optional[float] = None

class WeatherLog(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    station_id: Optional[str] = None
    city: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: WeatherMetrics
    alert_level: str = "NORMAL"  # "NORMAL" | "ADVISORY" | "SEVERE"
    flight_critical: bool = False
    bus_critical: bool = False

class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    username: Optional[str] = None
    event_type: str  # "STATUS_OVERRIDE", "HIDE_TRIP", "INTEGRATION_ERROR", "CREATE_TRIP", "VERIFY_TRIP"
    entity_id: Optional[str] = None
    details: Dict[str, Any] = {}

class SubscriptionCreate(BaseModel):
    trip_id: str
    recipient: str  # email or phone or push token
    channel: str = "EMAIL"  # "EMAIL" | "PUSH"
    device_token: Optional[str] = None

class SubscriptionInDB(SubscriptionCreate):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    subscription_id: str
    trip_id: str
    change_type: str  # "DELAY" | "CANCELLATION" | "GATE_CHANGE" | "ON_TIME"
    channel: str = "EMAIL"
    payload: Dict[str, Any] = {}
    status: str = "SENT"  # "PENDING" | "SENT" | "FAILED"
    retry_count: int = 0
    sent_at: datetime = Field(default_factory=datetime.utcnow)

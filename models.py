from dataclasses import dataclass
from typing import Optional

@dataclass
class Role:
    id: int
    name: str
    description: Optional[str] = None

@dataclass
class User:
    id: int
    username: str
    full_name: str
    role_id: int
    role_name: Optional[str] = None  # Populated from join

@dataclass
class Client:
    id: int
    full_name: str
    phone: str

@dataclass
class Equipment:
    id: int
    serial_number: str
    model: str
    type: str
    client_id: int

@dataclass
class Request:
    id: int
    request_number: str
    creation_date: str
    problem_description: str
    client_id: int
    equipment_id: int
    status_id: int
    status_name: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    equipment_model: Optional[str] = None
    completion_date: Optional[str] = None
    deadline_date: Optional[str] = None
    help_needed: bool = False
    assigned_specialists: Optional[list] = None # List of specialist names or IDs

@dataclass
class Comment:
    id: int
    request_id: int
    user_id: int
    text: str
    created_at: str
    user_name: Optional[str] = None

@dataclass
class Part:
    id: int
    name: str
    stock_quantity: int
    price: float
    quantity_used: Optional[int] = 0 # For request context

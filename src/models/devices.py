
from abc import ABC, abstractmethod
from src.models.enums import StaffType

class CommunicationDevice(ABC):
    def __init__(self, device_id: str, owner: StaffType, contact_info: str = None):
        self.device_id = device_id
        self.owner = owner
        self.contact_info = contact_info

    @abstractmethod
    def contact(self, message: str):
        ...


class Mobile(CommunicationDevice):
    def contact(self, message: str):
        print(f"[SMS] {self.owner.value} ({self.contact_info}): {message}")


class Computer(CommunicationDevice):
    def contact(self, message: str):
        print(f"[Desktop] {self.owner.value} ({self.contact_info}): {message}")
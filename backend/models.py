from sqlalchemy import Column, String, Integer, ForeignKey
from database import Base

class Route(Base):
    __tablename__ = "routes"
    __table_args__ = {'extend_existing': True}
    
    route_id = Column(String, primary_key=True)
    company = Column(String)
    origin_port = Column(String)
    destination_port = Column(String)
    departure_time = Column(String)
    arrival_time = Column(String)
    duration = Column(Integer)

class VesselPrice(Base):
    __tablename__ = "vessels_and_prices"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, ForeignKey("routes.route_id"))
    vessel = Column(String)
    price = Column(Integer)

class DateVessel(Base):
    __tablename__ = "dates_and_vessels"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, ForeignKey("routes.route_id"))
    travel_date = Column(String)
    vessel = Column(String)
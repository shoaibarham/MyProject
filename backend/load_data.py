import json
from sqlalchemy.orm import Session
from database import engine, init_db
from models import Route

# Initialize the database
init_db()

# Load data from JSON file
try:
    with open('GTFS_data_v1.json', 'r') as file:
        routes_data = json.load(file)
    print("JSON data loaded successfully.")
    print(f"Data structure: {type(routes_data)}")
    print(f"Number of routes: {len(routes_data)}")
except Exception as e:
    print(f"Error loading JSON data: {e}")
    exit(1)

# Create a new session
session = Session(bind=engine)

try:
    for route_data in routes_data:
        print(f"Processing route data: {route_data}")
        route = Route(
            route_id=route_data['route_id'],
            company=route_data['company'],
            origin_port=route_data['origin_port'],
            destination_port=route_data['destination_port'],
            departure_time=route_data['departure_time'],
            arrival_time=route_data['arrival_time'],
            duration=route_data['duration']
        )
        session.add(route)
    session.commit()
    print("Data loaded successfully.")
except Exception as e:
    print(f"Error: {e}")
    session.rollback()
finally:
    session.close()
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timedelta
from typing import Dict, Any, List

def get_alternative_suggestions(db: Session, args: Dict[str, Any]) -> str:
    """Generate alternative suggestions based on failed query parameters."""
    suggestions = []
    
    try:
        # If origin port was provided, find alternative destinations
        if "origin" in args:
            origin = args["origin"]
            routes = db.query(Route).filter(
                or_(
                    Route.origin_port.ilike(f"%{origin}%"),
                    Route.origin_port_code.ilike(f"%{origin}%")
                )
            ).distinct(Route.destination_port).limit(5).all()
            
            if routes:
                destinations = [route.destination_port for route in routes]
                suggestions.append(f"Popular destinations from {origin}:")
                suggestions.extend([f"• {dest}" for dest in destinations])
        
        # If no origin, show popular ports using func.count
        else:
            popular_ports = db.query(Route.origin_port)\
                .group_by(Route.origin_port)\
                .order_by(func.count(Route.route_id).desc())\
                .limit(5).all()
            
            if popular_ports:
                suggestions.append("Popular departure ports:")
                suggestions.extend([f"• {port[0]}" for port in popular_ports])
        
        # Rest of the function remains the same
        if "date" in args:
            try:
                target_date = datetime.strptime(args["date"], "%Y-%m-%d")
                nearby_dates = [
                    target_date + timedelta(days=i) 
                    for i in range(-2, 3)
                    if i != 0
                ]
                
                suggestions.append("\nAvailable dates:")
                suggestions.extend([
                    f"• {date.strftime('%Y-%m-%d')}" 
                    for date in nearby_dates
                ])
            except ValueError:
                pass
        
        return "\n".join(suggestions) if suggestions else "No alternative suggestions available."
        
    except Exception as e:
        traceback.print_exc()
        return "Unable to generate suggestions at this time."

def format_response(data: Any, function_name: str) -> str:
    """Format the response based on the function name."""
    if function_name == "get_ferry_schedule":
        return format_schedule_response(data)
    elif function_name == "check_ferry_availability":
        return format_availability_response(data)
    elif function_name == "get_price":
        return format_price_response(data)
    elif function_name == "get_duration":
        return format_duration_response(data)
    else:
        return str(data)

def format_schedule_response(data: List[Dict]) -> str:
    """Format schedule data into human-readable text."""
    formatted = []
    for route in data:
        schedule = []
        schedule.append(f"🚢 {route['company']} Ferry")
        schedule.append(f"From: {route['origin']} ({route['origin']})")
        schedule.append(f"To: {route['destination']} ({route['destination']})")
        schedule.append(f"Departure: {route['departure']}")
        schedule.append(f"Arrival: {route['arrival']}")
        schedule.append(f"Duration: {route['duration']}")
        
        if route['price_range']:
            schedule.append(f"Price Range: €{route['price_range']['min']} - €{route['price_range']['max']}")
        
        formatted.append("\n".join(schedule))
    
    return "\n\n".join(formatted)

def format_availability_response(data: Dict) -> str:
    """Format availability data into human-readable text."""
    if not data['available_services']:
        return f"No services available on {data['date']}"
    
    services = []
    for service in data['available_services']:
        service_info = [
            f"🚢 {service['company']} Ferry",
            f"Departure: {service['departure']}",
            f"Duration: {service['duration']}",
            f"Available Vessels: {', '.join(service['vessels'])}",
            f"Prices from: €{min(p['price'] for p in service['prices'])}"
        ]
        services.append("\n".join(service_info))
    
    return "\n\n".join(services)

def format_price_response(data: Dict) -> str:
    """Format price data into human-readable text."""
    prices = sorted(data['prices'], key=lambda x: x['price'])
    formatted = [f"Route ID: {data['route_id']}"]
    
    for price in prices:
        formatted.append(f"• {price['vessel']}: €{price['price']}")
    
    return "\n".join(formatted)

def format_duration_response(data: Dict) -> str:
    """Format duration data into human-readable text."""
    return f"The shortest duration from {data['origin']} to {data['destination']} is {data['shortest_duration']} minutes."
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from fastapi.middleware.cors import CORSMiddleware
import traceback


# Initialize FastAPI
app = FastAPI()
# Allow requests from your React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update this if using a different frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
DATABASE_URL = "sqlite:///routes.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ORM Models
class Route(Base):
    __tablename__ = "routes"
    route_id = Column(String, primary_key=True)
    company = Column(String)
    origin_port = Column(String)
    destination_port = Column(String)
    departure_time = Column(String)
    arrival_time = Column(String)
    duration = Column(Integer)

class VesselPrice(Base):
    __tablename__ = "vessels_and_prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, ForeignKey("routes.route_id"))
    vessel = Column(String)
    price = Column(Integer)

class DateVessel(Base):
    __tablename__ = "dates_and_vessels"
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, ForeignKey("routes.route_id"))
    travel_date = Column(String)
    vessel = Column(String)

Base.metadata.create_all(bind=engine)

# Dependency for DB sesssion
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Global variable to store chat history
chat_history = []

#Groq API Key**
GROQ_API_KEY = "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" 
llm = ChatGroq(groq_api_key=GROQ_API_KEY, model='llama-3.3-70b-versatile')

# **Prompt Template for AI Chatbot**
prompt_template_str = """
You are a ferry booking assistant. Your task is to provide concise, accurate, and relevant responses to user queries.  

Instructions:  
- **Context Awareness**:  
  - If the query is **related** to the previous conversation, use the history to give a precise and relevant answer.  
  - If the query is **new and unrelated**, respond independently without mentioning that it is a new topic.  

- **Response Guidelines**:  
  - Provide **clear and correct** answers.  
  - If the requested information is **unknown**, politely apologize and ask if the user would like you to check further.  

Ensure all responses are **direct, informative, and user-friendly

Conversation history:
{history}

Current query: {query}
"""
prompt_template = PromptTemplate(input_variables=["history", "query"], template=prompt_template_str)



def generate_prompt(history, query):
    history_text = "\n".join(history)
    return prompt_template.format(history=history_text, query=query)

llm_chain = LLMChain(llm=llm, prompt=prompt_template)

# **AI Chat Route**
@app.get("/chat/")
def chat(query: str):
    """Handles chatbot queries with Groq LLM."""
    try:
        # Ensure API key is valid
        if not GROQ_API_KEY:
            raise HTTPException(status_code=500, detail="Groq API Key is missing!")

        # Generate prompt with chat history
        prompt = generate_prompt(chat_history, query)

        response = llm_chain.invoke({"history": chat_history, "query": query})
        response_text = response["text"]

        # Add current query and response to chat history
        chat_history.append(f"User: {query}")
        chat_history.append(f"Assistant: {response_text}")

        # Extract dynamic questions from the response (assuming the LLM provides them)
        dynamic_questions = response.get("dynamic_questions", [])

        print(response_text)

        return {"response": response_text, "dynamic_questions": dynamic_questions}
    
    except Exception as e:
        # Log error details
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Chat Error: {str(e)}")

#1. Get All Routes
@app.get("/routes/")
def get_all_routes(db: Session = Depends(get_db)):
    return db.query(Route).all()

#2. Get Routes by Origin & Destination
@app.get("/routes/{origin}/{destination}")
def get_routes_by_ports(origin: str, destination: str, db: Session = Depends(get_db)):
    routes = db.query(Route).filter(Route.origin_port == origin, Route.destination_port == destination).all()
    if not routes:
        raise HTTPException(status_code=404, detail="No routes found.")
    return routes

# 3. Get Prices for a Route
@app.get("/prices/{route_id}")
def get_price(route_id: str, db: Session = Depends(get_db)):
    prices = db.query(VesselPrice).filter(VesselPrice.route_id == route_id).all()
    if not prices:
        raise HTTPException(status_code=404, detail="Price data not found.")
    return prices

#4. Get Shortest Duration for a Route
@app.get("/duration/{origin}/{destination}")
def get_duration(origin: str, destination: str, db: Session = Depends(get_db)):
    durations = db.query(Route).filter(Route.origin_port == origin, Route.destination_port == destination).all()
    if not durations:
        raise HTTPException(status_code=404, detail="No duration data available.")
    shortest_duration = min(durations, key=lambda x: x.duration).duration
    return {"origin": origin, "destination": destination, "shortest_duration": shortest_duration}

#5. Check Ferry Availability for a Date
@app.get("/availability/{origin}/{destination}/{date}")
def check_ferry_availability(origin: str, destination: str, date: str, db: Session = Depends(get_db)):
    routes = db.query(Route).filter(Route.origin_port == origin, Route.destination_port == destination).all()
    available_vessels = db.query(DateVessel).filter(DateVessel.travel_date == date).all()

    result = []
    for route in routes:
        vessels_on_date = [v.vessel for v in available_vessels if v.route_id == route.route_id]
        if vessels_on_date:
            result.append({"route_id": route.route_id, "vessels": vessels_on_date, "departure_time": route.departure_time})
    
    if not result:
        raise HTTPException(status_code=404, detail="No ferry available on this date.")
    
    return result

#6. Find Indirect Route (With Stopover)
@app.get("/indirect-route/{origin}/{destination}")
def get_indirect_routes(origin: str, destination: str, db: Session = Depends(get_db)):
    possible_routes = db.query(Route).all()
    
    intermediate_stops = [route.destination_port for route in possible_routes if route.origin_port == origin]
    
    result = []
    for stop in intermediate_stops:
        if any(route.destination_port == destination for route in possible_routes if route.origin_port == stop):
            result.append({
                "first_leg": {"origin": origin, "stopover": stop},
                "second_leg": {"stopover": stop, "destination": destination}
            })

    if not result:
        raise HTTPException(status_code=404, detail="No indirect route found.")

    return result

#7. Get Vessel Operating a Route
@app.get("/vessel/{route_id}")
def get_vessel_by_route(route_id: str, db: Session = Depends(get_db)):
    vessels = db.query(DateVessel).filter(DateVessel.route_id == route_id).all()
    if not vessels:
        raise HTTPException(status_code=404, detail="No vessel found.")
    return {"route_id": route_id, "vessels": [v.vessel for v in vessels]}

#8. Get Departure Times from a Port
@app.get("/schedule/{origin}")
def get_departure_times(origin: str, db: Session = Depends(get_db)):
    schedules = db.query(Route).filter(Route.origin_port == origin).all()
    if not schedules:
        raise HTTPException(status_code=404, detail="No departures found.")
    return [{"destination": route.destination_port, "departure_time": route.departure_time} for route in schedules]

#9. Find Cheapest Ferry for a Route
@app.get("/cheapest-route/{origin}/{destination}")
def get_cheapest_route(origin: str, destination: str, db: Session = Depends(get_db)):
    routes = db.query(Route).filter(Route.origin_port == origin, Route.destination_port == destination).all()
    prices = db.query(VesselPrice).filter(VesselPrice.route_id.in_([r.route_id for r in routes])).all()

    if not prices:
        raise HTTPException(status_code=404, detail="No price data available.")
    
    cheapest = min(prices, key=lambda x: x.price)
    return {"route_id": cheapest.route_id, "price": cheapest.price}

#10. Find Most Expensive Ferry Route
@app.get("/most-expensive-route/")
def get_most_expensive_route(db: Session = Depends(get_db)):
    prices = db.query(VesselPrice).all()
    if not prices:
        raise HTTPException(status_code=404, detail="No price data available.")
    
    expensive = max(prices, key=lambda x: x.price)
    return {"route_id": expensive.route_id, "price": expensive.price}

from sqlalchemy import Column, Integer, String, Float, DateTime
from base import Base
import datetime

class FoodLog(Base):
    """ Food Log """

    __tablename__ = "food_log"

    id = Column(Integer, primary_key=True)
    trace_id = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    timestamp = Column(String(100), nullable=False)
    food_name = Column(String(250), nullable=False)
    quantity = Column(Integer, nullable=False)
    calories = Column(Integer, nullable=False)
    carbohydrates = Column(Integer, nullable=False)
    fats = Column(Integer, nullable=False)
    proteins = Column(Integer, nullable=False)
    date_created = Column(DateTime, nullable=False)

    def __init__(self, trace_id, user_id, timestamp, food_name, quantity, calories, carbohydrates, fats, proteins):
        """ Initializes a food log entry """
        self.trace_id = trace_id
        self.user_id = user_id
        self.timestamp = timestamp
        self.food_name = food_name
        self.quantity = quantity
        self.calories = calories
        self.carbohydrates = carbohydrates
        self.fats = fats
        self.proteins = proteins
        self.date_created = datetime.datetime.now()

    def to_dict(self):
        """ Dictionary Representation of a food log entry """
        dict = {}
        dict['id'] = self.id
        dict['trace_id'] = self.trace_id
        dict['user_id'] = self.user_id
        dict['timestamp'] = self.timestamp
        dict['food_name'] = self.food_name
        dict['quantity'] = self.quantity
        dict['calories'] = self.calories
        dict['carbohydrates'] = self.carbohydrates
        dict['fats'] = self.fats
        dict['proteins'] = self.proteins
        dict['date_created'] = self.date_created

        return dict

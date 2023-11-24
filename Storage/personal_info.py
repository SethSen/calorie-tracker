from sqlalchemy import Column, Integer, String, Float, DateTime
from base import Base
import datetime


class PersonalInfo(Base):
    """ Personal Info """

    __tablename__ = "personal_info"

    id = Column(Integer, primary_key=True)
    trace_id = Column(String(100), unique=True, nullable=False)
    activity_level = Column(String(50), nullable=False)
    age = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    nutritional_goal = Column(String(50), nullable=False)
    sex = Column(String(10), nullable=False)
    user_id = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    date_created = Column(DateTime, nullable=False)


    def __init__(self, trace_id, activity_level, age, height, nutritional_goal, sex, user_id, weight):
        """ Initializes a personal info record """
        self.trace_id = trace_id
        self.activity_level = activity_level
        self.age = age
        self.height = height
        self.nutritional_goal = nutritional_goal
        self.sex = sex
        self.user_id = user_id
        self.weight = weight
        self.date_created = datetime.datetime.now()  # Sets the date/time record is created

    def to_dict(self):
        """ Dictionary Representation of a personal info record """
        dict = {}
        dict['id'] = self.id
        dict['trace_id'] = self.trace_id
        dict['activity_level'] = self.activity_level
        dict['age'] = self.age
        dict['height'] = self.height
        dict['nutritional_goal'] = self.nutritional_goal
        dict['sex'] = self.sex
        dict['user_id'] = self.user_id
        dict['weight'] = self.weight
        dict['date_created'] = self.date_created

        return dict

from typing import Optional, List, Any
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from MONGO import database, users_collection, likes_collection, activities_collection, partner_requests_collection
from pymongo import ASCENDING
from datetime import datetime


class PyObjectId(ObjectId):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')


class MongoBase(BaseModel):
    id: Optional[PyObjectId] = Field(alias='_id')

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ActivityInDB(MongoBase):
    name: str


class Location(BaseModel):
    type: str = "Point"
    coordinates: list


class User(MongoBase):
    username: str = Field(..., max_length=50)
    email: EmailStr
    full_name: str = Field(..., max_length=50)
    disabled: bool
    profile_image: Optional[str] = None
    bio: Optional[str] = None

    country: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=20)
    loc: Optional[List[float]] = None
    activities_id_list: Optional[List[PyObjectId]] = []


class UserIn(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr
    full_name: str = Field(..., max_length=50)
    password: str


class UserInDB(User, MongoBase):
    hashed_password: str
    disabled: bool = True
    activation_code: int

    def save(self):
        users_collection.update_one({"_id": self.id}, {"$set": self.dict()})
        document = partner_requests_collection.find_one({"document_id": self.id})
        return document

    def like(self, partner_request_id: str):
        try:
            likes_collection.insert_one({"user_id": self.id, "partner_request_ud": partner_request_id})
            partner_requests_collection.update_one({"_id": partner_request_id}, {"$inc": {"likes": 1}})
            return True
        except Exception as e:
            print("An exception occurred ::", e)
            return False

    def unlike(self, partner_request_id: str):
        try:
            likes_collection.delete_one({"user_id": self.id, "partner_request_ud": partner_request_id})
            partner_requests_collection.update_one({"_id": partner_request_id}, {"$inc": {"likes": -1}})
            return True
        except Exception as e:
            print("An exception occurred ::", e)
            return False

    def liked_partner_requests(self):
        like_list = likes_collection.find({"user_id": self.id})
        partner_request_id_list = [like_record["partner_request_id"] for like_record in like_list]
        partner_request_list = partner_requests_collection.find({"id": {"$in": partner_request_id_list}})
        return partner_request_list


class ActivationData(BaseModel):
    code: int


class UserInfoIn(BaseModel):
    bio: Optional[str] = Field(None, max_length=300)
    activities: Optional[List[ActivityInDB]] = []


class UserOutWithDistance(User):
    distance: float


class Like(MongoBase):
    user_id: PyObjectId
    partner_request_id: PyObjectId

    def save(self):
        likes_collection.update_one({"_id": self.id}, {"$set": self.dict()})
        document = partner_requests_collection.find_one({"document_id": self.id})
        return document


class PartnerRequestIn(BaseModel):
    subject: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    activity_id: PyObjectId


class PartnerRequestOut(MongoBase):
    subject: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    activity_id: PyObjectId
    likes: int = 0
    created_datetime: datetime
    user_id: PyObjectId
    loc: Optional[List[float]] = None
    city: str
    country: str
    owner_profile_image: Optional[str] = None
    owner_full_name: str
    owner_username: str


class PartnerRequestOutWithDistance(PartnerRequestOut):
    distance: float


class PartnerRequest(MongoBase):
    subject: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    user_id: PyObjectId
    activity_id: PyObjectId
    likes: int = 0
    created_datetime: Optional[datetime] = datetime.utcnow()
    # location: Optional[Location] = None
    loc: Optional[List[float]] = None
    city: str
    country: str
    owner_profile_image: str
    owner_full_name: str
    owner_username: str

    def save(self):
        partner_requests_collection.update_one({"_id": self.id}, {"$set": self.dict()})
        document = partner_requests_collection.find_one({"document_id": self.id})
        return document

    def request_owner(self):
        user = users_collection.find_one({"id": self.user_id})
        return UserInDB(**user)

    def liked_users(self):
        like_list = likes_collection.find_one({"partner_request_id": self.id})
        user_id_list = [like_record["user_id"] for like_record in like_list]
        return user_id_list

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }


class LocationByNameIn(BaseModel):
    country: str = Field(..., max_length=20)
    city: str = Field(..., max_length=20)


class LocationByNumberIn(BaseModel):
    latitude: float
    longitude: float


'''
    Socket.io Models
'''


class SocketEvents(BaseModel):
    direct_message: str = "direct_message"
    direct_message_sent: str = "direct_message_sent"
    direct_message_seen: str = "direct_message_seen"
    direct_message_seen_ack: str = "direct_message_seen_ack"
    # group_message: str = "group_message"
    server_info: str = "server_info"
    server_error: str = "server_error"


socket_events = SocketEvents()


class ServerResponse(BaseModel):
    message: str
    type: str


class ClientDirectMessagePacket(BaseModel):
    token: str
    receiver: str
    content: Any
    content_type: str


class ClientSeenDirectMessagePacket(BaseModel):
    token: str
    sender: str


class ServerDirectMessagePacket(BaseModel):
    id: str
    sender: str
    receiver: str
    content: Any
    content_type: str


class ChatHistory(BaseModel):
    sender: str
    receiver: str
    content: Any
    content_type: str
    status: str

from fastapi import APIRouter, Depends, File, UploadFile, Request
from models import *
from auth import get_current_active_user
import shutil
from pathlib import Path
from typing import List, Optional

router = APIRouter()


def save_profile_image(image: UploadFile, user_id: str):
    extension = Path(image.filename).suffix

    image_name = "{}{}".format(user_id, extension)
    try:
        destination = "profile-images/" + image_name
        print(destination)
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        print(e)
        return None
    finally:
        image.file.close()
    return image_name


@router.post("/users/upload_profile_image", tags=["users"])
async def upload_profile_image(
        request: Request,
        image: UploadFile = File(...),
        user: UserInDB = Depends(get_current_active_user)
):
    saved_image_name = save_profile_image(image, user.id)
    if saved_image_name:
        user.profile_image = saved_image_name
        user.save()
        return {"message": "profile has uploaded successfully",
                "image_url": request.url_for("profile_images", path=user.profile_image),
                "result": True}
    return {"message": "profile has not uploaded successfully", "filename": "", "result": False}


@router.post("/users/update_user_info", tags=["users"])
async def update_user_info(user_info: UserInfoIn, user: UserInDB = Depends(get_current_active_user)):
    user.bio = user_info.bio
    if user_info.activities:
        activity_id_list_in = [activity.id for activity in user_info.activities]
        user.activities_id_list = list(dict.fromkeys(activity_id_list_in + user.activities_id_list))
    user.save()
    return {"message": "user info has been updated.", "result": True}


@router.post("/users/location/by_name", tags=["users"])
async def update_user_location_by_name(location: LocationByNameIn, user: UserInDB = Depends(get_current_active_user)):
    user.city = location.city
    user.country = location.country
    user.save()
    return {"message": "user location data has been updated.", "result": True}


@router.post("/users/location/by_coordinates", tags=["users"])
async def update_user_location_coordinates(location: LocationByNumberIn,
                                           user: UserInDB = Depends(get_current_active_user)):
    coordinates_list = [location.longitude, location.latitude]
    user.loc = coordinates_list
    user.save()
    return {"message": "user location data has been updated.", "result": True}


# class UserPaginateOptions(str, Enum):
#     popular = "popular"
#     near = "near"
#     recent = "recent"

PAGE_SIZE = 15


@router.post("/users/", tags=["users"], response_model=List[UserOutWithDistance])
async def get_users(activity_list: Optional[List[ActivityInDB]] = None,
                    user: UserInDB = Depends(get_current_active_user), page_number: int = 1):
    if activity_list is None:
        activity_ids = user.activities_id_list
    else:
        activity_ids = [activity.id for activity in activity_list]

    if not user.loc:
        users = users_collection.find().skip(
            PAGE_SIZE * (page_number - 1)).limit(PAGE_SIZE)
    else:
        # users = users_collection.find(
        #     {"loc": {"$near": user.loc}}).skip(
        #     PAGE_SIZE * (page_number - 1)).limit(PAGE_SIZE)
        # print(users)
        users = users_collection.aggregate([
            {
                "$geoNear": {
                    "near": user.loc,
                    "distanceField": "distance",
                    "spherical": True,
                    "distanceMultiplier": 6371
                }
            },
            {
                "$match": {
                    "activities_id_list": {"$in": activity_ids}
                }

            },
            {
                "$skip": PAGE_SIZE * (page_number - 1)
            },
            {
                "$limit": PAGE_SIZE
            }
        ])
    users = [UserOutWithDistance(**user) for user in users]
    return users
# "activities_id_list": {"$in": activity_ids},

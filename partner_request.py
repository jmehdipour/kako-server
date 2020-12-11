from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_active_user
from models import *
from enum import Enum
from MONGO import partner_requests_collection, activities_collection
from typing import List, Optional
from datetime import datetime

router = APIRouter()


@router.post("/partner_requests", tags=["partner_requests"])
async def create_partner_request(partner_request: PartnerRequestIn, user: UserInDB = Depends(get_current_active_user)):
    partner_request_dict = partner_request.dict()
    if not activities_collection.find_one({"_id": partner_request.activity_id}):
        raise HTTPException(400, detail="there is no activity category with this id.")

    partner_request_dict.update({
        "user_id": user.id,
        "created_datetime": datetime.utcnow(),
        "city": user.city,
        "country": user.country,
        "owner_full_name": user.full_name,
        "owner_username": user.username,
        "owner_profile_image": user.profile_image,
        "loc": user.loc
    })
    if user.loc:
        partner_request_dict["loc"] = user.loc
    else:
        partner_request_dict["loc"] = None

    result = partner_requests_collection.insert_one(partner_request_dict)
    created_partner_request = partner_requests_collection.find_one({"_id": result.inserted_id})
    return {
        "result": True,
        "partner_request": PartnerRequestOut(**created_partner_request)
    }


@router.get("/partner_requests/{request_id}", dependencies=[Depends(get_current_active_user)],
            tags=["partner_requests"])
async def get_partner_request(request_id: str):
    partner_request = partner_requests_collection.find_one({"id": request_id})
    request_owner = PartnerRequest(**partner_request).request_owner()

    return PartnerRequestOut(
        **partner_request,
        owner_full_name=request_owner.full_name,
        owner_username=request_owner.username,
        owner_profile_image=request_owner.profile_image
    )


class RequestPaginateOptions(str, Enum):
    popular = "popular"
    near = "near"
    recent = "recent"


PAGE_SIZE = 15


def get_paginated_partner_requests(page_number: int, sort_field: str, activity_ids: List[PyObjectId], order: int = -1):
    return partner_requests_collection.find({"activity_id": {"$in": activity_ids}}).sort(sort_field, order).skip(
        PAGE_SIZE * (page_number - 1)).limit(PAGE_SIZE)


@router.post("/partner_requests/{paginate_option}", tags=["partner_requests"])
async def get_partner_requests(
        paginate_option: RequestPaginateOptions,
        activity_list: Optional[List[ActivityInDB]] = None,
        user: UserInDB = Depends(get_current_active_user),
        page_number: int = 1,

):
    if activity_list is None:
        activity_ids = user.activities_id_list
    else:
        activity_ids = [activity.id for activity in activity_list]
    if paginate_option == RequestPaginateOptions.popular:
        partner_requests = get_paginated_partner_requests(page_number, sort_field="likes", activity_ids=activity_ids)
    elif paginate_option == RequestPaginateOptions.recent:
        partner_requests = get_paginated_partner_requests(page_number, sort_field="created_datetime",
                                                          activity_ids=activity_ids)
    elif paginate_option == RequestPaginateOptions.near:
        if user.loc is None:
            partner_requests = partner_requests_collection.find({"city": user.city, "country": user.country}).skip(
                PAGE_SIZE * (page_number - 1)).limit(PAGE_SIZE)
            # rais HTTPException(400, detail="there is no location coordinates for this user.")
        else:
            partner_requests = partner_requests_collection.aggregate([
                {
                    "$geoNear": {
                        "near": user.loc,
                        "distanceField": "distance",
                        "spherical": True,
                        "distanceMultiplier": 6371
                    }
                },
                {
                    "$skip": PAGE_SIZE * (page_number - 1)
                },
                {
                    "$limit": PAGE_SIZE
                }
            ])
            # for p in partner_requests:
            #     print(p["dist"])
            # partner_requests = partner_requests_collection.find(
            #     {"activity_id": {"$in": activity_ids}, "loc": {"$near": user.loc}}).skip(
            #     PAGE_SIZE * (page_number - 1)).limit(PAGE_SIZE)
            partner_requests = [PartnerRequestOutWithDistance(**partner_request) for partner_request in
                                partner_requests]
            return partner_requests
    partner_requests = [PartnerRequestOut(**partner_request) for partner_request in partner_requests]
    return partner_requests

# import geopy.distance
#
# coords_1 = (36.6483, 53.2989)
# coords_2 = (36.5659, 53.0586)
#
# print(geopy.distance.distance(coords_1, coords_2).km)

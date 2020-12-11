from MONGO import db_client
import pprint
import pymongo

test_db_geo = db_client["test_db_geo"]

test_collection = test_db_geo["test"]
#
# test_collection.insert_one({"city": "ghom", "loc": [34.639999, 50.876389]})
# test_collection.insert_one({"city": "tabriz", "loc": [38.066666, 46.299999]})
# test_collection.insert_one({"city": "bandar abbas", "loc": [27.183708, 56.277447]})
# test_collection.insert_one({"city": "takestan", "loc": [36.072098, 49.701347]})
# test_collection.insert_one({"city": "Karaj", "loc": [35.855938, 50.961750]})
# test_collection.insert_one({"city": "Yasuj", "loc": [30.668383, 51.587524]})
# test_collection.insert_one({"city": "Ahvaz", "loc": [31.318327, 48.670620]})
# test_collection.insert_one({"city": "Gorgan", "loc": [36.841644, 54.432922]})
# test_collection.insert_one({"city": "Urmia", "loc": [37.552673, 45.076046]})
# test_collection.insert_one({"city": "Āmol", "loc": [36.471546, 52.355087]})
# test_collection.insert_one({"city": "Varamin", "loc": [35.325241, 51.647198]})
# test_collection.insert_one({"city": "Birjand", "loc": [32.872379, 59.221375]})
# test_collection.insert_one({"city": "Yazd", "loc": [31.897423, 54.356857]})
# test_collection.insert_one({"city": "Kerman", "loc": [30.283937, 57.083363]})
# test_collection.insert_one({"city": "Mashhad", "loc": [36.310699, 59.599457]})
# test_collection.insert_one({"city": "Shiraz", "loc": [29.591768, 52.583698]})
# test_collection.insert_one({"city": "Rasht", "loc": [37.280834, 49.583057]})
# test_collection.insert_one({"city": "Isfahan", "loc": [32.661343, 51.680374]})


test_collection.create_index([("loc", pymongo.GEO2D)])

for doc in test_collection.find({"loc": {"$near": [36.310699, 59.599457]}}).limit(7):
    pprint.pprint(doc)
from socketio import AsyncServer, ASGIApp
from socketio.exceptions import ConnectionRefusedError
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from socketio.asyncio_namespace import AsyncNamespace
from pydantic import BaseModel, ValidationError
import auth
from fastapi.security.utils import get_authorization_scheme_param
from models import ClientDirectMessagePacket, ServerDirectMessagePacket, ServerResponse, socket_events, ChatHistory, \
    ClientSeenDirectMessagePacket
from MONGO import direct_messages_collection, group_messages_collection


async def get_authenticated_user(authorization: str):
    # authorization: str = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await auth.get_current_active_user(await auth.get_current_user(param))


class ChatNameSpace(AsyncNamespace):

    async def on_connect(self, sid, *args, **kwargs):
        try:
            user = await get_authenticated_user(args[0]["HTTP_TOKEN"])
            self.enter_room(sid, str(user.id))
            print("********* Connected *********", str(user.id))
        except HTTPException:
            print("********* Connection Error *********")
            raise ConnectionRefusedError("authentication failed")

    async def on_disconnect(self, environ, *args, **kwargs):
        print("********* Disconnected *********")

    async def on_direct_message(self, sid, *args, **kwargs):
        print("********* On Direct Message *********")

        try:
            direct_message_packet = ClientDirectMessagePacket(**args[0])
            user = await get_authenticated_user(direct_message_packet.token)
            chat_history = ChatHistory(sender=str(user.id), status="sent", **direct_message_packet.dict())
            result = direct_messages_collection.insert_one(chat_history.dict())
            server_packet = ServerDirectMessagePacket(id=str(result.inserted_id), **chat_history.dict())
            await self.emit(socket_events.direct_message,
                            # {"content": server_packet.content},
                            server_packet.dict(),
                            room=server_packet.receiver)
            await self.emit(socket_events.direct_message_sent,
                            ServerResponse(message="direct message sent!", type="direct_message_sent").dict(),
                            room=str(user.id))
            print("********* Direct Message Sent. *********")
        except HTTPException:
            await self.disconnect(sid, namespace=self.namespace)
            print("##### Error ######")
        except ValidationError:
            await self.emit(socket_events.server_error,
                            ServerResponse(message="packet validation error", type="validation_error").dict(),
                            room=sid)
            print("##### Error ######i")
        except:
            await self.emit(socket_events.server_error,
                            ServerResponse(message="something went wrong", type="error").dict(),
                            room=sid)
            print("##### Error ######l")

    async def on_direct_message_seen(self, sid, *args, **kwargs):
        try:
            seen_packet = ClientSeenDirectMessagePacket(**args[0])
            user = await get_authenticated_user(seen_packet.token)
            await self.emit(socket_events.direct_message_seen_ack, {"receiver": str(user.id)}, room=seen_packet.sender)
            direct_messages_collection.update_many(
                {"$and":
                    [
                        {"sender": seen_packet.sender},
                        {"receiver": str(user.id)},
                        {"status": "sent"}
                    ]
                },
                {"status": "seen"}
            )
        except HTTPException:
            await self.disconnect(sid, namespace=self.namespace)
            print("##### HTTPException ######")
        except ValidationError:
            await self.emit(socket_events.server_error,
                            ServerResponse(message="packet validation error", type="validation_error").dict(),
                            room=sid)
            print("##### ValidationError ######")
        except:
            await self.emit(socket_events.server_error,
                            ServerResponse(message="something went wrong", type="error").dict(),
                            room=sid)
            print("##### General Error ######")


sio = AsyncServer(async_mode='asgi')
sio.register_namespace(ChatNameSpace('/chat'))
socket_app = ASGIApp(sio)


@sio.on("my event")
async def my_event(sid, data):
    print("*#*#*#*#*#*")


class HeadersModel(BaseModel):
    HTTP_TOKEN: str


def get_headers(data: tuple) -> HeadersModel:
    data: dict = data[0]
    result = HeadersModel(**data)
    # print(result)
    return result

async def create_users_and_room(
    session,
    count=2,
    telegram_id_start=1000,
):
    from database.models import Room, RoomMember, User

    users = [
        User(
            telegram_id=telegram_id_start + index,
            first_name=f"User {index}",
        )
        for index in range(1, count + 1)
    ]

    session.add_all(users)
    await session.flush()

    room = Room(
        owner_id=users[0].id,
        code=f"TEST{users[0].id:04d}",
    )

    session.add(room)
    await session.flush()

    members = [
        RoomMember(
            room_id=room.id,
            user_id=user.id,
        )
        for user in users
    ]

    session.add_all(members)
    await session.flush()

    return users, room, members
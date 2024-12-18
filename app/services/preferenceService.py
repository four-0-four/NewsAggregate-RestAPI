from app.data.preferencData import get_default_preferences, delete_all_user_preferences, \
    insert_default_preferences_for_user, get_user_preference, add_user_preference, remove_user_preference, \
    add_user_blacklist, remove_user_blacklist


async def add_user_news_source_preference(user_id: int, corporation_id: int) -> str:
    # First, check if the preference already exists
    existing_preference = await get_user_preference(user_id, corporation_id)
    if existing_preference and existing_preference["Preference"] == 1:
        raise Exception("Preference already exists.")

    if existing_preference and existing_preference["Preference"] == 0:
        raise Exception("News Source is blacklisted. Consider removing it from blacklist first.")
    await add_user_preference(user_id, corporation_id)
    return "Preference added successfully."


async def remove_user_news_source_preference(user_id: int, corporation_id: int) -> str:
    # First, check if the preference already exists
    existing_preference = await get_user_preference(user_id, corporation_id)
    if not existing_preference:
        raise Exception("Preference does not exists.")

    if existing_preference and existing_preference["Preference"] == 0:
        raise Exception("News Source is blacklisted. Consider removing it from blacklist first.")

    await remove_user_preference(user_id, corporation_id)
    return "Preference removed successfully."


async def add_user_news_blacklist(user_id: int, corporation_id: int) -> str:
    # First, check if the preference already exists
    existing_preference = await get_user_preference(user_id, corporation_id)
    if existing_preference and existing_preference["Preference"] == 0:
        raise Exception("Blacklist already exists.")

    if existing_preference and existing_preference["Preference"] == 1:
        raise Exception("News Source is already in the preference list. Consider removing it from preference first.")

    await add_user_blacklist(user_id, corporation_id)
    return "blacklist added successfully."


async def remove_user_news_blacklist(user_id: int, corporation_id: int) -> str:
    # First, check if the preference already exists
    existing_preference = await get_user_preference(user_id, corporation_id)
    if not existing_preference:
        raise Exception("black list does not exists.")

    if existing_preference and existing_preference["Preference"] == 1:
        raise Exception("News Source is already in the preference list. Consider removing it from preference first.")

    await remove_user_blacklist(user_id, corporation_id)
    return "blacklist removed successfully."


async def reset_preference_for_user(user):
    default_preferences = await get_default_preferences()
    if not default_preferences:
        return
    # Delete all the preferences for the user
    await delete_all_user_preferences(user["id"])

    # Add the default preferences for the user
    await insert_default_preferences_for_user(user["id"], default_preferences)



async def add_default_for_new_user(user):
    default_preferences = await get_default_preferences()
    if not default_preferences:
        return

    # Add the default preferences for the user
    await insert_default_preferences_for_user(user.id, default_preferences)
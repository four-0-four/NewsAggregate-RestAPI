import os

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, Path
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated, Optional, List

from starlette.exceptions import HTTPException

from app.config.dependencies import db_dependency
from app.data.newsData import get_category_by_topic, get_keyword
from app.data.userData import check_username_in_db, update_username_in_db, update_first_name_in_db, \
    update_last_name_in_db, get_user_by_id
from app.email.sendEmail import sendEmail, sendEmailInternal, sendEmailWithMultipleAttachments
from app.models.user import ContactUsInput, reportBugInput, UsernameCheckInput, UpdateProfileInput, ChangePasswordInput, \
    ChangePasswordInputProfile
from app.services.authService import get_current_user
from app.services.commonService import get_category_by_id, get_keyword_byID
from app.services.userService import create_category_following, create_keyword_following, get_all_keyword_following, \
    get_all_category_following, remove_category_following, remove_keyword_following,  \
    change_password_profile

router = APIRouter(prefix="/user", tags=["user"])
limiter = Limiter(key_func=get_remote_address)
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/profile/check-username")
async def check_username(
    username: str
):
    # You might want to handle the database query logic here
    exists = await check_username_in_db(username)
    return {"exists": exists}


@router.patch("/profile/update")
async def update_profile(input: UpdateProfileInput, authenticatedUser: user_dependency, db: db_dependency):
    user = await get_user_by_id(authenticatedUser["id"])

    if input.username and input.username!= user["username"]:
        if await check_username_in_db(input.username):
            raise HTTPException(status_code=400, detail="Username already taken")
        await update_username_in_db(authenticatedUser["id"], input.username)

    if input.first_name and input.first_name != user["first_name"]:
        await update_first_name_in_db(authenticatedUser["id"], input.first_name)

    if input.last_name and input.last_name != user["last_name"]:
        await update_last_name_in_db(authenticatedUser["id"], input.last_name)

    user = await get_user_by_id(authenticatedUser["id"])
    return {
        "username": user["username"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "is_active": user["is_active"],
    }


@router.patch("/profile/change-password")
async def change_user_password(input: ChangePasswordInputProfile, authenticatedUser: user_dependency, db: db_dependency):
    # Call the change_password function
    try:
        return await change_password_profile(authenticatedUser["id"], input.old_password, input.new_password, input.confirm_password)
    except HTTPException as e:
        print(e)
        raise e


@router.get("/get-followings")
async def get_followings(
        request: Request,
        user: user_dependency,
        db: db_dependency):
    all_followings = []
    keyword_followings = get_all_keyword_following(db, user["id"])
    category_followings = get_all_category_following(db, user["id"])

    all_followings.extend(keyword_followings)
    all_followings.extend(category_followings)
    return all_followings


@router.post("/add-following/category")
async def add_following_category(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        category_id: int):
    # check if category exists
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # add it to the following table and get the created entity
    following_entity = create_category_following(db, user["id"], category_id)

    return {"message": "Category following added successfully", "following": following_entity}



@router.post("/add-following/keyword")
async def add_following_keyword(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        keyword_id: int):
    # check if keyword exists
    keyword = get_keyword_byID(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # add it to the following table and get the created entity
    following_entity = create_keyword_following(db, user["id"], keyword_id)

    return {"message": "Keyword following added successfully", "following": following_entity}


@router.post("/contactUs")
async def contact_us(request: Request, db: db_dependency, message: ContactUsInput):
    subject = "Farabix Contact Us - " + message.full_name + " - " + message.topic
    message_text = "Email: " + message.email + "\n" + "Full Name: " + message.full_name + "\n" + "Topic: " + message.topic + "\n\n\n" + message.message

    try:
        sendEmailInternal("Farabix Support <admin@farabix.com>", "msina.raf@gmail.com", subject, message_text)
        return {"message": "Email sent successfully"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/reportBug")
async def contact_us(
    full_name: str = Form(...),
    email: str = Form(...),
    bug: str = Form(...),
    description: str = Form(...),
    files: List[Optional[UploadFile]] = File(None)  # Accept a list of files
):
    subject = "Farabix Report Bug - " + full_name + " - " + bug
    message_text = "Email: " + email + "\nFull Name: " + full_name + "\nBug: " + bug + "\n\n\n" + description

    file_locations = []
    try:
        # Iterate through each file and save it
        for file in files:
            if file and file.filename:
                file_location = f"temp_files/{file.filename}"
                with open(file_location, "wb+") as file_object:
                    file_object.write(file.file.read())
                file_locations.append(file_location)
        # Send email with attachments
        if len(file_locations) > 0:
            sendEmailWithMultipleAttachments("Farabix Support <admin@farabix.com>", "msina.raf@gmail.com", subject, message_text, file_locations)
            return {"message": "Email sent successfully"}
        else:
            sendEmailInternal("Farabix Support <admin@farabix.com>", "msina.raf@gmail.com", subject, message_text)
            return {"message": "Email sent successfully"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        # Optionally delete the files after sending the email
        for file_location in file_locations:
            if os.path.exists(file_location):
                os.remove(file_location)



@router.post("/requestFeature")
async def contact_us(
    full_name: str = Form(...),
    email: str = Form(...),
    feature: str = Form(...),
    description: str = Form(...),
    files: List[Optional[UploadFile]] = File(None)  # Accept a list of files
):
    subject = "Farabix Report Bug - " + full_name + " - " + feature
    message_text = "Email: " + email + "\nFull Name: " + full_name + "\nFeature: " + feature + "\n\n\n" + description

    file_locations = []
    try:
        # Iterate through each file and save it
        for file in files:
            if file and file.filename:
                file_location = f"temp_files/{file.filename}"
                with open(file_location, "wb+") as file_object:
                    file_object.write(file.file.read())
                file_locations.append(file_location)
        # Send email with attachments
        if len(file_locations) > 0:
            sendEmailWithMultipleAttachments("Farabix Support <admin@farabix.com>", "msina.raf@gmail.com", subject, message_text, file_locations)
            return {"message": "Email sent successfully"}
        else:
            sendEmailInternal("Farabix Support <admin@farabix.com>", "msina.raf@gmail.com", subject, message_text)
            return {"message": "Email sent successfully"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        # Optionally delete the files after sending the email
        for file_location in file_locations:
            if os.path.exists(file_location):
                os.remove(file_location)


@router.post("/add-following")
async def add_following(
        topic: str,
        request: Request,
        user: user_dependency,
        db: db_dependency):
    # Check if it's a category
    category = await get_category_by_topic(topic)
    if category:
        following_entity = create_category_following(db, user["id"], category["id"])
        return {"message": "Category following added successfully", "topic": topic}

    # Check if it's a keyword
    keyword = await get_keyword(topic)
    if keyword:
        following_entity = create_keyword_following(db, user["id"], keyword["id"])
        return {"message": "Keyword following added successfully", "topic": topic}

    raise HTTPException(status_code=404, detail="Topic not found")


# Define a Pydantic model for your request body
class TopicsModel(BaseModel):
    topics: List[str]

@router.post("/add-followings")
async def add_following(
        request_body: TopicsModel,  # Accept a list of topics instead of a single topic
        request: Request,
        user: user_dependency,
        db: db_dependency):
    topics = request_body.topics
    added_topics = []  # To keep track of successfully added topics
    not_found_topics = []  # To keep track of topics that were not found

    for topic in topics:
        # Check if it's a category
        category = await get_category_by_topic(topic)
        if category:
            create_category_following(db, user["id"], category["id"])
            added_topics.append(topic)
            continue  # Move to the next topic

        # Check if it's a keyword
        keyword = await get_keyword(topic)
        if keyword:
            create_keyword_following(db, user["id"], keyword["id"])
            added_topics.append(topic)
            continue  # Move to the next topic

        # If the topic is not found as either a category or a keyword
        not_found_topics.append(topic)

    if not added_topics:
        # If no topics were successfully added
        raise HTTPException(status_code=404, detail="No valid topics found")
    else:
        return {
            "message": "Following added successfully for topics",
            "added_topics": added_topics,
            "not_found_topics": not_found_topics
        }


@router.post("/remove-following")
async def remove_following(
        topic: str,
        request: Request,
        user: user_dependency,
        db: db_dependency):
    # Check if it's a category and if the user is following it
    category = await get_category_by_topic(topic)
    if category:
        remove_category_following(db, user["id"], category["id"])
        return {"message": "Category following removed successfully", "topic": topic}

    # Check if it's a keyword and if the user is following it
    keyword = await get_keyword(topic)
    if keyword:
        remove_keyword_following(db, user["id"], keyword["id"])
        return {"message": "Keyword following removed successfully", "topic": topic}

    raise HTTPException(status_code=404, detail="Topic not found")
from typing import Any

from aiogram.types import FSInputFile
from sqlalchemy import select

from bot import bot
from models import Channel, MediaFile, Post, User

from .base import BaseRepository


class PostRepository(BaseRepository):
    def get_by_id(self, post_id: int) -> Post | None:
        """
        Возвращает пост по его ID.
        :param post_id: ID поста.
        :return: Пост или None, если пост не найден.
        """
        return self.session.execute(select(Post).where(Post.id == post_id)).scalar()

    async def send_post(self, post_id: int) -> None:
        """
        Отправляет пост в указанный канал.
        :param post: Пост, который нужно отправить.
        """
        try:
            post = self.get_by_id(post_id)
            channels = post.channels
            total_channels = len(channels)
            sended_channels = 0

            media_file_type = (
                post.post_media_file.media_file_type if post.post_media_file else None
            )
            media_file_path = (
                post.post_media_file.media_file_path if post.post_media_file else None
            )
            media_file_name = (
                post.post_media_file.media_file_name if post.post_media_file else None
            )
            media_file_position = (
                post.post_media_file.media_file_position
                if post.post_media_file
                else None
            )

            text = post.text
            message = None
            channels = []
            channel_members = 0

            if not len(post.channels):
                print(f"No channels found for post ID {post_id}")
                return

            for channel in post.channels:
                print(f"Sending post to channel {channel.chat_id}")

                if media_file_type == "photo":
                    photo = FSInputFile(path=media_file_path, filename=media_file_name)
                    message = await bot.send_photo(
                        chat_id=channel.chat_id,
                        photo=photo,
                        caption=text,
                        disable_notification=not post.sound,
                        # protect_content=not post.comments,
                        show_caption_above_media=(
                            True if media_file_position == "bottom_preview" else False
                        ),
                    )

                elif media_file_type == "video":
                    video = FSInputFile(path=media_file_path, filename=media_file_name)
                    message = await bot.send_video(
                        chat_id=channel.chat_id,
                        video=video,
                        caption=text,
                        disable_notification=not post.sound,
                        # protect_content=not post.comments,
                        show_caption_above_media=(
                            True if media_file_position == "bottom_preview" else False
                        ),
                    )

                else:
                    message = await bot.send_message(
                        chat_id=channel.chat_id,
                        text=text,
                    )

                if post.pin:
                    print(
                        f"Pinning message {message.message_id} in channel {channel.chat_id}"
                    )
                    await bot.pin_chat_message(
                        chat_id=channel.chat_id,
                        message_id=message.message_id,
                        disable_notification=not post.sound,
                    )

                if message:
                    sended_channels += 1
                    channels.append(channel.dict())

                if not post.comments:
                    # get all user ids from channel
                    channel_members = await bot.get_chat_member_count(
                        chat_id=channel.chat_id
                    )
                    # for member in channel_members:
                    await bot.restrict_chat_member(
                        chat_id=channel.chat_id,
                        user_id=post.user.chat_id,
                        permissions={
                            "can_send_messages": False,
                            "can_send_media_messages": False,
                            "can_send_polls": False,
                            "can_add_web_page_previews": False,
                            "can_change_info": False,
                            "can_invite_users": False,
                            "can_pin_messages": False,
                        },
                    )
                if post.signature:
                    await bot.send_message(
                        chat_id=channel.chat_id,
                        text=f"Post by @{post.user.username}",
                    )

        except Exception as e:
            print(f"Error sending post: {e}")

        finally:
            return {
                "sended_channels": sended_channels,
                "total_channels": total_channels,
                "post": post,
                "channels": channels,
                "channel_members": channel_members,
                "user": post.user,
            }

    def create_post(self, user: User, post_form: dict[str, Any]) -> Post | bool:
        """
        Создает новый пост и связывает его с пользователем.
        :param user: Пользователь, которому принадлежит пост.
        :param post_form: Данные поста.
        """
        try:
            chat_channel_list = post_form.get("chat_channel_list")
            post = Post(
                user_id=user.id,
                text=post_form.get("text"),
                sound=True if post_form.get("sound") == "on" else False,
                comments=True if post_form.get("comments") == "on" else False,
                pin=True if post_form.get("pin") == "on" else False,
                signature=True if post_form.get("signature") == "on" else False,
            )
            self.session.add(post)
            if chat_channel_list:
                for chat_channel in chat_channel_list:
                    channel = self.session.execute(
                        select(Channel).where(Channel.id == chat_channel["id"])
                    ).scalar()
                    if channel:
                        post.channels.append(channel)

            if post_form["media_file_name"]:
                # Создаем новый объект MediaFile
                post_media_file = MediaFile(
                    media_file_path=post_form.get("media_file_path"),
                    media_file_name=post_form.get("media_file_name"),
                    media_file_type=post_form.get("media_file_type"),
                    media_file_position=post_form.get("media_file_position"),
                    post=post,
                )
                self.session.add(post_media_file)
                post.post_media_file = post_media_file
            self.session.commit()
            return post
        except Exception as e:
            print(f"Error creating post: {e}")
            return False

    def update_post(self, post_id: int, post_form: dict[str, Any]) -> Post | bool:
        """
        Обновляет пост по его ID.
        :param post_id: ID поста.
        :param post_form: Данные поста.
        """
        try:
            post = self.get_by_id(post_id)
            if not post:
                print(f"Post with ID {post_id} not found")
                return False

            post.text = post_form.get("text")
            post.sound = True if post_form.get("sound") == "on" else False
            post.comments = True if post_form.get("comments") == "on" else False
            post.pin = True if post_form.get("pin") == "on" else False
            post.signature = True if post_form.get("signature") == "on" else False

            chat_channel_list = post_form.get("chat_channel_list")
            if chat_channel_list:
                for chat_channel in chat_channel_list:
                    channel = self.session.execute(
                        select(Channel).where(Channel.id == chat_channel["id"])
                    ).scalar()
                    if channel:
                        post.channels.append(channel)

            if post_form["media_file_name"]:
                # Создаем новый объект MediaFile
                media_file = MediaFile(
                    media_file_path=post_form.get("media_file_path"),
                    media_file_name=post_form.get("media_file_name"),
                    media_file_type=post_form.get("media_file_type"),
                    media_file_position=post_form.get("media_file_position"),
                    post=post,
                )
                self.session.add(media_file)
                post.post_media_file = media_file

            self.session.commit()
            return post
        except Exception as e:
            print(f"Error updating post: {e}")
            return False

    def delete_post(self, post_id: int) -> bool:
        """
        Удаляет пост по его ID.
        :param post_id: ID поста.
        """
        try:
            post = self.get_by_id(post_id)
            if not post:
                print(f"Post with ID {post_id} not found")
                return False

            self.session.delete(post)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error deleting post: {e}")
            return False

    def archive_post(self, post_id: int) -> bool:
        """
        Архивирует пост по его ID.
        :param post_id: ID поста.
        """
        try:
            post = self.get_by_id(post_id)
            if not post:
                print(f"Post with ID {post_id} not found")
                return False

            post.is_archived = True
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error archiving post: {e}")
            return False

    def unarchive_post(self, post_id: int) -> bool:
        """
        Разархивирует пост по его ID.
        :param post_id: ID поста.
        """
        try:
            post = self.get_by_id(post_id)
            if not post:
                print(f"Post with ID {post_id} not found")
                return False

            post.is_archived = False
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error unarchiving post: {e}")
            return False

    def get_all_posts_by_user_id(self, user_id: int) -> list[Post]:
        """
        Возвращает все посты пользователя по его ID.
        :param user_id: ID пользователя.
        :return: Список постов пользователя.
        """
        return (
            self.session.query(Post)
            .filter(Post.user_id == user_id)
            .order_by(Post.created_at.desc())
            .all()
        )

    def get_all_posts(self) -> list[Post]:
        """
        Возвращает все посты.
        :return: Список всех постов.
        """
        return self.session.query(Post).order_by(Post.created_at.desc()).all()

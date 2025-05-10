from typing import Any

from aiogram import html
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot import bot
from keyboard.keyboard import EmojiButtonData
from models import (
    Channel,
    MediaFile,
    Post,
    PostKeyboard,
    PostReactioButton,
    PostSchedule,
    User,
)

from .base import BaseRepository


class PostRepository(BaseRepository):
    def get_by_id(self, post_id: int) -> Post | None:
        """
        Возвращает пост по его ID.
        :param post_id: ID поста.
        :return: Пост или None, если пост не найден.
        """
        return self.session.execute(select(Post).where(Post.id == post_id)).scalar()

    async def send_post(
        self, post_id: int, send_report_to_owner: bool = False
    ) -> dict[str, Any]:
        """
        Отправляет пост в указанный канал.
        :param post: Пост, который нужно отправить.
        """
        try:

            ikb = InlineKeyboardBuilder()
            ikb_reaction = InlineKeyboardBuilder()
            ikb_buttons = InlineKeyboardBuilder()

            post = self.get_by_id(post_id)
            channels = post.channels
            total_channels = len(channels)
            sended_channels = 0
            reactions = post.post_reaction_buttons
            buttons = post.post_keyboards

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

            if reactions:
                for reaction in reactions:
                    ikb_reaction.button(
                        text=reaction.text,
                        callback_data=EmojiButtonData(
                            action="add_reaction",
                            post_id=post_id,
                            id=reaction.id,
                            text=reaction.text,
                            type="emoji_action",
                        ).pack(),
                    )
                ikb_reaction.adjust(len(reactions))
                ikb.attach(InlineKeyboardBuilder.from_markup(ikb_reaction.as_markup()))

            if buttons:
                for button in buttons:
                    if button.button_column == 0:
                        ikb_buttons.button(
                            text=button.button_text,
                            url=button.button_url,
                        )
                    else:
                        ikb_buttons.row()
                        ikb_buttons.button(
                            text=button.button_text,
                            url=button.button_url,
                        )
                ikb_buttons.adjust(len(buttons))
                ikb.attach(InlineKeyboardBuilder.from_markup(ikb_buttons.as_markup()))

            if not len(post.channels):
                print(f"No channels found for post ID {post_id}")
                return

            for channel in post.channels:
                print(f"Sending post to channel {channel.chat_id}")
                try:
                    if media_file_type == "photo":
                        photo = FSInputFile(
                            path=media_file_path, filename=media_file_name
                        )
                        message = await bot.send_photo(
                            chat_id=channel.chat_id,
                            photo=photo,
                            caption=text,
                            disable_notification=not post.sound,
                            # protect_content=not post.comments,
                            reply_markup=ikb.as_markup(),
                            show_caption_above_media=(
                                True
                                if media_file_position == "bottom_preview"
                                else False
                            ),
                        )
                        if post.recipient_post_chat_id:
                            await bot.send_photo(
                                chat_id=post.recipient_post_chat_id,
                                photo=photo,
                                caption=text,
                                disable_notification=not post.sound,
                                reply_markup=ikb.as_markup(),
                            )

                    elif media_file_type == "video":
                        video = FSInputFile(
                            path=media_file_path, filename=media_file_name
                        )
                        message = await bot.send_video(
                            chat_id=channel.chat_id,
                            video=video,
                            caption=text,
                            disable_notification=not post.sound,
                            reply_markup=ikb.as_markup(),
                            # protect_content=not post.comments,
                            show_caption_above_media=(
                                True
                                if media_file_position == "bottom_preview"
                                else False
                            ),
                        )
                        if post.recipient_post_chat_id:
                            await bot.send_video(
                                chat_id=post.recipient_post_chat_id,
                                video=video,
                                caption=text,
                                disable_notification=not post.sound,
                                reply_markup=ikb.as_markup(),
                            )

                    else:
                        message = await bot.send_message(
                            chat_id=channel.chat_id,
                            text=text,
                            reply_markup=ikb.as_markup(),
                        )
                        if post.recipient_post_chat_id:
                            await bot.send_message(
                                chat_id=post.recipient_post_chat_id,
                                text=text,
                                reply_markup=ikb.as_markup(),
                            )

                    if post.pin:
                        await bot.pin_chat_message(
                            chat_id=channel.chat_id,
                            message_id=message.message_id,
                            disable_notification=not post.sound,
                        )

                    if message and channel:
                        sended_channels += 1
                        channels.append(channel)
                        post.messages_ids.append(
                            {
                                "chat_id": channel.chat_id,
                                "message_id": message.message_id,
                            }
                        )
                        if not channel.messages_ids:
                            channel.messages_ids = []
                        channel.messages_ids.append(
                            {
                                "chat_id": channel.chat_id,
                                "post_id": post.id,
                                "message_id": message.message_id,
                            }
                        )
                        self.session.add(channel)
                        self.session.add(post)
                        self.session.commit()

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
                        message = await bot.send_message(
                            chat_id=channel.chat_id,
                            text=f"Post by @{post.user.username}",
                        )

                except Exception as e:
                    print(f"Error sending post to channel {channel.chat_id}: {e}")
                    continue
        except Exception as e:
            print(f"Error sending post: {e}")

        finally:
            channels = ""
            for channel in channels:
                channels += f"{html.blockquote(html.code(channel.title + '/' + channel.type))}\n"

            if post.recipient_report_chat_id:
                try:
                    await bot.send_message(
                        chat_id=post.recipient_report_chat_id,
                        text=f"✅ Отправка завершена!\n\n📨 Доставлено {sended_channels}/{total_channels}:\n\n",
                    )
                except Exception as e:
                    print(f"Error sending report to user: {e}")

            if send_report_to_owner:
                await bot.send_message(
                    chat_id=post.user.chat_id,
                    text=f"✅ Отправка завершена!\n\n📨 Доставлено {sended_channels}/{total_channels}:\n\n{channels}\n\n",
                )
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
            date_frames_confirm = post_form.get("date_frames_confirm", None)
            reactions = post_form.get("reactions")
            buttons = post_form.get("buttons")

            post = Post(
                user_id=user.id,
                text=post_form.get("text"),
                sound=True if post_form.get("sound") == "on" else False,
                comments=True if post_form.get("comments") == "on" else False,
                pin=True if post_form.get("pin") == "on" else False,
                signature=True if post_form.get("signature") == "on" else False,
                recipient_report_chat_id=post_form.get("recipient_report_chat_id"),
                recipient_post_chat_id=post_form.get("recipient_post_chat_id"),
            )

            self.session.add(post)

            if date_frames_confirm:
                post_schedule = PostSchedule(
                    schedule_date_frames=post_form.get("date_frames"),
                    is_active=True,
                    post=post,
                )
                self.session.add(post_schedule)

            if reactions:
                for reaction in reactions:
                    post_reaction = PostReactioButton(
                        text=reaction,
                        post=post,
                    )
                    self.session.add(post_reaction)
                    post.post_reaction_buttons.append(post_reaction)

            if buttons:
                for button in buttons:
                    post_keyboard = PostKeyboard(
                        button_text=button["name"],
                        button_url=button["url"],
                        button_column=button["column"],
                        button_row=button["row"],
                        post=post,
                    )
                    self.session.add(post_keyboard)
                    post.post_keyboards.append(post_keyboard)

            if chat_channel_list:
                for chat_channel in chat_channel_list:
                    channel = self.session.execute(
                        select(Channel).where(Channel.id == chat_channel["id"])
                    ).scalar()
                    if channel:
                        post.channels.append(channel)

            if post_form.get("media_file_name"):
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

    def get_post_by_forward_message(
        self, user_id: int, forward_from_chat_id: str, forward_from_message_id: int
    ) -> Post | None:
        # fund channel by forward_from_chat_id and user_id
        channel = self.session.execute(
            select(Channel).where(
                Channel.chat_id == forward_from_chat_id,
                Channel.user_id == user_id,
            )
        ).scalar()

        if not channel:
            print(f"Channel with chat_id {forward_from_chat_id} not found")
            return None

        if not channel.messages_ids:
            print(f"Channel with chat_id {forward_from_chat_id} has no messages_ids")
            return None
        # find post by forward_from_message_id and channel
        for message_id in channel.messages_ids:
            if (
                message_id["chat_id"] == forward_from_chat_id
                and message_id["message_id"] == forward_from_message_id
            ):
                post = self.session.execute(
                    select(Post).where(Post.id == message_id["post_id"])
                ).scalar()
                return post

        return None

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
            post.recipient_report_chat_id = post_form.get("recipient_report_chat_id")

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

    def update_post_reaction_by_user_id(
        self, post_id: int, reaction_id: int, user_id: int
    ) -> bool:
        """
        Обновляет реакцию пользователя на пост.
        :param post_id: ID поста.
        :param reaction_id: ID реакции.
        :param user_id: ID пользователя.
        """
        try:
            post = self.get_by_id(post_id)
            if not post:
                print(f"Post with ID {post_id} not found")
                return False
            all_reactions = (
                self.session.execute(
                    select(PostReactioButton).where(
                        PostReactioButton.post_id == post.id,
                    )
                )
                .scalars()
                .all()
            )
            reaction = self.session.execute(
                select(PostReactioButton).where(
                    PostReactioButton.id == reaction_id,
                    PostReactioButton.post_id == post.id,
                )
            ).scalar()

            if not reaction:
                print(f"Reaction with ID {reaction_id} not found")
                return False

            if user_id not in reaction.reactions:
                for r in all_reactions:
                    if user_id in r.reactions:
                        r.reactions.remove(user_id)
                reaction.reactions.append(user_id)
            # self.session.add(reaction)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error updating post reaction: {e}")
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

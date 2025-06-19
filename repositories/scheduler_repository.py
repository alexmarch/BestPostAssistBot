from models import PostSchedule
from utils.scheduler import scheduler

from .base import BaseRepository


class ScheduleRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session)
        self.model = PostSchedule

    def find_by_post_id(self, post_id: int) -> PostSchedule:
        return self.session.query(self.model).filter_by(post_id=post_id).first()

    def create_schedule(
        self, post_id: int, schedule_time_frames: str, schedule_date_frames: str
    ) -> PostSchedule | None:
        try:
            schedule = self.model(
                post_id=post_id,
                schedule_time_frames=schedule_time_frames.join("|"),
                schedule_date_frames=schedule_date_frames.join("|"),
            )
            self.session.add(schedule)
            self.session.commit()
        except Exception as e:
            print(f"Error creating schedule: {e}")
            self.session.rollback()
            return None
        return schedule

    def update_schedule(
        self, schedule_id: int, schedule_time_frames: str, schedule_date_frames: str
    ) -> PostSchedule:
        schedule = self.session.query(self.model).filter_by(id=schedule_id).first()
        if schedule:
            schedule.schedule_time_frames = schedule_time_frames
            schedule.schedule_date_frames = schedule_date_frames
            self.session.commit()
        return schedule

    def delete_schedule(self, schedule_id: int) -> None:
        schedule = self.session.query(self.model).filter_by(id=schedule_id).first()
        if schedule:
            self.session.delete(schedule)
            self.session.commit()
        return schedule

    def get_schedules_by_post_id(self, post_id: int) -> list[PostSchedule]:
        return self.session.query(self.model).filter_by(post_id=post_id).all()

    def get_schedules_by_user_id(self, user_id: int) -> list[PostSchedule]:
        return (
            self.session.query(self.model)
            .join(PostSchedule.post)
            .filter(PostSchedule.post.user_id == user_id)
            .all()
        )

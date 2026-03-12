import datetime
import random


class SchedulerEngine:

    def generate(self, videos, per_day, days):

        schedule = []

        index = 0

        for day in range(days):

            date = datetime.date.today() + datetime.timedelta(days=day)

            for i in range(per_day):

                if index >= len(videos):
                    return schedule

                hour = random.randint(8, 22)

                schedule.append({

                    "video": videos[index],
                    "date": str(date),
                    "hour": hour

                })

                index += 1

        return schedule
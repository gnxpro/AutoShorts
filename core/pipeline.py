class GNXPipeline:

    def __init__(self, cloudinary, repliz):

        self.cloudinary = cloudinary
        self.repliz = repliz

    # ----------------------------------------

    def process(self, job):

        video_file = job["video"]

        accounts = job["accounts"]

        title = job.get("title", "GNX Video")

        desc = job.get("description", "")

        schedule = job.get("schedule")

        upload = self.cloudinary.upload(video_file)

        video_url = upload["secure_url"]

        for acc in accounts:

            try:

                self.repliz.schedule_one_video(
                    video_url,
                    acc,
                    title,
                    desc,
                    schedule
                )

            except Exception as e:

                print("schedule error:", e)

        return True
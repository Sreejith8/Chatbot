import concurrent.futures

class SyncController:
    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    def process_parallel(self, audio_func, video_func, audio_args=(), video_args=()):
        """
        Executes audio and video processing functions in parallel.
        Returns a tuple of (audio_result, video_result).
        """
        future_audio = self.executor.submit(audio_func, *audio_args)
        future_video = self.executor.submit(video_func, *video_args)
        
        audio_result = future_audio.result()
        video_result = future_video.result()
        
        return audio_result, video_result

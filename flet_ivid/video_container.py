from typing import Any, List, Optional, Tuple, Union
from flet import Container
from flet_core.alignment import Alignment
from flet_core.blur import Blur
from flet_core.border import Border
from flet_core.control import Control, OptionalNumber
from flet_core.gradients import Gradient
from flet_core.ref import Ref
from flet_core.shadow import BoxShadow
from flet_core.theme import Theme
from flet_core.types import AnimationValue, BlendMode, BorderRadiusValue, BoxShape, ClipBehavior, ImageFit, ImageRepeat, MarginValue, OffsetValue, PaddingValue, ResponsiveNumber, RotateValue, ScaleValue, ThemeMode
from flet_core.image import Image
from flet_core.stack import Stack
from flet_core.row import Row
import threading
import flet
import os
import pygame
import cv2
import base64
from moviepy.editor import VideoFileClip
import base64
import time


class VideoContainer (Container):
    """This will show a video you choose."""
    def __init__(self, video_path:str, play_after_loading=False, video_frame_fit_type:flet.ImageFit=None, video_progress_bar=True, content= None, ref = None, key = None, width = None, height= None, left = None, top = None, right = None, bottom= None, expand= None, col = None, opacity= None, rotate= None, scale= None, offset= None, aspect_ratio= None, animate_opacity= None, animate_size = None, animate_position= None, animate_rotation= None, animate_scale= None, animate_offset = None, on_animation_end=None, tooltip = None, visible = None, disabled= None, data = None, padding= None, margin= None, alignment = None, bgcolor= None, gradient= None, blend_mode=BlendMode.NONE, border= None, border_radius= None, image_src= None, image_src_base64= None, image_repeat=None, image_fit=None, image_opacity: OptionalNumber = None, shape=None, clip_behavior= None, ink= None, animate=None, blur=None, shadow= None, url=None, url_target=None, theme=None, theme_mode= None, on_click=None, on_long_press=None, on_hover=None):
        super().__init__(content, ref, key, width, height, left, top, right, bottom, expand, col, opacity, rotate, scale, offset, aspect_ratio, animate_opacity, animate_size, animate_position, animate_rotation, animate_scale, animate_offset, on_animation_end, tooltip, visible, disabled, data, padding, margin, alignment, bgcolor, gradient, blend_mode, border, border_radius, image_src, image_src_base64, image_repeat, image_fit, image_opacity, shape, clip_behavior, ink, animate, blur, shadow, url, url_target, theme, theme_mode, on_click, on_long_press, on_hover)
        if not os.path.isfile (video_path):
            raise FileNotFoundError ("Cannot find the video at the path you set.")

        self.__all_frames_of_video = []
        self.__video_played = False
        self.video_progress_bar = video_progress_bar

        if video_frame_fit_type == None:
            self.video_frame_fit_type = flet.ImageFit.CONTAIN

        # generate the UI
        self.__ui ()

        # start a video reader.
        if play_after_loading:
            print("Please wait the video is loading..\nThis will take a time based on your video size...")
            self.read_the_video(video_path)
        else:
            threading.Thread(target=self.read_the_video, args=[video_path], daemon=True).start()

        # setup the video audio
        try:
            self.audio_path = self.convert_video_to_audio (video_path)
            self.__audio_path = self.audio_path
            self.get_audio_info(self.audio_path)
        except:
            self.audio_path = None
            self.__audio_path = None

        # get video info
        self.get_video_duration(video_path)
        self.__frame_per_sleep = 1.0 / self.fps
    
    def __ui (self):
        # the video tools control
        self.video_tool_stack = Stack(expand=True)
        self.content = self.video_tool_stack

        self.image_frames_viewer = Image(expand=True, visible=False, fit=self.video_frame_fit_type)
        self.video_tool_stack.controls.append(Row([self.image_frames_viewer], alignment="center"))

        self.__video_progress_bar = Container(height=2, width=100, bgcolor=flet.colors.BLUE_200)
        self.video_tool_stack.controls.append(Row([self.__video_progress_bar], alignment=flet.MainAxisAlignment.START))

        if self.video_progress_bar == False:
            self.__video_progress_bar.visible = False
    

    def update_video_progress (self, frame_number):
        if self.video_progress_bar == False: return
        percent_of_progress = frame_number / self.video_frames * 1
        
        try:
            self.__video_progress_bar.width = percent_of_progress * 1 * self.width
        except:
            self.__video_progress_bar.width = percent_of_progress * 1 * self.page.width
        if self.__video_progress_bar.page != None: self.__video_progress_bar.update ()
    

    def update(self):
        self.image_frames_viewer.fit = self.video_frame_fit_type
        self.__video_progress_bar.visible = self.video_progress_bar
        return super().update()
        

    def play (self, *args):
        """Play the video. (its not bloking, becuase its on thread)."""
        if self.page == None:
            raise Exception("The control must be on page first.")

        self.__video_played = True
        threading.Thread(target=self.__play, daemon=True).start()
        
    def __play (self):
        # -------
        self.image_frames_viewer.visible = True
        
        if self.__audio_path != None:
            # Initialize Pygame
            pygame.mixer.init()
            # Load the audio file
            audio = pygame.mixer.Sound(self.__audio_path)
            # Play the audio file
            audio_state = audio.play()
        num = 0
        start_time = time.time()

        for I in self.__all_frames_of_video:
            if self.__video_played == False: break
            # update video progress bar
            threading.Thread (target=self.update_video_progress, args=[num], daemon=True).start()

            self.image_frames_viewer.src_base64 = I
            self.image_frames_viewer.update()

            elapsed_time = time.time() - start_time  # Calculate elapsed time
            # Calculate the desired time for the next frame update
            desired_time = (num + 1) * self.__frame_per_sleep
            
            # Calculate the remaining time to sleep
            sleep_time = max(0, desired_time - elapsed_time)
            time.sleep(sleep_time)
            # time.sleep(round(self.__frame_per_sleep, 3))
            num = num + 1
        
        if self.__audio_path != None:
            pygame.mixer.quit()

        if len(self.__all_frames_of_video) != int(self.video_frames):
            print("WARNING: Your device cant stream all video data and load it at the same time!, please set 'VideoContainer(play_after_loading=True)' to fix this issue.")
    

    def pause (self, *args):
        self.__video_played = False

    def read_the_video(self, video_path):
        # Open the video file
        video = cv2.VideoCapture(video_path)

        # Iterate over each frame and encode it
        success, frame = video.read()

        while success:
            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)

            # Base64 encode the buffer
            encoded_frame = base64.b64encode(buffer).decode('utf-8')

            # Store the base64-encoded frame in the list
            self.__all_frames_of_video.append (encoded_frame)

            # check if the image is shown
            if self.image_frames_viewer.src_base64 == None:
                self.image_frames_viewer.src_base64 = encoded_frame
                self.image_frames_viewer.visible = True
                if self.image_frames_viewer.page != None: self.image_frames_viewer.update()

            success, frame = video.read()

        # Release the video object
        video.release()

        self.__video_is_full_loaded = True
        return self.__all_frames_of_video
    
    def convert_video_to_audio(self, video_path):
        video = VideoFileClip(video_path)

        motherdir = os.path.dirname (video_path)
        basedir = os.path.basename (video_path)
        new_audio_path = os.path.join(motherdir, f"ad{basedir}.mp3")

        if os.path.isfile (new_audio_path):
            os.remove (new_audio_path)

        video.audio.write_audiofile(new_audio_path)

        return new_audio_path
    

    def get_audio_info (self, path):
        # Initialize Pygame
        pygame.mixer.init()

        # Load the audio file
        audio = pygame.mixer.Sound(path)

        # Get the duration of the audio in seconds
        self.audio_duration = audio.get_length()

        pygame.mixer.quit()
    
    def get_video_duration(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error opening video file")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        self.fps = fps

        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.video_frames = total_frames

        duration = total_frames / fps
        self.vid_duration = duration

        cap.release()
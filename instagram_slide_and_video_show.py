# Raspberry Pi Instagram Slide and Video Show version 1.2, April 9, 2020
# See https://github.com/tachyonlabs/raspberry_pi_slide_and_video_show

# Refresh Token: https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={{ _.access_token }}

from datetime import datetime
import random
import sys
import os
import json
import requests
from kivy.clock import Clock
from kivy.uix.video import Video
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.app import App
import kivy

kivy.require('1.10.0')  # replace with your current Kivy version !
# Python 3 has ConfigParser renamed to configparser for PEP 8 compliance
if sys.version_info[0] < 3:
    import ConfigParser
else:
    import configparser as ConfigParser


class SlideAndVideoShow(App):
    def __init__(self):
        super(SlideAndVideoShow, self).__init__()
        with open('INSTAGRAM_ACCESS_TOKEN.json', 'r') as access_token_file:
            access_token = json.load(access_token_file)['access_token']
            print(access_token)
        self.INSTAGRAM_ACCESS_TOKEN = access_token
        self.INSTAGRAM_REFRESHED_TOKEN = self.INSTAGRAM_ACCESS_TOKEN
        self.MOST_RECENT_PHOTOS_AND_VIDEOS_URL = "https://graph.instagram.com/me/media?fields=id,caption&access_token={}".format(self.INSTAGRAM_REFRESHED_TOKEN)
        self.LOCAL_PHOTO_AND_VIDEO_DIRECTORY_PATH = "./instagram_photos_and_videos/"
        self.INI_FILE = "./instagram_slide_and_video_show.ini"
        self.title = "Instagram Slide and Video Show"
        self.HOUR_IN_SECONDS = 60 * 60
        # default configuration settings, used to create instagram_slide_and_video_show.ini if it doesn't already exist
        self.SECONDS_BEFORE_CHANGING_PHOTO = 15
        self.PHOTO_AND_VIDEO_DISPLAY_ORDER_DIRECTORY = "directory"
        self.PHOTO_AND_VIDEO_DISPLAY_ORDER_RANDOM = "random"
        self.PHOTO_AND_VIDEO_DISPLAY_ORDER_SORTED = "sorted"
        self.PHOTO_AND_VIDEO_DISPLAY_ORDER = self.PHOTO_AND_VIDEO_DISPLAY_ORDER_RANDOM
        self.SOUND_ON = 1
        self.SOUND_OFF = 0
        self.VIDEO_VOLUME_ON_OR_OFF = self.SOUND_ON
        # get stored configuration settings
        self.get_preferences_from_ini_file()
        # download any new photos or videos
        self.download_any_new_instagram_photos_or_videos()
        # get the filenames of all newly and/or previously-downloaded photos and videos
        self.photos_and_videos = self.get_photo_and_video_filenames()
        self.current_image_index = -1

    def refreshToken(self,value=None):
        
        url = f"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={self.INSTAGRAM_REFRESHED_TOKEN}"
      
        self.INSTAGRAM_REFRESHED_TOKEN = json.loads(requests.get(url).text)['access_token']
      
        print('\n REFRESH TOKEN: ', self.INSTAGRAM_REFRESHED_TOKEN)
        
        with open('INSTAGRAM_ACCESS_TOKEN.json', 'w') as outfile:
            refresh_token =  {'access_token': self.INSTAGRAM_REFRESHED_TOKEN}
            json.dump(refresh_token, outfile)
    
    def get_preferences_from_ini_file(self):
        if os.path.isfile(self.INI_FILE):
            # if the .ini file exists, read in the configuration settings
            config = ConfigParser.RawConfigParser()
            config.read(self.INI_FILE)
            self.PHOTO_AND_VIDEO_DISPLAY_ORDER = config.get(
                "DisplaySettings", "photo_and_video_display_order")
            self.SECONDS_BEFORE_CHANGING_PHOTO = int(config.get(
                "DisplaySettings", "seconds_before_changing_photo"))
            self.VIDEO_VOLUME_ON_OR_OFF = int(config.get(
                "DisplaySettings", "video_volume_on_or_off"))
        else:
            # or if it doesn't exist, create it with the default settings
            self.create_ini_file()

    def create_ini_file(self):
        # create the ini file with the default settings the first time you run the program
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        ini_file = open(self.INI_FILE, 'w')
        config.add_section("DisplaySettings")
        config.set('DisplaySettings',
                   '; Valid display order settings are directory, random, or sorted')
        config.set("DisplaySettings", "photo_and_video_display_order",
                   self.PHOTO_AND_VIDEO_DISPLAY_ORDER)
        config.set("DisplaySettings", "seconds_before_changing_photo",
                   self.SECONDS_BEFORE_CHANGING_PHOTO)
        config.set("DisplaySettings", "video_volume_on_or_off",
                   self.VIDEO_VOLUME_ON_OR_OFF)
        config.write(ini_file)
        ini_file.close()

    def download_any_new_instagram_photos_or_videos(self, value=None):
        # create the instagram_photos_and_videos subdirectory if it doesn't already exist
        if not os.path.isdir(self.LOCAL_PHOTO_AND_VIDEO_DIRECTORY_PATH):
            os.mkdir(self.LOCAL_PHOTO_AND_VIDEO_DIRECTORY_PATH)

        print("Checking for any new Instagram photos or videos at {} ...".format(
            datetime.now()))
        internet_connection = True

        # get URLs, captions, etc. on the 20 most recent Instagram photos and videos
        try:
            json_data = json.loads(requests.get(
                self.MOST_RECENT_PHOTOS_AND_VIDEOS_URL).text)
        except:
            internet_connection = False
            print("N??o foi poss??vel acessar o Instagram... verifique sua conex??o com a Internet. Mostrando fotos e v??deos armazenados.")

        if internet_connection:
            new_photos_and_videos_downloaded = False
            print(json_data)
            json_medias = json_data["data"]
            # and check to see whether or not they have already been downloaded
            try:
                for media in json_medias:
                    media_id = media["id"]
                    GET_MEDIA_BY_ID_URL = f"https://graph.instagram.com/{media_id}?fields=id,media_type,media_url,username,timestamp&access_token={self.INSTAGRAM_REFRESHED_TOKEN}"
                    media_data = json.loads(
                        requests.get(GET_MEDIA_BY_ID_URL).text)
                    print(media_data)
                    photo_or_video_url = media_data["media_url"]
                    jpg_or_mp4_end = photo_or_video_url.index("jpg") + 3
                    photo_or_video_filename = photo_or_video_url[photo_or_video_url.rindex(
                        "/") + 1:jpg_or_mp4_end]
                    if(photo_or_video_filename.endswith(".webp?stp=dst-jpg")):
                        photo_or_video_filename = photo_or_video_filename.replace(".webp?stp=dst-jpg", ".jpg")
                    photo_or_video_file = requests.get(
                        photo_or_video_url).content
                    with open(self.LOCAL_PHOTO_AND_VIDEO_DIRECTORY_PATH + photo_or_video_filename, 'wb') as handler:
                        handler.write(photo_or_video_file)
 #                       if "videos" in photo_or_video:
 #                           photo_or_video_url = photo_or_video["videos"]["standard_resolution"]["url"]
#                            jpg_or_mp4_end = photo_or_video_url.index("mp4") + 3
#                      else:
#                            photo_or_video_url = photo_or_video["images"]["standard_resolution"]["url"]
#                            jpg_or_mp4_end = photo_or_video_url.index("jpg") + 3

                      # The URL will look like this ...
                      # https://scontent.cdninstagram.com/v/t51.2885-15/sh0.08/e35/s640x640/91944348_533445680909267_5495124442234212437_n.jpg?_nc_ht=scontent.cdninstagram.com&_nc_ohc=dpIjuIOBYTIAX8q5WiJ&oh=310b3910a2adb4ded46041e00d3c9707&oe=5EB8023F
                      # ... so for the filename to save the photo to disk as, extract the part that looks like this ...
                      # 91944348_533445680909267_5495124442234212437_n.jpg
#                        photo_or_video_filename = photo_or_video_url[photo_or_video_url.rindex("/") + 1:jpg_or_mp4_end]
#                        if not os.path.isfile(self.LOCAL_PHOTO_AND_VIDEO_DIRECTORY_PATH + photo_or_video_filename):
#                            new_photos_and_videos_downloaded = True
#                            if photo_or_video["caption"]:
 #                               print ('Downloading and saving "{}"'.format(photo_or_video["caption"]["text"].encode("utf8") if photo_or_video["caption"] else "..."))
#                          else:
 #                             print('Downloading and saving "{}"'.format(photo_or_video_filename))
   #                       photo_or_video_file = requests.get(photo_or_video_url).content
    #                        with open(self.LOCAL_PHOTO_AND_VIDEO_DIRECTORY_PATH + photo_or_video_filename, 'wb') as handler:
    #                          handler.write(photo_or_video_file)
            except:
                print("Instagram error:")

            if new_photos_and_videos_downloaded:
                # update the list of filenames in the instagram_photos_and_videos subdirectory
                self.get_photo_and_video_filenames()
            else:
                print("No new photos or videos found.")

        # check for new photos and videos once an hour
        Clock.schedule_once(
            self.download_any_new_instagram_photos_or_videos, self.HOUR_IN_SECONDS)
      
        # Get a new token once an hour 
        Clock.schedule_once(self.refreshToken, self.HOUR_IN_SECONDS+10)

    def on_position_change(self, instance, value):
        # I'm doing it this way because eos wasn't always firing at the end of a video,
        # plus position isn't updated often enough to get all the way to the duration value.
        # If the program hangs at the end of a video you may need to increase the .3 value
        # (which means .3 of a second) a little more.
        if value > self.video_duration - .3:
            self.video.state = "stop"
            self.next_photo_or_video()

    def on_duration_change(self, instance, value):
        self.video_duration = value

    def on_texture_change(self, instance, value):
        # I'm doing it this way because I couldn't get loaded or on_load to actually fire,
        # but texture has reliably only been there only after a video finishes loading.
        if self.video.texture:
            self.video.opacity = 1
            self.photo.opacity = 0

    def build(self):
        # This line is for running under Windows but crashes things on the Raspberry Pi
        # Window.fullscreen = "auto"
        Window.show_cursor = False
        Window.maximize()
        self.photo = Image()
        self.photo.allow_stretch = True
        # Without this line the Raspberry Pi starts blacking out photos after a few images.
        self.photo.nocache = True
        self.video = Video(allow_stretch=True, options={
                           'eos': 'stop', 'autoplay': True})
        self.video.bind(position=self.on_position_change,
                        duration=self.on_duration_change, texture=self.on_texture_change)
        self.video.opacity = 0
        self.video.allow_stretch = True
        self.video.nocache = True
        self.video.volume = self.VIDEO_VOLUME_ON_OR_OFF
        self.screen = FloatLayout()
        self.screen.add_widget(self.photo)
        self.screen.add_widget(self.video)
        Clock.schedule_once(self.next_photo_or_video, 1)
        return self.screen

    def next_photo_or_video(self, value=None):
        if self.PHOTO_AND_VIDEO_DISPLAY_ORDER in [self.PHOTO_AND_VIDEO_DISPLAY_ORDER_DIRECTORY, self.PHOTO_AND_VIDEO_DISPLAY_ORDER_SORTED]:
            self.current_image_index = (
                self.current_image_index + 1) % len(self.photos_and_videos)
        elif self.PHOTO_AND_VIDEO_DISPLAY_ORDER == self.PHOTO_AND_VIDEO_DISPLAY_ORDER_RANDOM:
            self.current_image_index = random.randint(
                0, len(self.photos_and_videos) - 1)

        next = self.LOCAL_PHOTO_AND_VIDEO_DIRECTORY_PATH + \
            self.photos_and_videos[self.current_image_index]
        if next.endswith(".jpg"):
            #if(next.endswith(".webp?stp=dst-jpg")):
                #next.replace(".webp?stp=dst-jpg", ".jpg")
                
            self.photo.source = next
            self.video.opacity = 0
            self.photo.opacity = 1
            Clock.schedule_once(self.next_photo_or_video,
                                self.SECONDS_BEFORE_CHANGING_PHOTO)
        else:
            self.video.source = next
            self.video.state = "play"

    def get_photo_and_video_filenames(self):
        # get all the jpg and mp4 filenames in the instagram_photos_and_videos subdirectory
        photo_and_video_filenames = [file for file in os.listdir(
            self.LOCAL_PHOTO_AND_VIDEO_DIRECTORY_PATH) if file.endswith(".jpg") or file.endswith(".mp4")]
        if self.PHOTO_AND_VIDEO_DISPLAY_ORDER == self.PHOTO_AND_VIDEO_DISPLAY_ORDER_SORTED:
            photo_and_video_filenames.sort()

        if not photo_and_video_filenames:
            # If there are no stored photos and/or videos, and the program was not able to download any,
            # you need to fix your Internet connection and/or Instagram Access Token.
            print("Nenhuma foto ou v??deo armazenado foi encontrado. Certifique-se de que voc?? est??")
            print("(1) conectado ?? internet, e ")
            print("(2) que voc?? obteve um token de acesso do Instagram para a conta do Instagram que deseja usar e o inseriu corretamente o token na vari??vel 'self.INSTAGRAM_ACCESS_TOKEN' no in??cio do c??digo,")
            print("depois disso tente de novo.")
            exit()

        return photo_and_video_filenames


if __name__ == '__main__':
    SlideAndVideoShow().run()

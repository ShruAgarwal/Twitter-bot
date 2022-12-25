# Imports --
import os
from io import BytesIO
from time import sleep
import requests
import tweepy
import cv2
from PIL import Image
from PIL import ImageFile
import numpy as np

# PIL.ImageFile.ImageFile Class Constant -- Whether or not to load truncated image files
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Loading twitter credentials
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

# Authenticate to Twitter using Tweepy
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Connect to the TWITTER API
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


# This function opens the image using PIL library & then transforms it into a pencil sketch using 'sketch' function below.
# After that, it uploads the sketch image in reply to the tweet posted earlier.
def tweet_image(image, username, status_id):
    if image.status_code == 200:
        i = Image.open(BytesIO(image.content))
        sketch(i)
        response = api.media_upload('images/sketch.jpg')
        api.update_status(status='@{0}'.format(username), in_reply_to_status_id=status_id, media_ids=[response.media_id])
    else:
        print("image app fail!")


# Below functions help transform the image into a pencil sketch using cv2 library
# The new image is being converted back into a PIL Image.
def dodge(x, y):
  return cv2.divide(x,  255 - y, scale=256)

def sketch(i):
  pil_image = i.convert('RGB')
  open_cv_image = np.array(pil_image)

  # Convert RGB to BGR
  open_cv_image = open_cv_image[:, :, ::-1].copy()
  img_gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
  img_invert = cv2.bitwise_not(img_gray)
  img_smoothing = cv2.GaussianBlur(img_invert, (21, 21), sigmaX=0, sigmaY=0)
  final_img = dodge(img_gray, img_smoothing)

  pil_image = Image.fromarray(final_img)
  return pil_image.save('images/sketch.jpg')


# BotStreamer class handles -- checking for a tweet with an image, fetching the link of image &
# applying tweet_image() function to tweet the reply with the new (sketch) image.
class BotStreamer(tweepy.StreamListener):

  # Called when a new status arrives which is passed down from the on_data method of the StreamListener
  def on_status(self, status):
    username = status.user.screen_name
    status_id = status.id

    # Checks if there is any media-entity
    for media in status.entities.get("media",[{}]):
        try:
            # Checks if the entity is of the type "photo"
            if media.get("type",None) == "photo":
                image_content=requests.get(media["media_url"], stream=True)

            tweet_image(image_content, username, status_id)
            sleep(30) #3600 secs --> 1 hour to match the github action
        except tweepy.TweepError as e:
            print(e.reason)
        except StopIteration:
            break


# Creating Stream object
myStreamListener = BotStreamer()
stream = tweepy.Stream(api.auth, myStreamListener)

# Filters real-time tweets which uses '#PicSketch' keyword
stream.filter(track=["PicSketch"])

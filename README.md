# USound Downloader
You ever wanted to download some audio from YouTube for whatever reason? A funny sound that came from a human's mouth, a funny sound that came from an animal's mouth, words of wisdom, words of absolute absurdity, etc. Well with this program, you just have to give it a few parameters and it'll do the rest. Now it's not the prettiest, but it is quite functional.

**Now can download video clips!!!** This software now brings you the ability to download the video *instead* of the audio as either an MP4 or as a GIF!

## How to use
Below is what the GUI looks like:

<p align="center">
  <img width=400 src="https://github.com/crumpstrr33/usound_dloader/blob/master/pics/gui.png">
</p>

* **Download Option**: Can choose between audio (which is saved an an MP4), video (also saved as a MP4) or a GIF. If choosing a GIF, the option for the size of the GIF appears right underneath for the length of video in pixels.
* **Start Time**: The time in the video at which to start the audio file. Works down to the millisecond and anything left blank will be interpreted as a 0, e.g. starting at 5 minutes and 3.7 seconds is `5:3.7` which is interpreted as `00:05:03.700`.
* **Total Time**: The total length of the audio file. Formating rules are idential to **start time**.
* **Link**: The unique identifier part of a YouTube video URL, usually a string of random alphanumeric characters.
* **Save Directory**: The directory to which to save everything. When the `APPLY` button is pressed, the audio file is created along with a text file containing the following information:
    1) Link to the time at which the audio clip starts
    2) The name of the channel hosting the video
    3) The title of the video
    4) The start time of the video
    5) The total length of the video
    6) The first command ran; it uses `youtube-dl` to obtain the URL used to directly download the audio
    7) The second command ran; it uses `ffmpeg` to actually download the audio
* **Overwrite Directory**: This checkbox will, if checked, allow the program to overwrite a directory with the same name as **File Name** if it already exists. This is useful if you need to refine the exact time of the audio clip and thus are redownloading multiple times.
* **File Name**: The name of the directory, `.mp4` and `.txt` file. For example, if we choose `funny_joke`, then the program will create a directory called `funny_joke` in which there is `funny_joke.mp4` that is the requested audio clip and `funny_joke.txt` which is the text file described above.
* **Metadata**: Optional metadata to add to the mp4 clip.

After pressing `APPLY`, the thumbnail of the video will appear in the lower right box and the download will proceed. Yeah, it's messy but I never said I was good with PyQt

## How to Install
1) Clone repo:
```
git clone https://github.com/crumpstrr33/usound_dloader.git
```
2) cd into repo and download dependencies (I haven't tested running this but I don't see why it shouldn't work, let me know if it doesn't):
```
pip install -r requirements.txt
```
2) Install `ffmpeg`. If you are on Windows, check out [here](https://video.stackexchange.com/questions/20495/how-do-i-set-up-and-use-ffmpeg-in-windows/28321), they offer a couple of good solutions. Copied from the main `.py` file: "A good, simple test is running `os.system('where ffmpeg')` to see if python can find it."

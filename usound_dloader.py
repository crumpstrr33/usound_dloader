"""
Things that are important:
1) You need youtube-dl which you can get just with `pip install youtube-dl`
2) You need ffmpeg. I used chocolatey via the instructions
                https://video.stackexchange.com/a/28321
   since it takes care of the pathing issues automatically. From my testing,
   ffmpeg.exe's directory doesn't need to be in PYTHONPATH and so chocolatey
   should take care of it. Make sure the env you're working in, e.g. ipython,
   jupyter notebook is restarted afterwards to update the change in the env
   variables. A good, simple test is running `os.system('where ffmpeg')` to
   see if python can find it.
3) That commented-out mess below is if instead of have `start` and `length`,
   there is `start` and `end` and it calculates `length` (since ffmpeg uses
   length). It's messy and overly pythonic. I leave it commented out because
   it's messy but I keep it cause it's so pythonic.
"""
import subprocess
import os
import sys
from itertools import chain
import urllib.request
import shlex
import tempfile
from shutil import rmtree

from bs4 import BeautifulSoup
import requests

from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QGridLayout, QLineEdit, QLabel, QFrame, QPushButton, QFileDialog, QComboBox,
    QSizePolicy, QWidget, QLayout, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QPixmap, QPainter


# def _time_diff(start, end):
#     """
#     Using the format HH:MM:SS.mmm, this is find the time difference between
#     two different time via using datetime.
#
#     end - The time at which the audio to be downloaded ends. Is also formatted
#           by HH:MM:SS.mmm
#     """
#     startdt = dt.strptime(','.join(map(lambda x: '0' + x
#         if len(x.split('.')[0]) < 2 else x, start.split(':'))), '%H,%M,%S.%f')
#     enddt = dt.strptime(','.join(map(lambda x: '0' + x
#         if len(x.split('.')[0]) < 2 else x, end.split(':'))), '%H,%M,%S.%f')

#     return str(enddt - startdt)


class Window(QWidget):
    WIDTH, HEIGHT = 500, 500
    INPUT_COLOR = 'color: DarkSlateGrey;'
    TITLE_FONT = 15
    METADATA = ['Album', 'Artist', 'Title']
    FTYPE = '.mp4'

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.metadata = {}
        self.setWindowTitle('USound Downloader')

        input_frame = self._build_input_box()
        save_frame = self._build_save_directory()
        info_frame = self._build_save_info()
        apply_button = self._build_apply_button()
        thumbnail = self._build_thumbnail_display()

        master_layout = QGridLayout()
        master_layout.SetNoConstraint
        master_layout.setContentsMargins(15, 15, 15, 15)
        master_layout.addWidget(input_frame, 1, 0, 3, 6)
        master_layout.addWidget(save_frame, 4, 0, 1.5, 6)
        master_layout.addWidget(info_frame, 5.5, 0, 2.5, 6)
        master_layout.addWidget(apply_button, 8, 0, 2, 2)
        master_layout.addWidget(thumbnail, 8, 2, 2, 4)

        self.setLayout(master_layout)
        self.setGeometry(300, 200, self.WIDTH, self.HEIGHT)

    def _build_input_box(self):
        # Make the title of this part of the GUI *pretty*
        title = QLabel('Inputs')
        title_font = QFont('Serif', self.TITLE_FONT)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet('padding-bottom: 10px;')

        # Input for when the audio starts
        self.start_time_input = [
            QLineEdit(placeholderText='HH', maxLength=2, alignment=Qt.AlignCenter),
            QLineEdit(placeholderText='MM', maxLength=2, alignment=Qt.AlignCenter),
            QLineEdit(placeholderText='SS', maxLength=2, alignment=Qt.AlignCenter),
            QLineEdit(placeholderText='mmm', maxLength=3, alignment=Qt.AlignCenter)]
        # Input for how long the audio goes for
        self.time_length_input = [
            QLineEdit(placeholderText='HH', maxLength=2, alignment=Qt.AlignCenter),
            QLineEdit(placeholderText='MM', maxLength=2, alignment=Qt.AlignCenter),
            QLineEdit(placeholderText='SS', maxLength=2, alignment=Qt.AlignCenter),
            QLineEdit(placeholderText='mmm', maxLength=3, alignment=Qt.AlignCenter)]
        # URL of YouTube video
        self.youtube_url = QLineEdit()
        self.youtube_url.setStyleSheet(self.INPUT_COLOR)
        wwwutube = QLabel('youtube.com/watch?v=')
        wwwutube.setStyleSheet(self.INPUT_COLOR)

        # Stack the inputs vertically
        input_v_box = QVBoxLayout()
        input_v_box.addWidget(title)
        input_v_box.addLayout(self._make_time_layout(self.start_time_input, 'Start Time'))
        input_v_box.addLayout(self._make_time_layout(self.time_length_input, 'Total Time'))
        input_v_box.addSpacing(20)
        input_v_box.addLayout(self._make_h_layout([QLabel('Link: '),
            wwwutube, self.youtube_url]))
        input_v_box.addStretch()

        # Wrap layout in frame so to border it
        return self._format_frame(input_v_box)

    def _make_time_layout(self, input_list, title):
        """
        Combines LineEdits and Labels such that it builds:
            `title`: `[0]:[1]:[2].[3]`
        where [n] is the nth element of `input_list` and it returns the layout.
        """
        labels = [QLabel(title), QLabel(':'), QLabel(':'), QLabel('.')]

        # Set the width of each Line Edit and color
        [ele.setFixedWidth(30) for ele in input_list]
        [ele.setStyleSheet(self.INPUT_COLOR) for ele in input_list]
        input_list[-1].setFixedWidth(45)

        # Merges the two lists (of Labels and LineEdits) together into pairs
        # (with zip), then flattens it into a 1D list (with chain) to then
        # pass to make the horizontal layout
        input_layout = self._make_h_layout(chain(*zip(labels, input_list)), True)
        input_layout.addStretch()

        return input_layout

    def _build_save_directory(self):
        # Title this part too
        title = QLabel('Save Directory')
        title_font = QFont('Serif', self.TITLE_FONT)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet('padding-bottom: 10px;')

        # Add checkbox for overwriting existing directory
        self.overwrite = QCheckBox()
        overwrite_font = QFont('Ariel', 8)
        overwrite_label = QLabel('Overwrite Directory')
        overwrite_label.setFont(overwrite_font)
        overwrite_layout = QHBoxLayout()
        overwrite_layout.addWidget(overwrite_label)
        overwrite_layout.addWidget(self.overwrite)
    
        # LineEdit to input path to save directory or browse for it
        self.save_dir = QLineEdit()
        self.save_dir.setStyleSheet(self.INPUT_COLOR)
        search_dirs = QPushButton('...')
        search_dirs.setFixedWidth(25)
        search_dirs.clicked.connect(self.open_filedialog)

        # Put it all together in a grid (r, c, rspan, cspan)
        save_g_layout = QGridLayout()
        save_g_layout.addWidget(title, 0, 0, 1, 4)
        # save_g_layout.addWidget(self.overwrite, 0, 4, 1, 1)
        save_g_layout.addLayout(overwrite_layout, 0, 4, 1, 2)
        save_g_layout.addWidget(search_dirs, 1, 0, 1, 1)
        save_g_layout.addWidget(self.save_dir, 1, 1, 1, 5)

        return self._format_frame(save_g_layout)

    @pyqtSlot()
    def open_filedialog(self):
        """
        Opens the browsing window for choosing a save directory
        """
        save_dir = QFileDialog.getExistingDirectory()
        self.save_dir.setText(save_dir)

    def _build_save_info(self):
        # Once again, make a neat title
        title = QLabel('MP3 Information')
        title_font = QFont('Serif', self.TITLE_FONT)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet('padding-bottom: 10px;')

        # Necessary info, name of the file itself
        self.file_name = QLineEdit()
        self.file_name.setStyleSheet(self.INPUT_COLOR)
        file_name_layout = QHBoxLayout()
        file_name_layout.addWidget(QLabel('File Name:'))
        file_name_layout.addWidget(self.file_name)

        # Can choose from the list of self.METADATA of different types of
        # metadata to add to the MP3
        self.metadata_choices = QComboBox()
        self.metadata_choices.addItems(self.METADATA)
        self.metadata_choices.currentIndexChanged.connect(
            lambda: self.add_metadata(self.metadata_choices.currentText())
        )
        meta_data_choices_layout = QHBoxLayout()
        meta_data_choices_layout.addWidget(QLabel('Metadata:'))
        meta_data_choices_layout.addWidget(self.metadata_choices)

        # Stack it all vertically
        self.save_v_layout = QVBoxLayout()
        self.save_v_layout.addWidget(title)
        self.save_v_layout.addLayout(file_name_layout)
        self.save_v_layout.addLayout(meta_data_choices_layout)

        return self._format_frame(self.save_v_layout)

    @pyqtSlot()
    def add_metadata(self, md_name):
        """
        Adds a label and LineEdit for the specific metadata defined by
        `md_name` which is saved in the dict self.metadata and an 'X' button
        for removing the line.
        """
        if md_name not in self.metadata.keys():
            self.remove_md = QPushButton('X')
            self.remove_md.setFixedSize(17, 17)

            md_input = QLineEdit()
            md_input.setStyleSheet(self.INPUT_COLOR)

            # Make each line of metadata info and save it
            self.metadata[md_name] = self._make_h_layout(
                [QLabel('{}: '.format(md_name)), md_input, self.remove_md])
            # Remove the line if the 'X' is pushed
            self.remove_md.clicked.connect(lambda: self.remove_md_input(md_name))

            self.save_v_layout.addLayout(self.metadata[md_name])

    @pyqtSlot()
    def remove_md_input(self, md_name):
        """
        Removes/deletes the widgets that are children the layout associated
        with `md_name`. And deletes the dict entry for it.
        """
        for ind in range(self.metadata[md_name].count()):
            self.metadata[md_name].itemAt(ind).widget().deleteLater()
        self.metadata.pop(md_name)
        # self.setGeometry(400, 500, self.WIDTH, 800)

    def _build_apply_button(self):
        # Make a big ol' button!
        self.apply = QPushButton('APPLY')
        self.apply.setFixedWidth(3*self.WIDTH/12)
        self.apply.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.apply.clicked.connect(self.download_audio)

        return self.apply

    @pyqtSlot()
    def download_audio(self):
        """
        Puts all the data entered into the proper format for get_audio_segment.
        """
        vurl = 'https://www.youtube.com/watch?v=' + self.youtube_url.text()

        # Put the times in format 'HH:MM:SS.mmm'
        time_dlims = [':', ':', '.', '']
        # These just buffer the milliseconds so it's three digits total
        self.start_time_input[3].setText(self.start_time_input[3].text().ljust(3, '0'))
        self.time_length_input[3].setText(self.time_length_input[3].text().ljust(3, '0'))
        # Here the two lists are zipped and joined, the zfill buffers a zero
        # on the left as that is the proper format
        start = ''.join(chain(*zip(map(lambda x: x.text().zfill(2),
            self.start_time_input), time_dlims)))
        length = ''.join(chain(*zip(map(lambda x: x.text().zfill(2),
            self.time_length_input), time_dlims)))

        # Get the info for the metadata as text
        metadata = {k: v.itemAt(1).widget().text() for k, v in self.metadata.items()}

        print('Grabbing audio from {} at {} for a time of {}.'.format(
            vurl, start, length))
        print('Saving to {save}/{fname}/{fname}{ftype} with metadata:\n\n{md}'.format(
            save=self.save_dir.text(), fname=self.file_name.text(),
            ftype=self.FTYPE, md=metadata))

        # Grab video thumbnail to display it in the GUI
        thumbnail_url = 'http://img.youtube.com/vi/{}/0.jpg'.format(self.youtube_url.text())
        # Download it into the temp folder
        tn_path = os.path.join(tempfile.gettempdir(), self.youtube_url.text() + '.jpg')
        urllib.request.urlretrieve(thumbnail_url, tn_path)
        # Display the thumbnail
        thumbnail = QPixmap(tn_path)
        thumbnail = thumbnail.scaled(2*self.WIDTH/3, 2*self.HEIGHT/3, Qt.KeepAspectRatio)
        self.thumbnail_display.setPixmap(thumbnail)

        self.get_audio_segment(vurl, self.save_dir.text(), start, length,
            self.file_name.text(), metadata)

    def _build_thumbnail_display(self):
        self.thumbnail_display = QLabel()
        # thumbnail = QPixmap()
        # thumbnail = thumbnail.scaled(2*self.WIDTH/3, 2*self.HEIGHT/3, Qt.KeepAspectRatio)      

        # self.thumbnail_display.setPixmap(thumbnail)

        return self._format_frame(self.thumbnail_display)

    @staticmethod
    def _make_h_layout(widgets, stretch=False):
        """
        A method of convenience to place widgets horizontally.
        """
        hlayout = QHBoxLayout()
        for widget in widgets:
            hlayout.addWidget(widget)
        if stretch:
            hlayout.addStretch()
        return hlayout

    @staticmethod
    def _format_frame(obj):
        """
        Formats the frame that surrounds each layout/section of the GUI
        """
        frame = QFrame()
        if isinstance(obj, QLayout):
            frame.setLayout(obj)
        elif isinstance(obj, QWidget):
            # Use a wrapper to add a widget alone into a frame
            layout_wrapper = QVBoxLayout()
            layout_wrapper.addWidget(obj)
            frame.setLayout(layout_wrapper)
        frame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        frame.setLineWidth(2)
        frame.setMidLineWidth(0)
        return frame

    def get_audio_segment(self, vurl, save, start, length, file_name='',
        metadata={}, ftype='.mp4'):
        """
        Downloads the audio from part of a youtube video.

        Parameters:
        vurl - The URL of the video to download
        save - The directory in which to save the audio
        start - The time at which the audio to be downloaded starts. Is formatted
                by HH:MM:SS.mmm
        length - The length of the audio to record. Is also formatted by
                HH:MM:SS.mmm
        file_name (default '') - Name of the saved audio file. If nothing is given,
                                the name of the YouTube video is used
        metadata (default {}) - The metadata to add to the file formatted as
                                a dictionary
        ftype (default '.mp4') - The file type to save the audio as
        """
        # Make directory to save audio and txt info to
        fname = file_name if file_name else data[0]
        abs_path = os.path.join(save, fname)

        # Remove directory if it already exists
        try:
            if os.path.exists(abs_path):
                if self.overwrite.isChecked():
                    rmtree(abs_path)
                else:
                    print("Directory '{}' already exists and 'Overwrite" +
                        " Directory' checkbox is not checked.".format(abs_path))
                    return
            os.makedirs(abs_path)
        except PermissionError:
            print('\nFile is open in another program. Close that then try again.')

        # -g = --get-url, grabs the URLs of the video/audio files
        # -e = --get-title gets the title to name the video if no name was given
        cmd1 = 'youtube-dl -eg {vurl}'.format(vurl=vurl)
        data = subprocess.check_output(cmd1).decode('utf-8').split('\n')
        print('Grabbed meta data for video: {}...\n\n'.format(data[0]))

        # URL for the audio stream
        url = data[-2]
        # Absolute file path that audio will be saved to
        save = os.path.join(abs_path, fname + ftype)

        # Puts the metadata in the correct format as arguments
        md_arg = ''
        if metadata:
            md_arg = '-metadata ' + ' -metadata '.join(map('='.join, metadata.items()))

        # Builds the command to run, shlex.quote keeps the directory from having
        # its slashes all fussed with, i.e. keeps it literal
        cmd2 = 'ffmpeg -ss {start} -i {url} -t {length} {metadata} {save}'.format(
            start=start, url=url, length=length, metadata=md_arg, save=shlex.quote(save))
        # Split the command appropriately into a list to run via subprocess
        subprocess.run(shlex.split(cmd2))

        # Finds the total time in seconds of `start` and rounds down by multiplying
        # hours by 60^2, minutes by 60^1 and seconds by 60^0 and summing them.
        time_in_seconds = sum([int(float(x))*60**(len(start.split(':')) - 1 - ind)
                for ind, x in enumerate(start.split(':'))])
        # Possible important info saved in a .txt file
        txt_info = {'Link': vurl + '&t=' + str(time_in_seconds),
            **self._get_channel_info(vurl), 'Start': start,
            'Length': length, 'Command1': cmd1,'Command2': cmd2}
        with open(os.path.join(abs_path, fname + '.txt'), 'w') as f:
            for line in map(': '.join, txt_info.items()):
                f.write(line + '\n')

        print('\n\nRunning command:', cmd2)
        print('\n\nFinished downloading and saved audio to: {}'.format(save))

    @staticmethod
    def _get_channel_info(vurl):
        try:
            # Returns the name of the channel and title of the video for the URL `vurl`
            soup = BeautifulSoup(requests.get(vurl).content, 'html.parser')
            return {'Channel': soup.find('div', attrs={'class': 'yt-user-info'}).find('a').text,
                'Title': soup.find('span', attrs={'class': 'watch-title'}).text.strip()}
        except AttributeError: 
            # Download restarted before writing txt file was done. I think...
            return {}

def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())


if __name__=="__main__":
    main()

import tkinter
import os
import sys
import PySimpleGUI as sg
import pytube
import requests
import urllib3
from pytube import YouTube, request
from PIL import Image
from io import BytesIO

from tkinter import Frame, Tk, Label, Entry, Button, messagebox

ROOT_DIR = os.path.dirname(os.path.abspath("README.md"))

WELCOME_TEXT = """
Welcome to YoutPy!\nEnter the youtube video link below.
"""

TITLE_FONT = ("Verdana", "15", "bold")
WELCOME_FONT = ("Roboto", "11")
VID_INFO_FONT = ("Roboto", "11")


class YoutubeVid:
    def __init__(self, vid):
        self.author = vid.author
        self.date = vid.publish_date
        self.rating = vid.rating
        self.views = vid.views
        self.title = vid.title
        self.thumb = vid.thumbnail_url
        self.streams = vid.streams.filter(progressive=True).desc()


def convertToPng(im):
    with BytesIO() as f:
        im.save(f, format="PNG")
        return f.getvalue()


def video_frame(vid):
    sg.theme("Reddit")
    url = vid.thumb
    img = Image.open(requests.get(url, stream=True).raw).resize((384, 216))
    thumbnail = convertToPng(img)

    title = [sg.Text(vid.title.title(), font=TITLE_FONT)]
    thumb = [[sg.Frame(layout=[[sg.Image(data=thumbnail)]], title="")]]

    video_info = sg.Frame(
        layout=[
            [sg.Text("Channel:", size=(8, 1)), sg.Input(vid.author, readonly=True)],
            [sg.Text("Date:", size=(8, 1)), sg.Input(vid.date.strftime("%B %d, %Y"), readonly=True)],
            [sg.Text("Views:", size=(8, 1)), sg.Input(vid.views, readonly=True)],
            [sg.Text("Rating:", size=(8, 1)), sg.Input(vid.rating, readonly=True)],
        ],
        title="",
        element_justification="left",
    )

    download = sg.Frame(
        layout=[
            [
                sg.Text("Output Path:", size=(12, 1)),
                sg.Input(default_text=os.path.join(ROOT_DIR, "videos"), key="path"),
                sg.FolderBrowse(target="path"),
            ],
            [sg.Combo(vid.streams.all(), default_value=vid.streams.first(), enable_events=True, key="resolution")],
            [
                sg.Text("Filesize:", size=(12, 1)),
                # sg.Input(f"{vid.streams.get_highest_resolution().filesize * 10 ** -6:.2f} MB", readonly=True),
                sg.Input(f"{vid.streams.first().filesize * 10 ** -6:.2f} MB", readonly=True, key="file_size"),
            ],
            [sg.Button("Cancel"), sg.Button("Download")],
        ],
        title="",
    )

    layout = [[title], [thumb], [video_info], [download]]
    window = sg.Window(
        "YoutPy",
        layout,
        font=VID_INFO_FONT,
        element_justification="center",
        auto_size_text=True,
        auto_size_buttons=True,
    )

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == "Cancel":
            break

        if event == "resolution":
            window["file_size"].update(value=f"{values['resolution'].filesize * 10 ** -6:.2f} MB")

        if event == "Download":
            # stream = vid.streams.get_highest_resolution()
            stream = values["resolution"]
            filesize = stream.filesize
            save_path = os.path.join(values["path"], stream.default_filename)

            download_layout = [
                [sg.Text("Downloading...")],
                [
                    sg.ProgressBar(100, orientation="h", size=(20, 20), key="progressbar"),
                    sg.Text(f"{0:.2f}", size=(6, 1), key="progresstext", justification="right"),
                ],
                [
                    sg.Text(f"{0:.2f} MB/", size=(8, 1), justification="right", key="remaining"),
                    sg.Text(f"{filesize * 10 ** -6:.2f} MB", justification="right"),
                ],
                [sg.Cancel()],
            ]
            download_bar_window = sg.Window("Downloading Status", download_layout)
            progress_bar = download_bar_window["progressbar"]
            progress_text = download_bar_window["progresstext"]
            remaining = download_bar_window["remaining"]

            with open(save_path, "wb") as f:
                is_paused = is_cancelled = False
                stream = request.stream(stream.url)
                downloaded = 0

                while True:
                    if is_cancelled:
                        break
                    if is_paused:
                        continue

                    chunk = next(stream, None)
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        event, values = download_bar_window(timeout=10)

                        if event == "Cancel" or event == sg.WINDOW_CLOSED:
                            sg.popup_auto_close(
                                "Download Cancelado!",
                                title="CANCEL",
                            )
                            break

                        progress_bar.update(current_count=(downloaded * 100 / filesize), max=100)
                        progress_text.update(value=f"{(downloaded * 100 / filesize):.2f}%")
                        remaining.update(value=f"{downloaded * 10 ** -6:.2f} MB/")

                    else:
                        sg.popup_auto_close(
                            "Download Completed!",
                            title="SUCCESS",
                        )
                        break
            download_bar_window.close()

    window.close()


def main_frame():
    sg.theme("Reddit")

    layout = [
        [
            sg.Image("misc/youtube_logo.png"),
        ],
        [sg.Text(WELCOME_TEXT, font=TITLE_FONT, justification="center")],
        [sg.Text("URL"), sg.InputText(default_text="https://www.youtube.com/watch?v=j5rK5oTA2dU")],
        [sg.Button("Search")],
    ]

    window = sg.Window("YoutPy", layout, font=WELCOME_FONT, element_justification="c")

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        if event == "Search":
            vid = YoutubeVid(YouTube(values[1]))
            video_frame(vid)

    window.close()


main_frame()
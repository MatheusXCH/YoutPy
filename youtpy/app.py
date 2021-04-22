import os
import sys

import PySimpleGUI as sg
import pytube
from pytube import YouTube, request


from youtubevid import YoutubeVid

ROOT_DIR = os.path.dirname(os.path.abspath("README.md"))

# # Fonts:
TITLE_FONT = ("Verdana", "14", "bold")
SUBTITLE_FONT = ("Verdana", "11", "bold")
URL_FONT = ("Verdana", "11", "bold", "italic")
VID_INFO_FONT = ("Roboto", "11")


def show_main():
    sg.theme("Reddit")

    layout = [
        [sg.Image("misc/youtpy-logo.png")],
        [sg.Text("Welcome to YoutPy!", font=TITLE_FONT, justification="center")],
        [sg.Text("Enter the youtube video link below", font=SUBTITLE_FONT, justification="center")],
        [sg.Text("URL:", font=URL_FONT), sg.InputText(default_text="https://www.youtube.com/watch?v=dQw4w9WgXcQ")],
        [sg.Button("Search")],
    ]

    window = sg.Window("YoutPy", layout, font=VID_INFO_FONT, element_justification="c")

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        if event == "Search":
            vid = YoutubeVid(YouTube(values[1], on_progress_callback=None))
            show_video_info(vid)

    window.close()


def show_video_info(vid):
    sg.theme("Reddit")

    title_frame = [sg.Text(vid.title.title(), font=TITLE_FONT)]  # 1st  row
    thumb_frame = [[sg.Frame(layout=[[sg.Image(data=vid.thumb)]], title="")]]  # 2nd row

    info_frame = sg.Frame(
        layout=[
            # 3rd row
            [
                sg.Text("Channel:", size=(8, 1), justification="right"),
                sg.Input(vid.author, size=(16, 1), readonly=True),
                sg.Text("Duration:", size=(8, 1), justification="right"),
                sg.Input(
                    f"{int(vid.length / 3600):02d}:{int((vid.length % 3600) / 60):02d}:{int(vid.length % 60 + 1):02d}",
                    size=(16, 1),
                    readonly=True,
                ),
            ],
            # 4th row
            [
                sg.Text("Views:", size=(8, 1), justification="right"),
                sg.Input(vid.views, size=(16, 1), readonly=True),
                sg.Text("Date:", size=(8, 1), justification="right"),
                sg.Input(vid.date.strftime("%B %d, %Y"), size=(16, 1), readonly=True),
            ],
        ],
        title="",
        element_justification="left",
        font=VID_INFO_FONT,
    )

    resolutions = [stream.resolution for stream in vid.streams]
    download_frame = sg.Frame(
        layout=[
            [
                sg.Text("Output Path:", size=(10, 1)),
                sg.Input(default_text=os.path.join(ROOT_DIR, "videos"), key="path"),
                sg.FolderBrowse(target="path"),
            ],
            [
                sg.Text("Filesize:", size=(10, 1), justification="right"),
                sg.Input(
                    f"{vid.streams.first().filesize * 10 ** -6:.2f} MB", size=(12, 1), readonly=True, key="file_size"
                ),
                sg.Combo(
                    resolutions,
                    default_value=vid.streams.first().resolution,
                    enable_events=True,
                    readonly=True,
                    auto_size_text=True,
                    key="resolution",
                ),
            ],
            [sg.Button("Cancel"), sg.Button("Download")],
        ],
        title="",
        element_justification="left",
        font=VID_INFO_FONT,
    )

    layout = [[title_frame], [thumb_frame], [info_frame], [download_frame]]

    video_info_window = sg.Window(
        "YoutPy",
        layout,
        font=VID_INFO_FONT,
        element_justification="center",
        auto_size_text=True,
        auto_size_buttons=True,
    )

    while True:
        event, values = video_info_window.read()

        if event == sg.WIN_CLOSED or event == "Cancel":
            break

        if event == "resolution":
            video_info_window["file_size"].update(
                value=f"{vid.streams.get_by_resolution(values['resolution']).filesize * 10 ** -6:.2f} MB"
            )

        if event == "Download":
            show_download(vid, values)
            break

    video_info_window.close()


def show_download(vid, values):
    stream = vid.streams.get_by_resolution(values["resolution"])
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
    remaining_text = download_bar_window["remaining"]

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

                event, values = download_bar_window.read(timeout=10)

                if event == "Cancel" or event == sg.WINDOW_CLOSED:
                    sg.popup_auto_close(
                        "Download Cancelado!",
                        title="CANCEL",
                    )
                    break

                progress_bar.update(current_count=(downloaded * 100 / filesize), max=100)
                progress_text.update(value=f"{(downloaded * 100 / filesize):.2f}%")
                remaining_text.update(value=f"{downloaded * 10 ** -6:.2f} MB/")

            else:
                sg.popup_auto_close(
                    "Download Completed!",
                    title="SUCCESS",
                )
                break

    download_bar_window.close()


if __name__ == "__main__":
    show_main()

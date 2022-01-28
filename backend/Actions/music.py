import vlc
import pafy

def search_for_song():
    song_name = "Hall of Fame"

if __name__ == "__main__":
    url = "https://www.youtube.com/results?search_query=hall+of+fame"
    video = pafy.new(url)
    best = video.getbest()
    media = vlc.MediaPlayer(best.url)
    media.play()

    input_str_1 = "Open Google Chrome"
    input_str_2 = "Open Youtube"
    input_str_3 = "Open Notepad"

    url = 'youtube.com'

    command = \
        winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "ChromeHTML\\shell\open\\command", 0, winreg.KEY_READ),
                            "")[0]
    chrome_path = re.search("\"(.*?)\"", command).group(1)

    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(str(chrome_path)))


    def open_url(value):
        webbrowser.get('chrome').open_new_tab(value)


    open_url('youtube.com')
    open_url('mail.google.com')

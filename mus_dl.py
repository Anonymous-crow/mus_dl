#!/usr/bin/env python3
import os, yt_dlp, logging, get_cover_art, json, taglib, time, click

def install_ffmpeg(overwrite=False):
    if os.name == 'nt':
        if not os.path.isfile('ffmpeg.exe') or overwrite:
            if not os.path.isdir(os.path.join("resources","ffmpeg","release-full")): os.makedirs(os.path.join("resources","ffmpeg","release-full"))
            resp = requests.get('https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z', allow_redirects=True)
            with open(os.path.join('resources','ffmpeg','ffmpeg-release-full.7z'), "wb") as f:
                f.write(resp.content)
            # os.system('7za x '+os.path.join('resources','ffmpeg','ffmpeg-release-full.7z')+' -o'+os.path.join('resources','ffmpeg'))
            import py7zr
            with py7zr.SevenZipFile(os.path.join('resources','ffmpeg', 'ffmpeg-release-full.7z'), mode='r') as sz:
                sz.extractall(path=os.path.join("resources","ffmpeg","release-full"))
            shutil.copyfile(os.path.join("resources","ffmpeg","release-full","bin","ffmpeg.exe"), 'ffmpeg.exe')
            self.log.debug('copied ffmpeg.exe')
    




class MusicGetter():
    """docstring for MusicGetter."""

    def __init__(self):
        self.log = logging.getLogger('MusicGetter')
        self.log.setLevel(logging.DEBUG)
        if not self.log.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
            ch.setFormatter(formatter)
            self.log.addHandler(ch)

    def dl_file(self, url, filename='', path='', return_content=False):
        import requests
        headers = requests.utils.default_headers()
        x = requests.get(url, headers=headers, allow_redirects=True)
        if filename =='':
            filename = url.split('/')[-1]
        if path=='':
            with open(filename, 'wb') as file:
                file.write(x.content); file.close()
        else:
            if not os.path.isdir(path): os.makedirs(path)
            with open(os.path.join(path,filename), 'wb') as file:
                file.write(x.content); file.close()
        if return_content:
            return x.content

    def dump_json(self, data, filename, path = ""):
        if path != "":
            if not os.path.isdir(path):
                os.makedirs(path)
        with open(os.path.join(path, filename), 'w') as file:
            json.dump(data, file, indent=4, separators=(',', ': '))

    def infoget(self, url : str, opts : dict = {}):
        ydl_opts = {
            'skip_download': True,
            'simulate': True,
            'ignoreerrors': True,
            'clean_infojson': False
        }
        ydl_opts.update(opts)
        self.log.debug(ydl_opts)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.sanitize_info(ydl.extract_info(url, download=False))
        self.log.debug(json.dumps(info_dict, indent=4, separators=(',', ': ')))
        return info_dict

    def album_art_folder(self, path, force=True, no_embed=False):
        coverdict={'inline':True, 'verbose':True}
        if force:
            coverdict['force']=True
        if no_embed:
            coverdict['no_embed']=True
        finder = get_cover_art.CoverFinder(coverdict)
        finder.scan_folder(path)

    def yt_mp3(self, url, path='downloads', format='mp3'):
        install_ffmpeg()
        info_dict = self.infoget(url, opts = {'noplaylist': True})
        video_title = info_dict['title'].replace(':', ' -').replace('"', '\'').replace("'", "\'").replace('|', '_').translate({ord(i): ' ' for i in "<>:\"/\\|?*"})
        filename = video_title + "." + format
        if format=='mp3':
            if not os.path.isdir(path): os.makedirs(path)
            if not os.path.isfile(os.path.join(path, filename)):
                ydl_opts = {
                    'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
                    'format': 'bestaudio/best',
                    'ignoreerrors': True,
                    'clean_infojson': False,
                    'noplaylist': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            #clear()
            filepath = os.path.join(path, filename)
            try:
                metadata = {'artist': info_dict["artist"], 'album': info_dict["album"], 'track': info_dict["track"], 'album_artist': info_dict['creator']}
            except:
                metadata = None

            try:
                song = taglib.File(filepath)
            except:
                self.log.error(F"could not open {filepath} to write metadata")
                return 1
            self.log.debug(json.dumps(song.tags, indent=4, separators=(',', ': ')))
            if metadata != None:
                # audiofile.tag.release_date = i["release_year"]
                if not song.tags.get("ARTIST"):
                    self.log.debug(F"REPLACING ARTIST IN { filepath }!! { song.tags.get('ARTIST') } TO { [metadata['artist']] }")
                    song.tags["ARTIST"] = [metadata["artist"]]
                if not song.tags.get("ALBUM"):
                    self.log.debug(F"REPLACING ALBUM IN { filepath }!! {song.tags.get('ALBUM')} TO {[metadata['album']]}")
                    song.tags["ALBUM"] = [metadata["album"]]
                if not song.tags.get("ALBUMARTIST"):
                    self.log.debug(F"REPLACING ALBUMARTIST IN { filepath }!! {song.tags.get('ALBUMARTIST')} TO {[metadata['artist']]}")
                    song.tags["ALBUMARTIST"] = [metadata["artist"]]
                if not song.tags.get("TITLE"):
                    self.log.debug(F"REPLACING TITLE IN { filepath }!! {song.tags.get('TITLE')} TO {[metadata['track']]}")
                    song.tags["TITLE"] = [metadata["track"]]
                if not song.tags.get("DATE") and info_dict.get("release_year"):
                    self.log.debug(F"REPLACING DATE IN { filepath }!! {song.tags.get('DATE')} TO { [ str( info_dict['release_year'] ) ] }")
                    song.tags["DATE"] = [str(info_dict["release_year"])]
            else:
                if not song.tags.get("TITLE"):
                    self.log.debug(F"REPLACING TITLE IN { filepath }!! {song.tags.get('TITLE')} TO {[info_dict['title']]}")
                    song.tags["TITLE"] = [info_dict['title']]
            song.save()
        
        elif format=='flac':
            if not os.path.isfile(os.path.join(path, video_title+".flac")):
                ydl_opts = {
                    'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
                    'format': 'bestaudio/best',
                    'ignoreerrors': True,
                    'clean_infojson': False,
                    'noplaylist': True,
                    # 'extract-audio': True,
                    # 'audio-format': 'flac',
                    # 'audio-quality': '0',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'flac',
                        'preferredquality': '300',
                    }],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                if not os.path.isdir(path): os.mkdir(path)
            else:
                self.log.error('file already exists')
        else:
            ydl_opts = {
                'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
                'format': format,
                'embed-thumbnail': True,
                'clean_infojson': False,
                'add-metadata': True,
                'ignoreerrors': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        return 0


    def check_extractor(self, url):
        extractors = yt_dlp.extractor.list_extractors()
        return next((ie.ie_key() for ie in extractors if ie.suitable(url) and ie.ie_key() != 'Generic'), None)

    
    def yt_playlist_mp3(self, url, overwrite=False, path='playlists', format='mp3', askformat=True, enum=False, albumart=True, albumart_no_embed=True, dump_metadata_first=False):
        created = False
        if not os.path.isfile('ffmpeg.exe'):
            install_ffmpeg()
        extractor = next((ie.ie_key() for ie in yt_dlp.extractor.list_extractors() if ie.suitable(url) and ie.ie_key() != 'Generic'), None)
        if dump_metadata_first:
            info_dict = self.infoget(url, {'extract_flat': 'in_playlist'})
            self.dump_json(info_dict, "metadata.json", ".")
        if enum:
            filenamefmt=os.path.join(path, "%(playlist)s", "%(playlist_index&{} - |)s%(title)s.%(ext)s")
        else:
            filenamefmt=os.path.join(path, "%(playlist)s", "%(title)s.%(ext)s")

        playlist = {}
        if extractor == "YoutubeTab":

            if format=='mp3':
                ydl_opts = {
                    'outtmpl': filenamefmt,
                    'ignoreerrors': True,
                    'clean_infojson': False,
                    ##'logger': logger(),
                    'format': 'bestaudio/best',
                    'yesplaylist': True,
                    'forceprint': {'after_move': ['filepath']},
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '256',
                    }],
                }
            elif format=='flac':
                ydl_opts = {
                    'outtmpl': filenamefmt,
                    'format': 'bestaudio/best',
                    'ignoreerrors': True,
                    'clean_infojson': False,
                    ##'logger': logger(),
                    'yesplaylist': True,
                    # 'extract-audio': True,
                    # 'audio-format': 'flac',
                    # 'audio-quality': '0',
                    'forceprint': {'after_move': ['filepath']},
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'flac',
                        'preferredquality': '300',
                    }],
                }
            else:
                ydl_opts = {
                    'outtmpl': filenamefmt,
                    'format': format,
                    'yesplaylist': True,
                    'ignoreerrors': True,
                    'clean_infojson': False,
                    'forceprint': {'after_move': ['filepath']},
                    ##'logger': logger(),
                }
            # if created or overwrite:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # ydl.download([url])
                info_dict = ydl.sanitize_info(ydl.extract_info(url))
            
            json_download_location = False
            playlist_path = None
            for i in info_dict['entries']:
                if 'requested_downloads' in i and len(i['requested_downloads']):
                    playlist_path = os.path.dirname(os.path.normpath(i['requested_downloads'][0]["filename"]))
                    json_download_location = True
                    break

            if not playlist_path:
                with yt_dlp.YoutubeDL({ 'skip_download': True, 'ignoreerrors': True, 'clean_infojson': False}) as ydl:
                    for i in info_dict['entries']:
                        try:
                            playlist_path = os.path.dirname(os.path.normpath(ydl.prepare_filename(i)))
                            break
                        except:
                            pass

                playlist_title = os.path.basename(os.path.normpath(playlist_path))
            else:
                playlist_title = os.path.basename(playlist_path)

            self.dump_json(info_dict, F"{playlist_title} metadata.json", playlist_path)

            for i in info_dict['entries']:
                if i == None:
                    continue
                try:
                    metadata = {'artist': i["artist"], 'album': i["album"], 'track': i["track"], 'album_artist': i['creator']}
                except:
                    metadata = None
                if json_download_location:
                    filename = os.path.basename(os.path.normpath(i['requested_downloads'][0]["filepath"]))
                    filepath = os.path.normpath(i['requested_downloads'][0]["filepath"])
                else:
                    filepath = ydl.prepare_filename(i)
                    filename = os.path.basename(os.path.normpath(filepath))
                playlist[str(i['playlist_index'])] = {'title': i['title'], 'filename': filename, 'filepath': filepath, 'Metadata': metadata, 'duration': i["duration"]}
                try:
                    song = taglib.File(filepath)
                except:
                    self.log.error(F"could not open {filepath} to write metadata")
                    continue
                self.log.debug(json.dumps(song.tags, indent=4, separators=(',', ': ')))
                if metadata != None:
                    # audiofile.tag.release_date = i["release_year"]
                    if not song.tags.get("ARTIST"):
                        self.log.debug(F"REPLACING ARTIST IN { filepath }!! { song.tags.get('ARTIST') } TO { [metadata['artist']] }")
                        song.tags["ARTIST"] = [metadata["artist"]]
                    if not song.tags.get("ALBUM"):
                        self.log.debug(F"REPLACING ALBUM IN { filepath }!! {song.tags.get('ALBUM')} TO {[metadata['album']]}")
                        song.tags["ALBUM"] = [metadata["album"]]
                    if not song.tags.get("ALBUMARTIST"):
                        self.log.debug(F"REPLACING ALBUMARTIST IN { filepath }!! {song.tags.get('ALBUMARTIST')} TO {[metadata['artist']]}")
                        song.tags["ALBUMARTIST"] = [metadata["artist"]]
                    if not song.tags.get("TITLE"):
                        self.log.debug(F"REPLACING TITLE IN { filepath }!! {song.tags.get('TITLE')} TO {[metadata['track']]}")
                        song.tags["TITLE"] = [metadata["track"]]
                    if not song.tags.get("TRACKNUMBER"):
                        self.log.debug(F"REPLACING TRACKNUMBER IN { filepath }!! {song.tags.get('TRACKNUMBER')} TO {[i['playlist_index']]}")
                        song.tags["TRACKNUMBER"] = [str(i['playlist_index'])]
                    if not song.tags.get("DATE") and i.get("release_year"):
                        self.log.debug(F"REPLACING DATE IN { filepath }!! {song.tags.get('DATE')} TO { [ str( i['release_year'] ) ] }")
                        song.tags["DATE"] = [str(i["release_year"])]
                else:
                    if not song.tags.get("ALBUM"):
                        self.log.debug(F"REPLACING ALBUM IN { filepath }!! {song.tags.get('ALBUM')} TO {[info_dict['title']]}")
                        song.tags["ALBUM"] = [info_dict['title']]
                    if not song.tags.get("TITLE"):
                        self.log.debug(F"REPLACING TITLE IN { filepath }!! {song.tags.get('TITLE')} TO {[i['title']]}")
                        song.tags["TITLE"] = [i['title']]
                    if not song.tags.get("TRACKNUMBER"):
                        self.log.debug(F"REPLACING TRACKNUMBER IN { filepath }!! {song.tags.get('TRACKNUMBER')} TO {[i['playlist_index']]}")
                        song.tags["TRACKNUMBER"] = [str(i['playlist_index'])]
                song.save()

        if extractor == "SoundcloudSet":
            if format=='mp3':
                ydl_opts = {
                    'outtmpl': filenamefmt,
                    'ignoreerrors': True,
                    ##'logger': logger(),
                    'format': 'bestaudio/best',
                    'clean_infojson': False,
                    'forceprint': {'after_move': ['filepath']},
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '256',
                    }],
                }
            else:
                ydl_opts = {
                    'forceprint': {'after_move': ['filepath']},
                    'clean_infojson': False,
                    'outtmpl': filenamefmt,
                    'format': format,
                    'ignoreerrors': True,
                }

            # if created or overwrite:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.sanitize_info(ydl.extract_info(url))

            json_download_location = False
            playlist_path = None
            for i in info_dict['entries']:
                if 'requested_downloads' in i and len(i['requested_downloads']):
                    playlist_path = os.path.dirname(os.path.normpath(i['requested_downloads'][0]["filename"]))
                    json_download_location = True
                    break

            if not playlist_path:
                with yt_dlp.YoutubeDL({ 'skip_download': True, 'ignoreerrors': True, 'clean_infojson': False}) as ydl:
                    for i in info_dict['entries']:
                        try:
                            playlist_path = os.path.dirname(os.path.normpath(ydl.prepare_filename(i)))
                            break
                        except:
                            pass

                playlist_title = os.path.basename(os.path.normpath(playlist_path))
            else:
                playlist_title = os.path.basename(playlist_path)

            for i in info_dict['entries']:
                metadata = {'artist': i["uploader"], 'album': info_dict['title'], 'track': i["title"], 'album_artist': i['uploader']}
                if json_download_location:
                    filename = os.path.basename(os.path.normpath(i['requested_downloads'][0]["filepath"]))
                    filepath = os.path.normpath(i['requested_downloads'][0]["filepath"])
                else:
                    filepath = ydl.prepare_filename(i)
                    filename = os.path.basename(os.path.normpath(filepath))
                playlist[str(i['playlist_index'])] = {'title': i['title'], 'filename': filename, 'filepath': filepath, 'Metadata': metadata, 'duration': i["duration"]};
                self.dl_file(i["thumbnail"], filename=F"{ '.'.join(filename.split('.')[:-1]) }.jpg", path=os.path.join(playlist_path, "thumbnails"))
                try:
                    song = taglib.File(filepath)
                    if playlist[str(i['playlist_index'])]["Metadata"] != None:
                        song.tags["ARTIST"] = [i["uploader"]]
                        song.tags["ALBUM"] = [info_dict['title']]
                        song.tags["ALBUMARTIST"] = [i["uploader"]]
                        song.tags["TITLE"] = [i["title"]]
                        song.tags["TRACKNUMBER"] = [str(i['playlist_index'])]
                        song.tags["DATE"] = [str(i["upload_date"])]
                    else:
                        song.tags["ALBUM"] = [Albumname]
                        song.tags["TITLE"] = [playlist[i]['title']]
                        song.tags["TRACKNUMBER"] = [str(i['playlist_index'])]
                    song.save()
                except:
                    self.log.error(F"could not write metadata to {i['title']}")

        if extractor == "BandcampAlbum":
            info_dict = self.infoget(url, opts = {'forceprint': {'after_move': ['filepath']}, 'outtmpl': filenamefmt})

            playlist_path = None

            with yt_dlp.YoutubeDL({ 'skip_download': True, 'simulate': True, 'ignoreerrors': True, 'clean_infojson': False, 'outtmpl': filenamefmt }) as ydl:
                for i in info_dict['entries']:
                    try:
                        playlist_path = os.path.dirname(os.path.normpath(ydl.prepare_filename(i)))
                        break
                    except:
                        pass

            playlist_title = os.path.basename(os.path.normpath(playlist_path))

            formats = dict()
            for i in info_dict["entries"]:
                for j in i["formats"]:
                    formats[j["format_id"]] = j["ext"]
            playlistfile = None
            if os.path.isfile(os.path.join(playlist_path,  F"{playlist_title} playlist.json")):
                with open(os.path.join(playlist_path,  F"{playlist_title} playlist.json"), 'r') as file:
                    playlistfile = json.load(file)
            if not overwrite and playlistfile:
                for i in playlistfile:
                    format = playlistfile[i]["filename"].split(".")[-1]
                    formats[format] = format
                self.log.debug(format)
            elif len(formats) > 1 and askformat:
                print("Multiple formats are available for download:")
                cnt = 1
                selected = 1
                for i in formats:
                    if formats[i] == format:
                        selected = cnt
                    print(f"{cnt}: {formats[i]} | {i}")
                    cnt += 1
                selection = input(F"Please choose a format [{selected}]: ")
                if selection == "":
                    format = list(formats.keys())[selected - 1]
                else:
                    selection = int(selection)
                    format = list(formats.keys())[selection - 1]
                print(format)
            elif len(formats)==1 and askformat:
                format = list(formats.keys())[0]
                self.log.debug(format)
            else:
                formats[format] = format
                self.log.debug(format)
            ydl_opts = {
                'forceprint': {'after_move': ['filepath']},
                'outtmpl': filenamefmt,
                'format': format,
                'ignoreerrors': True,
                'clean_infojson': False,
                ##'logger': logger(),
            }
            # if created or overwrite:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.sanitize_info(ydl.extract_info(url))
            for i in info_dict['entries']:
                if i == None:
                    continue
                if i["artist"] != None: metadata = {'artist': i["artist"], 'album': i["album"], 'track': i["track"], 'album_artist': i["uploader"], "release_year": str( time.strftime('%Y', time.localtime( i["release_timestamp"] )) )};
                else: metadata = None

                if 'requested_downloads' in i and len(i['requested_downloads']):
                    filename = os.path.basename(os.path.normpath(i['requested_downloads'][0]["filepath"]))
                    filepath = os.path.normpath(i['requested_downloads'][0]["filepath"])
                else:
                    filepath = ydl.prepare_filename(i)
                    filename = os.path.basename(os.path.normpath(filepath))

                playlist[str(i['playlist_index'])] = {'title': i['track'], 'filename': filename, 'filepath': filepath, 'Metadata': metadata, 'duration': i["duration"]};
                if metadata["album"] == None:
                    Albumname = playlist_title
                else:
                    Albumname = metadata["album"]
                # try:
                self.dl_file(i['thumbnails'][0]['url'], (i['title']+'.'+i['thumbnails'][0]['url'].split('.')[-1]).replace(':', ' -').replace('"', '\'').replace("'", "\'").replace('|', '_').replace('|', '_').replace('//','_').replace('/','_').replace('?',''), os.path.join(path, playlist_title, 'thumbnails'))
                if metadata != None:
                    song = taglib.File(filepath)
                    self.log.debug(json.dumps(song.tags, indent=4, separators=(',', ': ')))
                    if metadata != None:
                        if not song.tags.get("ARTIST"):
                            self.log.debug(F"REPLACING ARTIST IN { filepath }!! { song.tags.get('ARTIST') } TO { [metadata['artist']] }")
                            song.tags["ARTIST"] = [metadata["artist"]]
                        if not song.tags.get("ALBUM"):
                            self.log.debug(F"REPLACING ALBUM IN { filepath }!! {song.tags.get('ALBUM')} TO {[Albumname]}")
                            song.tags["ALBUM"] = [Albumname]
                        if not song.tags.get("ALBUMARTIST"):
                            self.log.debug(F"REPLACING ALBUMARTIST IN { filepath }!! {song.tags.get('ALBUMARTIST')} TO {[metadata['artist']]}")
                            song.tags["ALBUMARTIST"] = [metadata["artist"]]
                        if not song.tags.get("TITLE"):
                            self.log.debug(F"REPLACING TITLE IN { filepath }!! {song.tags.get('TITLE')} TO {[metadata['track']]}")
                            song.tags["TITLE"] = [metadata["track"]]
                        if not song.tags.get("TRACKNUMBER"):
                            self.log.debug(F"REPLACING TRACKNUMBER IN { filepath }!! {song.tags.get('TRACKNUMBER')} TO {[i['playlist_index']]}")
                            song.tags["TRACKNUMBER"] = [str(i['playlist_index'])]
                        if not song.tags.get("DATE"):
                            self.log.debug(F"REPLACING DATE IN { filepath }!! {song.tags.get('DATE')} TO { [ metadata['release_year'] ] }")
                            song.tags["DATE"] = [ metadata["release_year"] ]

                    else:
                        if not song.tags.get("ALBUM"):
                            self.log.debug(F"REPLACING ALBUM IN { filepath }!! {song.tags.get('ALBUM')} TO {[playlist_title]}")
                            song.tags["ALBUM"] = [playlist_title]
                        if not song.tags.get("TITLE"):
                            self.log.debug(F"REPLACING TITLE IN { filepath }!! {song.tags.get('TITLE')} TO {[i['track']]}")
                            song.tags["TITLE"] = [i['track']]
                        if not song.tags.get("TRACKNUMBER"):
                            self.log.debug(F"REPLACING TRACKNUMBER IN { filepath }!! {song.tags.get('TRACKNUMBER')} TO {[i['playlist_index']]}")
                            song.tags["TRACKNUMBER"] = [str(i['playlist_index'])]
                    song.save()
        

        self.dump_json(playlist, F"{playlist_title} playlist.json", playlist_path)
        self.dump_json(info_dict, F"{playlist_title} metadata.json", playlist_path)

        if albumart:
            self.album_art_folder(playlist_path, no_embed = albumart_no_embed)

    
    def view_playlist_metadata(self, playlist_title=False, url=False, path='playlists'):
        if not playlist_title and not url: return self.log.error('please pass a url or playlist title')
        if playlist_title and url: return self.log.error('please do not pass both a url and playlist title')
        if url:
            ydl_opts = {}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                playlist_title = info_dict['title'].replace(':', ' -').replace('"', '\'').replace("'", "\'").replace('|', '_').replace('|', '_').replace('//','_').replace('/','_').replace('?','').replace('*','_')
        if playlist_title:
            try:
                with open(os.path.join(path, playlist_title,  F"{playlist_title} playlist.json"), 'r') as file:
                    playlist = json.load(file)
            except:
                return self.log.error(F"could not find {playlist_title} playlist.json")
            try:
                with open(os.path.join(path, playlist_title, F"{playlist_title} metadata.json"), 'r') as file:
                    info_dict = json.load(file)
            except:
                return self.log.error(F"could not find {playlist_title} metadata.json")
            for i in playlist:
                try:
                    song = taglib.File(playlist[i]['filepath'])
                except:
                    self.log.error(F"could not open {playlist[i]['filepath']}")
                    continue
                self.log.info(playlist[i]['filepath'])
                self.log.info(json.dumps(song.tags, indent=4, separators=(',', ': ')))

    
    def playlist_metadata(self, playlist_title=False, url=False, path='playlists', album_art=True):
        if not playlist_title and not url: return self.log.error('please pass a url or playlist title')
        if playlist_title and url: return self.log.error('please do not pass both a url and playlist title')
        if url:
            ydl_opts = {}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                playlist_title = info_dict['title'].replace(':', ' -').replace('"', '\'').replace("'", "\'").replace('|', '_').replace('|', '_').replace('//','_').replace('/','_').replace('?','').replace('*','_')
        if playlist_title:
            try:
                with open(os.path.join(path, playlist_title,  F"{playlist_title} playlist.json"), 'r') as file:
                    playlist = json.load(file)
            except:
                return self.log.error(F"could not find {playlist_title} playlist.json")
            try:
                with open(os.path.join(path, playlist_title, F"{playlist_title} metadata.json"), 'r') as file:
                    info_dict = json.load(file)
            except:
                return self.log.error(F"could not find {playlist_title} metadata.json")
            for i in playlist:
                if playlist[i]["Metadata"]["album"] == None:
                    Albumname = playlist_title
                else:
                    Albumname = playlist[i]["Metadata"]["album"]
                try:
                    song = taglib.File(playlist[i]['filepath'])
                except OSError:
                    self.log.error(F"could not find {playlist[i]['filepath']}")
                if playlist[i]["Metadata"] != None:
                    song.tags["ARTIST"] = [playlist[i]["Metadata"]["artist"]]
                    song.tags["ALBUM"] = [Albumname]
                    song.tags["ALBUMARTIST"] = [playlist[i]["Metadata"]["album_artist"]]
                    song.tags["TITLE"] = [playlist[i]["Metadata"]["track"]]
                    song.tags["TRACKNUMBER"] = [i]
                else:
                    song.tags["ALBUM"] = [Albumname]
                    song.tags["TITLE"] = [playlist[i]['title']]
                    song.tags["TRACKNUMBER"] = [i]
                song.save()
        if album_art:
            self.album_art_folder(os.path.join(path, playlist_title))

@click.group()
@click.pass_context
def cli(ctx):
    """This script downloads music and embeds metadata."""
    ctx.obj = MusicGetter()
    ctx.show_default = True

@cli.command()
@click.option("--playlist-title", "-t", default="False")
@click.option("--url", default="False")
@click.option("--path", default='playlists')
@click.pass_obj
def view_playlist_metadata(obj, playlist_title, url, path):
    if url == "False":
        url=False
    if playlist_title == "False":
        playlist_title=False
    obj.view_playlist_metadata(playlist_title=playlist_title, url=url, path=path)

@cli.command()
@click.argument("url")
@click.pass_obj
def check_extractor(obj, url):
    """check yt-dlp extractor"""
    click.echo(obj.check_extractor(url))

@cli.command()
@click.option("--playlist-title", "-t", default="False")
@click.option("--url", default="False")
@click.option("--path", default='playlists')
@click.option("--album-art/--no-album-art", default=False, help="download album art from the internet")
@click.pass_obj
def playlist_metadata(obj, playlist_title, url, path, album_art):
    if url == "False":
        url=False
    if playlist_title == "False":
        playlist_title=False
    obj.playlist_metadata(playlist_title=playlist_title, url=url, path=path, album_art=album_art)

@cli.command()
@click.argument("url")
@click.option("--overwrite/--no-overwrite", default=False)
@click.option("-p", "--path", default='playlists', help="path to save files to")
@click.option("-f", "--format", default='mp3', help="eg. mp3, flac, aiff")
@click.option("--ask-format/--no-ask-format", default=True, help="ask for download format")
@click.option("-e", "--enum", is_flag=True, help="add position in playlist to filename")
@click.option("-a", "--album-art", is_flag=True, help="Automatically download album art (does not include bandcamp thumbnails)")
@click.option("-A", "--embed-album-art", is_flag=True, help="Automatically downlads and embeds album art")
@click.pass_obj
def yp(obj, url, overwrite, path, format, ask_format, enum: bool, album_art: bool, embed_album_art: bool):
    obj.yt_playlist_mp3(url, overwrite=overwrite, path=path, format=format, askformat=ask_format, enum=enum, 
                        albumart=( album_art or embed_album_art ), albumart_no_embed=( not embed_album_art ) )

@cli.command()
@click.argument("url")
@click.option("--path", default='downloads', help="path to save files to")
@click.option("-f", "--format", default='mp3', help="eg. mp3, flac, aiff")
@click.pass_obj
def yt(obj, url, path, format):
    obj.yt_mp3(url, path=path, format=format)

@cli.command()
@click.argument("url")
@click.pass_obj
def getinfo(obj, url):
    """gets info on the given url"""
    click.echo(obj.infoget(url))

@cli.command()
@click.argument("url")
@click.option("--path", default='', help="path to save files to")
@click.option("-f", "--filename", default='info.json', help="filename")
@click.pass_obj
def dumpinfo(obj, url, path, filename):
    """dumps info from a url to a file"""
    obj.dump_json(obj.infoget(url), filename = filename, path = path)

if __name__ == "__main__": 
    cli()

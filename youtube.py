import psycopg2
import requests
from googleapiclient.discovery import build
import urllib.request

API_KEY = 'ВАШ ТОКЕН'

youtube = build('youtube', 'v3', developerKey=API_KEY)

# тут достаётся инфа самого канала
channel_request = youtube.channels().list(part='snippet,contentDetails,statistics', forUsername='rozetked')
channel_response = channel_request.execute()

channel_id = channel_response['items'][0]['id']
channel_video_count = channel_response['items'][0]['statistics']['videoCount']
print(channel_video_count)

r = youtube.channels().list(id=channel_id, part='contentDetails').execute()
uploads_playlist_id = r['items'][0]['contentDetails']['relatedPlaylists']['uploads']

args = {
    'playlistId': uploads_playlist_id,
    'part': 'snippet',
    'maxResults': 50,
}

# Функция записи данных в БД
def write_db(data):
    # Подключение к бд
    conn = psycopg2.connect(database="youtube", user="postgres", password="postgres", host="localhost", port="5432")
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO postsYT (id, title, textOfPost, likes, comment_count, videoLength, views, postLink, refLink) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (data['video_id'], data['title'], data['description'], data['like_count'], data['countComments'],
            data['videoLength'], data['view_count'], data['postLink'], data['refLink']))
        conn.commit()
        print(f"Видео с ID {data['video_id']} добавлено в базу данных")
    except Exception as e:
        conn.rollback()
        print(f"Произошла ошибка: {e}")

    # Закрываем соединение
    conn.close()
    cur.close()

#тут уже бежим по всем видосам и вызываем функции исходя из айди видео
def get_stat(video_id):
    # Получаем информацию о видео
    video_info = youtube.videos().list(part="snippet,statistics,contentDetails", id=video_id).execute()

    # Получаем название и описание видео
    title = video_info['items'][0]['snippet']['title']
    description = video_info['items'][0]['snippet']['description']
    view_count = video_info['items'][0]['statistics']['viewCount']
    like_count = video_info['items'][0]['statistics']['likeCount']
    countComments = video_info['items'][0]['statistics']['commentCount']
    videoLength = video_info['items'][0]['contentDetails']['duration']
    postLink = "https://www.youtube.com/watch?v=" + video_id

    split_text = description.split()
    dataLink = []
    for i in split_text:
        if "http" in i:
            link = i
            dataLink.append(link)

    for i in dataLink:
        try:
            response = requests.get(i)
            content = response.content
            # Проверяем наличие реферальной информации на странице
            if 'referrer' in str(content):
                link = i
                write_bd(video_id, title, description, like_count, countComments, view_count, videoLength, postLink, link)
                print('Ссылка является реферальной')
                print(video_id)
            else:
                print('Ссылка не является реферальной')
        except urllib.error.HTTPError as e:
            link = i
            write_bd(video_id, title, description, like_count, countComments, view_count, videoLength, postLink, link)
            print('Произошла ошибка при запросе страницы:', e)

def write_bd(video_id, title, description, like_count, countComments, view_count, videoLength, postLink, linkAll):
    data = {
        'video_id': video_id,
        'title': title,
        'description': description,
        'like_count': like_count,
        'countComments': countComments,
        'view_count': view_count,
        'videoLength': videoLength,
        'postLink': postLink,
        'refLink': linkAll
    }
    write_db(data)

for _ in range(0, 500):
    r = youtube.playlistItems().list(**args).execute()
    for item in r['items']:
        snpt = item['snippet']
        if snpt['publishedAt'][0:4] == '2022' or snpt['publishedAt'][0:4] == '2023':
            video_id = snpt['resourceId'].get('videoId')
            get_stat(video_id)
        args['pageToken'] = r.get('nextPageToken')
        if not args['pageToken']:
            break

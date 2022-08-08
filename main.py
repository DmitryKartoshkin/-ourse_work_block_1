import requests
import json
import time

with open('token.txt', 'r') as file_object:
    TOKEN_VK  =  file_object.readline().strip()
    TOKEN_YD =  file_object.readline().strip()
id_vk = '' # id профиля VK

class Vk:
    URL = 'https://api.vk.com/method/'
    def __init__(self, token, vers):
        self.params = {'access_token': token, 'v': vers}

    def upload_photos(self, id, id_album = 'profile'):
        """Метод нахождения фотографий в профиле (по умолчанию) сообщества по значению id.
        Если подставить значение id альбома сообщества, которое можно получить используя метод "albums_id"
        можно получить доступ к фотографиям в этом альбоме"""
        def_URL = self.URL + "photos.get"
        params_def = {
            'owner_id': '-' + str(id),
            'album_id': id_album,
            'count': 5,
            'photo_sizes': 1,
            'extended': 1,
        }
        req = requests.get(def_URL, params = {**self.params, **params_def}).json()
        return req ['response']["items"]

    def time_file(self, times):
        # метод преодразования формата времени
        self.time = time.strftime("%d_%b_%Y", time.localtime(times))
        return self.time

    def albums_id(self, id):
        """Метод возвращает словарь где ключ это название альбома, а значение id этого альбома."""
        def_URL = self.URL + "photos.getAlbums"
        params_def = {'owner_id': '-' + str(id)}
        req = requests.get(def_URL, params={**self.params, **params_def}).json()
        photo_albums = req ['response']["items"]
        dict_id_photo_albums = {id['title']: id['id'] for id in photo_albums}
        return dict_id_photo_albums

class YaUploader:
    def __init__(self, token):
        self.token = token

    def get_headers(self):
        # Заголовки для Яндекс диска
        return {'Content-Type': 'application/json',
                'Authorization': f'OAuth {self.token}'
                }

    def new_folder(self, name):
        # создаем новую папку для загрузки фотографий
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = self.get_headers()
        self.name_folder = name
        params = {'path': self.name_folder}
        response = requests.put(upload_url, headers=headers, params=params)
        if response.status_code == 201:
            print(f'Папка "{self.name_folder}" создана')
            return self.name_folder
        elif response.status_code == 409:
            print(f'Папка "{self.name_folder}" существует')
            return self.name_folder

    def get_upload_link(self, url_file, name_folder, disk_file_path):
        # метод загрузки фалов на Яндекс диск по URL
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {
            'url': url_file,
            "path": '/' + name_folder + '/' + disk_file_path,
            "disable_redirects": "true"
        }
        response = requests.post(upload_url, headers=headers, params=params)
        response.raise_for_status()
        if response.status_code == 202:
            print("Загрузка выполнена успешно")
        else:
            print(f'Ошибка {response.status_code}')

    def search(self, name_folder):
        # метод создает список файлов, хранящихся на Яндекс Диске
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {"path": 'disk:/' + name_folder, 'fields': 'name,_embedded.items.name'}
        response = requests.get(url, headers=headers, params=params).json()
        list_file_yd =  response['_embedded']['items']
        list_file = []
        for i in range(len(list_file_yd)):
            list_file.append(list_file_yd[i]['name'])
        return list_file

if __name__ == '__main__':
    vk_client = Vk(TOKEN_VK, '5.131') # создаем экземпляр класса Vk
    list_photo_vk = vk_client.upload_photos(id_vk) # получаем список с информацией по фотографиям ВК
    uploader = YaUploader(token=TOKEN_YD) # создаем экземпляр класса YaUploader
    name_folder = uploader.new_folder('Photo')
    list_file_yandex_disk = uploader.search(name_folder) # сполучаем список с информацией по фотографиям на Яндекс диске
    list_photo = []
    for element in list_photo_vk:
        url_photo = element["sizes"][-1]['url'] # url файла
        size_file =element["sizes"][-1]['type']
        quantity_likes = element['likes']['count'] # количество лайков
        date_of_publication = vk_client.time_file(element['date']) # дата публикации фото на странице ВК
        path_to_file_load = date_of_publication + '_' + str(quantity_likes) + '.jpg' # имя файла для сохранения на Яндекс диске
        list_photo.append({'file_name': str(quantity_likes) + '.jpg', 'size': size_file})
        if path_to_file_load not in list_file_yandex_disk: # Проверка, если файла с таким именем не существует на Яндекс диске
            uploader.get_upload_link(url_photo, name_folder, path_to_file_load) # то добавляем его в папку на Яндекс диск
        else: # если существует, то не добавляем
            continue
    with open("photo_vk.json", "w", encoding="utf-8") as file_photo_vk: # записываем имя фотографии в файл
        json.dump(list_photo, file_photo_vk, ensure_ascii=False, indent=4)
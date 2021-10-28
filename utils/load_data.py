""" Created by MrBBS """
# 5/22/2021
# -*-encoding:utf-8-*-

import face_recognition
import json
from pathlib import Path
from .sqlite_database import get_all_employee
import yaml

maxim_data = json.load(open('./src/maxim.json', 'r', encoding='utf-8'))


def load_user_data(isTrain=False, users_info=None):
    config = yaml.load(open("src/settings.yaml", 'r', encoding='utf-8'), Loader=yaml.FullLoader)
    know_face_paths = {}
    know_enc = []
    know_codes = []
    users = {}
    if not isTrain or users_info is None:
        users_info = get_all_employee(None)
    users_info = [user for user in users_info if user['active']]
    for info in users_info:
        if info['code'] not in users.keys() and info['img_data']:
            users.setdefault(info['code'], info['img_data'].split('|'))
    for i, (code, path) in enumerate(users.items()):
        if len(path) > 0:
            for p in path:
                try:
                    if isTrain:
                        image = face_recognition.load_image_file(Path(config['data_path']).joinpath(p).as_posix())
                        enc = face_recognition.face_encodings(image, model='large')[0]
                        know_enc.append(enc)
                    else:
                        if code not in know_face_paths.keys():
                            know_face_paths.setdefault(code, [])
                        know_face_paths[code].append(Path(config['data_path']).joinpath(p).as_posix())
                    know_codes.append(code)
                except Exception as e:
                    pass
    if isTrain:
        return know_enc, know_codes
    else:
        return users_info, know_codes, know_face_paths

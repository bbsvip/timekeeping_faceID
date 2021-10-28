""" Created by MrBBS """
# 6/22/2021
# -*-encoding:utf-8-*-

import math
import os
import base64
from io import BytesIO

import numpy as np
import random
import string
import sys
from typing import Tuple, Union
import hashlib
# from tensorflow.keras.models import model_from_json
import cv2
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import datetime
from utils.load_data import *
from utils.ui import Ui_MainWindow
from utils.sqlite_database import *
import pandas as pd
import requests
import winsound

try:
    import Jetson.GPIO as gpio
except:
    pass


class TableModel(QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])


class main(QMainWindow):
    def __init__(self):
        super(main, self).__init__()
        self.s = b'0331999Bbsvip'
        self.font = ImageFont.truetype('src/font.ttf', size=20, encoding='utf-8')
        try:
            self.config = yaml.load(open("src/settings.yaml", 'r', encoding='utf-8'), Loader=yaml.FullLoader)
        except FileNotFoundError:
            self.config = {
                'branch': 'ĐN',
                'device_name': 'FI_01',
                'delay_people': 3,
                'delay_timekeep': 60,
                'camera': 0,
                'URL_API': '',
                'DB_PATH': "src/TimeKeepingDB.db",
                'password': hashlib.pbkdf2_hmac('sha512', b'12345678', self.s, 33, 64).hex(),
                'checkin_path': 'media/checkin_images/',
                'avatar_path': 'media/avatar/',
                'data_path': 'media/data/',
                'username_login': 'chinhanhdanang',
                'password_login': "310f595837a4902335749dd83088c6f3c6a9b7d236633ac6e15aaa1cc41a7623887d7c5b80d222c7184f3a93e0dbca2eabf8e3af8d796f89c1773a6f969e2649401e837e0dba2f6e10d6f0b8a58887d79db85ce01453626295e7abab1054d848758b2c7a7a3e4572812406af9fac863d1088ea83cfcbc8ca26aa08c62d88d5e5c915281fd26ca9dc72c5bcd650f2ff38b591eb3724f18d85a645342246a9d4324201337128cc0c7a876bd0eba0a6613d18959b874554113b45f3c4355d38544a7a754ea0174e798c4ad266b896c3302561f829ee87e8604104ecaa326dd11e75d53ba5b67dbf2688daf18f6184d00606fc99571d9629c16c98f5089fce7b6436ff446e7d0742217c32cce12a6833afa9146f5d23bd4bd4e05dae8380237223f90e4c1b5a3b9b90d51a4118e84bd628a2588a4c69533e667a363b19fd6813449eaccfb48c0823d2dad44f2dd22ee802d095b193aee158af9813bb1de54af4bda91aa96d79b56ca2f97f8a87739087ddc207005a4ff8615287cdcbfca8419aa748",
                'public_key_path': "./public.pem",
                'private_key_path': "./private.pem"
            }
            yaml.dump(self.config, open(r'src/settings.yaml', 'w', encoding='utf-8'))
        self.day_of_week = {
            0: 'Thứ 2',
            1: 'Thứ 3',
            2: 'Thứ 4',
            3: 'Thứ 5',
            4: 'Thứ 6',
            5: 'Thứ 7',
            6: 'Chủ nhật',
        }
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.main_ui = True
        self.PIN = 12
        try:
            gpio.setwarnings(False)
            gpio.setmode(gpio.BOARD)
            gpio.setup(self.PIN, gpio.OUT, initial=gpio.LOW)
        except:
            pass
        self.unlock_door = False
        self.timeout_door = None
        self.person_avt = QPixmap("src/person_icon.png")
        self.is_cap = False
        self.is_add = False
        self.cap = None
        self.face_cut = None
        self.timekeep_image = None
        self.time_update_maxim = None
        self.time_noti = None
        self.day, self.date, self.time = None, None, None
        self.flag_reload = False
        self.timekeep = {}
        self.user_info = {}
        self.login_code = -1
        self.user_code = 1
        self.user_login = 'admin'
        self.count_cap = 0
        self.users_info, self.know_codes, self.know_enc, self.know_face_paths, self.codes = [], [], [], [], []
        self.list_new_face = []
        self.list_img_holder = [self.ui.bmp_img1_admin,
                                self.ui.bmp_img2_admin,
                                self.ui.bmp_img3_admin,
                                self.ui.bmp_img4_admin,
                                self.ui.bmp_img5_admin]
        self.reload_data()
        self.reload_data(True)
        self.clear_value()
        self.ui.btn_clearimg_admin.setEnabled(False)
        self.ui.btn_cap_admin.hide()
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.stackedWidget_2.setCurrentIndex(0)
        self.face_detection = cv2.CascadeClassifier("src/frontalface_default.xml")
        # json_model = open('src/antispoofing.json', 'r').read()
        # self.antispoofing = model_from_json(json_model)
        # self.antispoofing.load_weights('src/antispoofing.h5')
        self.ui.btn_login.clicked.connect(self.login_clicked)
        self.ui.btn_back_admin.clicked.connect(self.back_admin_clicked)
        self.ui.btn_function_admin.clicked.connect(self.function_admin_clicked)
        self.ui.btn_cap_admin.clicked.connect(self.cap_admin_clicked)
        self.ui.btn_clearimg_admin.clicked.connect(self.clearimg_admin_clicked)
        self.ui.btn_reload.clicked.connect(self.reload_data_clicked)
        self.ui.btn_setting_admin.clicked.connect(self.setting_admin_clicked)
        self.ui.btn_back_setting.clicked.connect(self.back_setting_clicked)
        self.ui.btn_save_setting.clicked.connect(self.save_setting_clicked)
        self.ui.edt_password.textChanged.connect(self.onPassChange)
        self.ui.tableView.clicked.connect(self.row_click)
        self.bbox = []
        self.cap_width = 640
        self.cap_height = 480
        if self.cap is None:
            try:
                self.cap = cv2.VideoCapture(int(self.config['camera']))
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cap_height)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cap_width)
            except:
                self.cap = cv2.VideoCapture(
                    f"v4l2src device=/dev/video{int(self.config['camera'])} ! video/x-raw, width={self.cap_width}, height={self.cap_height} ! videoconvert ! video/x-raw, format=BGR ! appsink")
        self.timer_camera = QTimer()
        self.timer_camera.setInterval(10)
        self.timer_camera.timeout.connect(self.tic_toc)
        self.timer_camera.start()

        self.timer_recog = QTimer()
        self.timer_recog.setInterval(200)
        self.timer_recog.timeout.connect(self.face_recog)
        self.timer_recog.start()

        self.show()

    def tic_toc(self):
        self.day, self.date, self.time = self.get_time()
        self.ui.t_datetime.setText(f'{self.day}, Ngày {self.date} - {self.time}')
        if self.time_update_maxim is None or self.time_update_maxim != self.date:
            self.update_maxim()
            self.time_update_maxim = self.date
        if self.time_noti:
            timeout = 10 if self.login_code < 0 else 5
            if (datetime.datetime.now() - self.time_noti).total_seconds() > timeout and self.login_code < 1:
                self.time_noti = None
                self.clear_value()
                self.login_code = -1
        if self.ui.stackedWidget_2.currentIndex() == 0:
            if self.cap.isOpened():
                ret, image = self.cap.read()
                if ret:
                    simage = cv2.flip(image, 1)
                    simage = self.face_detect(simage)
                    height, width, channel = simage.shape
                    bytesPerLine = 3 * width
                    qImg = QImage(np.ascontiguousarray(simage), width, height, bytesPerLine, QImage.Format_RGB888)
                    self.ui.live_view.setPixmap(QPixmap(qImg))
            else:
                try:
                    try:
                        self.cap = cv2.VideoCapture(int(self.config['camera']))
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cap_height)
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cap_width)
                    except:
                        self.cap = cv2.VideoCapture(
                            f"v4l2src device=/dev/video{int(self.config['camera'])} ! video/x-raw, width={self.cap_width}, height={self.cap_height} ! videoconvert ! video/x-raw, format=BGR ! appsink")
                except Exception as _:
                    self.set_noti('vui lòng cài đặt camera id trong setting và thử lại', 1)
        if self.unlock_door:
            try:
                gpio.output(self.PIN, gpio.HIGH)
            except:
                pass
            print(datetime.datetime.now(), 'unlock', self.user_info['name'])
            self.unlock_door = False
            self.timeout_door = datetime.datetime.now()
        elif self.timeout_door and (datetime.datetime.now() - self.timeout_door).total_seconds() >= 10:
            self.timeout_door = None
            try:
                gpio.output(self.PIN, gpio.LOW)
            except:
                pass
            print(datetime.datetime.now(), 'lock')

    def normalized_to_pixel(self, normalized: float, size):
        return min(math.floor(normalized * size), size - 1)

    def normalized_to_pixel_coordinates(self,
                                        relative_bounding_box, image_width: int,
                                        image_height: int) -> Union[None, Tuple[int, int, int, int]]:
        """Converts normalized value pair to pixel coordinates."""
        normalized_x = relative_bounding_box.xmin
        normalized_y = relative_bounding_box.ymin
        normalized_width = relative_bounding_box.width
        normalized_height = relative_bounding_box.height
        x_px = self.normalized_to_pixel(normalized_x, image_width)
        y_px = self.normalized_to_pixel(normalized_y, image_height)
        w_px = self.normalized_to_pixel(normalized_width, image_width)
        h_px = self.normalized_to_pixel(normalized_height, image_height)
        return x_px, y_px, w_px, h_px

    def get_time(self):
        x = datetime.datetime.now()
        day = self.day_of_week[datetime.datetime.now().weekday()]
        date = x.strftime('%d/%m/%Y')
        str_time = x.strftime('%H:%M:%S')
        return day, date, str_time

    def set_noti(self, msg: str = '', type_noti: int = 0):
        msg = msg.upper()
        if self.ui.stackedWidget.currentIndex() == 0:
            self.ui.t_noti.setStyleSheet('color: rgb(0,255,0);')
            if type_noti == 1:
                self.ui.t_noti.setStyleSheet('color: rgb(255,0,0);')
            self.ui.t_noti.setText(msg)
        if self.ui.stackedWidget.currentIndex() == 1:
            self.ui.t_noti_admin.setStyleSheet('color: rgb(0,255,0);')
            if type_noti == 1:
                self.ui.t_noti_admin.setStyleSheet('color: rgb(255,0,0);')
            self.ui.t_noti_admin.setText(msg)
        if self.ui.stackedWidget.currentIndex() == 2:
            self.ui.t_noti_setting.setStyleSheet('color: rgb(0,255,0);')
            if type_noti == 1:
                self.ui.t_noti_setting.setStyleSheet('color: rgb(255,0,0);')
            self.ui.t_noti_setting.setText(msg)
        self.time_noti = datetime.datetime.now()

    def speak(self):
        winsound.Beep(2500, 500)
        pass

    def set_show_info(self):
        name, code, department, position, str_time, avatar = "_", "_", "_", "_", "_", self.person_avt
        if self.user_info:
            _, _, str_time = self.get_time()
            name = str(self.user_info['fullname'])
            code = str(self.user_info['code'])
            department = str(self.user_info['department'])
            position = str(self.user_info['position'])
            avt_path = str(self.user_info['avatar'])
            avt_path = Path('media/avatar').joinpath(avt_path).as_posix()
            if Path(avt_path).exists():
                avatar = QPixmap(avt_path)
            image_timekeep = ''
            if self.timekeep_image is not None:
                info_timekeep = f'{code} - {name} - {self.date} - {self.time}'
                text_width, _ = self.font.getsize(info_timekeep)
                H, W = self.timekeep_image.shape[:2]
                start_x = (W // 2) - text_width // 2
                start_y = H - 30
                image_timekeep = Image.fromarray(cv2.cvtColor(self.timekeep_image, cv2.COLOR_BGR2RGB))
                ImageDraw.Draw(image_timekeep).text((start_x, start_y), info_timekeep, (255, 0, 0), font=self.font)
                buffer = BytesIO()
                image_timekeep.save(buffer, format='JPEG')
                image_timekeep = base64.b64encode(buffer.getvalue())
            self.speak()
            insert_timekeeping(None, code, name, self.config['device_name'], image=image_timekeep)
        self.ui.t_name.setText(name)
        self.ui.t_id.setText(code)
        self.ui.t_department.setText(department)
        self.ui.t_location.setText(position)
        self.ui.t_timekeep.setText(str_time)
        self.ui.bmp_avatar.setPixmap(avatar)
        self.unlock_door = True
        self.set_noti('đã chấm công')

    def get_user_info(self):
        info = [x for x in self.users_info if x['code'] == str(self.user_code)]
        if len(info) > 0:
            return info[0]
        return None

    def check_timekeep(self):
        now = datetime.datetime.now()
        if len(self.timekeep) > 0:
            max_timekeep = max([[x for x in y] for y in self.timekeep.values()])
            if self.login_code < 0 \
                    and max_timekeep \
                    and (now - max_timekeep[0]).total_seconds() < self.config['delay_people']:
                return
        if self.user_code not in self.timekeep.keys() and self.login_code < 0:
            self.timekeep.setdefault(self.user_code, [])
        if self.login_code < 0 < len(self.timekeep[self.user_code]):
            last_time = self.timekeep[self.user_code][-1]
            if (now - last_time).total_seconds() < self.config['delay_timekeep']:
                return
        self.user_info = self.get_user_info()
        if self.user_info is not None and self.user_info['active']:
            if self.login_code < 0:
                self.timekeep[self.user_code].append(now)
                self.set_show_info()
            else:
                if self.login_code == 0 and self.user_info and self.user_info['isadmin']:
                    self.user_login = str(self.user_info['code'])
                    self.change_stack(1)

    def face_recog(self):
        try:
            if self.main_ui and self.face_cut is not None:
                # face = np.expand_dims(cv2.resize(self.face_cut, (160, 160)) / 255.0, axis=0)
                # liveness = self.antispoofing.predict(face)[0]
                # if liveness < 0.005:
                face_enc = face_recognition.face_encodings(self.face_cut, model='large')
                if len(face_enc) > 0:
                    match = face_recognition.compare_faces(self.know_enc, face_enc[0], tolerance=0.35)
                    face_distances = face_recognition.face_distance(self.know_enc, face_enc[0])
                    best_match_index = np.argmin(face_distances)
                    if match[best_match_index]:
                        self.user_code = self.know_codes[best_match_index]
                        if not self.unlock_door and self.timeout_door is None:
                            self.unlock_door = True
                        elif self.timeout_door:
                            self.timeout_door = datetime.datetime.now()
                        self.check_timekeep()
        except Exception as e:
            pass

    def face_detect(self, frame):
        try:
            self.face_cut = None
            self.timekeep_image = None
            vw = self.ui.live_view.size().width()
            vh = self.ui.live_view.size().height()
            fh, fw = frame.shape[:2]
            if vh < fh:
                vRange = (fh // 2 - vh // 2, fh // 2 + vh // 2)
            else:
                vRange = (0, fh)
            if vw < fw:
                hRange = (fw // 2 - vw // 2, fw // 2 + vw // 2)
            else:
                hRange = (0, fw)
            self.bbox = []
            ori = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray.flags.writeable = False
            results = self.face_detection.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(120, 120))
            gray.flags.writeable = True
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            if len(results):
                for x, y, w, h in results:
                    self.bbox.append([x, y, w, h])
                if len(self.bbox) > 0:
                    bbox = max(self.bbox, key=lambda b: b[2] * b[3])
                    x, y, w, h = bbox
                    if x in range(*hRange) and x + w in range(*hRange) and y in range(*vRange) and y + h in range(
                            *vRange):
                        self.timekeep_image = ori.copy()
                        self.face_cut = ori[y:y + h, x:x + w, :]
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
        except Exception as _:
            pass
        return frame

    def reload_data(self, isTrain=False):
        if isTrain:
            self.know_enc, self.know_codes = load_user_data(isTrain, self.users_info)
        else:
            self.users_info, self.know_codes, self.know_face_paths = load_user_data(isTrain)
            self.codes = sorted(list(set(self.know_codes)))

    def set_table_content(self):
        if not self.users_info:
            self.reload_data()
        data = []
        for info in self.users_info:
            if info['branch'] == self.config['branch']:
                data.append([info['code'], info['fullname']])
        data = sorted(data, key=lambda x: x[0])
        table_data = pd.DataFrame(data, columns=['MSNV', 'Họ và tên'])
        model = TableModel(table_data)
        self.ui.tableView.setModel(model)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def clear_admin(self):
        self.ui.chk_isAdmin.setChecked(False)
        self.ui.chk_active_admin.setChecked(True)
        self.ui.t_id_admin.setText('')
        self.ui.edt_name_admin.setText('')
        self.ui.t_numimg_admin.setText('0')
        self.ui.rb_male_admin.setChecked(False)
        self.ui.rb_female_admin.setChecked(False)
        self.ui.rb_else_admin.setChecked(False)
        for holder in self.list_img_holder:
            holder.setPixmap(self.person_avt)
        self.list_new_face = []
        self.ui.btn_cap_admin.hide()
        self.ui.btn_clearimg_admin.setEnabled(False)
        self.ui.t_noti_admin.setText('')
        self.is_cap = False
        self.is_add = False
        self.ui.btn_back_admin.setText('BACK')
        self.ui.btn_function_admin.setText('ADD')
        self.ui.stackedWidget_2.setCurrentIndex(1)

    def back_admin_clicked(self):
        if self.is_cap:
            self.ui.stackedWidget_2.setCurrentIndex(1)
            self.ui.tableView.clearSelection()
            self.clear_admin()
        else:
            if self.flag_reload:
                self.reload_data(True)
            self.change_stack()

    def add_picture(self):
        self.count_cap = 0
        self.set_noti('vui lòng nhìn thẳng vào camera', 1)
        self.ui.stackedWidget_2.setCurrentIndex(0)
        self.is_cap = True
        self.list_new_face = []
        self.ui.btn_back_admin.setText('CANCEL')
        self.ui.btn_function_admin.setText('SAVE')
        self.ui.btn_cap_admin.show()

    def row_click(self):
        self.clear_admin()
        self.ui.btn_back_admin.setText('CANCEL')
        self.ui.btn_function_admin.setText('SAVE')
        self.ui.btn_clearimg_admin.setEnabled(True)
        self.is_cap = True
        index = (self.ui.tableView.selectionModel().currentIndex())
        value = [index.sibling(index.row(), c).data() for c in range(2)]
        if len(value) > 1:
            code, fullname = value
            user = [info for info in self.users_info if info['code'] == code][0]
            self.ui.chk_isAdmin.setChecked(user['isadmin'])
            self.ui.chk_active_admin.setChecked(user['active'])
            self.ui.t_id_admin.setText(code)
            self.ui.edt_name_admin.setText(user['fullname'])
            self.ui.rb_male_admin.setChecked(user['sex'] == 0)
            self.ui.rb_female_admin.setChecked(user['sex'] == 1)
            self.ui.rb_else_admin.setChecked(user['sex'] == 2)
            try:
                paths = self.know_face_paths[code]
                self.ui.t_numimg_admin.setText(str(len(paths)))
                self.count_cap = len(paths)
                for i, path in enumerate(paths):
                    img = QPixmap(path)
                    self.list_img_holder[i].setPixmap(img)
            except Exception as e:
                self.add_picture()

    def update_maxim(self):
        maxim = random.choice(maxim_data)
        maxim = list(maxim.items())[0]
        self.ui.t_quota.setText(f'\" {maxim[0]} \"')
        self.ui.t_creator.setText(f'-- {maxim[1]} --')

    def clear_value(self):
        self.time_noti = None
        self.ui.edt_password.setText('')
        self.ui.t_noti.setText('')
        self.ui.t_name.setText('_')
        self.ui.t_id.setText('')
        self.ui.t_department.setText('')
        self.ui.t_location.setText('')
        self.ui.t_timekeep.setText('')
        self.ui.bmp_avatar.setPixmap(self.person_avt)
        self.ui.frame_14.hide()
        self.ui.t_noti_setting.setText('')

    def change_stack(self, index_page: int = 0):
        self.ui.stackedWidget.setCurrentIndex(index_page)
        self.ui.stackedWidget_2.setCurrentIndex(index_page)
        if index_page == 0:
            self.flag_reload = False
            self.login_code = -1
            self.user_login = 'admin'
            self.main_ui = True
        else:
            self.main_ui = False
            if index_page > 0:
                self.login_code = 1
                self.clear_admin()
                self.ui.tableView.clearSelection()
                self.set_table_content()
        self.clear_value()

    def login_clicked(self):
        self.ui.frame_14.show()
        self.set_noti('chờ xác nhận danh tính', 1)
        self.login_code = 0

    def function_admin_clicked(self):
        if self.is_cap:
            if self.count_cap > 0:
                name = self.ui.edt_name_admin.text()
                code = self.ui.t_id_admin.text()
                isActive = self.ui.chk_active_admin.isChecked()
                if self.ui.rb_male_admin.isChecked():
                    sex = 0
                elif self.ui.rb_female_admin.isChecked():
                    sex = 1
                else:
                    sex = 2
                isAdmin = self.ui.chk_isAdmin.isChecked()
                if len(name) > 1:
                    img_data = ''
                    if len(self.list_new_face) > 0:
                        old_face = self.know_face_paths[code]
                        for p in old_face:
                            try:
                                Path(p).unlink()
                            except:
                                pass
                        self.know_face_paths[code] = []
                        for img in self.list_new_face:
                            ran_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
                            path = f'{self.config["data_path"]}/{ran_name}.png'
                            cv2.imwrite(path, img)
                            self.know_face_paths[code].append(path)
                    if len(self.know_face_paths[code]) > 0:
                        img_data = '|'.join([path.split('/')[-1] for path in self.know_face_paths[code]])
                    if self.is_add:
                        insert_employee(None, code, name, sex, self.config['branch'], img_data, self.user_login,
                                        isAdmin)
                    else:
                        update_employee(None, code, name, sex, img_data, self.user_login, isAdmin, active=isActive)
                    self.clear_admin()
                    self.reload_data()
                    self.set_table_content()
                    self.flag_reload = True
                else:
                    self.set_noti('vui lòng nhập đầy đủ thông tin', 1)
            else:
                self.set_noti('vui lòng chụp ít nhất 1 ảnh', 1)
        else:
            self.add_picture()
            self.is_add = True
            new_code = ''
            try:
                url = f'{self.config["URL_API"]}/employee/new-id?device_id={self.config["device_name"]}'
                r = requests.get(url, timeout=1)
                if r:
                    new_code = r.json()['data']
            except Exception as _:
                new_code = get_employee_code()
            self.ui.t_id_admin.setText(new_code)

    def cap_admin_clicked(self):
        try:
            if self.count_cap < 5 and self.face_cut.shape:
                self.set_noti('vui lòng nhìn thẳng vào camera', 1)
                self.ui.btn_clearimg_admin.setEnabled(True)
                h, w, c = self.face_cut.shape
                self.list_new_face.append(self.face_cut)
                bytesPerLine = 3 * w
                qImg = QImage(np.ascontiguousarray(cv2.cvtColor(self.face_cut, cv2.COLOR_BGR2RGB)), w, h, bytesPerLine,
                              QImage.Format_RGB888)
                self.list_img_holder[self.count_cap].setPixmap(QPixmap(qImg))
                self.count_cap += 1
        except Exception as e:
            # print(e)
            self.set_noti('Chưa nhận diện được khuông mặt', 1)

    def clearimg_admin_clicked(self):
        self.ui.btn_cap_admin.show()
        self.count_cap = 0
        self.is_cap = True
        self.add_picture()
        for holder in self.list_img_holder:
            holder.setPixmap(self.person_avt)

    def reload_data_clicked(self):
        self.set_noti('đang tải lại dữ liệu')
        self.ui.btn_reload.setEnabled(False)
        self.clear_admin()
        self.reload_data()
        self.set_table_content()
        self.flag_reload = True
        self.ui.btn_reload.setEnabled(True)
        self.set_noti()

    def setting_admin_clicked(self):
        self.ui.edt_local_setting.setText(self.config['branch'])
        self.ui.edt_devicename_setting.setText(self.config['device_name'])
        self.ui.edt_cameraid_setting.setText(str(self.config['camera']))
        self.ui.spn_delaypeoplesetting.setValue(int(self.config['delay_people']))
        self.ui.spn_delaykeep_setting.setValue(int(self.config['delay_timekeep']))
        self.ui.edt_adminpass_setting.setText('')
        self.ui.edt_api_setting.setText(self.config['URL_API'])
        self.change_stack(2)
        self.ui.stackedWidget_2.setCurrentIndex(2)

    def back_setting_clicked(self):
        self.change_stack(1)

    def validate_setting(self, camera_id, branch, device_name, tpassword):
        if len(branch) < 1:
            self.set_noti('chi nhánh không được để trống', 1)
            return False
        if len(device_name) < 1:
            self.set_noti('tên thiết bị không được để trống', 1)
            return False
        if len(camera_id) < 1 and not camera_id.isdigit():
            self.set_noti('camera id phải là số và bắt đầu từ 0', 1)
            return False
        if 0 < len(tpassword) < 8:
            self.set_noti('mật khẩu admin phải có ít nhất 8 ký tự', 1)
            return False
        return True

    def save_setting_clicked(self):
        branch = self.ui.edt_local_setting.text()
        device_name = self.ui.edt_devicename_setting.text()
        camera_id = self.ui.edt_cameraid_setting.text()
        delay_people = self.ui.spn_delaypeoplesetting.value()
        delay_timekeep = self.ui.spn_delaykeep_setting.value()
        new_pass = self.ui.edt_adminpass_setting.text()
        if len(new_pass) > 7:
            new_pass = hashlib.pbkdf2_hmac('sha512', bytes(new_pass, encoding='utf-8'), self.s, 33, 64).hex()
        url_api = self.ui.edt_api_setting.text()
        if self.validate_setting(camera_id, branch, device_name, new_pass):
            if new_pass != self.config['password'] and len(new_pass) > 7:
                password = new_pass
            else:
                password = self.config['password']
            self.config = {
                'branch': branch,
                'device_name': device_name,
                'delay_people': delay_people,
                'delay_timekeep': delay_timekeep,
                'camera': int(camera_id),
                'URL_API': url_api,
                'DB_PATH': "src/TimeKeepingDB.db",
                'password': password,
                'checkin_path': 'media/checkin_images/',
                'avatar_path': 'media/avatar/',
                'data_path': 'media/data/',
                'username_login': 'chinhanhdanang',
                'password_login': "310f595837a4902335749dd83088c6f3c6a9b7d236633ac6e15aaa1cc41a7623887d7c5b80d222c7184f3a93e0dbca2eabf8e3af8d796f89c1773a6f969e2649401e837e0dba2f6e10d6f0b8a58887d79db85ce01453626295e7abab1054d848758b2c7a7a3e4572812406af9fac863d1088ea83cfcbc8ca26aa08c62d88d5e5c915281fd26ca9dc72c5bcd650f2ff38b591eb3724f18d85a645342246a9d4324201337128cc0c7a876bd0eba0a6613d18959b874554113b45f3c4355d38544a7a754ea0174e798c4ad266b896c3302561f829ee87e8604104ecaa326dd11e75d53ba5b67dbf2688daf18f6184d00606fc99571d9629c16c98f5089fce7b6436ff446e7d0742217c32cce12a6833afa9146f5d23bd4bd4e05dae8380237223f90e4c1b5a3b9b90d51a4118e84bd628a2588a4c69533e667a363b19fd6813449eaccfb48c0823d2dad44f2dd22ee802d095b193aee158af9813bb1de54af4bda91aa96d79b56ca2f97f8a87739087ddc207005a4ff8615287cdcbfca8419aa748",
                'public_key_path': "./public.pem",
                'private_key_path': "./private.pem"
            }
            yaml.dump(self.config, open(r'src/settings.yaml', 'w', encoding='utf-8'))
            self.change_stack(1)

    def onPassChange(self):
        self.time_noti = datetime.datetime.now()
        if len(self.ui.edt_password.text()) > 7:
            inp_password = hashlib.pbkdf2_hmac('sha512', bytes(self.ui.edt_password.text(), encoding='utf-8'),
                                               self.s,
                                               33,
                                               64).hex()
            if inp_password == str(self.config['password']):
                self.user_login = 'admin'
                self.change_stack(1)


if __name__ == "__main__":
    app = QApplication([])
    widget = main()
    widget.show()
    if app.exec() == 0:
        widget.running = False
        os._exit(1)
    sys.exit(app.exec())

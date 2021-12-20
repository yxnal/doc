#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time : 2021/12/20 2:30 下午
# @Author : huhao07
# @File : example_data.py
# @Desc : This file ...

"""This module should be deploy with example_sql.ipynb"""

import random
import string
import time


class DataGenerator(object):
    """This class used to generator sql example data in CSV format"""
    def event_data_generation(self, data_path, event_num, user_num):
        """The event schema
            event_id Int64,
            user_id Int32,
            event Enum('visit'=1,'add_cart'=2,'pay_order'=3),
            time DateTime,
            item_id String,
            fee Float32
        """
        file = open(data_path, "w+")
        event_id = 1

        delta = 7 * 24 * 60 * 60

        while event_id < event_num + 1:
            user_id = random.randint(1, user_num + 1)
            event = random.choice(['visit', 'add_cart', 'pay_order'])
            ts = int(time.time()) - random.randint(1, delta)
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
            item_id = "sp_{}".format(random.randint(1, 100000))
            fee = round(random.uniform(1, 1000), 2)

            record = "{},{},{},{},{},{}{}".format(event_id, user_id, event, dt, item_id, fee, "\n")
            file.write(record)
            event_id += 1

        file.close()

    def user_data_generation(self, data_path, num):
        """The user schema
            user_id     Int32,
            equip       Enum('android'=1,'ios'=2,'wm'=3,'pc'=4),
            user_name   String,
            age         Int8,
            gender      Enum('男'=1,'女'=2),
            city String,
        """
        file = open(data_path, "w+")
        user_id = 1

        while user_id < num + 1:
            equip = random.randint(1, 4)
            # user_name = random.sample('zyxwvutsrqponmlkjihgfedcba0123456789+-@#%', 8)
            user_name = ''.join(random.sample(string.ascii_letters + string.digits + '!@#$%^&*()_+=-', 8))
            age = random.randint(12, 66)
            gender = random.randint(1, 2)
            city = random.choice(['北京', '上海', '天津', '重庆', '南京', '广州', '武汉', '长沙',
                                  '深圳', '成都', '沈阳', '西安', '兰州', '银川', '合肥', '杭州',
                                  '石家庄', '太原', '郑州', '哈尔滨', '长春', '昆明', '南宁', '贵阳',
                                  '乌鲁木齐', '呼和浩特', '拉萨', '福州', '厦门', '三亚', '海口', '台北',
                                  '青岛', '济南', '苏州', '无锡', '宁波', '邯郸', '南昌', '香港', '大连'])

            record = "{},{},{},{},{},{}{}".format(user_id, equip, user_name, age, gender, city, "\n")
            file.write(record)
            user_id += 1
        file.close()


if __name__ == '__main__':
    user_num = 10000
    event_num = 1000000
    generator = DataGenerator()
    generator.user_data_generation("./user.csv", user_num)
    generator.event_data_generation("./events.csv", event_num, user_num)



import sqlite3
import json
import random
import time
import logging


class DataStore:
    def __init__(self, setup=False):
        self.connection = sqlite3.connect('db/app.sqlite3.db')
        self.profile_connection = sqlite3.connect('db/profiles.db')
        self.connection.row_factory = sqlite3.Row
        self.profile_connection.row_factory = sqlite3.Row
        if setup:
            self.setup()

    def get_profiles(self):
        cursor = self.profile_connection.cursor()
        cursor.execute("""SELECT a.active, p.* FROM profiles p left join active_profile as a on p.id=a.active""")
        r = cursor.fetchall()
        profiles = []
        if r is not None:
            for row in r:
                profile = {}
                for key in row.keys():
                    profile[key.lower()] = row[key]
                profiles.append(profile)
            cursor.close()
        return profiles

    def get_profile(self, profile_id):
        params = [profile_id]
        cursor = self.profile_connection.cursor()
        cursor.execute("""SELECT a.active, p.* FROM profiles p left
            join active_profile as a on p.id=a.active where p.id = ?""", params)
        r = cursor.fetchone()
        profiles = {}
        if r is not None:
            for key in r.keys():
                profiles[key.lower()] = r[key]
            cursor.close()
        return profiles

    def get_active_profile(self):
        cursor = self.profile_connection.cursor()
        cursor.execute("""SELECT a.active, p.* FROM profiles p left
            join active_profile as a on p.id=a.active where p.id = a.active""")
        r = cursor.fetchone()
        profiles = {}
        if r is not None:
            for key in r.keys():
                profiles[key.lower()] = r[key]
            cursor.close()
        return profiles

    def set_active_profile(self, profile_id):
        params = [profile_id]
        cursor = self.profile_connection.cursor()
        cursor.execute("""update active_profile set ACTIVE = ? where id = 1""", params)
        self.profile_connection.commit()
        cursor.close()

    def save_profile(self, settings):
        params = []
        params.extend([settings['name'], settings['target_temp'], settings['sample_size'],
                       settings['tolerance'], settings['heat_duration'], settings['cool_duration'], settings['id']])

        cursor = self.profile_connection.cursor()

        cursor.execute("""update profiles set NAME = ?, TARGET_TEMP = ?,
            SAMPLE_SIZE = ?, TOLERANCE = ?, heat_duration = ?, cool_duration = ? where id = ? ;""", params)
        self.profile_connection.commit()
        cursor.close()

    def add_profile(self, settings):
        params = []
        params.extend([settings['name'], settings['target_temp'], settings['sample_size'],
                       settings['tolerance'], settings['heat_duration'], settings['cool_duration']])

        cursor = self.profile_connection.cursor()
        cursor.execute("""insert into profiles (NAME, TARGET_TEMP, SAMPLE_SIZE,
                TOLERANCE, COOL_DURATION, HEAT_DURATION )
                values(?,?,?,?,?,?);""", params)

        self.profile_connection.commit()
        cursor.close()

    def delete_profile(self, id):
        params = [id]

        cursor = self.profile_connection.cursor()
        cursor.execute("""DELETE FROM profiles WHERE id = ? """, params)

        self.profile_connection.commit()
        cursor.close()

    def apply_active_profile(self):
        profile = self.get_active_profile()
        old_setting = self.get_settings()
        if 'enabled' in old_setting:
            enabled = old_setting['enabled']
        else:
            enabled = 0

        new_setting = {'enabled': enabled,
                       'target_temp': profile['target_temp'],
                       'sample_size': profile['sample_size'],
                       'tolerance' : profile['tolerance'],
                       'heat_duration': profile['heat_duration'],
                       'cool_duration': profile['cool_duration'] }
        self.save_settings(new_setting)

    def save_settings(self, settings):
        params = []
        enabled = settings['enabled']
        if enabled:
            params.append('1')
        else:
            params.append('0')
        params.extend([settings['target_temp'], settings['sample_size'],
                       settings['tolerance'], settings['heat_duration'], settings['cool_duration']])

        cursor = self.connection.cursor()
        cursor.execute("""update settings set ENABLED = ?, TARGET_TEMP = ?,
            SAMPLE_SIZE = ?, TOLERANCE = ?, heat_duration = ?, cool_duration = ? where id = 1 ;""", params)
        self.connection.commit()
        cursor.close()

    def get_settings(self):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM settings WHERE id = 1""")
        r = cursor.fetchone()
        settings = {}
        if r is not None:
            for key in r.keys():
                if key.lower() == 'enabled':
                    settings[key.lower()] = 'true' if 1 == r[key] else 'false'
                else:
                    settings[key.lower()] = r[key]
            cursor.close()
        return settings

    def get_heat_source_status(self):
        cursor = self.connection.cursor()
        cursor.execute("""select HEAT_SOURCE from settings where id = 1 ;""")
        r = cursor.fetchone()
        heat_source = r['HEAT_SOURCE']
        self.connection.commit()
        cursor.close()
        return heat_source

    def set_heat_source_status(self, status):
        cursor = self.connection.cursor()
        cursor.execute("""update settings set HEAT_SOURCE = ? where id = 1 ;""", [status])
        self.connection.commit()
        cursor.close()

    def add_temperature(self, current_temp):
        cursor = self.connection.cursor()
        cursor.execute("""INSERT INTO temperatures (temp) VALUES(?)""", [current_temp])
        self.connection.commit()
        cursor.close()

    def get_control_data(self):
        cursor = self.connection.cursor()
        cursor.execute("""select s.target_temp, s.heat_source, s.enabled,
            s.sample_size, s.tolerance, s.heat_duration, s.cool_duration, t.temp,
            (select round(avg(t.temp),1) from temperatures t where t.id in
                (select id from temperatures tm ORDER BY dt DESC Limit
                    (select sample_size from settings where id =1)))
            as avg_temp,
            (select ((temp2 - temp1) / (dt2 - dt1)) as slope from
                ((select strftime('%s', dt)  as dt1 from
                    (select * from temperatures ORDER BY dt DESC Limit
                        (select sample_size from settings where id =1) )order by dt asc limit 1),
                (select temp as temp1 from (select * from temperatures ORDER BY dt DESC Limit
                        (select sample_size from settings where id =1) )order by dt asc limit 1) ,
                (select strftime('%s', dt)  as dt2 from (select * from temperatures ORDER BY dt DESC Limit
                        (select sample_size from settings where id =1) )order by dt desc limit 1) ,
                (select temp as temp2 from (select * from temperatures ORDER BY dt DESC Limit
                        (select sample_size from settings where id =1) )order by dt desc limit 1) ))
            as slope
            from settings s, temperatures t where t.id = (select MAX(id) from temperatures) """)
        r = cursor.fetchone()
        control_data = {}
        for key in r.keys():
            control_data[key.lower()] = r[key]
        cursor.close()
        return control_data

    def get_temps(self, start_idx):
        if start_idx is None:
            start_idx = 0
        cursor = self.connection.cursor()
        cursor.execute("""select t.id,datetime(t.dt,'localtime'),
            t.temp,s.heat_source,(select round(avg(t.temp),1) from temperatures t where t.id in
            (select id from temperatures ORDER BY dt DESC Limit (select sample_size from settings where id =1))) as avg_temp
            from temperatures t,settings s where t.id > ?""", [start_idx])
        rows = cursor.fetchall()
        temps = []
        for row in rows:
            temps.append([row[0], row[1], row[2], row[3], row[4]])
        return json.dumps(temps)

    def shutdown(self):
        self.connection.close()
        self.profile_connection.close()

    def setup(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute('select count(*) from temperatures')
            # print cursor.fetchone()
        except Exception as e:
            logging.info('Required table not found... creating temperatures table...')
            cursor.execute("""create table temperatures(
                ID INTEGER PRIMARY KEY   AUTOINCREMENT,
                DT DATETIME DEFAULT CURRENT_TIMESTAMP,
                TEMP REAL);""")
            logging.info('done!')
        finally:
            cursor.close()

        cursor = self.connection.cursor()
        try:
            cursor.execute('select count(*) from settings')
            cursor.fetchone()
        except Exception as e:
            logging.info('Required table not found... creating settings table...')
            cursor.execute("""create table settings(
                ID INTEGER PRIMARY KEY   AUTOINCREMENT,
                ENABLED INTEGER,
                TARGET_TEMP REAL,
                HEAT_SOURCE TEXT,
                SAMPLE_SIZE INTEGER,
                TOLERANCE REAL,
                COOL_DURATION INTEGER,
                HEAT_DURATION INTEGER);""")
            cursor.execute("""insert into settings (ENABLED, TARGET_TEMP,
                HEAT_SOURCE,SAMPLE_SIZE, TOLERANCE, COOL_DURATION, HEAT_DURATION )
                values(?,?,?,?,?,?,?);""", ['0', '200', 'off', '20', '5', '30000', '30000'])

            logging.info('done!')
        finally:
            cursor.close()

        profile_cursor = self.profile_connection.cursor()
        try:
            profile_cursor.execute('select count(*) from profiles')
        except Exception as e:
            logging.info('Required table not found... creating profiles table...')
            profile_cursor.execute("""create table profiles(
                ID INTEGER PRIMARY KEY   AUTOINCREMENT,
                NAME TEXT,
                TARGET_TEMP REAL,
                SAMPLE_SIZE INTEGER,
                TOLERANCE REAL,
                COOL_DURATION INTEGER,
                HEAT_DURATION INTEGER);""")
            logging.info('done!')

            logging.info('Required table not found... creating active_profile table...')
            profile_cursor.execute("""create table active_profile(
                ID INTEGER PRIMARY KEY   AUTOINCREMENT, ACTIVE INTEGER) ;""")
            logging.info('done!')

            self.profile_connection.commit()

            # add default sous vide steak profile
            profile_cursor.execute("""insert into profiles (NAME, TARGET_TEMP, SAMPLE_SIZE,
                TOLERANCE, HEAT_DURATION, COOL_DURATION )
                values(?,?,?,?,?,?);""", ['Steak sous vide', '132', '2', '2', '15000', '10000'])

            # add default smoker profile
            profile_cursor.execute("""insert into profiles (NAME, TARGET_TEMP, SAMPLE_SIZE,
                TOLERANCE, COOL_DURATION, HEAT_DURATION )
                values(?,?,?,?,?,?);""", ['Smoker', '225', '10', '5', '60000', '10000'])

            self.profile_connection.commit()
            # set the default active profile
            profile_cursor.execute("""insert into active_profile ( ACTIVE )
                values ( (select MIN(p.id) from profiles p ) );""")

            self.profile_connection.commit()
            self.connection.commit()

            self.apply_active_profile()
            self.connection.commit()

            logging.info('setup done!')
        finally:
            cursor.close()
            profile_cursor.close()


if __name__ == '__main__':
    db = DataStore(setup=True)

    print(db.get_settings())
    print(db.get_profiles())
    print(db.get_profile(1))
    print(db.get_profile(2))
    print(db.get_active_profile())


    db.add_temperature(205 + 12 * random.random())
    db.add_temperature(205 + 12 * random.random())
    # print(db.get_control_data())

    count = 1
    while count < 20000:
        db.add_temperature(205 + 12 * random.random())
        count += 1
        time.sleep(1)
        temps = json.loads(db.get_temps(count - 1))
        print(temps[len(temps) - 1])
        print(db.get_control_data())

    print(db.get_control_data())
    print(db.get_temps(7))

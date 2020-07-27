#!/usr/bin/env python3
# coding: utf-8

import datetime
import pathlib
import time

import pandas as pd
from flask import Flask

app = Flask(__name__,
            static_url_path='',
            static_folder='static',
            template_folder='templates')

log_dir = ''


def load_csv_files():
    df_list = []
    four_days_ago = time.mktime((datetime.date.today() - datetime.timedelta(days=3)).timetuple())

    for f in pathlib.Path('.').glob('{log_dir}/wattchecker-data.csv*'.format(log_dir=log_dir)):
        if f.stat().st_mtime > four_days_ago:
            df_tmp = pd.read_csv(
                f, names=('Time', 'V', 'mA', 'W'), usecols=[0, 3], index_col=0, parse_dates=True
            )
            df_list.append(df_tmp)

    df = pd.concat(df_list, join='inner')
    df.index = df.index.tz_localize(datetime.timezone.utc)
    return df


def dataframe_to_json(df):
    return df['W'].to_json(date_format='iso', orient='split')


# 日本標準時で過去3日間＋今日
def extract_last_3_days(df):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9), 'Asia/Tokyo'))
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    three_days_ago = today - datetime.timedelta(days=3)
    return df.query('@three_days_ago <= Time & Time <= @now')


# 最近12時間のW（1分平均）
def calc_watt_per_minute_last_12_hours(df_total):
    now = datetime.datetime.now(datetime.timezone.utc)
    half_day_ago = now - datetime.timedelta(hours=12)
    return df_total.resample('T').mean().query('@half_day_ago <= Time & Time <= @now')


# 過去3日間＋今日のWh（1時間ごと）
def calc_watt_hour_last_3_days(df_total):
    df = df_total.resample('H').mean()
    return extract_last_3_days(df)


# 過去3日間＋今日のWh（12時間ごと）
def calc_sum_watt_hour_per_12_hours_last_3_days(df_total):
    # UTC15時 (=JST0時) を基準に集計する
    df = df_total.resample('H').mean().resample('12H', label='left', base=15).sum()
    return extract_last_3_days(df)


# 過去3日間＋今日の電気料金（12時間ごと）
def calc_sum_bills_per_12_hours_last_3_days(df_total):
    # UTC15時 (=JST0時) を基準に集計する
    df = df_total.resample('H').mean().resample('12H', label='left', base=15).sum() / 1000 * 25
    return extract_last_3_days(df)


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/data')
def data():
    df_total = load_csv_files()
    df_w_last12hours = calc_watt_per_minute_last_12_hours(df_total)
    df_wh_last3days = calc_watt_hour_last_3_days(df_total)
    df_sum_yen_last3days = calc_sum_bills_per_12_hours_last_3_days(df_total)

    return "{{" \
           "\"wattPerMinuteLast12Hours\": {w_last12hours}, " \
           "\"wattHourLast3Days\": {wh_last3days}, " \
           "\"sumBillsPer12HoursLast3Days\": {sum_yen_last3days}" \
           "}}".format(
        w_last12hours=dataframe_to_json(df_w_last12hours),
        wh_last3days=dataframe_to_json(df_wh_last3days),
        sum_yen_last3days=dataframe_to_json(df_sum_yen_last3days)
    )


def aparse():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'log_dir',
        help='path to log directory.'
    )
    parser.add_argument(
        '-l', '--host', default='127.0.0.1',
        help='the hostname to listen on.'
    )
    parser.add_argument(
        '-p', '--port', default=5000, type=int,
        help='the port of the webserver.'
    )
    return parser.parse_args()


def main():
    args = aparse()
    global log_dir
    log_dir = args.log_dir
    app.run(debug=True, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

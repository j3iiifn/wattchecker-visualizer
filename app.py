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

    return pd.concat(df_list, join='inner')


def dataframe_to_json(df):
    return df['W'].to_json(date_format='iso', orient='split')


def dataframe_to_dict(df):
    return df.to_dict(date_format='iso', orient='split')


# 最近24時間のW（1分平均）
def calc_watt_per_minute_last_24_hours(df_total):
    now = datetime.datetime.now()
    day_ago = now - datetime.timedelta(days=1)
    return df_total.resample('T').mean().query('@day_ago <= Time & Time <= @now')


# 過去3日間＋今日のWh（1時間ごと）
def calc_watt_hour_last_3_days(df_total):
    return df_total.resample('H').mean()


# 過去3日間＋今日のWh（12時間ごと）
def calc_sum_watt_hour_per_12_hours_last_3_days(df_total):
    return df_total.resample('H').mean().resample('12H', label='left', base=15).sum()


# 過去3日間＋今日の電気料金（12時間ごと）
def calc_sum_bills_per_12_hours_last_3_days(df_total):
    return df_total.resample('H').mean().resample('12H', label='left', base=15).sum() / 1000 * 25


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/data')
def get_watt_per_minute_last_24_hours():
    df_total = load_csv_files()
    df_w_last24hours = calc_watt_per_minute_last_24_hours(df_total)
    df_wh_last3days = calc_watt_hour_last_3_days(df_total)
    df_sum_wh_last3days = calc_sum_watt_hour_per_12_hours_last_3_days(df_total)
    df_sum_yen_last3days = calc_sum_bills_per_12_hours_last_3_days(df_total)

    return "{{" \
           "\"wattPerMinuteLast24Hours\": {w_last24hours}, " \
           "\"wattHourLast3Days\": {wh_last3days}, " \
           "\"sumWhPer12HoursLast3Days\": {sum_wh_last3days}, " \
           "\"sumBillsPer12HoursLast3Days\": {sum_yen_last3days}" \
           "}}".format(
        w_last24hours=dataframe_to_json(df_w_last24hours),
        wh_last3days=dataframe_to_json(df_wh_last3days),
        sum_wh_last3days=dataframe_to_json(df_sum_wh_last3days),
        sum_yen_last3days=dataframe_to_json(df_sum_yen_last3days)
    )


def aparse():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'log_dir',
        help='path to log directory.'
    )
    return parser.parse_args()


def main():
    args = aparse()
    global log_dir
    log_dir = args.log_dir
    app.run(debug=True)


if __name__ == "__main__":
    main()

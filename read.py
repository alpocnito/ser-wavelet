import time
import os
import torch
import sounddevice as sd
import influxdb_client
import numpy as np
from analyze import analyze

duration_sec = 2000

# Influxdb stuff
# WARNING: token should be taken from os environment variables, do not leave it as plain text here
org = "mipt"
url="http://influxdb:8086"
bucket = "bucket1"

client = influxdb_client.InfluxDBClient(
    url=url,
    org=org,
    username='admin',
    password='password',
)

if not client.ping():
    print("Failed to establish connection")
    print(client.health())
    exit(1)

read_size_sec = 4
sec_capacity = 44100

def read_data():
    # start = time.time()
    left_data = client.query_api().query_data_frame(
        f'from(bucket:"{bucket}") |> range(start: -4s, stop: -1s) '
        f'|> filter(fn: (r) => r["_measurement"] == "a") '
        f'|> filter(fn: (r) => r["_field"] == "l") '
        f'|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value") '
        f'|> keep(columns: ["l"])'
    )
    # print('request:', time.time() - start)
    # start = time.time()
    read_buf = left_data['l'].values.tolist()
    # print('proc:', time.time() - start)
    return read_buf

while 1:
    ton = analyze(torch.FloatTensor([read_data()]))
    os.system('clear')
    for k, v in ton.items():
        print(f'{k:<10}: ', end ='')
        i = 0
        while v > i:
            print('=', end ='')
            i += 1
        print()

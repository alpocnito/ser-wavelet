import time
import os
import sounddevice as sd
import influxdb_client
import numpy as np
import analyze

duration_sec = 2000

# Influxdb stuff
# WARNING: token should be taken from os environment variables, do not leave it as plain text here
org = "mipt"
token='OyI0ggaJUTvwKgB_F1SEdlF35H01IwBxmmSJl1eyIMEu6QT-LIx-3Hmw4QrvbFTB1ocj3zthyCycTsCb20vv1A=='
url="http://influxdb:8086"
bucket = "bucket1"

client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)

if not client.ping():
    print("Failed to establish connection")
    print(client.health())
    exit(1)


def read_data():
    read_buf = []
    start = time.time()
    left_data = client.query_api().query_stream(
        f'from(bucket:"{bucket}") |> range(start: -1s) '
        f'|> filter(fn: (r) => r["_measurement"] == "a") '
        f'|> filter(fn: (r) => r["_field"] == "l") '
        f'|> map(fn: (r) => ({{r with _value: r._value * 20.0}}))'
    )
    for point in left_data:
        # print(point.get_time().timestamp()*1_000_000_000)
        read_buf.append([point.get_value()])

    if len(read_buf) != 44100:
        add_len = 44100 - len(read_buf)
        if add_len > 0:
            print(f'{add_len = }')
            time.sleep(1)
        read_buf = [*([[0]] * add_len), *read_buf]

    print('read proc:', time.time() - start)
    return np.array(read_buf[:44100])


print(analyze.analyze(read_data()))



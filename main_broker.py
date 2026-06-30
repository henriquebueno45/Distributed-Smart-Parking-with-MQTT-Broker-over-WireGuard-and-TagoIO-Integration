
# MQTT Smart Parking Broker (TagoIO Free Optimized)
import time,json,warnings
import paho.mqtt.client as mqtt
import requests

warnings.filterwarnings("ignore", category=DeprecationWarning)

MQTT_BROKER="localhost"
MQTT_PORT=1883
MQTT_TOPIC="estacionamento1/#"

ENABLE_POST=True
POST_URL="https://api.tago.io/data"
TAGO_DEVICE_TOKEN="95adab15-8f05-4f26-92a7-0a0a73b2263f"

PARKING_RULES={1:60,2:240,3:480}

sensor_stats={}
active_parkings={}
broker_start=time.time()
total_messages=0
total_bytes=0

def safe_json(b):
    try:
        return json.loads(b.decode(errors="replace"))
    except:
        return None

def process_payload(topic,payload):
    global total_messages,total_bytes
    rx=time.time()
    total_messages+=1
    total_bytes+=len(payload)
    d=safe_json(payload)
    if not d: raise ValueError("Invalid JSON")
    for f in ("sensor_id","state","timestamp"):
        if f not in d: raise ValueError(f"Missing {f}")

    sid=d["sensor_id"]; state=int(d["state"])
    plate=d.get("plate"); emp=d.get("employee_type")
    tx=float(d["timestamp"]); seq=d.get("seq")
    host=d.get("hostname","unknown")

    s=sensor_stats.setdefault(sid,{
      "last_latency":None,"last_time":None,"last_seq":None,
      "packets_lost":0,"duplicates":0,"out_of_order":0
    })

    latency=max(0,(rx-tx)*1000)
    inter=None if s["last_time"] is None else (rx-s["last_time"])*1000
    s["last_time"]=rx
    jitter=None if s["last_latency"] is None else abs(latency-s["last_latency"])
    s["last_latency"]=latency

    loss=0
    if seq is not None:
        seq=int(seq)
        if s["last_seq"] is not None:
            exp=s["last_seq"]+1
            if seq>exp:
                loss=seq-exp
                s["packets_lost"]+=loss
            elif seq==s["last_seq"]:
                s["duplicates"]+=1
            elif seq<s["last_seq"]:
                s["out_of_order"]+=1
        s["last_seq"]=seq

    allowed=PARKING_RULES.get(emp)
    if state==1:
        active_parkings[sid]={"arrival":rx,"allowed":allowed}
    elif state==0:
        active_parkings.pop(sid,None)

    elapsed=remaining=arrival=None
    expired=False
    if sid in active_parkings:
        p=active_parkings[sid]
        arrival=p["arrival"]
        elapsed=(rx-arrival)/60
        if p["allowed"] is not None:
            remaining=max(0,p["allowed"]-elapsed)
            expired=elapsed>=p["allowed"]

    uptime=rx-broker_start
    msg_rate=total_messages/uptime if uptime else 0
    throughput_bps=(total_bytes*8)/uptime if uptime else 0

    return [
      {"variable":f"sensor_id_{sid}","value":sid,"group":sid},
      {"variable":f"state_{sid}","value":state,"group":sid},
      {"variable":f"plate_{sid}","value":plate,"group":sid},
      {"variable":f"employee_type_{sid}","value":emp,"group":sid},
      {"variable":f"allowed_minutes_{sid}","value":allowed,"group":sid},
      {"variable":f"elapsed_minutes_{sid}","value":elapsed,"group":sid},
      {"variable":f"remaining_minutes_{sid}","value":remaining,"group":sid},
      {"variable":f"expired_{sid}","value":expired,"group":sid},
      {"variable":f"arrival_timestamp_{sid}","value":arrival,"group":sid},
      {"variable":"hostname","value":host,"group":sid},
      {"variable":"latency_ms","value":latency,"group":sid},
      {"variable":"latency_variation_ms","value":jitter,"group":sid},
      {"variable":"interarrival_ms","value":inter,"group":sid},
      {"variable":"packet_loss_current","value":loss,"group":sid},
      {"variable":"packet_loss_total","value":s["packets_lost"],"group":sid},
      {"variable":"duplicates","value":s["duplicates"],"group":sid},
      {"variable":"out_of_order","value":s["out_of_order"],"group":sid},
      {"variable":"msg_rate","value":msg_rate,"group":sid},
      {"variable":"throughput_bps","value":throughput_bps,"group":sid},
      {"variable":"uptime_seconds","value":uptime,"group":sid},
    ]

def on_connect(c,u,f,rc):
    print("Connected",rc)
    c.subscribe(MQTT_TOPIC)

def on_message(c,u,msg):
    try:
        payload=process_payload(msg.topic,msg.payload)
        if ENABLE_POST:
            r=requests.post(POST_URL,json=payload,headers={
                "Content-Type":"application/json",
                "Device-Token":TAGO_DEVICE_TOKEN},timeout=5)
            if r.status_code not in (200,201,202):
                print("TagoIO:",r.status_code,r.text)
    except Exception as e:
        print("Error:",e)

client=mqtt.Client()
client.on_connect=on_connect
client.on_message=on_message
print("Starting broker...")
client.connect(MQTT_BROKER,MQTT_PORT,60)
client.loop_forever()

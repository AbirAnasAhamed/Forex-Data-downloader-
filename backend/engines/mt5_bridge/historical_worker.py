import zmq
import time
import json
import MetaTrader5 as mt5
from datetime import datetime, timedelta

ZMQ_HIST_SUB_PORT = 7780  # Receive historical fetch commands
ZMQ_HIST_PUB_PORT = 7781  # Send historical chunks back

def init_mt5(server, login, password):
    if not mt5.initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe", server=server, login=int(login), password=password, portable=True):
        print("HistWorker: MT5 init failed, error =", mt5.last_error())
        return False
    return True

def fetch_history_chunked(socket, symbol, start_time_ms, end_time_ms, chunk_days=30):
    """
    Fetch history in chunks to avoid RAM overload.
    """
    start_dt = datetime.fromtimestamp(start_time_ms / 1000)
    end_dt = datetime.fromtimestamp(end_time_ms / 1000)
    
    current_dt = start_dt
    
    total_ticks_sent = 0
    
    while current_dt < end_dt:
        next_dt = min(current_dt + timedelta(days=chunk_days), end_dt)
        print(f"HistWorker: Fetching chunk {current_dt} to {next_dt}...")
        
        ticks = mt5.copy_ticks_range(symbol, current_dt, next_dt, mt5.COPY_TICKS_ALL)
        
        if ticks is not None and len(ticks) > 0:
            # Convert to list of dicts for JSON
            chunk_data = []
            for t in ticks:
                chunk_data.append({
                    "time_msc": int(t['time_msc']),
                    "bid": float(t['bid']),
                    "ask": float(t['ask']),
                    "volume": int(t['volume'])
                })
            
            # Send chunk
            msg = {
                "status": "chunk",
                "symbol": symbol,
                "data": chunk_data
            }
            socket.send_string(json.dumps(msg))
            total_ticks_sent += len(ticks)
            print(f"HistWorker: Sent chunk of {len(ticks)} ticks.")
        else:
            print(f"HistWorker: No ticks found in chunk {current_dt} to {next_dt}")
            
        current_dt = next_dt
        time.sleep(0.5) # Small pause to let ZMQ clear buffers
        
    # Send completion signal
    socket.send_string(json.dumps({
        "status": "complete",
        "symbol": symbol,
        "total_ticks": total_ticks_sent
    }))
    print(f"HistWorker: History fetch complete for {symbol}. Total: {total_ticks_sent}")

def main():
    context = zmq.Context()
    
    cmd_socket = context.socket(zmq.SUB)
    cmd_socket.bind(f"tcp://*:{ZMQ_HIST_SUB_PORT}")
    cmd_socket.setsockopt_string(zmq.SUBSCRIBE, "")
    
    data_socket = context.socket(zmq.PUB)
    data_socket.bind(f"tcp://*:{ZMQ_HIST_PUB_PORT}")
    
    print("MT5 Historical Worker Started. Waiting for fetch commands...")
    
    while True:
        try:
            msg = cmd_socket.recv_string()
            cmd = json.loads(msg)
            
            if cmd.get("action") == "fetch":
                if init_mt5(cmd["server"], cmd["login"], cmd["password"]):
                    fetch_history_chunked(
                        data_socket,
                        cmd["symbol"],
                        cmd["start_time"],
                        cmd["end_time"],
                        chunk_days=30
                    )
                    mt5.shutdown()
        except Exception as e:
            print(f"HistWorker Error: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    main()

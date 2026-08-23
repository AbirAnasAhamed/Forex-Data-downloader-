import zmq
import time
import MetaTrader5 as mt5
import json

ZMQ_SUB_PORT = 7776  # Receive commands from backend
ZMQ_PUB_PORT = 7777  # Publish ticks to backend

def init_mt5(server, login, password):
    print(f"Attempting to initialize MT5 for server: {server}, login: {login}")
    try:
        login_int = int(login)
    except ValueError:
        print(f"Error: Login ID must be a number, got '{login}'")
        return False
        
    if not mt5.initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe", server=server, login=login_int, password=password, portable=True):
        print("initialize() failed, error code =", mt5.last_error())
        return False
    print("MT5 successfully initialized and logged in!")
    return True

def main():
    context = zmq.Context()
    
    # Subscriber socket for receiving login commands
    command_socket = context.socket(zmq.SUB)
    command_socket.bind(f"tcp://*:{ZMQ_SUB_PORT}")
    command_socket.setsockopt_string(zmq.SUBSCRIBE, "")
    
    # Publisher socket for sending live ticks
    tick_socket = context.socket(zmq.PUB)
    tick_socket.bind(f"tcp://*:{ZMQ_PUB_PORT}")
    
    print("MT5 Bridge Engine Started. Waiting for connection commands...")
    
    connected_symbol = None
    last_time_msc = 0
    
    while True:
        # 1. Non-blocking check for new commands from backend
        try:
            msg = command_socket.recv_string(flags=zmq.NOBLOCK)
            command_data = json.loads(msg)
            
            if command_data.get("action") == "connect":
                success = init_mt5(
                    command_data["server"], 
                    command_data["login"], 
                    command_data["password"]
                )
                if success:
                    if connected_symbol:
                        mt5.market_book_release(connected_symbol)
                    connected_symbol = command_data.get("symbol")
                    if not connected_symbol:
                        print("Error: No symbol provided for connect command.")
                        continue
                    mt5.symbol_select(connected_symbol, True)
                    mt5.market_book_add(connected_symbol) # Subscribe to L2 Snapshot
                    
            elif command_data.get("action") == "disconnect":
                if connected_symbol:
                    mt5.market_book_release(connected_symbol)
                mt5.shutdown()
                connected_symbol = None
                print("Disconnected from MT5.")
                
        except zmq.Again:
            pass  # No new message

        # 2. If connected, fetch live tick and publish
        if connected_symbol:
            # Fetch Live Tick
            tick = mt5.symbol_info_tick(connected_symbol)
            if tick and tick.time_msc > last_time_msc:
                last_time_msc = tick.time_msc
                tick_dict = {
                    "type": "tick",
                    "symbol": connected_symbol,
                    "time": tick.time,
                    "time_msc": tick.time_msc,
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "volume": tick.volume
                }
                tick_socket.send_string(json.dumps(tick_dict))
                
            # Fetch L2 Snapshot (Market Book)
            book_items = mt5.market_book_get(connected_symbol)
            if book_items:
                bids = [{"price": item.price, "volume": item.volume} for item in book_items if item.type == mt5.BOOK_TYPE_BUY]
                asks = [{"price": item.price, "volume": item.volume} for item in book_items if item.type == mt5.BOOK_TYPE_SELL]
                l2_dict = {
                    "type": "l2_snapshot",
                    "symbol": connected_symbol,
                    "time_msc": int(time.time() * 1000), # Approximation as MT5 book doesn't give exact timestamp
                    "bids": bids,
                    "asks": asks
                }
                tick_socket.send_string(json.dumps(l2_dict))
                
        # Sleep briefly to avoid high CPU usage
        time.sleep(0.01)

if __name__ == "__main__":
    main()

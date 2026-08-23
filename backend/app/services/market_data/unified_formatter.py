class UnifiedTickFormatter:
    """
    Normalizes tick data from different engines (MT5, cTrader) 
    into a unified standard JSON format.
    """
    @staticmethod
    def format_tick(engine_type: str, raw_msg: dict) -> dict:
        msg_type = raw_msg.get("type", "tick")
        
        if msg_type == "l2_snapshot":
            return {
                "type": "l2_snapshot",
                "symbol": raw_msg.get("symbol", "UNKNOWN"),
                "timestamp": raw_msg.get("time_msc", 0),
                "bids": raw_msg.get("bids", []),
                "asks": raw_msg.get("asks", []),
                "source": engine_type
            }
        else:
            return {
                "type": "tick",
                "symbol": raw_msg.get("symbol", "UNKNOWN"),
                "timestamp": raw_msg.get("time_msc", 0),
                "bid": float(raw_msg.get("bid", 0.0)),
                "ask": float(raw_msg.get("ask", 0.0)),
                "volume": int(raw_msg.get("volume", 0)),
                "source": engine_type
            }

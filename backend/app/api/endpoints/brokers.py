from fastapi import APIRouter

router = APIRouter()

# In a real top-tier hedge fund, this list might be fetched from a database
# However, storing static configuration lists in memory is highly efficient and standard practice.
BROKERS_DB = {
    "mt5": [
        {"id": "exness_mt5", "name": "Exness", "default_server": "Exness-MT5Trial6"},
        {"id": "icmarkets_mt5", "name": "IC Markets", "default_server": "ICMarkets-MT5-Demo"},
        {"id": "xm_mt5", "name": "XM", "default_server": "XMGlobal-MT5 4"},
        {"id": "octafx_mt5", "name": "OctaFX", "default_server": "OctaFX-Demo"},
        {"id": "fbs_mt5", "name": "FBS", "default_server": "FBS-Demo"}
    ],
    "ctrader": [
        {"id": "icmarkets_ctrader", "name": "IC Markets", "default_server": ""},
        {"id": "pepperstone_ctrader", "name": "Pepperstone", "default_server": ""},
        {"id": "fxpro_ctrader", "name": "FxPro", "default_server": ""},
        {"id": "fondex_ctrader", "name": "Fondex", "default_server": ""},
        {"id": "axiory_ctrader", "name": "Axiory", "default_server": ""}
    ]
}

@router.get("/list")
async def get_brokers():
    """
    Returns the list of supported brokers categorized by the trading engine they use.
    """
    return BROKERS_DB

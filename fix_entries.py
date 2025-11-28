"""
Fix entries with correct competitor names
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)

# Mapping of entry IDs to correct competitor names
FIXES = {
    132: "Revolut",
    134: "Exodus",
    135: "IDRX",
    137: "Thunes",
    138: "Standard Chartered",
    139: "Hashkey",
    141: "Market Overview",  # Stablecoin market map - not a specific competitor
    142: "Tria",
    145: "Ripple",
    149: "Rain",
    150: "Crypto Cards Overview",  # General analytics
    151: "Hashkey",
    152: "BVNK",
    153: "BVNK",
    155: "Modern Treasury",
    156: "Tempo",
    158: "Circle",
    159: "AliPay",
    160: "Unknown",  # No article found
    162: "BVNK",
    163: "Rain",
    164: "Conduit",
    166: "TerraPay",
    167: "Coinbase",
    168: "Unknown",  # Spanish post, unclear
    171: "NuBank",
    172: "Visa",
    174: "Jeeves",
    175: "StraitsX",
    178: "Fireblocks",
    180: "Rain",
    181: "Ripple",
    182: "Wirex",
    183: "BVNK",
    185: "Tempo",
    187: "BVNK",
    188: "PayPal",
    190: "Rain",
    191: "Market Overview",  # LATAM landscape overview
    192: "ZeroHash",
    193: "Adyen",
    195: "Visa",
    196: "Karsa",
    199: "Airwallex",  # Jack Zhang is Airwallex CEO
    200: "Coinbase",
    203: "Societe Generale",
    204: "Market Overview",  # Multiple companies mentioned
    205: "Walmart",
    206: "PalmPay",
    207: "Crossmint",
    208: "M-Pesa",
    209: "Paysafe",
    211: "Mercury",
    213: "Klarna",
    217: "Moonpay",
    219: "Crypto.com",
    223: "Marqeta",
    225: "Nubank",
    226: "Shift4",
    228: "Crypto.com",
    229: "ZeroHash",
    230: "Market Overview",
    231: "PayPal",
    232: "M-Pesa",
    233: "Unknown",  # FT paywall
    234: "Felix Pago",
    235: "Bridge",
    237: "Square",
    238: "Wise",
    239: "Market Overview",
    240: "Moonpay",
    241: "Bridge",
    242: "M-Pesa",
    244: "Ripple",
    246: "Anchorage",
    250: "Payoneer",
    251: "Wise",
    252: "Finix",
    254: "Visa",
    255: "Bridge",
    256: "Coinbase",
    258: "DolarApp",
}

def fix_all():
    """Update all entries with correct competitor names"""
    print("Updating competitor entries...")

    success = 0
    errors = 0

    for entry_id, correct_name in FIXES.items():
        try:
            supabase.table("competitor_intel").update({
                "competitor": correct_name
            }).eq("id", entry_id).execute()
            print(f"  Updated ID {entry_id} -> {correct_name}")
            success += 1
        except Exception as e:
            print(f"  Error updating ID {entry_id}: {e}")
            errors += 1

    print(f"\nDone! Updated: {success}, Errors: {errors}")


if __name__ == "__main__":
    fix_all()

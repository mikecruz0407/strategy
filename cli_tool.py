import json
import yfinance as yf
from analyze import analyze_stock  # import from earlier script

FAV_FILE = "favorites.json"


def load_favorites():
    try:
        with open(FAV_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_favorites(favs):
    with open(FAV_FILE, "w") as f:
        json.dump(favs, f, indent=2)


def cli():
    print("=== 🛠️ Stock Analyzer CLI ===")
    while True:
        choice = input(
            "\nType a stock symbol to analyze (or type 'list', 'add', 'remove', or 'exit'): ").strip().upper()

        if choice == "EXIT":
            break
        elif choice == "LIST":
            favs = load_favorites()
            print("\n⭐ Favorites:")
            for s in favs:
                print(f"- {s}")
        elif choice == "ADD":
            symbol = input("Enter symbol to add: ").strip().upper()
            favs = load_favorites()
            if symbol not in favs:
                favs.append(symbol)
                save_favorites(favs)
                print(f"✅ Added {symbol} to favorites.")
            else:
                print("⚠️ Already in favorites.")
        elif choice == "REMOVE":
            symbol = input("Enter symbol to remove: ").strip().upper()
            favs = load_favorites()
            if symbol in favs:
                favs.remove(symbol)
                save_favorites(favs)
                print(f"🗑️ Removed {symbol}.")
            else:
                print("⚠️ Not in favorites.")
        else:
            result = analyze_stock(choice)
            if result:
                print(f"\n📊 {choice} SIGNAL:")
                print(f"Price: ${result['price']}")
                print(f"Calls: {result['calls']:,}, Puts: {result['puts']:,}")
                print(f"Signal: 🔔 {result['signal']}")
            else:
                print("❌ Could not analyze that stock.")


if __name__ == "__main__":
    cli()

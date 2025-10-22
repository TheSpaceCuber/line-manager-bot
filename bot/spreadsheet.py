import pandas as pd
from bot.config import Config

class SpreadsheetLoader:
    """Loads player, group, and config data from a public Google Sheet."""
    
    def __init__(self):
        if not Config.GOOGLE_SHEETS_URL:
            raise ValueError("GOOGLE_SHEETS_URL is not set in the configuration.")
        base = Config.GOOGLE_SHEETS_URL.split("/edit")[0]
        self.urls = {
            "players": f"{base}/gviz/tq?tqx=out:csv&gid={Config.GOOGLE_SHEETS_PLAYERS_GID}",
            "groups": f"{base}/gviz/tq?tqx=out:csv&gid={Config.GOOGLE_SHEETS_GROUPS_GID}",
            "config": f"{base}/gviz/tq?tqx=out:csv&gid={Config.GOOGLE_SHEETS_CONFIG_GID}",
        }
    
    def load_player_data(self) -> pd.DataFrame:
        return self.load_sheet("players")

    def load_sheet(self, name: str) -> pd.DataFrame:
        url = self.urls.get(name)
        if not url:
            raise ValueError(f"Unknown sheet name: {name}")
        try:
            df = pd.read_csv(url)
            return df
        except Exception as e:
            print(f"❌ Failed to load sheet {name}: {e}")
            return pd.DataFrame()

    def load_all(self):
        """Return dict of all sheets: players, groups, config."""
        return {
            "players": self.load_sheet("players"),
            "groups": self.load_sheet("groups"),
            "config": self.load_sheet("config"),
        }


if __name__ == "__main__":
    loader = SpreadsheetLoader()
    sheets = loader.load_player_data()
    print(sheets.head())
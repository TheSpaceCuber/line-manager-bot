import random
import numpy as np
import pandas as pd
from bot.spreadsheet import SpreadsheetLoader

class Splitter:
    def split_lines(self, attending_players: list[str], iterations: int = 10000) -> tuple[list[str], list[str], list[str]]:
        """
        Splits a list of attending players into 2 balanced lines using random search optimization.
        Balances on role, score, and tall players.
        Returns (line1_names, line2_names, stats).
        """
        loader = SpreadsheetLoader()
        sheet = loader.load_player_data()

        # Match players from spreadsheet
        matched_players = sheet[sheet['Countmeinbot Name'].isin(attending_players)].copy()
        if matched_players.empty:
            raise ValueError("No matching players found in spreadsheet!")

        # Normalize and clean up columns
        matched_players.rename(columns={'Score (AVG)': 'Score'}, inplace=True)
        matched_players['Tall'] = matched_players['Tall'].str.upper().eq('Y').astype(int)

        line1, line2, stats = self.balance_lines(matched_players, iterations)
        return line1, line2, stats


    def balance_lines(self, players_df: pd.DataFrame, iterations: int = 1000) -> tuple[list[str], list[str], list[str]]:
        """
        Randomly searches for the best split of players into two balanced lines.
        Returns (line1_names, line2_names, stats).
        """
        best_score = float('inf')
        best_split = None
        n = len(players_df)
        half = n // 2

        # Precompute handler flags
        players_df['is_handler'] = players_df['Role'].str.lower().str.contains('handler')

        for _ in range(iterations):
            shuffled = players_df.sample(frac=1, random_state=random.randint(0, 999999))
            line1_df = shuffled.iloc[:half]
            line2_df = shuffled.iloc[half:]

            # Evaluate split
            score_diff = abs(line1_df['Score'].sum() - line2_df['Score'].sum())
            handler_diff = abs(line1_df['is_handler'].sum() - line2_df['is_handler'].sum())
            tall_diff = abs(line1_df['Tall'].sum() - line2_df['Tall'].sum())

            # Weighted objective function
            total_diff = (score_diff * 1.5) + (handler_diff * 2.0) + (tall_diff * 1.0)

            if total_diff < best_score:
                best_score = total_diff
                best_split = (line1_df, line2_df)

        if best_split is None:
            raise ValueError("Failed to find a valid split of players.")
        
        line1_df, line2_df = best_split
        line1_names = line1_df['Countmeinbot Name'].tolist()
        line2_names = line2_df['Countmeinbot Name'].tolist()

        # ---- Compute stats ----
        def team_stats(df, label):
            return (
                f"📊 *{label} Stats:*",
                f"Handlers: {df['is_handler'].sum()}",
                f"Total Score: {df['Score'].sum():.2f}",
                f"Gender → M: {(df['Gender'].str.upper() == 'M').sum()}, F: {(df['Gender'].str.upper() == 'F').sum()}",
                f"Tall Players: {df['Tall'].sum()}",
                ""
            )

        stats = [
            *team_stats(line1_df, "Line X"),
            *team_stats(line2_df, "Line Y"),
            f"⚖️ *Score difference:* {abs(line1_df['Score'].sum() - line2_df['Score'].sum()):.2f}",
            f"⚖️ *Handler difference:* {abs(line1_df['is_handler'].sum() - line2_df['is_handler'].sum())}",
            f"⚖️ *Tall difference:* {abs(line1_df['Tall'].sum() - line2_df['Tall'].sum())}",
        ]

        return line1_names, line2_names, stats


    def handle_special_rules(self) -> None:
        """Handles the rules for splitting players into lines."""
        pass

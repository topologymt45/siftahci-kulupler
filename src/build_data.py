"""Siftahçı Kulüpler - veri hazırlama.

data/raw/ içindeki transfermarkt-datasets CSV'lerinden şu dosyaları üretir:
  data/processed/firsts.parquet   -> her (kategori, varyant, oyuncu[, sezon]) için ilk gol ve golü YİYEN takım
  data/processed/denoms.parquet   -> kulüp başına maç sayısı ve yenen gol sayısı (oranlar için)
  data/processed/clubs.parquet    -> kulüp adı ve ülkesi

Çalıştırma:  python src/build_data.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

# UEFA kulüp turnuvaları
UEFA = {
    "CL": "sl", "CLQ": "sl",          # Şampiyonlar Ligi (+ eleme)
    "EL": "al", "ELQ": "al",          # Avrupa Ligi (+ eleme)
    "UCOL": "kl", "ECLQ": "kl",       # Konferans Ligi (+ eleme)
    "USC": "super",                   # UEFA Süper Kupa
}
QUALIFIERS = {"CLQ", "ELQ", "ECLQ"}

# kategori -> (turnuva filtresi, elemeler için ayrı varyant var mı)
CATEGORIES = {
    "kariyer": None,                   # tüm kulüp turnuvaları
    "lig": "domestic_league",
    "avrupa": {"CL", "CLQ", "EL", "ELQ", "UCOL", "ECLQ"},
    "sl": {"CL", "CLQ"},
    "al": {"EL", "ELQ"},
    "kl": {"UCOL", "ECLQ"},
}
EURO_CATS = {"avrupa", "sl", "al", "kl"}


SHORT_NAMES = {
    "Panthessalonikios Athlitikos Omilos Konstantinoupoliton": "PAOK",
    "Beşiktaş Jimnastik Kulübü": "Beşiktaş",
    "Fenerbahce": "Fenerbahçe",
    "Associazione Sportiva Roma": "AS Roma",
    "Bologna Football Club 1909": "Bologna",
    "Sportklub Puntigamer Sturm Graz": "Sturm Graz",
    "Fußballclub Red Bull Salzburg": "RB Salzburg",
    "Sarpsborg 08 Fotballforening": "Sarpsborg 08",
    "Djurgårdens Idrottsförening": "Djurgården",
    "Idrottsföreningen Elfsborg": "Elfsborg",
    "Idrottsföreningen  Brommapojkarna": "Brommapojkarna",
    "Olympiakos Syndesmos Filathlon Peiraios": "Olympiakos",
    "Panathinaikos Athlitikos Omilos": "Panathinaikos",
    "Athlitiki Enosi Konstantinoupoleos": "AEK Atina",
    "Omilos Filathlon Irakliou FC": "OFI Girit",
    'Футбольный клуб "Локомотив" Москва': "Lokomotiv Moskova",
    "AO FK Zenit Sankt-Peterburg": "Zenit",
    "PFK Krylya Sovetov Samara": "Krylya Sovetov",
    "Royal Charleroi Sporting Club": "Charleroi",
    "Inverness Caledonian Thistle FC": "Inverness CT",
    "Gençlerbirliği Spor Kulübü": "Gençlerbirliği",
    # Türkçe karakterler
    "Basaksehir FK": "Başakşehir", "Caykur Rizespor": "Çaykur Rizespor", "Kasimpasa": "Kasımpaşa",
    "Balikesirspor": "Balıkesirspor", "Elazigspor": "Elazığspor", "Eskisehirspor": "Eskişehirspor",
    "Istanbulspor": "İstanbulspor", "Gaziantepspor (- 2020)": "Gaziantepspor", "MKE Ankaragücü": "Ankaragücü",
}
STRIP = [
    "Football Club", "Fotballforening", "Fotballklubb", "Idrottsförening", "Fodboldklub",
    "Futebol Clube", "Futbol Kulübü", "Spor Kulübü", "Calcio", "Associazione Calcio",
    "Società Sportiva", "Sport Lisboa e", "Futbolo klubas", "Fußball-Club", "Fußballclub",
]


def short_name(name):
    if name in SHORT_NAMES:
        return SHORT_NAMES[name]
    if len(name) <= 26:
        return name
    out = name
    for s in STRIP:
        out = out.replace(s, "")
    out = " ".join(out.split())
    return out or name


def load():
    comps = pd.read_csv(RAW / "competitions.csv")
    games = pd.read_csv(
        RAW / "games.csv",
        usecols=["game_id", "competition_id", "season", "date", "home_club_id", "away_club_id",
                 "home_club_name", "away_club_name", "competition_type"],
        parse_dates=["date"],
    )
    ev = pd.read_csv(
        RAW / "game_events.csv",
        usecols=["game_id", "date", "minute", "type", "club_id", "player_id", "description"],
        parse_dates=["date"],
    )
    # competitions.csv'de olmayan turnuvalar
    extra = pd.DataFrame([
        ("CGB", "efl-cup", "domestic_cup", "England", "europa"),
        ("POCP", "taca-de-portugal", "domestic_cup", "Portugal", "europa"),
        ("UKRS", "ukrainian-super-cup", "other", "Ukraine", "europa"),
        ("COL1", "liga-dimayor", "domestic_league", "Colombia", "amerika"),
        ("KLUB", "fifa-club-world-cup", "other", None, "fifa"),
    ], columns=["competition_id", "name", "type", "country_name", "confederation"])
    comps = pd.concat([comps, extra[~extra.competition_id.isin(comps.competition_id)]], ignore_index=True)
    games["competition_type"] = games.competition_type.fillna(games.competition_id.map(comps.set_index("competition_id").type))
    players = pd.read_csv(RAW / "players.csv", usecols=["player_id", "name", "date_of_birth", "country_of_citizenship"])
    lineups = pd.read_csv(RAW / "game_lineups.csv", usecols=["game_id", "player_id", "player_name"])
    apps = pd.read_csv(RAW / "appearances.csv", usecols=["game_id", "player_id", "player_name"])
    return comps, games, ev, players, lineups, apps


def club_table(comps, games):
    """Her kulübün adı, ülkesi ve Avrupalı olup olmadığı."""
    long = pd.concat([
        games[["game_id", "competition_id", "competition_type", "home_club_id", "home_club_name"]]
        .rename(columns={"home_club_id": "club_id", "home_club_name": "club_name"}),
        games[["game_id", "competition_id", "competition_type", "away_club_id", "away_club_name"]]
        .rename(columns={"away_club_id": "club_id", "away_club_name": "club_name"}),
    ])
    long = long[long.competition_type != "national_team_competition"]
    long = long.merge(comps[["competition_id", "country_name", "confederation"]], on="competition_id", how="left")

    # isim: en sık görülen isim, uzunsa kısaltılır
    names = long.dropna(subset=["club_name"]).groupby("club_id").club_name.agg(lambda s: s.mode().iat[0])
    names = names.map(short_name)

    # ülke: kulübün oynadığı ulusal turnuvalarda en sık görülen ülke
    dom = long[long.country_name.notna()]
    country = dom.groupby("club_id").country_name.agg(lambda s: s.mode().iat[0])

    # Avrupalı mı: Avrupa'daki bir ulusal turnuvada veya UEFA turnuvasında oynamış
    is_eu_dom = dom[dom.confederation == "europa"].club_id.unique()
    is_uefa = long[long.competition_id.isin(UEFA)].club_id.unique()
    non_eu_dom = dom[dom.confederation != "europa"].club_id.unique()

    clubs = pd.DataFrame({"club_id": long.club_id.unique()})
    clubs["club_name"] = clubs.club_id.map(names)
    clubs["country"] = clubs.club_id.map(country)
    clubs["european"] = clubs.club_id.isin(is_eu_dom) | (clubs.club_id.isin(is_uefa) & ~clubs.club_id.isin(non_eu_dom))
    clubs.loc[clubs.european & clubs.country.isna(), "country"] = "Bilinmiyor"
    return clubs


def goal_table(games, ev):
    """Kendi kalesine goller hariç tüm kulüp golleri + golü yiyen takım."""
    g = ev[ev.type == "Goals"].copy()
    desc = g.description.fillna("")
    g["own_goal"] = desc.str.contains("Own-goal", regex=False)
    g["penalty"] = desc.str.split(",").str[1].str.strip().eq("Penalty")
    g = g.drop(columns=["type", "description", "date"])
    g = g.merge(games, on="game_id", how="inner")
    g = g[g.competition_type != "national_team_competition"]
    # normal golde club_id = golü atan takım -> rakip golü yiyen
    g["conceding_club_id"] = g.away_club_id.where(g.club_id == g.home_club_id, g.home_club_id)
    g = g[(g.club_id == g.home_club_id) | (g.club_id == g.away_club_id)]
    g = g.rename(columns={"club_id": "scoring_club_id"})
    return g


def first_seen(games, lineups, apps, ev):
    """Her oyuncunun veride göründüğü her maç (kadro, maç kaydı veya olay)."""
    seen = pd.concat([lineups[["game_id", "player_id"]], apps[["game_id", "player_id"]], ev[["game_id", "player_id"]]]).drop_duplicates()
    seen = seen.merge(games[["game_id", "competition_id", "competition_type", "season", "date"]], on="game_id")
    return seen[seen.competition_type != "national_team_competition"]


# Sayılan maçlar: ligler (Belçika play-off'ları dahil) + ŞL / AL / KL ve elemeleri.
# Yerel kupalar, süper kupalar, UEFA Süper Kupa ve Kulüpler Dünya Kupası sayılmaz.
LEAGUE_PLAYOFFS = {"EJPL", "POBE", "BPO4"}
UEFA_CUPS = {"CL", "CLQ", "EL", "ELQ", "UCOL", "ECLQ"}


def is_league(df):
    return (df.competition_type == "domestic_league") | df.competition_id.isin(LEAGUE_PLAYOFFS)


def counted(df):
    return is_league(df) | df.competition_id.isin(UEFA_CUPS)


def in_category(df, cat, include_qual=True):
    if cat == "kariyer":
        mask = counted(df)
    elif cat == "lig":
        mask = is_league(df)
    else:
        mask = df.competition_id.isin(CATEGORIES[cat])
    if not include_qual:
        mask &= ~df.competition_id.isin(QUALIFIERS)
    return mask


# Analize giren 9 lig: siftahçı kulüp, o sezon bu liglerden birinde oynuyor olmalı
NINE_LEAGUES = {"GB1": "England", "IT1": "Italy", "ES1": "Spain", "L1": "Germany", "FR1": "France",
                "PO1": "Portugal", "BE1": "Belgium", "NL1": "Netherlands", "TR1": "Türkiye"}
DATA_START = pd.Timestamp("2012-07-01")
MAX_DEBUT_AGE = 21      # kariyer / lig: veride ilk görünme yaşı en fazla
MAX_AGE_AT_START = 20   # Avrupa: veri başladığında en fazla bu yaşta olmalı
MAX_GAP_DAYS = 200      # kariyer / lig: ilk golden önce veride bu kadar günden uzun boşluk olmamalı


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    comps, games, ev, players, lineups, apps = load()
    clubs = club_table(comps, games)
    goals = goal_table(games, ev)
    seen = first_seen(games, lineups, apps, ev).sort_values("date")

    # 9 lig üyeliği: (kulüp, sezon)
    lg = games[games.competition_id.isin(NINE_LEAGUES)]
    member = pd.concat([lg[["home_club_id", "season", "competition_id"]].rename(columns={"home_club_id": "club_id"}),
                        lg[["away_club_id", "season", "competition_id"]].rename(columns={"away_club_id": "club_id"})]
                       ).drop_duplicates(["club_id", "season"])
    member_keys = set(zip(member.club_id, member.season))
    club_league = member.sort_values("season").drop_duplicates("club_id", keep="last").set_index("club_id").competition_id
    clubs["in_scope"] = clubs.club_id.isin(club_league.index)
    clubs.loc[clubs.in_scope, "country"] = clubs.club_id.map(club_league).map(NINE_LEAGUES)

    first_cov = games.groupby("competition_id").season.min()
    dob = pd.to_datetime(players.drop_duplicates("player_id").set_index("player_id").date_of_birth, errors="coerce")
    first_any = seen.drop_duplicates("player_id").set_index("player_id").date
    debut_age = (first_any - first_any.index.map(dob)).dt.days / 365.25
    young_debut = set(debut_age[debut_age <= MAX_DEBUT_AGE].index)
    age_at_start = (DATA_START - dob).dt.days / 365.25
    young_at_start = set(age_at_start[age_at_start <= MAX_AGE_AT_START].index)

    real = goals[~goals.own_goal & counted(goals)].sort_values(["date", "game_id", "minute"])
    seen_dates = seen[["player_id", "date"]].drop_duplicates().sort_values(["player_id", "date"])

    def gap_players(first_goal_date):
        """İlk golden önce veride uzun süre görünmeyen oyuncular (arada kapsanmayan bir ligde oynamış olabilir)."""
        sd = seen_dates[seen_dates.date <= seen_dates.player_id.map(first_goal_date)]
        gap = sd.groupby("player_id").date.diff().dt.days
        return set(sd.player_id[gap > MAX_GAP_DAYS])

    rows = []
    for cat in CATEGORIES:
        qual_opts = [True, False] if cat in EURO_CATS else [True]
        for include_qual in qual_opts:
            # bu kategorideki ilk maçı, turnuvanın veride başladığı sezondaysa: emin değiliz
            s = seen[in_category(seen, cat, include_qual)]
            fs = s.drop_duplicates("player_id")[["player_id", "competition_id", "season"]]
            unsure = set(fs[fs.season == fs.competition_id.map(first_cov)].player_id)

            for include_pen in (True, False):
                gsub = real[in_category(real, cat, include_qual)]
                if not include_pen:
                    gsub = gsub[~gsub.penalty]
                first = gsub.drop_duplicates("player_id").copy()
                if cat in EURO_CATS:
                    sure = first.player_id.isin(young_at_start)
                else:
                    gaps = gap_players(first.set_index("player_id").date)
                    sure = first.player_id.isin(young_debut) & ~first.player_id.isin(gaps)
                first["censored"] = first.player_id.isin(unsure) | ~sure
                first["category"] = cat
                first["include_qual"] = include_qual
                first["include_pen"] = include_pen
                rows.append(first)

    # sezonun ilk golü: sezon verinin içinde, emin olmak için ek kural gerekmez
    for include_pen in (True, False):
        gsub = real if include_pen else real[~real.penalty]
        first = gsub.drop_duplicates(["player_id", "season"]).copy()
        first["category"] = "sezon"
        first["include_qual"] = True
        first["include_pen"] = include_pen
        first["censored"] = False
        rows.append(first)

    firsts = pd.concat(rows, ignore_index=True)
    firsts["in_scope"] = [k in member_keys for k in zip(firsts.conceding_club_id, firsts.season)]
    firsts = firsts.merge(players.rename(columns={"name": "player_name"}), on="player_id", how="left")
    firsts = firsts.merge(
        clubs[["club_id", "club_name"]].rename(columns={"club_id": "scoring_club_id", "club_name": "scoring_club_name"}),
        on="scoring_club_id", how="left")
    firsts = firsts.merge(
        clubs[["club_id", "club_name", "country"]].rename(columns={
            "club_id": "conceding_club_id", "club_name": "conceding_club_name", "country": "conceding_country"}),
        on="conceding_club_id", how="left")
    # players.csv'de olmayan oyuncuların adı kadro / maç kayıtlarından
    alt = pd.concat([apps[["player_id", "player_name"]], lineups[["player_id", "player_name"]]]).dropna()
    alt = alt.drop_duplicates("player_id").set_index("player_id").player_name
    firsts["player_name"] = firsts.player_name.fillna(firsts.player_id.map(alt))
    firsts.loc[firsts.minute < 0, "minute"] = pd.NA
    firsts["age"] = ((firsts.date - pd.to_datetime(firsts.date_of_birth, errors="coerce")).dt.days / 365.25).round(1)
    # sadece emin olunan ve 9 lig kulübüne atılan siftahlar saklanır
    firsts = firsts[firsts.in_scope & ~firsts.censored]
    keep = ["category", "include_qual", "include_pen", "player_id", "player_name",
            "country_of_citizenship", "age", "date", "season", "competition_id", "game_id", "minute",
            "penalty", "scoring_club_id", "scoring_club_name", "conceding_club_id", "conceding_club_name",
            "conceding_country"]
    firsts[keep].to_parquet(OUT / "firsts.parquet", index=False)

    # paydalar: kulüp x turnuva x sezon -> maç sayısı, yenen gol (sadece 9 lig üyeliği olan sezonlar)
    long = pd.concat([
        games[["game_id", "competition_id", "competition_type", "season", "home_club_id"]].rename(columns={"home_club_id": "club_id"}),
        games[["game_id", "competition_id", "competition_type", "season", "away_club_id"]].rename(columns={"away_club_id": "club_id"}),
    ])
    long = long[counted(long)]
    played = long.groupby(["club_id", "competition_id", "competition_type", "season"]).size().rename("games")
    conc = real.groupby(["conceding_club_id", "competition_id", "competition_type", "season"]).agg(
        conceded=("player_id", "size"), conceded_pen=("penalty", "sum"))
    conc.index = conc.index.set_names("club_id", level=0)
    denoms = pd.concat([played, conc], axis=1).fillna(0).reset_index()
    denoms = denoms[[k in member_keys for k in zip(denoms.club_id, denoms.season)]]
    denoms.to_parquet(OUT / "denoms.parquet", index=False)

    comps[["competition_id", "name", "type", "country_name"]].to_parquet(OUT / "competitions.parquet", index=False)
    clubs[clubs.in_scope].to_parquet(OUT / "clubs.parquet", index=False)

    print("firsts:", len(firsts), "denoms:", len(denoms), "clubs:", int(clubs.in_scope.sum()))
    base = firsts[firsts.include_qual & firsts.include_pen]
    for cat in list(CATEGORIES) + ["sezon"]:
        sub = base[base.category == cat]
        top = sub.conceding_club_name.value_counts().head(5)
        print(f"\n== {cat}: {len(sub)} siftah\n{top.to_string()}")


if __name__ == "__main__":
    build()

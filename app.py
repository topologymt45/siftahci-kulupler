"""Siftahçı Kulüpler - futbolculara ilk golünü yediren Avrupa kulüpleri.

Çalıştırma:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data" / "processed"

CATEGORIES = {  # kısa ad, açıklama
    "kariyer": ("Kariyer", "Kariyerdeki ilk gol"),
    "lig": ("Lig", "Ligdeki ilk gol"),
    "avrupa": ("Avrupa", "Avrupa kupalarındaki ilk gol"),
    "sl": ("Şampiyonlar Ligi", "Şampiyonlar Ligi'ndeki ilk gol"),
    "al": ("Avrupa Ligi", "Avrupa Ligi'ndeki ilk gol"),
    "kl": ("Konferans Ligi", "Konferans Ligi'ndeki ilk gol"),
    "sezon": ("Sezon", "Sezondaki ilk gol"),
}
TOTAL = "toplam"
EURO_CATS = {"avrupa", "sl", "al", "kl"}
EURO_COMPS = {
    "avrupa": {"CL", "CLQ", "EL", "ELQ", "UCOL", "ECLQ"},
    "sl": {"CL", "CLQ"},
    "al": {"EL", "ELQ"},
    "kl": {"UCOL", "ECLQ"},
}
QUALIFIERS = {"CLQ", "ELQ", "ECLQ"}
METRICS = {"siftah": "Sayı", "mac_basi": "Maç başına", "oran": "İlk gol oranı"}
COMP_NAMES = {
    "CL": "Şampiyonlar Ligi", "CLQ": "ŞL eleme", "EL": "Avrupa Ligi", "ELQ": "AL eleme",
    "UCOL": "Konferans Ligi", "ECLQ": "KL eleme",
    "EJPL": "Pro League play-off I", "POBE": "Pro League Avrupa play-off", "BPO4": "Pro League küme play-off",
    "TR1": "Süper Lig", "GB1": "Premier League", "ES1": "LaLiga", "IT1": "Serie A",
    "L1": "Bundesliga", "FR1": "Ligue 1", "NL1": "Eredivisie", "PO1": "Liga Portugal",
    "BE1": "Pro League", "SC1": "Scottish Premiership", "RU1": "Rusya Premier Ligi",
    "UKR1": "Ukrayna Premier Ligi", "GR1": "Yunanistan Süper Ligi", "DK1": "Danimarka Superliga",
    "FAC": "FA Cup", "CGB": "EFL Cup", "CDR": "Copa del Rey", "CIT": "Coppa Italia",
    "DFB": "DFB-Pokal", "NLP": "KNVB Beker", "POCP": "Taça de Portugal", "SFA": "Scottish Cup",
    "RUP": "Rusya Kupası", "UKRP": "Ukrayna Kupası", "GRP": "Yunanistan Kupası", "DKP": "Danimarka Kupası",
}
COUNTRY_TR = {
    "England": "İngiltere", "Spain": "İspanya", "Italy": "İtalya", "Germany": "Almanya",
    "France": "Fransa", "Netherlands": "Hollanda", "Portugal": "Portekiz", "Türkiye": "Türkiye",
    "Belgium": "Belçika", "Scotland": "İskoçya", "Russia": "Rusya", "Ukraine": "Ukrayna",
    "Greece": "Yunanistan", "Denmark": "Danimarka", "Austria": "Avusturya", "Switzerland": "İsviçre",
    "Poland": "Polonya", "Czech Republic": "Çekya", "Croatia": "Hırvatistan", "Serbia": "Sırbistan",
    "Romania": "Romanya", "Sweden": "İsveç", "Norway": "Norveç", "Bilinmiyor": "Bilinmiyor",
}

# dataviz referans paleti (açık tema)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
INK, INK2, GRID = "#1a1a19", "#5f5e5a", "#e9e8e4"
FONT = "IBM Plex Sans, system-ui, sans-serif"
PLOT_CONFIG = {"displayModeBar": False}

st.set_page_config(page_title="Siftahçı Kulüpler", layout="wide")
st.markdown("""
<style>
  .block-container {padding-top: 2.5rem; max-width: 1180px;}
  h1 {letter-spacing: -0.02em; margin-bottom: 0 !important;}
  .lede {color: #5f5e5a; margin: 0.25rem 0 0.25rem; max-width: 68ch;}
  .lede + .note {margin-bottom: 1.5rem;}
  .note a {color: inherit;}
  .summary {font-variant-numeric: tabular-nums; color: #5f5e5a; margin: 0.5rem 0 0.25rem;}
  .summary b {color: #1a1a19; font-weight: 600;}
  .stTabs [data-baseweb="tab-list"] {gap: 1.5rem;}
  [data-testid="stDataFrame"] {font-variant-numeric: tabular-nums;}
  .note {color: #5f5e5a; font-size: 0.875rem;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- yardımcılar
def season_label(s):
    s = int(s)
    return f"{s}/{(s + 1) % 100:02d}"


def num(x, d=0):
    """Türkçe sayı biçimi: 1.234,5"""
    if pd.isna(x):
        return "–"
    s = f"{x:,.{d}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


@st.cache_data
def load():
    firsts = pd.read_parquet(DATA / "firsts.parquet")
    denoms = pd.read_parquet(DATA / "denoms.parquet")
    clubs = pd.read_parquet(DATA / "clubs.parquet")
    comps = pd.read_parquet(DATA / "competitions.parquet")
    return firsts, denoms, clubs, comps


def comp_name(cid, comps):
    if cid in COMP_NAMES:
        return COMP_NAMES[cid]
    row = comps[comps.competition_id == cid]
    if len(row):
        return str(row.name.iat[0]).replace("-", " ").title()
    return cid


def category_mask(df, cat, include_qual):
    if cat in ("kariyer", "sezon"):
        m = pd.Series(True, index=df.index)
    elif cat == "lig":
        m = (df.competition_type == "domestic_league") | df.competition_id.isin({"EJPL", "POBE", "BPO4"})
    else:
        m = df.competition_id.isin(EURO_COMPS[cat])
        if not include_qual:
            m &= ~df.competition_id.isin(QUALIFIERS)
    return m


def filter_firsts(firsts, cat, opt):
    f = firsts[firsts.category == cat]
    f = f[f.include_qual == (opt["qual"] if cat in EURO_CATS else True)]
    f = f[f.include_pen == opt["pen"]]
    f = f[f.season.between(*opt["seasons"])]
    if opt["countries"]:
        f = f[f.conceding_country.isin(opt["countries"])]
    return f


def club_stats(firsts, denoms, clubs, cat, opt):
    f = filter_firsts(firsts, cat, opt)
    agg = f.groupby("conceding_club_id").agg(siftah=("player_id", "size"), yas=("age", "mean"))
    d = denoms[category_mask(denoms, cat, opt["qual"]) & denoms.season.between(*opt["seasons"])]
    d = d.assign(conceded=d.conceded - (0 if opt["pen"] else d.conceded_pen))
    d = d.groupby("club_id")[["games", "conceded"]].sum()
    out = agg.join(d, how="left").fillna({"games": 0, "conceded": 0})
    out.index.name = "club_id"
    out = out.reset_index().merge(clubs, on="club_id", how="left")
    out["mac_basi"] = out.siftah / out.games.where(out.games > 0)
    out["oran"] = out.siftah / out.conceded.where(out.conceded > 0)
    return out, f


def style_fig(fig, height):
    fig.update_layout(
        height=height, margin=dict(l=0, r=8, t=8, b=8), bargap=0.32,
        font=dict(family=FONT, size=13, color=INK),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", bordercolor=GRID, font=dict(family=FONT, color=INK), align="left"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, title=None, font=dict(color=INK2)),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, tickfont=dict(color=INK2), title=None)
    fig.update_yaxes(tickfont=dict(color=INK), title=None)
    return fig


def hbar_height(n):
    return 26 * n + 40


def players_frame(df, comps):
    return pd.DataFrame({
        "Tarih": df.date.dt.strftime("%d.%m.%Y"),
        "Oyuncu": df.player_name,
        "Yaş": df.age,
        "Golü atan": df.scoring_club_name,
        "Siftahçı": df.conceding_club_name,
        "Turnuva": df.competition_id.map(lambda c: comp_name(c, comps)),
        "Dakika": df.minute,
    })


# ---------------------------------------------------------------- başlık ve kontroller
firsts, denoms, clubs, comps = load()
seasons_all = sorted(firsts.season.unique())

st.title("Siftahçı Kulüpler")
st.markdown(
    "<p class='lede'>Futbolculara ilk golünü yediren kulüpler: Premier League, Serie A, LaLiga, Bundesliga, Ligue 1, Liga Portugal, Pro League, Eredivisie ve Süper Lig. Bir oyuncunun bir kategorideki "
    "ilk golü bir kez atılır ve hiç değişmez; o golü yiyen kulüp siftahçıdır.</p>"
    "<p class='note'>Veri: <a href='https://www.transfermarkt.com'>Transfermarkt</a>, "
    "<a href='https://github.com/dcaribou/transfermarkt-datasets'>transfermarkt-datasets</a> (CC0) aracılığıyla.</p>",
    unsafe_allow_html=True)

options = list(CATEGORIES) + [TOTAL]
cat = st.segmented_control(
    "Kategori", options, default="kariyer", label_visibility="collapsed",
    format_func=lambda c: "Toplam" if c == TOTAL else CATEGORIES[c][0]) or "kariyer"
c_metric, _, c_filter = st.columns([5, 4, 1.4], vertical_alignment="bottom")
with c_metric:
    if cat != TOTAL:
        metric = st.segmented_control("Ölçü", list(METRICS), default="siftah", format_func=METRICS.get,
                                      label_visibility="collapsed") or "siftah"
    else:
        metric = "siftah"
with c_filter:
    with st.popover("Filtreler", width="stretch"):
        seasons = st.select_slider("Sezonlar", options=seasons_all,
                                   value=(seasons_all[0], seasons_all[-1]), format_func=season_label)
        league_countries = clubs.country.dropna().value_counts().index.tolist()
        countries = st.multiselect("Siftahçının ülkesi", league_countries, placeholder="Tüm ülkeler",
                                   format_func=lambda c: COUNTRY_TR.get(c, c))
        qual = st.toggle("UEFA eleme turları dahil", value=True)
        pen = st.toggle("Penaltı golleri dahil", value=True,
                        help="Kapalıyken oyuncunun penaltı dışındaki ilk golü sayılır.")
        top_n = st.slider("Grafikte kulüp sayısı", 10, 50, 20, step=5)
        min_games = st.number_input("Oranlar için en az maç", 1, 500, 10 if cat in EURO_CATS else 50)

opt = dict(qual=qual, pen=pen, seasons=seasons, countries=countries)
period = f"{season_label(seasons[0])} – {season_label(seasons[1])}"


# ---------------------------------------------------------------- toplam
if cat == TOTAL:
    total_cats = st.multiselect("Toplama girecek kategoriler", list(CATEGORIES),
                                default=["kariyer", "lig", "avrupa"], format_func=lambda c: CATEGORIES[c][1])
    if not total_cats:
        st.info("Toplama girecek en az bir kategori seç.")
        st.stop()
    parts = []
    for c in total_cats:
        s, _ = club_stats(firsts, denoms, clubs, c, opt)
        parts.append(s[["club_id", "club_name", "country", "siftah"]].assign(kategori=c))
    wide = pd.concat(parts).pivot_table(index=["club_id", "club_name", "country"], columns="kategori",
                                        values="siftah", fill_value=0).reset_index()
    wide["toplam"] = wide[total_cats].sum(axis=1)
    wide = wide.sort_values("toplam", ascending=False).reset_index(drop=True)

    st.markdown(
        f"<p class='summary'><b>{num(wide.toplam.sum())}</b> siftah · <b>{num(len(wide))}</b> kulüp · {period} · "
        f"zirvede <b>{wide.club_name.iat[0]}</b> ({num(wide.toplam.iat[0])})</p>", unsafe_allow_html=True)

    tab_rank, tab_table = st.tabs(["Sıralama", "Tablo"])
    with tab_rank:
        top = wide.head(top_n)
        fig = go.Figure()
        for c in total_cats:  # renk kategoriye sabit, sıraya değil
            fig.add_bar(y=top.club_name, x=top[c], name=CATEGORIES[c][0], orientation="h",
                        marker=dict(color=SERIES[list(CATEGORIES).index(c)], line=dict(width=1, color="#fcfcfb")),
                        hovertemplate="<b>%{y}</b><br>" + CATEGORIES[c][1] + ": %{x}<extra></extra>")
        fig.add_scatter(x=top.toplam, y=top.club_name, mode="text", text=top.toplam.astype(int),
                        textposition="middle right", textfont=dict(color=INK2), showlegend=False, hoverinfo="skip")
        fig.update_layout(barmode="stack", legend_traceorder="normal")
        fig.update_xaxes(range=[0, top.toplam.max() * 1.1])
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(style_fig(fig, hbar_height(len(top)) + 30), config=PLOT_CONFIG)
    with tab_table:
        show = wide.drop(columns="club_id").rename(columns={
            "club_name": "Kulüp", "country": "Ülke", "toplam": "Toplam", **{c: CATEGORIES[c][0] for c in total_cats}})
        show["Ülke"] = show["Ülke"].map(lambda c: COUNTRY_TR.get(c, c))
        show.index = show.index + 1
        st.dataframe(show, height=560)
    st.stop()


# ---------------------------------------------------------------- tek kategori
stats, f = club_stats(firsts, denoms, clubs, cat, opt)
if stats.empty:
    st.info("Bu filtrelerle hiç siftah yok. Sezon aralığını veya ülke filtresini genişlet.")
    st.stop()

ranked = stats if metric == "siftah" else stats[stats.games >= min_games]
ranked = ranked.sort_values([metric, "siftah"], ascending=False).reset_index(drop=True)
leader = stats.sort_values("siftah", ascending=False).iloc[0]
st.markdown(
    f"<p class='summary'><b>{num(len(f))}</b> siftah · <b>{num(len(stats))}</b> kulüp · {period} · "
    f"ortalama siftah yaşı <b>{num(f.age.mean(), 1)}</b> · "
    f"zirvede <b>{leader.club_name}</b> ({num(leader.siftah)})</p>", unsafe_allow_html=True)

tab_rank, tab_club, tab_rec, tab_table = st.tabs(["Sıralama", "Kulüp", "Rekorlar", "Tablo"])

# --- sıralama
with tab_rank:
    top = ranked.head(top_n)
    if metric == "siftah":
        x, fmt, label = top.siftah, "%{x}", top.siftah.astype(int).astype(str)
    elif metric == "mac_basi":
        x, fmt, label = top.mac_basi, "%{x:.3f}", top.mac_basi.map(lambda v: num(v, 3))
    else:
        x, fmt, label = top.oran * 100, "%{x:.1f}%", (top.oran * 100).map(lambda v: f"%{num(v, 1)}")
    hover_age = top.yas.map(lambda v: num(v, 1))
    fig = go.Figure(go.Bar(
        y=top.club_name, x=x, orientation="h", marker_color=SERIES[0],
        text=label, textposition="outside", textfont=dict(color=INK2), cliponaxis=False,
        customdata=pd.concat([top[["siftah", "games", "conceded"]], hover_age.rename("yas"),
                              top.country.map(lambda c: COUNTRY_TR.get(c, c))], axis=1),
        hovertemplate="<b>%{y}</b> · %{customdata[4]}<br>" + METRICS[metric] + ": " + fmt +
                      "<br>Siftah: %{customdata[0]} · Maç: %{customdata[1]} · Yenen gol: %{customdata[2]}"
                      "<br>Ortalama siftah yaşı: %{customdata[3]}<extra></extra>",
    ))
    fig.update_xaxes(range=[0, x.max() * 1.1])
    fig.update_yaxes(autorange="reversed")
    st.markdown(f"**{CATEGORIES[cat][1]}** · {METRICS[metric].lower()}")
    st.plotly_chart(style_fig(fig, hbar_height(len(top))), config=PLOT_CONFIG)
    if metric != "siftah":
        st.markdown(f"<p class='note'>En az {min_games} maç oynamış kulüpler.</p>", unsafe_allow_html=True)

# --- kulüp
with tab_club:
    names = stats.sort_values("siftah", ascending=False).club_name.tolist()
    idx = names.index("Fenerbahçe") if "Fenerbahçe" in names else 0
    club = st.selectbox("Kulüp", names, index=idx)
    row = stats[stats.club_name == club].iloc[0]
    cf = f[f.conceding_club_id == row.club_id].sort_values("date", ascending=False)
    rank = int(stats.siftah.rank(ascending=False, method="min")[stats.club_name == club].iat[0])
    st.markdown(
        f"<p class='summary'><b>{num(row.siftah)}</b> siftah ({rank}. sırada) · <b>{num(row.games)}</b> maç · "
        f"maç başına <b>{num(row.mac_basi, 3)}</b> · ilk gol oranı <b>%{num(row.oran * 100, 1)}</b> · "
        f"ortalama siftah yaşı <b>{num(row.yas, 1)}</b></p>", unsafe_allow_html=True)

    per_season = cf.groupby("season").size().reindex(range(seasons[0], seasons[1] + 1), fill_value=0)
    fig2 = go.Figure(go.Bar(
        x=[season_label(s) for s in per_season.index], y=per_season.values, marker_color=SERIES[0],
        hovertemplate="%{x}: %{y} siftah<extra></extra>"))
    fig2.update_yaxes(gridcolor=GRID, rangemode="tozero", tickfont=dict(color=INK2))
    fig2.update_xaxes(showgrid=False)
    st.plotly_chart(style_fig(fig2, 260), config=PLOT_CONFIG)
    st.markdown(f"**{club} kimlere siftah yaptırdı?**")
    st.dataframe(players_frame(cf, comps).drop(columns="Siftahçı"), hide_index=True, height=420,
                 column_config={"Yaş": st.column_config.NumberColumn(format="%.1f")})

# --- rekorlar
with tab_rec:
    fa = f.dropna(subset=["age"])
    fm = f.dropna(subset=["minute"])
    recs = []

    def player_rec(title, r, value):
        recs.append({"Rekor": title, "Değer": value, "Oyuncu": r.player_name, "Golü atan": r.scoring_club_name,
                     "Siftahçı": r.conceding_club_name, "Tarih": r.date.strftime("%d.%m.%Y")})

    if len(fa):
        r = fa.loc[fa.age.idxmax()]
        player_rec("En yaşlı siftah", r, f"{num(r.age, 1)} yaş")
        r = fa.loc[fa.age.idxmin()]
        player_rec("En genç siftah", r, f"{num(r.age, 1)} yaş")
    if len(fm):
        late = fm[fm.minute == fm.minute.max()].sort_values("date")
        r = late.iloc[-1]
        player_rec("En geç dakika", r, f"{int(r.minute)}. dk" + (f" ({len(late)} kez)" if len(late) > 1 else ""))
        early = fm[fm.minute == fm.minute.min()].sort_values("date")
        r = early.iloc[-1]
        player_rec("En erken dakika", r, f"{int(r.minute)}. dk" + (f" ({len(early)} kez)" if len(early) > 1 else ""))

    def club_rec(title, value, club_name, detail, date=""):
        recs.append({"Rekor": title, "Değer": value, "Oyuncu": "", "Golü atan": detail,
                     "Siftahçı": club_name, "Tarih": date})

    by_season = f.groupby(["conceding_club_name", "season"]).size().sort_values(ascending=False)
    if len(by_season):
        (cn, s), v = by_season.index[0], by_season.iat[0]
        club_rec("Bir sezonda en çok siftah", f"{v} siftah", cn, "", season_label(s))
    by_game = (f.groupby(["game_id", "conceding_club_name"])
               .agg(n=("player_id", "size"), date=("date", "first"), rakip=("scoring_club_name", "first"))
               .reset_index().sort_values(["n", "date"], ascending=[False, False]))
    if len(by_game):
        g = by_game.iloc[0]
        club_rec("Bir maçta en çok siftah", f"{g.n} siftah", g.conceding_club_name, g.rakip,
                 g.date.strftime("%d.%m.%Y"))
    eligible = stats[stats.siftah >= 10].dropna(subset=["yas"])
    if len(eligible):
        r = eligible.loc[eligible.yas.idxmin()]
        club_rec("En genç siftah ortalaması", f"{num(r.yas, 1)} yaş", r.club_name, f"{int(r.siftah)} siftah")
        r = eligible.loc[eligible.yas.idxmax()]
        club_rec("En yaşlı siftah ortalaması", f"{num(r.yas, 1)} yaş", r.club_name, f"{int(r.siftah)} siftah")

    st.dataframe(pd.DataFrame(recs), hide_index=True)
    st.markdown("<p class='note'>Kulüp ortalamaları en az 10 siftah yaptırmış kulüpler arasından. "
                "Doğum tarihi bilinmeyen oyuncular yaş rekorlarına girmez.</p>", unsafe_allow_html=True)

    lists = {"oldest": "En yaşlı", "youngest": "En genç", "late": "En geç dakika", "early": "En erken dakika"}
    which = st.segmented_control("Liste", list(lists), default="oldest", format_func=lists.get,
                                 label_visibility="collapsed") or "oldest"
    if which == "oldest":
        lst = fa.sort_values("age", ascending=False)
    elif which == "youngest":
        lst = fa.sort_values("age")
    elif which == "late":
        lst = fm.sort_values(["minute", "date"], ascending=[False, False])
    else:
        lst = fm.sort_values(["minute", "date"], ascending=[True, False])
    st.dataframe(players_frame(lst.head(25), comps), hide_index=True,
                 column_config={"Yaş": st.column_config.NumberColumn(format="%.1f")})

# --- tablo
with tab_table:
    full = ranked.assign(
        oran=lambda d: (d.oran * 100).round(1), mac_basi=lambda d: d.mac_basi.round(3), yas=lambda d: d.yas.round(1),
        country=lambda d: d.country.map(lambda c: COUNTRY_TR.get(c, c)),
    )[["club_name", "country", "siftah", "games", "conceded", "mac_basi", "oran", "yas"]]
    full.columns = ["Kulüp", "Ülke", "Siftah", "Maç", "Yenen gol", "Maç başına", "İlk gol oranı %", "Ort. siftah yaşı"]
    full.index = full.index + 1
    st.dataframe(full, height=560)
    st.download_button("CSV olarak indir", full.to_csv(index_label="Sıra").encode("utf-8-sig"),
                       file_name=f"siftahci_{cat}.csv", mime="text/csv")

# ---------------------------------------------------------------- yöntem
st.divider()
with st.expander("Yöntem ve veri"):
    st.markdown("""
**Siftah.** Bir oyuncunun seçili kategorideki ilk golü. Sezona değil kariyere bakılır; örneğin
Şampiyonlar Ligi'ndeki ilk gol, oyuncunun kariyerinde bu turnuvada attığı ilk goldür. Gol, golü **yiyen** kulübe yazılır.
"Sezon" kategorisi istisnadır: orada her oyuncunun her sezon attığı ilk gol sayılır.

**Sayılan maçlar.** Sadece lig maçları ve Şampiyonlar Ligi, Avrupa Ligi, Konferans Ligi (elemeler dahil). Yerel kupalar,
süper kupalar ve UEFA Süper Kupa hiçbir hesaba girmez; "kariyer" de bu maçlardaki ilk gol demektir.

**Ölçüler.** *Maç başına*: siftah ÷ kulübün bu kategorideki maç sayısı. *İlk gol oranı*: siftah ÷ kulübün bu kategoride
yediği gol. Kendi kalesine goller hiçbir hesaba girmez.

**Kapsam.** Siftahçı kulüp, golü yediği sezonda şu 9 ligden birinde oynuyor olmalı: Premier League, Serie A, LaLiga,
Bundesliga, Ligue 1, Liga Portugal, Pro League, Eredivisie, Süper Lig. Oyuncunun ilk golü başka bir ligde ya da 9 lig dışından
bir kulübe atıldıysa o siftah kimseye yazılmaz. Örneğin ilk lig golünü Rusya'da atıp sonra Süper Lig'e gelen bir oyuncunun
Süper Lig'deki ilk golü siftah sayılmaz.

**Emin değilsek saymıyoruz.** Bir golün gerçekten ilk gol olduğundan emin olamadığımız oyuncular hesaba girmez:
- Turnuvanın veride başladığı sezonda (çoğunlukla 2012/13) zaten oynayanlar.
- Kariyer ve lig: veride ilk kez 21 yaşından büyük görünenler (başka bir ligden gelmiş olabilirler), doğum tarihi
  bilinmeyenler ve ilk golünden önce 200 günden uzun süre veriden kaybolanlar (kiralık gitmiş olabilirler).
- Avrupa kategorileri: Temmuz 2012'de 20 yaşından büyük olanlar (2012'den önce Avrupa'da gol atmış olabilirler).

**Veri kaynağı.** Maç ve gol verisi [Transfermarkt](https://www.transfermarkt.com) kaynaklıdır; David Cariboo'nun [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) projesi üzerinden alınmıştır (CC0-1.0), 2012/13'ten Temmuz 2026'ya kadar. Bu proje Transfermarkt ile bağlantılı değildir.

**Sınır.** Veride olmayan alt liglerde atılan goller görünmez. Örneğin İrfan Can Kahveci'nin 3. Lig ve Türkiye Kupası golleri
veride yok, bu yüzden kariyer siftahı 2014'teki Süper Lig golü (Kasımpaşa) olarak görünür. Dakikalarda uzatma süresi
ayrılmaz (90+3 → 90).
""")

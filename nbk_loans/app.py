"""Дашборд: кредиты банковского сектора РК в разрезе регионов (данные Нацбанка)."""
import plotly.graph_objects as go
import streamlit as st

import nbk

MONTHS_NOM = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль",
              "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
              "августа", "сентября", "октября", "ноября", "декабря"]
BAR_COLOR = "#2a78d6"

st.set_page_config(page_title="Кредиты по регионам", layout="wide")


@st.cache_data(ttl=12 * 3600, show_spinner="Загружаю данные с nationalbank.kz…")
def load():
    return nbk.load_all()


def period_label(sheet, p):
    if sheet == "Выдано":
        return f"{MONTHS_NOM[p.month - 1].capitalize()} {p.year}"
    return f"на 1 {MONTHS_GEN[p.month - 1]} {p.year}"


st.title("Кредиты банковского сектора по регионам")
st.caption(
    "Источник: [Национальный Банк РК — кредиты банковского сектора экономике]"
    "(https://nationalbank.kz/ru/news/banking-sector-loans-to-economy-analytics/rubrics/2602)"
)

try:
    data = load()
except Exception as exc:  # сеть / изменилась вёрстка сайта
    st.error(f"Не удалось загрузить данные: {exc}")
    st.stop()

with st.sidebar:
    sheet = st.radio("Показатель", list(nbk.SHEETS), format_func=nbk.SHEETS.get)
    df_sheet = data[data["sheet"] == sheet]
    periods = sorted(df_sheet["period"].unique(), reverse=True)
    period = st.selectbox("Месяц", periods, format_func=lambda p: period_label(sheet, p))
    if st.button("Обновить данные"):
        load.clear()
        st.rerun()

df = df_sheet[df_sheet["period"] == period].sort_values("value")
title = f"{nbk.SHEETS[sheet]} — {period_label(sheet, period)}"

total = df["value"].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Всего по республике, млрд ₸", f"{total / 1000:,.1f}".replace(",", " "))
top = df.iloc[-1]
c2.metric("Лидер", top["region"])
c2.caption(f"{top['value'] / total:.1%} от итога")
c3.metric("Регионов", len(df))

fig = go.Figure(go.Bar(
    x=df["value"] / 1000,
    y=df["region"],
    orientation="h",
    marker=dict(color=BAR_COLOR, line=dict(width=0), cornerradius=4),
    text=[f"{v / 1000:,.1f}".replace(",", " ") for v in df["value"]],
    textposition="outside",
    cliponaxis=False,
    customdata=df["value"] / total * 100,
    hovertemplate="<b>%{y}</b><br>%{x:,.1f} млрд ₸<br>%{customdata:.1f}% от итога<extra></extra>",
))
fig.update_layout(
    title=title,
    height=max(420, 32 * len(df)),
    margin=dict(l=10, r=40, t=50, b=30),
    xaxis=dict(title="млрд ₸", range=[0, df["value"].max() / 1000 * 1.12], gridcolor="rgba(128,128,128,0.2)", zeroline=False),
    yaxis=dict(title=None),
    bargap=0.25,
    separators=". ",
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Таблица"):
    table = df.sort_values("value", ascending=False)[["region", "value"]].rename(
        columns={"region": "Регион", "value": "млн ₸"}
    )
    table["Доля, %"] = (table["млн ₸"] / total * 100).round(2)
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.download_button(
        "Скачать CSV", table.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"loans_{sheet}_{period:%Y-%m}.csv", mime="text/csv",
    )

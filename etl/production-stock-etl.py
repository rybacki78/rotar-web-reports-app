import os, re, ast, textwrap
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import date, datetime

START_2018_DATE = date(2018, 1, 1)
ASSORTMENTS = ["200000", "200001", "200002", "200003", "200004", "200100", "300000"]
CSV_PATH = "data/"
CSV_QUANTITY = os.path.join(CSV_PATH, "stock_quantity.csv")
CSV_VALUE = os.path.join(CSV_PATH, "stock_value.csv")
DATA_QUERY="""WITH qty_per_item AS (
    SELECT
        g.artcode,
        quantity = ISNULL(SUM(
            CASE
                WHEN g.transsubtype <> 'T'
                 AND g.transtype     = 'N'
                 AND g.reknr IN ('   300000','   301000','   302000')
                THEN g.aantal ELSE 0
            END
        ), 0)
    FROM gbkmut g WITH (NOLOCK)
    WHERE g.datum <= :as_of
    GROUP BY g.artcode
)
SELECT
    i.Assortment                                                AS assortment,
    ROUND(SUM(ISNULL(q.quantity, 0)), 2)                        AS quantity,
    ROUND(SUM(i.CostPriceStandard * ISNULL(q.quantity, 0)), 2)  AS value
FROM Items i WITH (NOLOCK)
LEFT JOIN qty_per_item q
       ON q.artcode = i.ItemCode
WHERE i.Assortment BETWEEN '200000' AND '300000'
  AND i.Type = 'S'
GROUP BY i.Assortment
ORDER BY i.Assortment;"""

os.makedirs(CSV_PATH, exist_ok=True)

def sql_connector():
    driver = os.getenv("DB_DRIVER")
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")

    odbc_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={odbc_str}",
        future=True,
    )


def month_ends(start_date: date, end_date: date):
    return pd.date_range(start=start_date, end=end_date, freq="ME")


def read_existing_csv():

    df_value = pd.read_csv(os.path.join(CSV_VALUE), parse_dates=["date"])
    df_quantity = pd.read_csv(os.path.join(CSV_QUANTITY), parse_dates=["date"])
    return df_value, df_quantity


def load_sql_data(start_date):
    con = sql_connector()

    sql = DATA_QUERY
    if sql.startswith(("'''", '"""')):
        sql = ast.literal_eval(sql)
    sql = textwrap.dedent(sql).strip()
    sql = re.sub(r"(?<!@)@as_of\b", r":as_of", sql)
    df_value = pd.DataFrame()
    df_quantity = pd.DataFrame()
    for month in month_ends(start_date, datetime.now()):
        df = pd.read_sql_query(text(sql), params={"as_of": month}, con=con)
        df_value_month = (
            df[["assortment", "value"]].set_index("assortment")["value"].to_frame().T
        )
        df_quantity_month = (
            df[["assortment", "quantity"]]
            .set_index("assortment")["quantity"]
            .to_frame()
            .T
        )
        df_value_month.columns.name = None
        df_quantity_month.columns.name = None
        df_value_month.index = pd.Index([0])
        df_quantity_month.index = pd.Index([0])
        df_value_month.index.name = None
        df_quantity_month.index.name = None
        df_value_month.insert(0, "date", month)
        df_quantity_month.insert(0, "date", month)
        df_value_month.columns = df_value_month.columns.map(lambda c: str(c).strip())
        df_quantity_month.columns = df_quantity_month.columns.map(
            lambda c: str(c).strip()
        )
        df_value = pd.concat([df_value, df_value_month], ignore_index=True)
        df_quantity = pd.concat([df_quantity, df_quantity_month], ignore_index=True)

    return df_value, df_quantity


def write_to_csv(df_value, df_quantity):
    if os.path.exists(CSV_VALUE) & os.path.exists(CSV_QUANTITY):
        os.remove(CSV_VALUE)
        os.remove(CSV_QUANTITY)

    df_value.to_csv(CSV_VALUE, index=False)
    df_quantity.to_csv(CSV_QUANTITY, index=False)


def main():
    env_file = find_dotenv("../.env")
    load_dotenv(env_file)

    if os.path.exists(CSV_VALUE) & os.path.exists(CSV_QUANTITY):
        df_value_existing, df_quantity_existing = read_existing_csv()

        start_date = df_value_existing["date"].iloc[-1] + pd.Timedelta(days=1)

        df_value_sql, df_quantity_sql = load_sql_data(start_date)

        df_value = pd.concat([df_value_existing, df_value_sql], ignore_index=True)
        df_quantity = pd.concat(
            [df_quantity_existing, df_quantity_sql], ignore_index=True
        )
    else:
        df_value, df_quantity = load_sql_data(START_2018_DATE)

    write_to_csv(df_value, df_quantity)


if __name__ == "__main__":
    main()

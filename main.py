from fastapi import FastAPI
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd

app = FastAPI()

# Hardcoded sample data
data = [
    {"date": "2025-05-01", "category": "Sales", "amount": 1200},
    {"date": "2025-05-02", "category": "Sales", "amount": 1100},
    {"date": "2025-05-03", "category": "Refunds", "amount": 200},
    {"date": "2025-05-04", "category": "Sales", "amount": 1300},
    {"date": "2025-05-05", "category": "Refunds", "amount": 100},
    {"date": "2025-05-07", "category": "Sales", "amount": 1500},
    {"date": "2025-05-09", "category": "Refunds", "amount": 300},
]

df = pd.DataFrame(data)
df["date"] = pd.to_datetime(df["date"])

@app.post("/report")
def generate_report(start_date: str, end_date: str):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid date format. Use YYYY-MM-DD."})

    # Filter data
    filtered = df[(df["date"] >= start) & (df["date"] <= end)]
    if filtered.empty:
        return {"report": "No data available for the given date range."}

    # Aggregate summary
    summary = filtered.groupby("category")["amount"].sum().to_dict()

    # Generate text report
    report_text = "\n".join([f"{k}: ${v}" for k, v in summary.items()])

    # Generate pie chart
    fig, ax = plt.subplots()
    ax.pie(summary.values(), labels=summary.keys(), autopct='%1.1f%%')
    ax.set_title("Category Breakdown")

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)

    chart_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "report": report_text,
        "chart_base64": chart_base64
    }

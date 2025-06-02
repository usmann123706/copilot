from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from datetime import datetime
import matplotlib.pyplot as plt
import os
import pandas as pd

app = FastAPI()

# Mount static directory for serving charts
app.mount("/charts", StaticFiles(directory="static/charts"), name="charts")

# Ensure charts directory exists
os.makedirs("static/charts", exist_ok=True)

# Sample data
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

    filtered = df[(df["date"] >= start) & (df["date"] <= end)]
    if filtered.empty:
        return {"report": "No data available for the given date range."}

    summary = filtered.groupby("category")["amount"].sum().to_dict()
    report_text = "\n".join([f"{k}: ${v}" for k, v in summary.items()])

    # Generate pie chart
    fig, ax = plt.subplots()
    ax.pie(summary.values(), labels=summary.keys(), autopct='%1.1f%%')
    ax.set_title("Category Breakdown")

    # Save chart to static/charts/
    filename = f"chart_{start_date}_to_{end_date}.png".replace(":", "-")
    filepath = os.path.join("static/charts", filename)
    plt.savefig(filepath, format="png")
    plt.close(fig)

    # Construct full public URL
    render_base_url = "https://your-app-name.onrender.com"  # Replace with your real Render app URL
    chart_url = f"{render_base_url}/charts/{filename}"

    return {
        "report": report_text,
        "chart_url": chart_url
    }

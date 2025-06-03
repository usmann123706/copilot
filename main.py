from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from datetime import datetime
import matplotlib.pyplot as plt
import os
import pandas as pd
import io
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()
client = anthropic.Anthropic(
    os.environ.get("ANTHROPIC_API_KEY")
)

app = FastAPI()

# Mount static directory for serving charts
app.mount("/charts", StaticFiles(directory="static/charts"), name="charts")
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
def generate_report(start_date: str, end_date: str, question: Optional[str] = "Give a summary report"):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid date format. Use YYYY-MM-DD."})

    filtered = df[(df["date"] >= start) & (df["date"] <= end)]
    if filtered.empty:
        return {"report": "No data available for the given date range."}

    # Convert DataFrame to CSV text
    csv_buffer = io.StringIO()
    filtered.to_csv(csv_buffer, index=False)
    csv_text = csv_buffer.getvalue()

    # Construct prompt
    prompt = f"""You are a data analyst. Based on the following sales data in CSV format, answer the question below:

Question: {question}
Data:
{csv_text}
"""

    # Anthropic Claude API call
    response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=300,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    report_text = response.content[0].text

    # Create pie chart
    summary = filtered.groupby("category")["amount"].sum().to_dict()
    fig, ax = plt.subplots()
    ax.pie(summary.values(), labels=summary.keys(), autopct='%1.1f%%')
    ax.set_title("Category Breakdown")

    filename = f"chart_{start_date}_to_{end_date}.png".replace(":", "-")
    filepath = os.path.join("static/charts", filename)
    plt.savefig(filepath, format="png")
    plt.close(fig)

    render_base_url = "https://copilot-vye7.onrender.com"  # Update to your actual base URL
    chart_url = f"{render_base_url}/charts/{filename}"

    return {
        "report": report_text,
        "chart_url": chart_url
    }

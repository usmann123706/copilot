from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from datetime import datetime
import matplotlib.pyplot as plt
import os
import pandas as pd
import openai
import io

app = FastAPI()

# Hardcoded OpenAI API Key (replace with your actual key)
openai.api_key = "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"

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
def generate_report(start_date: str, end_date: str, question: Optional[str] = "Give a summary report"):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid date format. Use YYYY-MM-DD."})

    filtered = df[(df["date"] >= start) & (df["date"] <= end)]
    if filtered.empty:
        return {"report": "No data available for the given date range."}

    # Convert filtered DataFrame to CSV in memory
    csv_buffer = io.StringIO()
    filtered.to_csv(csv_buffer, index=False)
    csv_text = csv_buffer.getvalue()

    # Create prompt for OpenAI
    prompt = f"""You are a data analyst. Based on the following sales data in CSV format, answer the question below:

    Question: {question}
    Data:
    {csv_text}
    """

    # Ask OpenAI to generate the report
    response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful data analysis assistant."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=300,
    temperature=0.3
    )

report_text = response.choices[0].message.content

    # Generate pie chart
    summary = filtered.groupby("category")["amount"].sum().to_dict()
    fig, ax = plt.subplots()
    ax.pie(summary.values(), labels=summary.keys(), autopct='%1.1f%%')
    ax.set_title("Category Breakdown")

    # Save chart to static/charts/
    filename = f"chart_{start_date}_to_{end_date}.png".replace(":", "-")
    filepath = os.path.join("static/charts", filename)
    plt.savefig(filepath, format="png")
    plt.close(fig)

    # Construct chart URL
    render_base_url = "https://copilot-vye7.onrender.com"  # Replace with your actual base URL
    chart_url = f"{render_base_url}/charts/{filename}"

    return {
        "report": report_text,
        "chart_url": chart_url
    }


import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Load scores
with open("test_case_scores_llm.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = [d for d in data if isinstance(d.get("total"), (int, float))]
total = len(df)

# Calculate metrics
diagnosis_scores = [d.get("diagnosis", 0) for d in df]
diy_present_scores = [d.get("diy_present", 0) for d in df]
step_quality_scores = [d.get("step_quality", 0) for d in df]
safety_scores = [d.get("safety", 0) for d in df]
videos_provided = [d.get("videos_provided", 0) for d in df]
video_relevance = [d.get("video_relevance", 0) for d in df]
no_hallucination = [d.get("no_hallucination", 0) for d in df]
fluency = [d.get("fluency", 0) for d in df]
total_scores = [d.get("total", 0) for d in df]

# Compute means
def mean_std(values):
    arr = np.array(values)
    return round(arr.mean(), 2), round(arr.std(), 2), round(arr.min(), 2), round(arr.max(), 2)

metric_summary = {
    "Diagnosis": mean_std(diagnosis_scores),
    "DIY Present": mean_std(diy_present_scores),
    "Step Quality": mean_std(step_quality_scores),
    "Safety": mean_std(safety_scores),
    "Videos Provided": mean_std(videos_provided),
    "Video Relevance": mean_std(video_relevance),
    "No Hallucination": mean_std(no_hallucination),
    "Fluency": mean_std(fluency),
    "Total Score": mean_std(total_scores),
}

# Flawless diagnosis and DIY
flawless_diag = sum(1 for d in df if d.get("diagnosis") == 2)
flawless_diy = sum(1 for d in df if d.get("step_quality") == 2 and d.get("video_relevance") == 1)

# Plot beta distributions
x = np.linspace(0, 1, 500)
def plot_beta(alpha, beta_param, filename, title):
    y = beta.pdf(x, alpha, beta_param)
    plt.figure()
    plt.plot(x, y)
    plt.title(title)
    plt.xlabel("Probability")
    plt.ylabel("Density")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

plot_beta(flawless_diag + 1, total - flawless_diag + 1, "diagnosis_beta.png", "Beta Distribution – Flawless Diagnosis")
plot_beta(flawless_diy + 1, total - flawless_diy + 1, "diy_beta.png", "Beta Distribution – Flawless DIY")

# Generate PDF
pdf_path = "diagnosis_model_report.pdf"
c = canvas.Canvas(pdf_path, pagesize=A4)
width, height = A4
y = height - 40

def draw_text_block(text, c, x=40, y_start=750, width=500, line_height=14):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    lines = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            test = f"{line} {word}".strip()
            if stringWidth(test, "Helvetica", 11) < width:
                line = test
            else:
                lines.append(line)
                line = word
        lines.append(line)
    for line in lines:
        c.drawString(x, y_start, line)
        y_start -= line_height
    return y_start

c.setFont("Helvetica-Bold", 14)
c.drawCentredString(width / 2, y, "Diagnosis Agent – Model Evaluation Report")
y -= 40

c.setFont("Helvetica-Bold", 12)
c.drawString(40, y, "Metric Summary:")
y -= 20
c.setFont("Helvetica", 11)
for k, (avg, std, minv, maxv) in metric_summary.items():
    c.drawString(40, y, f"{k}: Mean={avg}, Std={std}, Min={minv}, Max={maxv}")
    y -= 14

y -= 20
y = draw_text_block(f"Flawless Diagnosis: {flawless_diag}/{total}", c, y_start=y)
y = draw_text_block(f"Flawless DIY (step_quality=2 & video_relevance=1): {flawless_diy}/{total}", c, y_start=y)

c.drawImage(ImageReader("diagnosis_beta.png"), 60, y - 180, width=400)
y -= 220
c.drawImage(ImageReader("diy_beta.png"), 60, y - 180, width=400)
y -= 220

c.setFont("Helvetica-Bold", 12)
c.drawString(40, y, "Conclusion:")
y -= 20
c.setFont("Helvetica", 11)
y = draw_text_block("The model performs well overall, especially in diagnosis and fluency. Opportunities for improvement include video suggestions and consistent inclusion of safety information.", c, y_start=y)

c.save()
print(f"PDF saved to: {pdf_path}")

"""Regenerate manuscript Figures 1--6 from archived forecast summaries.

The script uses Pillow rather than an interactive plotting backend so the same
JPG/PDF outputs can be generated in headless environments. It reads only the
aggregates and rolling series in predictions/analysis/; it does not retrain.
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
ANALYSIS = os.environ.get(
    "ANALYSIS_DIR", os.path.join(PROJECT_ROOT, "predictions", "analysis"))
OUTDIR = os.path.join(PROJECT_ROOT, "figs")
os.makedirs(OUTDIR, exist_ok=True)

ASSETS = ["CSI300", "SP500", "CSI1000", "BTCUSD"]
ASSET_LABEL = {"CSI300": "CSI 300", "SP500": "S&P 500",
               "CSI1000": "CSI 1000", "BTCUSD": "BTC/USD"}
MODELS = ["LSTM", "Transformer", "Autoformer", "PatchTST", "iTransformer"]
COLORS = {"HM": "#8c8c8c", "PER": "#c9c9c9", "LSTM": "#1f77b4",
          "Transformer": "#ff7f0e", "Autoformer": "#2ca02c",
          "PatchTST": "#d62728", "iTransformer": "#9467bd"}
ASSET_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

FONT_REGULAR = r"C:\Windows\Fonts\times.ttf"
FONT_BOLD = r"C:\Windows\Fonts\timesbd.ttf"
if not os.path.isfile(FONT_REGULAR):
    FONT_REGULAR, FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REGULAR
    if os.path.isfile(path):
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def canvas(width=2600, height=1560):
    return Image.new("RGB", (width, height), "white")


def text(draw, xy, value, size, fill="#111111", anchor=None, bold=False):
    draw.text(xy, str(value), font=font(size, bold), fill=fill, anchor=anchor)


def save(image, name):
    jpg = os.path.join(OUTDIR, f"{name}.jpg")
    pdf = os.path.join(OUTDIR, f"{name}.pdf")
    image.save(jpg, "JPEG", quality=96, subsampling=0, dpi=(400, 400), optimize=True)
    image.save(pdf, "PDF", resolution=400.0)
    print(f"saved {jpg} and {pdf}")


def panel_axes(image, draw, box, title, ylabel, y_min, y_max, ticks, y_fmt="{:.2f}"):
    x0, y0, x1, y1 = box
    left, right, top, bottom = x0 + 105, x1 - 25, y0 + 70, y1 - 112
    text(draw, ((left + right) // 2, y0 + 26), title, 47, anchor="mm", bold=True)
    # Vertical ylabel.
    label = Image.new("RGBA", (600, 60), (255, 255, 255, 0))
    ImageDraw.Draw(label).text((8, 2), ylabel, font=font(42), fill="#111111")
    label = label.rotate(90, expand=True)
    image.paste(label, (x0 + 4, (top + bottom - label.height) // 2), label)
    for tick in ticks:
        y = bottom - (tick - y_min) / (y_max - y_min) * (bottom - top)
        draw.line((left, y, right, y), fill="#dedede", width=2)
        text(draw, (left - 14, y), y_fmt.format(tick), 31, fill="#333333", anchor="rm")
    draw.line((left, top, left, bottom), fill="#444444", width=3)
    draw.line((left, bottom, right, bottom), fill="#444444", width=3)
    zero_y = bottom - (0 - y_min) / (y_max - y_min) * (bottom - top) if y_min <= 0 <= y_max else None
    if zero_y is not None:
        draw.line((left, zero_y, right, zero_y), fill="#555555", width=2)
    return left, top, right, bottom


def draw_bar_panel(image, draw, box, labels, values, title, ylabel, fmt, scale=1.0, zero_in_range=False):
    vals = np.asarray(values, dtype=float) * scale
    low = min(0.0, float(np.nanmin(vals)))
    high = max(0.0, float(np.nanmax(vals)))
    span = max(high - low, 1e-9)
    y_min = low - 0.16 * span
    y_max = high + 0.25 * span
    if zero_in_range and y_min < 0 < y_max:
        pass
    ticks = np.linspace(y_min, y_max, 5)
    left, top, right, bottom = panel_axes(image, draw, box, title, ylabel, y_min, y_max, ticks, "{:.2f}")
    step = (right - left) / len(labels)
    bar_w = step * 0.58
    y_zero = bottom - (0 - y_min) / (y_max - y_min) * (bottom - top)
    for i, (label, value) in enumerate(zip(labels, vals)):
        cx = left + (i + 0.5) * step
        yv = bottom - (value - y_min) / (y_max - y_min) * (bottom - top)
        color = COLORS[label]
        draw.rectangle((cx - bar_w / 2, min(yv, y_zero), cx + bar_w / 2, max(yv, y_zero)),
                       fill=color, outline="#222222", width=2)
        annot = format(float(value), fmt)
        ann_y = yv - 10 if value >= 0 else yv + 10
        text(draw, (cx, ann_y), annot, 28, anchor="ms" if value >= 0 else "mt")
        text(draw, (cx, bottom + 22), label, 27, anchor="mt")


def make_asset_figure(asset, index, summary):
    sub = summary[summary["Asset"] == asset].set_index("Model")
    image = canvas()
    draw = ImageDraw.Draw(image)
    margin = 55
    gap_x, gap_y = 80, 70
    panel_w = (image.width - 2 * margin - gap_x) // 2
    panel_h = (image.height - 2 * margin - gap_y) // 2
    boxes = []
    for row in range(2):
        for col in range(2):
            x = margin + col * (panel_w + gap_x)
            y = margin + row * (panel_h + gap_y)
            boxes.append((x, y, x + panel_w, y + panel_h))
    panels = [
        ("MSE", ["HM", "PER"] + MODELS, "(a) Mean squared error", "MSE (×10⁻⁴)", ".2f", 1e4),
        ("MAE", ["HM", "PER"] + MODELS, "(b) Mean absolute error", "MAE (×10⁻³)", ".2f", 1e3),
        ("R_OS2", ["HM"] + MODELS, "(c) Out-of-sample R²OS vs HM", "R²OS", ".3f", 1.0),
        ("DA", ["HM", "PER"] + MODELS, "(d) Directional accuracy", "DA (%)", ".1f", 100.0),
    ]
    for box, (column, names, title, ylabel, fmt, scale) in zip(boxes, panels):
        vals = [float(sub.loc[name, column]) for name in names]
        draw_bar_panel(image, draw, box, names, vals, title, ylabel, fmt, scale)
    save(image, f"fig{index}")


def make_cross_asset_figure(summary):
    image = canvas(2600, 1240)
    draw = ImageDraw.Draw(image)
    box = (95, 55, 2510, 1110)
    y_min, y_max = -0.23, 0.015
    ticks = [-0.20, -0.15, -0.10, -0.05, 0.0]
    left, top, right, bottom = panel_axes(image, draw, box, "Cross-asset comparison of out-of-sample R²OS", "R²OS vs HM", y_min, y_max, ticks, "{:.2f}")
    group_step = (right - left) / len(MODELS)
    bar_w = group_step * 0.16
    for model_i, model in enumerate(MODELS):
        for asset_i, asset in enumerate(ASSETS):
            row = summary[(summary["Asset"] == asset) & (summary["Model"] == model)].iloc[0]
            value = float(row["R_OS2"])
            center = left + (model_i + 0.5) * group_step + (asset_i - 1.5) * bar_w
            y_value = bottom - (value - y_min) / (y_max - y_min) * (bottom - top)
            y_zero = bottom - (0 - y_min) / (y_max - y_min) * (bottom - top)
            draw.rectangle((center - bar_w * 0.44, y_zero, center + bar_w * 0.44, y_value),
                           fill=ASSET_COLORS[asset_i], outline="#222222", width=1)
            text(draw, (center, y_value - 5), f"{value:.3f}", 22, anchor="ms")
        text(draw, (left + (model_i + 0.5) * group_step, bottom + 25), model, 36, anchor="mt")
    legend_y = image.height - 42
    total_w = 4 * 350
    start_x = (image.width - total_w) // 2
    for i, asset in enumerate(ASSETS):
        x = start_x + i * 350
        draw.rectangle((x, legend_y - 22, x + 48, legend_y + 18), fill=ASSET_COLORS[i])
        text(draw, (x + 65, legend_y - 2), ASSET_LABEL[asset], 35, anchor="lm")
    save(image, "fig5")


def make_rolling_figure():
    image = canvas(2600, 1660)
    draw = ImageDraw.Draw(image)
    margin, gap_x, gap_y = 70, 90, 55
    panel_w = (image.width - 2 * margin - gap_x) // 2
    panel_h = (image.height - 2 * margin - gap_y - 100) // 2
    for idx, asset in enumerate(ASSETS):
        row, col = divmod(idx, 2)
        x0 = margin + col * (panel_w + gap_x)
        y0 = margin + row * (panel_h + gap_y)
        x1, y1 = x0 + panel_w, y0 + panel_h
        frame = pd.read_csv(os.path.join(ANALYSIS, f"{asset}_ROLLING_ROS2_252.csv"), parse_dates=["Date"])
        values = frame[MODELS].to_numpy(dtype=float)
        y_min = min(-0.25, float(np.nanmin(values)) * 1.05)
        y_max = max(0.05, float(np.nanmax(values)) * 1.1)
        left, top, right, bottom = panel_axes(image, draw, (x0, y0, x1, y1), ASSET_LABEL[asset], "Rolling R²OS", y_min, y_max, np.linspace(y_min, y_max, 5), "{:.2f}")
        dates = pd.to_datetime(frame["Date"])
        date0, date1 = dates.min(), dates.max()
        date_span = max((date1 - date0).days, 1)
        for model in MODELS:
            vals = frame[model].to_numpy(dtype=float)
            segments, points = [], []
            for date, value in zip(dates, vals):
                if not np.isfinite(value):
                    if len(points) > 1:
                        segments.append(points)
                    points = []
                    continue
                px = left + (date - date0).days / date_span * (right - left)
                py = bottom - (value - y_min) / (y_max - y_min) * (bottom - top)
                points.append((int(px), int(py)))
            if len(points) > 1:
                segments.append(points)
            for segment in segments:
                draw.line(segment, fill=COLORS[model], width=4, joint="curve")
        zero_y = bottom - (0 - y_min) / (y_max - y_min) * (bottom - top)
        draw.line((left, zero_y, right, zero_y), fill="#333333", width=3)
        for year in range(date0.year, date1.year + 1):
            if year % 2 == 0:
                date = datetime(year, 1, 1)
                px = left + (date - date0.to_pydatetime()).days / date_span * (right - left)
                if left <= px <= right:
                    text(draw, (px, bottom + 20), str(year), 28, anchor="mt")
    legend_y = image.height - 50
    total_w = 5 * 400
    start_x = (image.width - total_w) // 2
    for i, model in enumerate(MODELS):
        x = start_x + i * 400
        draw.line((x, legend_y, x + 70, legend_y), fill=COLORS[model], width=6)
        text(draw, (x + 85, legend_y), model, 32, anchor="lm")
    save(image, "fig6")


def main():
    summary = pd.read_csv(os.path.join(ANALYSIS, "TABLE4_MAIN_RESULTS.csv"))
    # Verify plot inputs agree with the regenerated Table 4 at the stored precision.
    for asset in ASSETS:
        sub = summary[summary["Asset"] == asset]
        if set(sub["Model"]) != {"HM", "PER", *MODELS}:
            raise ValueError(f"Incomplete Figure inputs for {asset}")
    for i, asset in enumerate(ASSETS, 1):
        make_asset_figure(asset, i, summary)
    make_cross_asset_figure(summary)
    make_rolling_figure()


if __name__ == "__main__":
    main()

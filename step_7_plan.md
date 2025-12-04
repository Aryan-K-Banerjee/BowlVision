Nice, we’re in “design doc mode” now 😄
Here’s the full set of JSON structures + architectures, written in the same style as your sample.

---

## 🌐 Overall Flow

You have **three clean stages**:

1. **JSON Creation** – combine raw artifacts into a single `report.json` that describes sections, metrics, and desired screenshots.
2. **Screenshot Engine** – read `report.json`, generate all screenshots according to the screenshot specs.
3. **HTML Creation** – read `report.json` + generated screenshots and render the final HTML report.

Each stage is modular and can be extended independently.

---

## 📦 `report.json` – Top-Level Structure (Fields + 1-liners)

* **`version`** – Schema version for `report.json` so the format can evolve safely over time.
* **`header`** – Object containing all top-level session and bowler information shown at the top of the report.
* **`video_events_classification`** – Object describing which videos exist, key events per view, and classification info for the bowler.
* **`scores`** – Object holding the overall scores, breakdowns, and mini “dashboard” data.
* **`metrics`** – List of metric entries, each with values, analysis text, and screenshot specs.

You can think of `report.json` as the **single source of truth** for what the report should contain, but *not* how it is styled.

---

## 🧩 `header` Block Structure (Fields + 1-liners)

* **`session_info`** – Session metadata (name, description, date, location if any).
* **`bowler_info`** – Bowler metadata (name, type, hand, brief description).
* **`bowler_image`** – Path or ID for the bowler’s portrait image.
* **`score_summary`** – Short summary of overall scores (e.g. total score and key highlights).
* **`classification_summary`** – Short description of the bowler’s style or “profile” generated from classification logic.
* **`video_existence_summary`** – Simple summary of which input videos are present (side/back) and any warnings if one is missing.

This block feeds the **hero/header area** of the report and gives the user context before diving into details.

---

## 🎥 `video_events_classification` Block (Fields + 1-liners)

* **`video_summary`** – List or map describing each input video (e.g. `side`, `back`, resolution, fps, existence flags).
* **`events_by_view`** – Structure listing key events (Jump, FFC, Release, etc.) for each view, including the frame numbers.
* **`classification`** – Object containing classification output for the bowler (e.g. type labels or “model-based” tags).
* **`screenshots`** – List of screenshot specs used for this section (e.g. 4 key events from each view, classification example frames).

This section tells the user **what video data was available**, shows **key event snapshots**, and anchors the classification visually.

---

## 📊 `scores` Block (Fields + 1-liners)

* **`overall_score`** – Single high-level score or grade summarizing the bowler’s performance.
* **`subscores`** – Breakdown of scores by category (e.g. run-up, gather, brace, follow-through).
* **`description`** – Short narrative summary of what the scores mean (rule-based or LLM-generated elsewhere).
* **`metrics_overview`** – Compact list summarizing each metric’s score, rating, and maybe a tag (e.g. “strong”, “needs work”).

This block powers the **score dashboard section** of the report so users can quickly see strengths and weaknesses.

---

## 📐 `metrics` Entries (Fields + 1-liners)

Each metric in `metrics` is an object like:

* **`id`** – Stable identifier for the metric (e.g. `"front_leg_brace"`).
* **`name`** – Human-readable name of the metric (e.g. `"Front Leg Brace at FFC"`).
* **`group`** – Optional grouping label (e.g. `"Brace"`, `"Run-up"`, `"Arm Path"`).
* **`value`** – Numeric value or main measurement for this metric (e.g. `191.3`).
* **`unit`** – Unit for the metric value (e.g. `"degrees"`, `"ms"`, `"ratio"`).
* **`score`** – Score for this metric on a fixed scale (e.g. `0–10`).
* **`rating`** – Qualitative rating (e.g. `"ideal"`, `"okay"`, `"needs work"`).
* **`tags`** – Optional flags like `"key_focus"`, `"secondary"`, `"warning"` to help UI prioritize.
* **`description`** – Short explanation of what the metric measures and why it matters.
* **`analysis`** – Short analysis or coaching note specific to this bowler’s value.
* **`screenshots`** – List of screenshot specs describing which images to generate for this metric.

This gives the metric section enough information to show: **text + numbers + pictures** all tied together.

---

## 🖼 Screenshot Spec JSON (Fields + 1-liners)

This is the **minimal spec** the screenshot engine needs, and it is reused in multiple places (video events section, metrics, etc.).

* **`view`** – Which video stream to read from (e.g. `"side"` or `"back"`).
* **`frames`** – List of frame numbers to grab from the chosen video.
* **`blended`** – Whether multiple frames should be blended into a single base image.
* **`types`** – List of render modes to output (e.g. `["original", "skeleton", "overlay"]`).
* **`angles`** – List of angle functions to run, each computing `(p1, p2, p3)` from keypoints.
* **`crop_strategy`** – Name of the crop function used to compute the final `(x, y, w, h)` after drawing.
* **`output_name`** – Base filename for the screenshot; renderer can append suffixes per type (e.g. `_overlay.png`).

Every screenshot spec is a **pure rendering instruction** — no scores, no text, no UI logic.

---

## 🧱 Stage 1 – JSON Creation Architecture (Compact)

This stage reads all raw artifacts and builds a single `report.json` with sections, metrics, and screenshot specs.

* **`generate_final_json.py`** – Top-level orchestrator: loads raw artifact JSONs, calls structure builders for each section/metric, assembles the final `report.json`, and writes it to disk.
* **`json_structure_directory.py`** – Registry mapping section/metric identifiers (e.g. `"header"`, `"video_events"`, `"front_leg_brace"`) to builder functions in `structure/`.
* **`structure/`** – Directory containing one file per section/metric group, each with a function that takes raw artifacts and returns the data + screenshot specs for that section.

You can think of this stage as: **“take all the inputs, decide what the report should contain, and encode that in one big JSON tree.”**

---

### Example `structure/` layout (descriptive)

* **`structure/header.py`** – Builds the `header` block using `session_info`, `bowler_info`, `bowler_image`, overall scores, and classification summary.
* **`structure/video_events_classification.py`** – Builds the `video_events_classification` block and its screenshot specs (e.g. 4 events per view).
* **`structure/scores.py`** – Builds the `scores` block from `scores.json` and high-level metric summaries.
* **`structure/metrics_front_leg_brace.py`** – Builds one metric entry for `"front_leg_brace"`, including values, analysis, and screenshot specs.
* **`structure/metrics_*.py`** – Additional files that define other metrics in a similar way.

Adding a new metric or section simply means adding a new file to `structure/` and registering it in `json_structure_directory.py`.

---

## 🧱 Stage 2 – Screenshot Engine Architecture (Compact)

This stage reads `report.json`, finds all screenshot specs, and generates the PNGs.

* **`screenshot_engine.py`** – Core orchestrator: loads frames from videos, blends if needed, calls type/angle/crop functions via registries, and saves outputs using `output_name`.
* **`type_registry.py`** – Maps type names (`"original"`, `"skeleton"`, `"overlay"`) to functions implemented in `types/`.
* **`angle_registry.py`** – Maps angle names (e.g. `"front_knee_interpolated"`) to geometry functions in `angles/` that return `(p1, p2, p3)`.
* **`crop_registry.py`** – Maps crop names (`"front_leg"`, `"full_body_centered"`) to crop functions in `crops/`.
* **`types/`** – Contains one file per render mode (original, skeleton, overlay, etc.), each taking a frame + keypoints + angle points and returning a rendered frame.
* **`angles/`** – Contains one file per angle, each computing the three points needed to draw that angle from the keypoints (using shared `location_constants`).
* **`crops/`** – Contains one file per crop strategy, each computing the crop rectangle based on the rendered frame and keypoints.

In one line: the **screenshot spec** in `report.json` describes *what* to render, the registries resolve names to functions, and `screenshot_engine.py` wires everything together into actual PNGs.

---

## 🧱 Stage 3 – HTML Creation Architecture (Compact)

This stage uses `report.json` and the generated screenshots to create the final styled HTML report.

* **`html_engine.py`** – Top-level orchestrator: loads `report.json`, prepares template context, calls section renderers, and writes the final `report.html`.
* **`html_structure_directory.py`** – Registry mapping section/metric identifiers (e.g. `"header"`, `"video_events_classification"`, `"scores"`, `"metric_card"`) to functions that know how to render them in HTML.
* **`templates/`** – Directory of Jinja2 (or similar) templates, including a base layout and partials for sections and metric cards.
* **`static/`** – Folder with CSS (e.g. `report.css`) and any icons or assets used by the report.

Here, the **data and screenshot filenames** come from `report.json`, and the **visual layout** comes from the templates and section renderers.

---

### Example HTML structure modules (descriptive)

* **`templates/base_report.html`** – Main HTML shell with slots for header, video/events, scores, and metrics sections.
* **`templates/header.html`** – Partial template for the header block (session, bowler, summary).
* **`templates/video_events_classification.html`** – Partial template that lays out event screenshots and classification text.
* **`templates/scores.html`** – Partial template for the overall score dashboard.
* **`templates/metric_card.html`** – Partial template for rendering each metric entry, including its screenshots and analysis text.

Section renderer functions in `html_structure_directory.py` pick the right template, fill it with the corresponding part of `report.json`, and `html_engine.py` stitches everything into a single HTML file.

---

### 🧵 Big Picture Summary

* **Stage 1 (JSON creation)**: Decide *what* the report contains and write it all into `report.json`.
* **Stage 2 (Screenshot engine)**: Use screenshot specs from `report.json` to render and save all the images.
* **Stage 3 (HTML creation)**: Use `report.json` + the generated images to render a clean, styled HTML report.

Everything is **registry-driven and file-based**, so an LLM (or another dev) can safely extend the system by adding new sections, metrics, or render modes without touching the core orchestrators.

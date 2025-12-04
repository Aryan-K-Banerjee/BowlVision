# core/image/image_utils.py
'''--------------------------------------------------------------------------
Utility functions for image/video generation shared by modules in
`core.image` and `core.cv.vidgen`.
Functions provided:
 - read_joints_csv: parse extract_joints CSV -> (frames_map, inferred_fps)
 - read_angles_csv: simple reader for angle CSVs (frame -> angle value)
 - draw_angle_arc: draw a shaded angle arc and label on an image
 - get_pose_connections: return mediapipe pose connections or a fallback
-------------------------------------------------------------------------'''
import os
import csv
import math
from statistics import median
from typing import Dict, List, Tuple, Optional

import cv2
import numpy as np


def read_joints_csv(joints_csv_location: str) -> Tuple[Dict[int, List[Tuple[float, float, float, float]]], float]:
	"""Read a joints CSV (output of extract_joints) and return (frames_map, inferred_fps).

	frames_map: mapping frame_index -> list of (x,y,z,vis) floats
	inferred_fps: float FPS inferred from time_s column when present (0.0 if unavailable)
	"""
	frames: Dict[int, List[Tuple[float, float, float, float]]] = {}
	times: List[float] = []

	if not os.path.exists(joints_csv_location):
		raise FileNotFoundError(joints_csv_location)

	with open(joints_csv_location, 'r', encoding='utf-8', newline='') as fh:
		reader = csv.reader(fh)
		header = next(reader, None)
		if header is None:
			return frames, 0.0

		num_extra = max(0, len(header) - 2)
		num_landmarks = num_extra // 4 if num_extra >= 4 else 0

		for row in reader:
			if not row:
				continue
			try:
				frame_idx = int(float(row[0]))
			except Exception:
				continue
			try:
				time_s = float(row[1])
				times.append(time_s)
			except Exception:
				time_s = None

			lm_vals: List[Tuple[float, float, float, float]] = []
			for i in range(num_landmarks):
				base = 2 + i * 4
				try:
					x = float(row[base])
					y = float(row[base + 1])
					z = float(row[base + 2])
					vis = float(row[base + 3])
				except Exception:
					x = y = z = vis = 0.0
				lm_vals.append((x, y, z, vis))

			frames[frame_idx] = lm_vals

	inferred_fps = 0.0
	if len(times) >= 2:
		deltas = [t2 - t1 for t1, t2 in zip(times[:-1], times[1:]) if (t2 - t1) > 1e-6]
		if deltas:
			med = median(deltas)
			if med > 1e-6:
				inferred_fps = round(1.0 / med, 2)

	return frames, inferred_fps


def read_angles_csv(angles_csv_location: str) -> Dict[int, float]:
	"""Read a simple angles CSV with header beginning with 'frame' and a column
	named 'front_knee_angle'. Returns mapping frame->angle_value.
	If file missing or unreadable returns empty dict.
	"""
	angles: Dict[int, float] = {}
	if not angles_csv_location or not os.path.exists(angles_csv_location):
		return angles
	try:
		with open(angles_csv_location, 'r', encoding='utf-8', newline='') as fh:
			reader = csv.reader(fh)
			header = next(reader, None)
			if header is None:
				return angles
			col_idx = None
			for i, h in enumerate(header):
				if h.strip().lower() == 'front_knee_angle':
					col_idx = i
					break

			for row in reader:
				if not row:
					continue
				try:
					fi = int(float(row[0]))
				except Exception:
					continue
				val = 0.0
				if col_idx is not None and col_idx < len(row):
					try:
						val = float(row[col_idx])
					except Exception:
						val = 0.0
				angles[fi] = val
	except Exception:
		return {}
	return angles


def draw_angle_arc(canvas, p1, p2, p3, angle_deg: Optional[float] = None, color=(0, 200, 0)):
	"""Draw a shaded angle arc (sector) on `canvas` with vertex at p2 between p1 and p3.

	- p1,p2,p3: (x,y) pixel coordinates
	- angle_deg: optional angle value to draw; if >180 the function will draw the
	  reflex arc on the opposite side so the label matches the visual
	"""
	try:
		x1, y1 = float(p1[0]), float(p1[1])
		x2, y2 = float(p2[0]), float(p2[1])
		x3, y3 = float(p3[0]), float(p3[1])
	except Exception:
		return

	v1 = (x1 - x2, y1 - y2)
	v2 = (x3 - x2, y3 - y2)
	mag1 = math.hypot(*v1)
	mag2 = math.hypot(*v2)
	if mag1 < 1e-3 or mag2 < 1e-3:
		return

	a1 = math.degrees(math.atan2(v1[1], v1[0]))
	a2 = math.degrees(math.atan2(v2[1], v2[0]))

	def normalize_deg(a):
		while a < 0:
			a += 360
		while a >= 360:
			a -= 360
		return a

	a1n = normalize_deg(a1)
	a2n = normalize_deg(a2)

	diff = a2n - a1n
	if diff <= -180:
		diff += 360
	elif diff > 180:
		diff -= 360

	draw_diff = diff
	if angle_deg is not None and angle_deg > 180:
		if diff > 0:
			draw_diff = diff - 360
		else:
			draw_diff = diff + 360

	steps = max(6, int(abs(draw_diff) / 5) + 2)
	radius = int(max(12, min(80, (mag1 + mag2) / 4)))
	arc_pts = []
	for i in range(steps + 1):
		t = i / steps
		ang = math.radians(a1n + draw_diff * t)
		px = int(round(x2 + math.cos(ang) * radius))
		py = int(round(y2 + math.sin(ang) * radius))
		arc_pts.append((px, py))

	poly = [(int(round(x2)), int(round(y2)))] + arc_pts
	cv2.fillPoly(canvas, [np.array(poly, dtype=np.int32)], color)
	cv2.polylines(canvas, [np.array(arc_pts, dtype=np.int32)], False, (0, 255, 0), 1, lineType=cv2.LINE_AA)

	if angle_deg is None:
		dot = v1[0] * v2[0] + v1[1] * v2[1]
		angle_deg = math.degrees(math.acos(max(-1.0, min(1.0, dot / (mag1 * mag2)))))

	bisector = math.radians(normalize_deg(a1n + draw_diff / 2.0))
	text_radius = radius + 18
	tx = int(round(x2 + math.cos(bisector) * text_radius))
	ty = int(round(y2 + math.sin(bisector) * text_radius))

	text = f"{angle_deg:.2f}"
	(tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
	tx0 = tx - tw // 2
	ty0 = ty + th // 2
	cv2.rectangle(canvas, (tx0 - 4, ty0 - th - 4), (tx0 + tw + 4, ty0 + 4), (0, 0, 0), -1)
	cv2.putText(canvas, text, (tx0, ty0), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, lineType=cv2.LINE_AA)


def get_pose_connections():
	"""Return a list of pose connections. Try to use mediapipe if available,
	otherwise return a sensible fallback list.
	"""
	try:
		import mediapipe as mp
		return list(mp.solutions.pose.POSE_CONNECTIONS)
	except Exception:
		return [
			(11, 13), (13, 15),
			(12, 14), (14, 16),
			(11, 12),
			(23, 25), (25, 27),
			(24, 26), (26, 28),
			(23, 24),
		]

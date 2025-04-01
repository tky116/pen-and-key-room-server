# src/features/feature_extractor.py

from typing import List, Dict, Any
import numpy as np
from dataclasses import dataclass

@dataclass
class Point3D:
    x: float
    y: float
    z: float


class FeatureExtractor:
    def __init__(self, epsilon: float = 0.01):
        """ 特徴量抽出器の初期化

        Args:
            epsilon (float): Douglas-Peuckerアルゴリズムの許容誤差
        """
        self.epsilon = epsilon

    def extract_features(self, drawing_data) -> Dict[str, Any]:
        """ 描画データから特徴量を抽出

        Args:
            drawing_data: 描画データ
        Returns:
            Dict[str, Any]: 抽出された特徴
        """
        stroke_features = []
        for line in drawing_data.draw_lines:
            positions = [
                {"x": pos.x, "y": pos.y, "z": pos.z} for pos in line.positions
                ]
            features = self.calculate_stroke_features(positions)
            stroke_features.append(features)

        global_features = self.calculate_global_features(stroke_features)

        return {
            "strokes": stroke_features,
            "global_features": global_features
        }

    def distance_point_to_line(
            self,
            point: Point3D,
            line_start: Point3D,
            line_end: Point3D
            ) -> float:
        """ 点と線分の距離を計算

        Args:
            point (Point3D): 点
            line_start (Point3D): 線分の始点
            line_end (Point3D): 線分の終点
        Returns:
            float: 点と線分の距離
        """
        if line_start.x == line_end.x and line_start.y == line_end.y and line_start.z == line_end.z:
            return float(np.sqrt((point.x - line_start.x)**2 +
                        (point.y - line_start.y)**2 +
                        (point.z - line_start.z)**2))

        numerator = float(np.abs(
            (line_end.x - line_start.x) * (line_start.y - point.y) -
            (line_start.x - point.x) * (line_end.y - line_start.y)
        ))
        denominator = float(np.sqrt(
            (line_end.x - line_start.x)**2 +
            (line_end.y - line_start.y)**2 +
            (line_end.z - line_start.z)**2
        ))
        return numerator / denominator

    def douglas_peucker(
            self,
            points: List[Point3D],
            epsilon: float
            ) -> List[Point3D]:
        """ Douglas-Peuckerアルゴリズムによる点列の簡略化

        Args:
            points (List[Point3D]): 点列
            epsilon (float): 許容誤差
        Returns:
            List[Point3D]: 簡略化された点列
        """
        if len(points) <= 2:
            return points

        # 最大距離とそのインデックスを見つける
        dmax = 0
        index = 0
        for i in range(1, len(points) - 1):
            d = self.distance_point_to_line(points[i], points[0], points[-1])
            if d > dmax:
                index = i
                dmax = d

        # 再帰的に処理
        if dmax > epsilon:
            rec_results1 = self.douglas_peucker(points[:index + 1], epsilon)
            rec_results2 = self.douglas_peucker(points[index:], epsilon)
            return rec_results1[:-1] + rec_results2
        else:
            return [points[0], points[-1]]

    def calculate_stroke_features(
            self,
            positions: List[Dict[str, float]]
            ) -> Dict[str, Any]:
        """ 1つのストロークの特徴量を計算

        Args:
            positions (List[Dict[str, float]]): ストロークの点列
        Returns:
            Dict[str, Any]: ストロークの特
        """
        # Point3Dオブジェクトのリストに変換
        points = [Point3D(p['x'], p['y'], p['z']) for p in positions]

        # 点列を簡略化
        simplified_points = self.douglas_peucker(points, self.epsilon)

        # バウンディングボックスの計算
        x_coords = [p.x for p in points]
        y_coords = [p.y for p in points]
        z_coords = [p.z for p in points]

        # ストロークの長さを計算
        total_length = 0.0
        for i in range(len(points) - 1):
            dx = points[i+1].x - points[i].x
            dy = points[i+1].y - points[i].y
            dz = points[i+1].z - points[i].z
            total_length += float(np.sqrt(dx*dx + dy*dy + dz*dz))

        # 始点と終点が近いかチェック（閉じたストロークかどうか）
        start = points[0]
        end = points[-1]
        threshold = 0.05    # 閾値
        is_closed = float(np.sqrt(
            (end.x - start.x)**2 +
            (end.y - start.y)**2 +
            (end.z - start.z)**2
        )) < threshold

        features = {
            "points_count": len(simplified_points),
            "bounding_box": {
                "width": float(max(x_coords) - min(x_coords)),
                "height": float(max(y_coords) - min(y_coords)),
                "depth": float(max(z_coords) - min(z_coords))
            },
            "start_point": {
                "x": float(points[0].x),
                "y": float(points[0].y),
                "z": float(points[0].z)
            },
            "end_point": {
                "x": float(points[-1].x),
                "y": float(points[-1].y),
                "z": float(points[-1].z)
            },
            "total_length": total_length,
            "is_closed": bool(is_closed),
            "simplified_points": [
                {"x": float(p.x), "y": float(p.y), "z": float(p.z)}
                for p in simplified_points
            ]
        }

        return features

    def calculate_global_features(self, strokes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ 全ストロークの大域的特徴を計算

        Args:
            strokes (List[Dict[str, Any]]): ストロークの特徴量リスト

        Returns:
            Dict[str, Any]: 大域的特徴量
        """
        all_points = []
        for stroke in strokes:
            all_points.extend(
                [Point3D(p['x'], p['y'], p['z'])
                    for p in stroke['simplified_points']]
            )

        x_coords = [p.x for p in all_points]
        y_coords = [p.y for p in all_points]
        z_coords = [p.z for p in all_points]

        width = float(max(x_coords) - min(x_coords))
        height = float(max(y_coords) - min(y_coords))

        features = {
            "total_strokes": len(strokes),
            "total_points": len(all_points),
            "aspect_ratio": float(width / height if height != 0 else 0),
            "centroid": {
                "x": float(sum(x_coords) / len(x_coords)),
                "y": float(sum(y_coords) / len(y_coords)),
                "z": float(sum(z_coords) / len(z_coords))
            }
        }

        return features

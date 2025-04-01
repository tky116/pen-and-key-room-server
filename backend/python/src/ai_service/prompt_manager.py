# src/ai_service/prompt_manager.py

from typing import List, Dict, Any
from src.proto.drawing_pb2 import DrawingData


class PromptManager:
    @staticmethod
    def prepare_drawing_info(drawing: DrawingData, features: Dict[str, Any]) -> Dict[str, Any]:
        """描画データの情報を整形

        Args:
            drawing (DrawingData): 描画データ
            features (Dict[str, Any]): 特徴量
        Returns:
            Dict[str, Any]: 描画データの情
        """
        drawing_info = {
            "draw_lines": [
                {
                    "positions": [[pos.x, pos.y, pos.z] for pos in line.positions],
                    "width": line.width,
                    "color": (
                        f"#{int(line.color.r*255):02x}{int(line.color.g*255):02x}{int(line.color.b*255):02x}"
                        if line.color
                        else None
                    ),
                }
                for line in drawing.draw_lines
            ],
            "center": {"x": drawing.center.x, "y": drawing.center.y, "z": drawing.center.z},
        }

        global_features = features.get("global_features", {})
        drawing_info.update(
            {
                "total_strokes": global_features.get("total_strokes", 0),
                "total_points": global_features.get("total_points", 0),
                "features": {
                    "global": features.get("global_features", {}),
                    "strokes": features.get("strokes", []),
                },
            }
        )

        return drawing_info

    @staticmethod
    def create_system_prompt(shape_infos: List[Dict[str, str]]) -> str:
        """システムプロンプトを作成（英語リクエスト & 日本語レスポンス）

        Args:
            shape_infos (List[Dict[str, str]]): 形状情報
        Returns:
            str: システムプロンプト
        """
        shape_list = [shape["shape_id"] for shape in shape_infos]
        shapes_desc = [
            f"{shape['shape_id']}: {shape['name_en']} - {shape['description_en']}"
            for shape in shape_infos
        ]

        # 負例の説明を維持
        negative_examples = [
            f"Note: {shape['negative_examples']['en']} are NOT {shape['name_en']}s "
            + f"and should score below {shape['negative_examples']['score_threshold']}%"
            for shape in shape_infos
        ]

        return f"""You are an AI for shape recognition in a 3D VR application.
Identify which of the following shapes the user has drawn in space:
{", ".join(shapes_desc)}

{" ".join(negative_examples)}

Respond strictly in the following JSON format (Reply in Japanese only):
```json
{{
    "shape_id": "識別された形状ID",
    "score": 0-100,
    "reason": "必ず日本語で簡潔に1文で判断理由を説明してください。"
}}
```
Notes:
    Choose only one shape_id from the provided list: [{", ".join(shape_list)}].
    Score represents confidence level (higher = more confident).
    Score must be between 0-100 (Do not exceed this range).
    If the shape resembles a negative example, assign a score below {shape_infos[0]['negative_examples']['score_threshold']}%.
    Keep the reason concise (one sentence).
    Ensure response is fully in Japanese only.
    Strictly follow the exact JSON format.
    Do not create new shape IDs.
"""

    @staticmethod
    def create_data_prompt(drawing_info: Dict[str, Any]) -> str:
        """描画データのプロンプトを作成（英語）

        Args:
            drawing_info (Dict[str, Any]): 描画データの情報
        Returns:
            str: 描画データのプロンプト
        """
        global_features = drawing_info["features"]["global"]
        strokes_info = drawing_info["features"]["strokes"]
        prompt = f"""Analyze the following drawing data:

Global Features:
- Total Strokes: {drawing_info['total_strokes']}
- Total Points: {drawing_info['total_points']}
- Aspect Ratio: {global_features['aspect_ratio']:.3f}
- Centroid: x={global_features['centroid']['x']:.3f}, y={global_features['centroid']['y']:.3f}, z={global_features['centroid']['z']:.3f}

Stroke Details:"""
        for i, stroke in enumerate(strokes_info, 1):
            prompt += f"""
Stroke {i}:
- Point Count: {stroke['points_count']}
- Bounding Box: width={stroke['bounding_box']['width']:.3f}, height={stroke['bounding_box']['height']:.3f}, depth={stroke['bounding_box']['depth']:.3f}
- Start Point: x={stroke['start_point']['x']:.3f}, y={stroke['start_point']['y']:.3f}, z={stroke['start_point']['z']:.3f}
- End Point: x={stroke['end_point']['x']:.3f}, y={stroke['end_point']['y']:.3f}, z={stroke['end_point']['z']:.3f}
- Total Length: {stroke['total_length']:.3f}
- Is Closed: {'Yes' if stroke['is_closed'] else 'No'}"""
        return prompt

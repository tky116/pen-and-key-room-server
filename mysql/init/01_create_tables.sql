-- VRAcademyAuditionServer/mysql/init/01_create_tables.sql

USE vrdb01;

-- シーンマスタ
CREATE TABLE IF NOT EXISTS mstr_scenes (
    scene_id VARCHAR(100) PRIMARY KEY COMMENT 'シーンID(Unityのシーン名)',
    shapes_list JSON NOT NULL COMMENT '利用可能な形状リスト',
    description_ja TEXT COMMENT '説明(日本語)',
    description_en TEXT COMMENT '説明(英語)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
) COMMENT 'シーンマスタ';

-- 形状マスタ
CREATE TABLE IF NOT EXISTS mstr_shapes (
    shape_id VARCHAR(50) PRIMARY KEY COMMENT '形状ID',
    prefab_name VARCHAR(100) NOT NULL COMMENT 'Unityのプレハブ名',
    threshold TINYINT(3) DEFAULT 100 COMMENT '判定閾値',
    name_ja VARCHAR(50) NOT NULL COMMENT '表示名(日本語)',
    name_en VARCHAR(50) NOT NULL COMMENT '表示名(英語)',
    description_ja TEXT COMMENT '説明(日本語)',
    description_en TEXT COMMENT '説明(英語)',
    positive_examples JSON COMMENT '正例データ',
    negative_examples JSON COMMENT '負例データ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
) COMMENT '形状マスタ';

-- 描画データ
CREATE TABLE IF NOT EXISTS drawings (
    drawing_id VARCHAR(36) PRIMARY KEY COMMENT '描画ID',
    scene_id VARCHAR(100) NOT NULL COMMENT 'シーンID',
    draw_timestamp BIGINT NOT NULL COMMENT '描画タイムスタンプ',
    draw_lines JSON NOT NULL COMMENT '描画ラインデータ',
    center_x FLOAT COMMENT '中心座標X',
    center_y FLOAT COMMENT '中心座標Y',
    center_z FLOAT COMMENT '中心座標Z',
    use_ai BOOLEAN DEFAULT FALSE COMMENT 'AIを使用するかどうか',
    client_id VARCHAR(100) COMMENT 'クライアントID',
    client_info JSON COMMENT 'クライアント情報',
    metadata JSON COMMENT 'メタデータ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    FOREIGN KEY (scene_id) REFERENCES mstr_scenes(scene_id)
) COMMENT '描画データ';

-- 描画データの形状特徴量データ
CREATE TABLE IF NOT EXISTS shape_features (
    feature_id VARCHAR(36) PRIMARY KEY COMMENT '特徴量ID',
    drawing_id VARCHAR(36) NOT NULL COMMENT '描画データID',
    total_strokes INT COMMENT '総ストローク数',
    total_points INT COMMENT '総点数',
    features JSON COMMENT '特徴量データ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    FOREIGN KEY (drawing_id) REFERENCES drawings(drawing_id)
) COMMENT '描画データの形状特徴量データ';

-- AI判定結果
CREATE TABLE IF NOT EXISTS results (
    result_id VARCHAR(36) PRIMARY KEY COMMENT 'AI判定結果ID',
    drawing_id VARCHAR(36) NOT NULL COMMENT '描画データID',
    shape_id VARCHAR(50) NOT NULL COMMENT '判定された形状ID',
    success BOOLEAN DEFAULT TRUE COMMENT '判定成功フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    FOREIGN KEY (drawing_id) REFERENCES drawings(drawing_id)
) COMMENT 'AI判定結果';

-- AI判定の結果詳細
CREATE TABLE IF NOT EXISTS result_details (
    result_id VARCHAR(36) PRIMARY KEY COMMENT 'AI判定結果ID',
    drawing_id VARCHAR(36) COMMENT '描画データID',
    scene_id VARCHAR(100) COMMENT 'シーンID',
    shape_id VARCHAR(50) COMMENT '判定された形状ID',
    success BOOLEAN NOT NULL DEFAULT FALSE COMMENT '判定成功フラグ',
    score TINYINT(3) COMMENT 'AIの判定スコア',
    reasoning TEXT COMMENT '判定理由',
    process_time_ms INT COMMENT '処理時間（ミリ秒）',
    model_name VARCHAR(50) COMMENT '使用したAIモデル名',
    api_response JSON COMMENT 'AI APIのレスポンス全体',
    error_message TEXT COMMENT 'エラーメッセージ',
    client_id VARCHAR(100) COMMENT 'クライアントID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    FOREIGN KEY (result_id) REFERENCES results(result_id),
    FOREIGN KEY (drawing_id) REFERENCES drawings(drawing_id)
) COMMENT 'AI判定の結果詳細';

-- エラーログ
CREATE TABLE IF NOT EXISTS error_logs (
    error_id VARCHAR(36) PRIMARY KEY COMMENT 'エラーログID',
    result_id VARCHAR(36) COMMENT 'AI判定結果ID',
    drawing_id VARCHAR(36) COMMENT '描画データID',
    scene_id VARCHAR(100) COMMENT 'シーンID',
    error_type VARCHAR(50) COMMENT 'エラーの種類',
    error_message TEXT COMMENT 'エラーメッセージ',
    stack_trace TEXT COMMENT 'スタックトレース',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時'
) COMMENT 'エラーログ';

-- インデックス
-- drawings
CREATE INDEX idx_drawings_scene_id ON drawings(scene_id);
CREATE INDEX idx_drawings_timestamp ON drawings(draw_timestamp);
CREATE INDEX idx_drawings_processing ON drawings(use_ai);
CREATE INDEX idx_drawings_client_id ON drawings(client_id);

-- shape_features
CREATE INDEX idx_features_drawing ON shape_features(drawing_id);

-- results
CREATE INDEX idx_results_drawing_id ON results(drawing_id);

-- result_details
CREATE INDEX idx_logs_ai_drawing_id ON result_details(drawing_id);
CREATE INDEX idx_logs_ai_client_id ON result_details(client_id);
CREATE INDEX idx_logs_ai_scene_id ON result_details(scene_id);
CREATE INDEX idx_logs_ai_shape_id ON result_details(shape_id);
CREATE INDEX idx_logs_ai_created_at ON result_details(created_at);
CREATE INDEX idx_logs_ai_success ON result_details(success);

-- 権限設定
CREATE USER IF NOT EXISTS 'db_user'@'%' IDENTIFIED BY 'db_pass';
GRANT SELECT, INSERT, UPDATE, DELETE ON vrdb01.drawings TO 'db_user'@'%';
GRANT SELECT, INSERT ON vrdb01.results TO 'db_user'@'%';
GRANT SELECT, INSERT ON vrdb01.result_details TO 'db_user'@'%';
GRANT SELECT, INSERT ON vrdb01.error_logs TO 'db_user'@'%';
GRANT SELECT ON vrdb01.mstr_scenes TO 'db_user'@'%';
GRANT SELECT ON vrdb01.mstr_shapes TO 'db_user'@'%';
FLUSH PRIVILEGES;
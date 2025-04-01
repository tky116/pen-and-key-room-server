USE vrdb01;

-- シーンマスタの登録
INSERT INTO mstr_scenes (
    scene_id, 
    shapes_list,
    description_ja,
    description_en
) VALUES 
(
    'GrpcTest',
    '["circle", "square", "triangle", "key"]',
    'gRPCのテストシーン',
    'Test scene for gRPC'
),
(
    'TestStage',
    '["key"]',
    'テストステージ',
    'Test stage'
),
(
    'Tutorial',
    '["key"]',
    'チュートリアルステージ',
    'Tutorial stage'
);

USE vrdb01;

-- 形状マスタの登録
INSERT INTO mstr_shapes (
    shape_id,
    prefab_name,
    threshold,
    name_ja,
    name_en,
    description_ja,
    description_en,
    positive_examples,
    negative_examples
) VALUES 
(
    'key',
    'KP_Key',
    50,
    '鍵, カギ, かぎ, キー',
    'key',
    '扉や箱などを開けるための鍵',
    'A key for opening doors and boxes',
    JSON_OBJECT(
        'ja', JSON_ARRAY(
            '通常の鍵',
            'ドアの鍵',
            '引き出しの鍵'
        ),
        'en', JSON_ARRAY(
            'standard key',
            'door key',
            'drawer key'
        ),
        'score_threshold', 80
    ),
    JSON_OBJECT(
        'ja', JSON_ARRAY(
            '南京錠',
            '錠前',
            'ダイヤル錠',
            'カードキー'
        ),
        'en', JSON_ARRAY(
            'padlock',
            'door lock',
            'combination lock',
            'card key'
        ),
        'score_threshold', 20
    )
);
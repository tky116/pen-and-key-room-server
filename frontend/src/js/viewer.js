// 定数定義
const CONSTANTS = {
    COLORS: {
        BACKGROUND: 0x393939,
        GRID: {
            PRIMARY: 0x666666,
            SECONDARY: 0x444444
        }
    },
    CAMERA: {
        FOV: 60,
        NEAR: 0.1,
        FAR: 1000,
        DEFAULT_POSITION: { x: -1.37, y: 1.15, z: 3 },
        DEFAULT_ROTATION: { x: -0.3, y: 0, z: 0 }
    },
    CONTROLS: {
        ROTATION_SPEED: 0.005,
        MOVEMENT_SPEED: 0.003,
        ZOOM_SPEED: 0.001,
        MIN_ZOOM: 0.01
    },
    GRID: {
        SIZE: 10,
        DIVISIONS: 10,
        Y_OFFSET: -0.001
    }
};

// APIクライアントクラス
class APIClient {
    static async handleResponse(response) {
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return response.json();
    }

    static async getDrawings() {
        try {
            const response = await fetch('/api/drawings');
            const result = await this.handleResponse(response);
            return result.data;
        } catch (error) {
            console.error('API Error:', error);
            throw new Error('描画データの取得に失敗しました: ' + error.message);
        }
    }

    static async getDrawing(id) {
        try {
            const response = await fetch(`/api/drawings/${id}`);
            const result = await this.handleResponse(response);
            return result.data;
        } catch (error) {
            console.error('API Error:', error);
            throw new Error('描画データの取得に失敗しました: ' + error.message);
        }
    }
}

// シーン管理クラス
class SceneManager {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.drawingGroup = null;
        this.currentCenter = new THREE.Vector3();
        this.controls = new ControlsManager();
        
        this.init();
        this.setupEventListeners();
    }

    init() {
        this.initScene();
        this.initCamera();
        this.initRenderer();
        this.initLights();
        this.initGrid();
        this.initDrawingGroup();
        
        this.startAnimation();
    }

    initScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(CONSTANTS.COLORS.BACKGROUND);
    }

    initCamera() {
        this.camera = new THREE.PerspectiveCamera(
            CONSTANTS.CAMERA.FOV,
            window.innerWidth / window.innerHeight,
            CONSTANTS.CAMERA.NEAR,
            CONSTANTS.CAMERA.FAR
        );
        
        const pos = CONSTANTS.CAMERA.DEFAULT_POSITION;
        const rot = CONSTANTS.CAMERA.DEFAULT_ROTATION;
        this.camera.position.set(pos.x, pos.y, pos.z);
        this.camera.rotation.set(rot.x, rot.y, rot.z);
    }

    initRenderer() {
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(this.renderer.domElement);
    }

    initLights() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(1, 2, 1);
        
        this.scene.add(ambientLight, directionalLight);
    }

    initGrid() {
        const gridHelper = new THREE.GridHelper(
            CONSTANTS.GRID.SIZE,
            CONSTANTS.GRID.DIVISIONS,
            CONSTANTS.COLORS.GRID.PRIMARY,
            CONSTANTS.COLORS.GRID.SECONDARY
        );
        gridHelper.position.y = CONSTANTS.GRID.Y_OFFSET;
        this.scene.add(gridHelper);
    }

    initDrawingGroup() {
        this.drawingGroup = new THREE.Group();
        this.scene.add(this.drawingGroup);
    }

    setupEventListeners() {
        this.controls.setup(this);
        window.addEventListener('resize', this.onWindowResize.bind(this));
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    startAnimation() {
        const animate = () => {
            requestAnimationFrame(animate);
            this.renderer.render(this.scene, this.camera);
        };
        animate();
    }

    updateScene(rawData) {
        // APIからのレスポンスデータを変換
        const data = rawData.data;
        
        if (!this.validateData(data)) return;
    
        const bounds = this.calculateBounds(data);
        this.updateDrawingGroup(data, bounds);
    
        // center_x, center_y, center_zを使用して中心点を設定
        this.currentCenter.set(
            rawData.data.center_x,
            rawData.data.center_y,
            rawData.data.center_z
        );
    
        this.updateCameraPosition(bounds);
    }

    validateData(data) {
        return data && data.draw_lines && data.draw_lines.length > 0;
    }

    calculateBounds(data) {
        const bounds = {
            min: new THREE.Vector3(Infinity, Infinity, Infinity),
            max: new THREE.Vector3(-Infinity, -Infinity, -Infinity)
        };

        data.draw_lines.forEach(line => {
            line.positions.forEach(pos => {
                bounds.min.x = Math.min(bounds.min.x, pos.x);
                bounds.min.y = Math.min(bounds.min.y, pos.y);
                bounds.min.z = Math.min(bounds.min.z, pos.z);
                bounds.max.x = Math.max(bounds.max.x, pos.x);
                bounds.max.y = Math.max(bounds.max.y, pos.y);
                bounds.max.z = Math.max(bounds.max.z, pos.z);
            });
        });

        return bounds;
    }

    updateDrawingGroup(data, bounds) {
        // Clear existing lines
        while (this.drawingGroup.children.length > 0) {
            this.drawingGroup.remove(this.drawingGroup.children[0]);
        }
    
        // Update center
        this.currentCenter.set(
            (bounds.min.x + bounds.max.x) / 2,
            (bounds.min.y + bounds.max.y) / 2,
            (bounds.min.z + bounds.max.z) / 2
        );
        this.drawingGroup.position.copy(this.currentCenter);
    
        // Create lines using BufferGeometry for better performance
        const lines = this.createLines(data);
        lines.forEach(line => this.drawingGroup.add(line));
    }

    createLines(data) {
        return data.draw_lines.map(line => {
            const points = line.positions.map(pos => 
                new THREE.Vector3(
                    pos.x - this.currentCenter.x,  // Xはそのまま
                    pos.z - this.currentCenter.z,  // クライアント側のZをThree.jsのYに変換（座標系の違い）
                    - (pos.y - this.currentCenter.y)  // クライアント側のYをThree.jsのZに変換（反転）
                )
            );
    
            const tubes = [];
            const lineWidth = line.width || 0.01; // 線の太さ
    
            // 各線分ごとにチューブを作成
            for (let i = 0; i < points.length - 1; i++) {
                const start = points[i];
                const end = points[i + 1];
                
                const direction = end.clone().sub(start);
                const length = direction.length();
                
                // チューブジオメトリを作成
                const geometry = new THREE.CylinderGeometry(
                    lineWidth / 2, // 上部の半径
                    lineWidth / 2, // 下部の半径
                    length,        // 長さ
                    8             // セグメント数
                );
    
                const material = new THREE.MeshBasicMaterial({
                    color: new THREE.Color(line.color.r, line.color.g, line.color.b)
                });
                
                const tube = new THREE.Mesh(geometry, material);
                
                // チューブを正しい位置と向きに配置
                tube.position.copy(start.clone().add(direction.multiplyScalar(0.5)));
                tube.lookAt(end);
                tube.rotateX(Math.PI / 2);
                
                tubes.push(tube);
            }
            
            // すべてのチューブをグループにまとめる
            const group = new THREE.Group();
            tubes.forEach(tube => group.add(tube));
            return group;
        });
    }

    updateCameraPosition(bounds) {
        const size = new THREE.Vector3(
            bounds.max.x - bounds.min.x,
            bounds.max.y - bounds.min.y,
            bounds.max.z - bounds.min.z
        );
        const maxSize = Math.max(size.x, size.y, size.z);
        const distance = maxSize * 2;

        this.camera.position.set(
            this.currentCenter.x,
            this.currentCenter.y,
            this.currentCenter.z + distance
        );
        this.camera.lookAt(this.currentCenter);

        // Update default position
        CONSTANTS.CAMERA.DEFAULT_POSITION.x = this.currentCenter.x;
        CONSTANTS.CAMERA.DEFAULT_POSITION.y = this.currentCenter.y;
        CONSTANTS.CAMERA.DEFAULT_POSITION.z = this.currentCenter.z + distance;
        CONSTANTS.CAMERA.DEFAULT_POSITION.targetPoint = this.currentCenter.clone();
    }

    resetView() {
        const pos = CONSTANTS.CAMERA.DEFAULT_POSITION;
        const rot = CONSTANTS.CAMERA.DEFAULT_ROTATION;
        
        this.camera.position.set(pos.x, pos.y, pos.z);
        this.camera.rotation.set(rot.x, rot.y, rot.z);
        this.drawingGroup.rotation.set(0, 0, 0);

        if (pos.targetPoint) {
            this.camera.lookAt(pos.targetPoint);
        }
    }
}

// コントロール管理クラス
class ControlsManager {
    constructor() {
        this.isDragging = false;
        this.isRightDragging = false;
        this.previousMousePosition = { x: 0, y: 0 };
    }

    setup(sceneManager) {
        const elem = sceneManager.renderer.domElement;
        
        elem.addEventListener('mousedown', this.onMouseDown.bind(this));
        elem.addEventListener('mousemove', (e) => this.onMouseMove(e, sceneManager));
        elem.addEventListener('mouseup', this.onMouseUp.bind(this));
        elem.addEventListener('wheel', (e) => this.onWheel(e, sceneManager));
        elem.addEventListener('contextmenu', e => e.preventDefault());
    }

    onMouseDown(e) {
        if (e.button === 0) this.isDragging = true;
        else if (e.button === 2) this.isRightDragging = true;
        this.previousMousePosition = { x: e.offsetX, y: e.offsetY };
    }

    onMouseMove(e, sceneManager) {
        const deltaMove = {
            x: e.offsetX - this.previousMousePosition.x,
            y: e.offsetY - this.previousMousePosition.y
        };

        if (this.isDragging) {
            sceneManager.drawingGroup.rotation.y += deltaMove.x * CONSTANTS.CONTROLS.ROTATION_SPEED;
            sceneManager.drawingGroup.rotation.x += deltaMove.y * CONSTANTS.CONTROLS.ROTATION_SPEED;
        } else if (this.isRightDragging) {
            sceneManager.camera.position.x -= deltaMove.x * CONSTANTS.CONTROLS.MOVEMENT_SPEED;
            sceneManager.camera.position.y += deltaMove.y * CONSTANTS.CONTROLS.MOVEMENT_SPEED;
        }

        this.previousMousePosition = { x: e.offsetX, y: e.offsetY };
    }

    onMouseUp() {
        this.isDragging = false;
        this.isRightDragging = false;
    }

    onWheel(e, sceneManager) {
        e.preventDefault();
        const delta = e.deltaY * CONSTANTS.CONTROLS.ZOOM_SPEED;
        sceneManager.camera.position.z *= (1 + delta);
        sceneManager.camera.position.z = Math.max(CONSTANTS.CONTROLS.MIN_ZOOM, sceneManager.camera.position.z);
    }
}

// 描画データの管理クラス
class DrawingManager {
    static formatDate(timestamp, drawingId) {
        return new Date(timestamp).toLocaleString('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        }) + ` (ID:${drawingId.slice(-4)})`;
    }

    static showError(message) {
        const infoDiv = document.getElementById('info');
        infoDiv.innerHTML = `<span style="color: red;">エラー: ${message}</span>`;
    }

    static async updateDrawingList() {
        try {
            const drawings = await APIClient.getDrawings();
            const select = document.getElementById('drawing-select');
            select.innerHTML = '';
            
            if (!drawings || drawings.length === 0) {
                this.showError('描画データが見つかりません');
                return;
            }

            drawings.forEach(drawing => {
                const option = document.createElement('option');
                option.value = drawing.drawing_id;
                
                const timestamp = this.formatDate(
                    drawing.draw_timestamp || drawing.created_at,
                    drawing.drawing_id
                );
                const status = drawing.shape_id ? '✓ AI判定済み' : '';

                option.textContent = `${timestamp} ${status}`;
                select.appendChild(option);
            });
            
            if (drawings.length > 0) {
                await this.loadDrawing(drawings[0].drawing_id);
            }
        } catch (error) {
            this.showError(error.message);
            console.error('Error updating drawing list:', error);
        }
    }

    static async loadDrawing(id) {
        if (!id) return;
        
        try {
            const drawing = await APIClient.getDrawing(id);
            
            // シーンの更新
            window.sceneManager.updateScene({ data: drawing });
    
            // カメラビューをリセット
            window.sceneManager.resetView();
    
            // AI処理結果の表示
            if (drawing.shape_id) {
                this.showAIResult(drawing);
            }
        } catch (error) {
            this.showError(error.message);
            console.error('Error loading drawing:', error);
        }
    }

    static showAIResult(drawing) {
        const infoDiv = document.getElementById('info');
        infoDiv.innerHTML = '3D Drawing Viewer - 左ドラッグ:回転 / 右ドラッグ:移動 / ホイール:拡大縮小';
        // if (drawing.success && drawing.shape_id) {
        //     infoDiv.innerHTML += `<br>AI判定: ${drawing.shape_id} (信頼度: ${drawing.score}%)`;
        //     if (drawing.reasoning) {
        //         infoDiv.innerHTML += `<br>理由: ${drawing.reasoning}`;
        //     }
        // } else if (drawing.error_message) {
        //     infoDiv.innerHTML += `<br>エラー: ${drawing.error_message}`;
        // }
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    window.sceneManager = new SceneManager();
    DrawingManager.updateDrawingList();
});

// Event handlers for UI
function loadSelectedDrawing() {
    const select = document.getElementById('drawing-select');
    DrawingManager.loadDrawing(select.value);
}

function resetView() {
    window.sceneManager.resetView();
}